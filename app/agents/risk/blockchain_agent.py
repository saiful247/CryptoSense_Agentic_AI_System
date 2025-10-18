

# app/agents/blockchain_agent.py
import os
import math
import time
from typing import Dict, Any, Optional, List

import requests
from web3 import Web3
from autogen import ConversableAgent
from app.agents.risk.common import AUTOGEN_CONFIG_LIST, clamp, optional_env

# ------------------------------------------------------------------
# 🔑 Configuration
# ------------------------------------------------------------------
ETHERSCAN_API = "https://api.etherscan.io/api"
ETHERSCAN_KEY = optional_env("ETHERSCAN_API_KEY", "")
DEXSCREENER_TOKEN_API = "https://api.dexscreener.com/latest/dex/tokens/{address}"
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "")

# Connect to Ethereum via Alchemy or Infura
try:
    w3 = Web3(Web3.HTTPProvider(WEB3_RPC_URL))
except Exception:
    w3 = None


# ------------------------------------------------------------------
# 🌐 Utility Functions
# ------------------------------------------------------------------
def _get(url: str, params: Dict[str, Any], timeout: float = 15.0) -> Optional[Dict[str, Any]]:
    """Helper for GET requests with safe error handling."""
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def _looks_like_evm(address: str) -> bool:
    """Check if the input is a valid Ethereum-style address."""
    return isinstance(address, str) and address.startswith("0x") and len(address) == 42


def _risk_bucket(score: int) -> str:
    """Map numeric score to human risk label."""
    return "low" if score < 30 else ("medium" if score < 60 else "high")


# ------------------------------------------------------------------
# 🔍 Etherscan Contract Metadata
# ------------------------------------------------------------------
def _contract_source_meta(address: str) -> Dict[str, Any]:
    """Fetch contract verification + detect risky functions via Etherscan."""
    reasons: List[str] = []
    flags: List[str] = []

    if not ETHERSCAN_KEY:
        return {"verified": None, "flags": flags, "reasons": ["Etherscan API key missing"]}

    meta = _get(
        ETHERSCAN_API,
        {"module": "contract", "action": "getsourcecode", "address": address, "apikey": ETHERSCAN_KEY},
    ) or {}

    if (meta.get("status") or "") != "1":
        return {"verified": None, "flags": flags, "reasons": ["Etherscan source unavailable or invalid response"]}

    result = (meta.get("result") or [{}])[0]
    verified = (result.get("SourceCode") or "") != ""
    reasons.append("Etherscan: source verified" if verified else "Etherscan: NOT verified")

    source_text = (result.get("SourceCode") or "").lower()
    # Quick scan for risky functions
    keywords = [
        ("mint", "mintable"),
        ("pause()", "pausable"),
        ("blacklist", "blacklist"),
        ("setTax", "tax_changeable"),
        ("onlyOwner", "owner_role"),
        ("transferOwnership", "owner_transfer"),
    ]
    for needle, tag in keywords:
        if needle.lower() in source_text and tag not in flags:
            flags.append(tag)

    return {"verified": verified, "flags": flags, "reasons": reasons}


# ------------------------------------------------------------------
# 💧 Dexscreener Liquidity Snapshot
# ------------------------------------------------------------------
def _dex_liquidity_snapshot(address: str) -> Optional[Dict[str, Any]]:
    """Get quick liquidity and price data from Dexscreener."""
    try:
        url = DEXSCREENER_TOKEN_API.format(address=address)
        r = requests.get(url, timeout=15)
        if not r.ok:
            return None
        js = r.json()
        pairs = js.get("pairs") or []
        if not pairs:
            return None
        best = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
        return {
            "dex": best.get("dexId"),
            "pair": best.get("pairAddress"),
            "base": best.get("baseToken", {}).get("symbol"),
            "quote": best.get("quoteToken", {}).get("symbol"),
            "liquidity_usd": float(best.get("liquidity", {}).get("usd", 0) or 0),
            "fdv_usd": float(best.get("fdv", 0) or 0),
            "price_usd": float(best.get("priceUsd", 0) or 0),
            "chain": best.get("chainId"),
        }
    except Exception:
        return None


