# app/agents/risk_guard.py
import re
from typing import Dict, Any, Optional, List

from autogen import ConversableAgent
from app.agents.risk.common import AUTOGEN_CONFIG_LIST, clamp
from app.adapters.price_adapter import PriceAdapter
from app.adapters.contract_adapter import etherscan_contract_source
from app.adapters.urlrep_adapter import (
    google_safe_browsing_check,
    urlscan_quick_check,
)

# NEW: history + threat intel
from app.agents.risk.history_agent import history_log, history_nearest_probe
from app.adapters.threatintel_adapter import ti_check_url, ti_check_address

# ---------------------- heuristics / helpers ----------------------
SUSPICIOUS_WORDS = [
    "giveaway", "airdrop", "double your", "send me", "private key",
    "seed phrase", "guaranteed profit", "100x", "whitelist now",
    "urgent", "limited time", "free mint", "claim reward",
]

_addr_pat = re.compile(r"0x[a-fA-F0-9]{40}$")
def looks_like_eth_address(s: str) -> bool:
    return bool(_addr_pat.fullmatch(s or ""))

def fuse(scores: List[int]) -> int:
    """Clamp summed subscores into 0..100."""
    return clamp(sum(scores), 0, 100)

_price_singleton: Optional[PriceAdapter] = None
def _price() -> PriceAdapter:
    global _price_singleton
    if _price_singleton is None:
        _price_singleton = PriceAdapter()
    return _price_singleton


# ---------------------- TOOL: URL risk ----------------------
def check_url(url: str = "", **kwargs) -> Dict[str, Any]:
    """
    Screen a URL using Google Safe Browsing + optional URLScan + heuristics
    + threat intel + history similarity. ALWAYS returns a structured dict.

    Aliases supported:
      - link -> url
    """
    # --- argument aliasing ---
    url = kwargs.get("link", url) or url

    reasons: List[str] = []
    subs: List[int] = []
    sources: Dict[str, Any] = {}

    # 1) Google Safe Browsing
    try:
        gsb = google_safe_browsing_check(url)
        if gsb is not None:
            sources["google_safe_browsing"] = gsb
            if gsb.get("flagged"):
                reasons.append("Google Safe Browsing: flagged")
                subs.append(70)
            else:
                reasons.append("Google Safe Browsing: clean")
                subs.append(0)
        else:
            reasons.append("Google Safe Browsing unavailable (no key or error)")
            subs.append(10)
    except Exception as e:
        reasons.append(f"Google Safe Browsing error: {e}")
        subs.append(10)

    # 2) URLScan (optional)
    try:
        us = urlscan_quick_check(url)
        if us is not None:
            sources["urlscan"] = us
            if us.get("submitted"):
                reasons.append("URLScan: submission accepted (view verdict on portal)")
                subs.append(10)
            else:
                reasons.append("URLScan: submission failed or rate-limited")
                subs.append(5)
        else:
            reasons.append("URLScan unavailable (no key or disabled)")
            # no subscore for unavailable
    except Exception as e:
        reasons.append(f"URLScan error: {e}")
        subs.append(5)

    # 3) Light lexical heuristics for phishing-y terms
    low_url = (url or "").lower()
    if any(w in low_url for w in ["bonus", "secure-login", "account-verify", "walletconnect"]):
        reasons.append("URL wording looks phishy (bonus/secure-login/verify/walletconnect)")
        subs.append(15)

    # 4) Threat intel (domains)
    try:
        ti = ti_check_url(url)
        if ti.get("hits"):
            sources["threat_intel"] = ti
            reasons.append("Threat intel: domain matched known phishing/scam feed(s)")
            subs.append(40)  # strong signal
    except Exception:
        pass

    # 5) History similarity (soft bump if very similar to past HIGH-risk)
    try:
        sims = history_nearest_probe("url", url, reasons)
        bumped = False
        for s in sims:
            meta = s.get("meta") or {}
            dist = s.get("distance") or 1.0
            # Chroma returns smaller distance for closer neighbors if enabled
            if meta.get("risk") == "high" and dist is not None and dist <= 0.15:
                reasons.append(f"History: very similar to a previous HIGH-risk item (dist={dist:.2f})")
                subs.append(10)
                bumped = True
                break
    except Exception:
        pass

    total = fuse(subs or [0])
    risk = "low" if total < 30 else ("medium" if total < 60 else "high")

    out = {
        "kind": "url",
        "url": url,
        "risk": risk,
        "score": total,
        "reasons": reasons if reasons else ["No sources available"],
        "sources": sources,
    }

    # 6) log to history (best-effort)
    try:
        history_log(out)
    except Exception:
        pass

    return out


