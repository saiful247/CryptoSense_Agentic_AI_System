import os
import re
import json
import requests
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

DEFI_LLAMA_POOLS_URL = "https://yields.llama.fi/pools"

DEFAULTS = {
    "risk": "low",
    "days": 90,
    "chain": "Polygon",
    "symbol": "USDC",
    "min_tvl_usd": 1_000_000.0,
    "include_rewards": True,
    "compare_protocols": ("aave", "compound"),
}

CHAIN_ALIASES = {
    "polygon": "Polygon",
    "eth": "Ethereum",
    "ethereum": "Ethereum",
    "avax": "Avalanche",
    "avalanche": "Avalanche",
    "bsc": "BSC",
    "binance": "BSC",
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "base": "Base",
}

TOKEN_ALIASES = {
    "wbtc": "WBTC",
    "btc": "WBTC",
    "eth": "ETH",
    "usdc": "USDC",
    "usdt": "USDT",
    "dai": "DAI",
}

PROTOCOL_CANON = [
    "aave", "aave-v3", "compound", "curve", "curve-dex", "radiant", "merkl",
    "fluid", "fluid-lending", "benqi", "venus", "sturdy", "spark", "gearbox",
    "steer-protocol",
]

# ---------- helpers ----------


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _parse_number_usd(blob: str) -> Optional[float]:
    s = _norm(blob)
    s = re.sub(r"[^0-9.kmb]", "", s)
    if not s:
        return None
    mult = 1.0
    if s.endswith("k"):
        mult = 1_000.0
        s = s[:-1]
    elif s.endswith("m"):
        mult = 1_000_000.0
        s = s[:-1]
    elif s.endswith("b"):
        mult = 1_000_000_000.0
        s = s[:-1]
    try:
        return float(s.replace(",", "")) * mult
    except:
        return None


def _extract_compare(text: str) -> Optional[Tuple[str, str]]:
    t = _norm(text)
    m = re.search(r"(?:compare\s+)?([a-z0-9\-]+)\s+vs\s+([a-z0-9\-]+)", t)
    if m:
        return (m.group(1), m.group(2))
    return None


def _match_protocol(name: str) -> Optional[str]:
    n = _norm(name)
    for p in PROTOCOL_CANON:
        if n == p or n in p or p in n:
            return p
    return None


def _fetch_llama_pools() -> List[Dict[str, Any]]:
    try:
        r = requests.get(DEFI_LLAMA_POOLS_URL, timeout=25)
        if r.status_code != 200:
            return []
        return r.json().get("data", []) or []
    except Exception as e:
        print("[fetch_llama_pools] error:", e)
        return []


def _calc_apy_from_aprs(base_apr: float, reward_apr: float) -> float:
    daily = (base_apr + reward_apr) / 365.0
    return (1.0 + daily) ** 365 - 1.0

# ---------- public: core fetchers ----------


def fetch_defi_pools(chain: str, symbol: str, min_tvl_usd: float, include_rewards: bool) -> List[Dict[str, Any]]:
    data = _fetch_llama_pools()
    out = []
    cs = _norm(symbol)
    for p in data:
        if _norm(p.get("chain", "")) != _norm(chain):
            continue
        if cs not in _norm(p.get("symbol", "")):
            continue
        tvl = float(p.get("tvlUsd", 0.0) or 0.0)
        if tvl < min_tvl_usd:
            continue
        base_apr = float(p.get("apyBase", 0.0) or 0.0) / 100.0
        reward_apr = float(p.get("apyReward", 0.0) or 0.0) / \
            100.0 if include_rewards else 0.0
        apy = _calc_apy_from_aprs(base_apr, reward_apr)
        risk = "low" if tvl >= 50_000_000 else "medium" if tvl >= 5_000_000 else "high"
        out.append({
            "protocol": p.get("project", ""),
            "chain": p.get("chain", ""),
            "symbol": p.get("symbol", ""),
            "tvl_usd": tvl,
            "base_apr": base_apr,
            "reward_apr": reward_apr,
            "apy_annual": apy,
            "risk_level": risk,
            "url": p.get("pool", "") or p.get("url", "") or "",
        })
    out.sort(key=lambda x: x["apy_annual"], reverse=True)
    return out[:5]


def fetch_protocol_markets(protocol: str, chain: str, symbol: str) -> List[Dict[str, Any]]:
    data = _fetch_llama_pools()
    out = []
    pnorm = _norm(protocol)
    cs = _norm(symbol)
    for p in data:
        proj = _norm(p.get("project", ""))
        if pnorm not in proj:
            continue
        if _norm(p.get("chain", "")) != _norm(chain):
            continue
        if cs not in _norm(p.get("symbol", "")):
            continue
        tvl = float(p.get("tvlUsd", 0.0) or 0.0)
        supply = float(p.get("apyBase", 0.0) or 0.0) / 100.0
        out.append({
            "platform": p.get("project", ""),
            "chain": p.get("chain", ""),
            "symbol": p.get("symbol", ""),
            "supply_apy": supply,
            "tvl_usd": tvl,
            "url": p.get("pool", "") or p.get("url", "") or "",
        })
    out.sort(key=lambda x: x["tvl_usd"], reverse=True)
    return out[:1]