# ------------------------------------------------------------------
# 🧠 Web3 Live On-chain Insights (Alchemy)
# ------------------------------------------------------------------
def _web3_live_info(address: str) -> Dict[str, Any]:
    """Check live blockchain info — owner, bytecode, and token balance."""
    info = {}
    if not w3 or not w3.is_connected():
        return {"connected": False, "reasons": ["Web3 RPC connection failed (check WEB3_RPC_URL)"]}

    info["connected"] = True
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(address))
        info["bytecode_size"] = len(code.hex()) if code else 0
        info["is_contract"] = len(code) > 0
        if info["is_contract"]:
            info["reasons"] = [f"Contract detected on-chain with bytecode size {info['bytecode_size']} bytes."]
        else:
            info["reasons"] = ["Address has no contract code — likely a wallet."]
    except Exception as e:
        info["reasons"] = [f"Web3 query failed: {e}"]
    return info


# ------------------------------------------------------------------
# ⚙️ Main On-chain Analyzer
# ------------------------------------------------------------------
def analyze_onchain(address: str) -> Dict[str, Any]:
    """Main tool: check verification, privileges, liquidity, and Web3 live data."""
    if not _looks_like_evm(address):
        return {
            "kind": "blockchain",
            "address": address,
            "risk": "high",
            "score": 90,
            "reasons": ["Invalid Ethereum address format"],
            "sources": {},
        }

    reasons: List[str] = []
    subs: List[int] = []
    sources: Dict[str, Any] = {}

    # 1️⃣ Etherscan source
    meta = _contract_source_meta(address)
    sources["etherscan_source"] = meta
    reasons += meta.get("reasons", [])
    for flag in meta.get("flags", []):
        reasons.append(f"Sensitive capability: {flag}")
        subs.append(20)

    # 2️⃣ Dexscreener
    snap = _dex_liquidity_snapshot(address)
    if snap:
        sources["dexscreener"] = snap
        liq = snap.get("liquidity_usd") or 0.0
        if liq < 10_000:
            subs.append(20)
            reasons.append(f"Very low liquidity (${int(liq):,}) on {snap.get('dex')}")
        elif liq < 100_000:
            subs.append(10)
            reasons.append(f"Low liquidity (${int(liq):,}) on {snap.get('dex')}")
        else:
            reasons.append(f"Good liquidity (${int(liq):,}) on {snap.get('dex')}")
    else:
        reasons.append("No DEX liquidity snapshot available.")
        subs.append(5)

    # 3️⃣ Web3 live check (Alchemy)
    live = _web3_live_info(address)
    sources["web3_live"] = live
    if live.get("connected"):
        reasons += live.get("reasons", [])
    else:
        subs.append(5)
        reasons.append("Web3 live connection unavailable (check Alchemy RPC).")

    # Final score
    score = clamp(sum(subs), 0, 100)
    return {
        "kind": "blockchain",
        "address": address,
        "risk": _risk_bucket(score),
        "score": score,
        "reasons": reasons,
        "sources": sources,
    }


# ------------------------------------------------------------------
# 🤖 Create Blockchain Agent
# ------------------------------------------------------------------
def create_blockchain_agent(name: str = "BlockchainAgent") -> ConversableAgent:
    sys_prompt = (
        "You are BlockchainAgent. You perform live on-chain checks for Ethereum contracts and tokens.\n"
        "Use Etherscan for source verification, Dexscreener for liquidity, and Web3 RPC for live code presence.\n"
        "Return concise JSON with fields: kind, address, risk, score, reasons, and sources.\n"
        "Do not ask for keys or give investment advice."
    )
    agent = ConversableAgent(
        name=name,
        system_message=sys_prompt,
        llm_config={"config_list": AUTOGEN_CONFIG_LIST, "temperature": 0.2},
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    agent.register_function({"analyze_onchain": analyze_onchain})
    return agent