# ---------------------- TOOL: Contract risk ----------------------
def check_contract(address: str = "", symbol: Optional[str] = "", **kwargs) -> Dict[str, Any]:
    """
    Contract-level checks using Etherscan metadata + heuristics
    + threat intel + history similarity. Always returns a structured dict.

    Aliases supported:
      - contract_address -> address
      - token_symbol     -> symbol
    """
    # --- argument aliasing ---
    address = kwargs.get("contract_address", address) or address
    symbol = kwargs.get("token_symbol", symbol) or symbol

    if not looks_like_eth_address(address):
        out = {
            "kind": "contract",
            "address": address,
            "symbol": symbol,
            "risk": "high",
            "score": 85,
            "reasons": ["Invalid EVM address format"],
            "sources": {},
        }
        try:
            history_log(out)
        except Exception:
            pass
        return out

    reasons: List[str] = []
    subs: List[int] = []
    sources: Dict[str, Any] = {}

    # 1) Etherscan metadata / verification
    try:
        es = etherscan_contract_source(address)
        if es is not None:
            sources["etherscan"] = es
            if es.get("is_verified"):
                reasons.append("Etherscan: source verified")
                subs.append(0)
            else:
                reasons.append("Etherscan: NOT verified")
                subs.append(35)
            if (es.get("source_len") or 0) == 0:
                reasons.append("No source code length (empty SourceCode)")
                subs.append(15)
        else:
            reasons.append("Etherscan unavailable or no key; using heuristics")
            subs.append(10)
    except Exception as e:
        reasons.append(f"Etherscan error: {e}")
        subs.append(15)

    # 2) Symbol hype heuristic
    s = (symbol or "").upper()
    if any(k in s for k in ["MOON", "100X", "AI", "GEM", "PEPE", "INU"]) and len(s) <= 5:
        reasons.append("Symbol looks hypey/short")
        subs.append(15)

    # 3) Threat intel (addresses)
    try:
        ti = ti_check_address(address)
        if ti.get("hits"):
            sources["threat_intel"] = ti
            reasons.append("Threat intel: address matched known scam list(s)")
            subs.append(50)  # very strong signal
    except Exception:
        pass

    # 4) History similarity bump
    try:
        sims = history_nearest_probe("contract", address, reasons)
        for s_ in sims:
            meta = s_.get("meta") or {}
            dist = s_.get("distance") or 1.0
            if meta.get("risk") == "high" and dist is not None and dist <= 0.15:
                reasons.append(f"History: similar to previous HIGH-risk contract (dist={dist:.2f})")
                subs.append(10)
                break
    except Exception:
        pass

    total = fuse(subs or [0])
    risk = "low" if total < 30 else ("medium" if total < 60 else "high")

    out = {
        "kind": "contract",
        "address": address,
        "symbol": symbol,
        "risk": risk,
        "score": total,
        "reasons": reasons,
        "sources": sources,
    }

    try:
        history_log(out)
    except Exception:
        pass

    return out


# ---------------------- TOOL: Token risk ----------------------
def check_token(symbol: Optional[str] = "", query: Optional[str] = "", **kwargs) -> Dict[str, Any]:
    """
    Token-level checks using CoinMarketCap quotes + heuristics
    + history similarity. Always returns a structured dict.

    Aliases supported:
      - token_symbol -> symbol
      - q            -> query
    """
    # --- argument aliasing ---
    symbol = kwargs.get("token_symbol", symbol) or symbol
    query = kwargs.get("q", query) or query

    reasons: List[str] = []
    subs: List[int] = []
    sources: Dict[str, Any] = {}

    md = None
    try:
        md = _price().cmc_quotes(symbol) if symbol else None
        if md:
            sources["market_data"] = md
            vol = md.get("volume_24h") or 0
            mcap = md.get("market_cap") or 0
            if vol and mcap:
                ratio = (vol / mcap) if mcap else 0
                if ratio < 0.005:
                    reasons.append("Very low 24h volume relative to market cap")
                    subs.append(25)
                elif ratio < 0.02:
                    reasons.append("Low volume/mcap ratio")
                    subs.append(10)
                else:
                    reasons.append("Healthy-ish activity (by volume/mcap)")
                    subs.append(0)
            else:
                reasons.append("Missing volume/mcap values; limited activity signal")
                subs.append(10)
            reasons.append(f"Data source: {md.get('source')}")
        else:
            reasons.append("No market data (symbol not found or CMC key missing)")
            subs.append(20)
    except Exception as e:
        reasons.append(f"Market data error: {e}")
        subs.append(20)

    # Light heuristic for very short hypey symbols
    s = (symbol or "").upper()
    if s and len(s) <= 4 and any(w in s for w in ["AI", "PEPE", "INU", "MOON"]):
        reasons.append("Symbol looks hype-driven (short/hot keywords)")
        subs.append(10)

    # (Optional future) Threat intel: resolve official contract and check address feed.

    # History similarity bump
    try:
        sims = history_nearest_probe("token", s, reasons)
        for s_ in sims:
            meta = s_.get("meta") or {}
            dist = s_.get("distance") or 1.0
            if meta.get("risk") == "high" and dist is not None and dist <= 0.15:
                reasons.append(f"History: similar to previous HIGH-risk token (dist={dist:.2f})")
                subs.append(8)
                break
    except Exception:
        pass

    total = fuse(subs or [0])
    risk = "low" if total < 30 else ("medium" if total < 60 else "high")

    out = {
        "kind": "token",
        "symbol": symbol,
        "risk": risk,
        "score": total,
        "reasons": reasons,
        "md": md or {},
        "sources": sources,
    }

    try:
        history_log(out)
    except Exception:
        pass

    return out


# ---------------------- Agent factory ----------------------
def create_risk_guard_agent(name: str = "RiskGuard") -> ConversableAgent:
    sys_prompt = (
        "You are RiskGuard, a cautious crypto risk screener.\n"
        "• Decide which tool(s) to call among: check_url, check_contract, check_token.\n"
        "• After tool calls, ALWAYS return a short structured summary:\n"
        "  - **Risk Level:** low | medium | high\n"
        "  - **Risk Score:** 0–100\n"
        "  - **Reasons:** top 3–5 bullets\n"
        "  - **Next Steps:** brief, practical actions\n"
        "If tool results are missing or inconclusive, state 'No data available' but still produce a summary.\n"
        "Never ask for seed phrases or provide investment advice; only risk insights."
    )
    agent = ConversableAgent(
        name=name,
        system_message=sys_prompt,
        llm_config={"config_list": AUTOGEN_CONFIG_LIST, "temperature": 0.2},
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    # ag2 (0.9.9) expects a dict mapping {name: func}
    agent.register_function({"check_url": check_url})
    agent.register_function({"check_contract": check_contract})
    agent.register_function({"check_token": check_token})
    return agent