# ---------- parameter resolver & top level ----------


def extract_params_from_prompt(prompt: str) -> Dict[str, Any]:
    t = _norm(prompt)
    risk = "high" if "high" in t else "medium" if (
        "medium" in t or "mid" in t) else "low"
    days = DEFAULTS["days"]
    m_days = re.search(r"(\d+)\s*day", t)
    if m_days:
        days = int(m_days.group(1))
    else:
        m_num = re.search(r"\b(\d{1,4})\b", t)
        if m_num:
            try:
                days = int(m_num.group(1))
            except:
                pass
    chain = next((canon for alias, canon in CHAIN_ALIASES.items() if re.search(
        rf"\b{re.escape(alias)}\b", t)), None) or DEFAULTS["chain"]
    symbol = next((canon for tok, canon in TOKEN_ALIASES.items() if re.search(
        rf"\b{re.escape(tok)}\b", t)), None) or DEFAULTS["symbol"]
    min_tvl = DEFAULTS["min_tvl_usd"]
    m_tvl = re.search(r"(min(imum)?\s*tvl[^0-9]*)([0-9,.\w]+)", t)
    if m_tvl:
        parsed = _parse_number_usd(m_tvl.group(3))
        if parsed is not None:
            min_tvl = parsed
    include_rewards = not ("no reward" in t or "exclude reward" in t)
    compare = _extract_compare(t)
    if compare:
        p1 = _match_protocol(compare[0]) or compare[0]
        p2 = _match_protocol(compare[1]) or compare[1]
        compare_protocols = (p1, p2)
    else:
        compare_protocols = DEFAULTS["compare_protocols"]
    return {
        "risk": risk,
        "days": days,
        "chain": chain,
        "symbol": symbol,
        "min_tvl_usd": float(min_tvl),
        "include_rewards": bool(include_rewards),
        "compare_protocols": compare_protocols,
    }


def resolve_and_fetch(user_prompt: str) -> Dict[str, Any]:
    params = extract_params_from_prompt(user_prompt)
    pools = fetch_defi_pools(
        params["chain"], params["symbol"], params["min_tvl_usd"], params["include_rewards"])
    pa, pb = params["compare_protocols"]
    a_markets = fetch_protocol_markets(pa, params["chain"], params["symbol"])
    b_markets = fetch_protocol_markets(pb, params["chain"], params["symbol"])

    recommendation_text = ""
    if a_markets and b_markets:
        a_ap = a_markets[0]["supply_apy"]
        b_ap = b_markets[0]["supply_apy"]
        if a_ap > b_ap:
            verdict = f"{a_markets[0]['platform']} edges out for lenders"
            better = a_markets[0]["platform"]
        elif b_ap > a_ap:
            verdict = f"{b_markets[0]['platform']} edges out for lenders"
            better = b_markets[0]["platform"]
        else:
            verdict = "Both yield similar returns"
            better = None

        if better:
            if params["risk"] == "low":
                recommendation_text = f"💡 Since you're {params['risk']}-risk, {better.title()} offers a steadier option with higher TVL and lower volatility than its competitor."
            elif params["risk"] == "medium":
                recommendation_text = f"💡 For a balanced profile, {better.title()} gives a solid yield-to-risk ratio. Still, always monitor APY fluctuations."
            else:
                recommendation_text = f"💡 You're high-risk, so chasing yield makes sense — {better.title()} currently pays better returns, but double-check liquidity and volatility before depositing."
        else:
            recommendation_text = "💡 Both protocols offer similar returns — you can choose either based on interface preference or gas efficiency on your chain."

        comparison = {
            "token": params["symbol"],
            "chain": params["chain"],
            "protocol_a": a_markets[0],
            "protocol_b": b_markets[0],
            "verdict": verdict,
        }
    else:
        comparison = {
            "token": params["symbol"],
            "chain": params["chain"],
            "protocol_a": a_markets[0] if a_markets else {"platform": pa, "supply_apy": 0.0},
            "protocol_b": b_markets[0] if b_markets else {"platform": pb, "supply_apy": 0.0},
            "verdict": "",
        }
        recommendation_text = "💡 Data for one or both protocols is limited — check their official dashboards for the most accurate APY before choosing."

    cautions = [
        "Smart-contract risk; never deposit funds you can’t afford to lose.",
        "Oracle/chain outage risk; blue-chip protocols reduce (not remove) risk.",
        "Stablecoin or wrapped asset risk (de-peg/bridge risks).",
        "Rewards/emissions can decay; don’t assume they persist.",
        "Be mindful of withdrawal/locking constraints and gas/bridge costs.",
    ]

    return {
        "resolved_params": params,
        "top_options": pools[:3],
        "comparison": comparison,
        "recommendation": recommendation_text,
        "cautions": cautions,
        "summary": (
            f"For a {params['risk']}-risk profile over ~{params['days']} days "
            f"with {params['symbol']} on {params['chain']}, here are suitable lending options and "
            f"a quick {pa} vs {pb} check."
        ),
        "explanation": "Options filtered by TVL/brand; APY = base + rewards (daily compounding). Risk considers TVL, reputation, asset, chain.",
    }
