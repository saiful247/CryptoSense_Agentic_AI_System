import os, json, time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from web3 import Web3

from app.auth.deps import require_bearer
from app.schemas.risk import RiskCheckIn
from app.agents.risk_guard import (
    create_risk_guard_agent, check_url, check_contract, check_token
)
from app.agents.history_agent import history_log, history_nearest_probe
from app.services.adapters.contract_adapter import etherscan_contract_source
from app.services.adapters.urlrep_adapter import google_safe_browsing_check

router = APIRouter(prefix="/risk", tags=["Risk & Health"])

risk_agent = create_risk_guard_agent()
HISTORY_ENABLED = os.getenv("HISTORY_ENABLED", "1").lower() not in ("0","false","no")
HISTORY_SIM_THRESHOLD = float(os.getenv("HISTORY_SIM_THRESHOLD", "0.25"))

_SUSPICIOUS_WORDS = [
    "giveaway","airdrop","double your","send me","private key",
    "seed phrase","guaranteed profit","100x","whitelist now",
    "urgent","limited time","free mint","claim reward",
]

def _norm(v: Optional[str]) -> Optional[str]:
    v = (v or "").strip()
    return None if v in ("", "string") else v

def _generate_with_retry(agent, prompt: str, attempts: int = 3, base_sleep: float = 0.8):
    last = None
    for i in range(attempts):
        try:
            out = agent.generate_reply(messages=[{"role":"user","content":prompt}])
            return str(out), None
        except Exception as e:
            last = e; time.sleep(base_sleep * (2**i))
    return "", (f"{type(last).__name__}: {last}" if last else "UnknownError")

def _bump_for_blurb(res: Dict[str, Any], blurb: Optional[str]) -> Dict[str, Any]:
    if not blurb: return res
    low = blurb.lower()
    hits = [w for w in _SUSPICIOUS_WORDS if w in low]
    if not hits: return res
    res.setdefault("reasons", []); res.setdefault("score", 0)
    bump = min(10, 2*len(hits))
    res["reasons"].append(f"Marketing copy contains suspicious terms: {', '.join(hits[:5])}")
    res["score"] = min(100, int(res["score"]) + bump)
    s = int(res["score"]); res["risk"] = "low" if s < 30 else ("medium" if s < 60 else "high")
    return res

def _history_probe_and_merge(findings: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"matches": []}
    if not HISTORY_ENABLED: return out
    kind = findings.get("kind")
    value = findings.get("url") or findings.get("symbol") or findings.get("address")
    reasons: List[str] = findings.get("reasons") or []
    if not kind or not value: return out
    try:
        matches = history_nearest_probe(str(kind), str(value), reasons) or []
        out["matches"] = matches
        findings.setdefault("sources", {}); findings["sources"]["history"] = matches
        close = [m for m in matches if (m.get("distance") is None or m["distance"] <= HISTORY_SIM_THRESHOLD)]
        if close:
            meta = (close[0] or {}).get("meta") or {}
            reason = f"History: similar to a previous {meta.get('kind')}='{meta.get('input')}' ({str(meta.get('risk','?')).upper()} risk, score {meta.get('score','?')})"
            findings.setdefault("reasons", []).insert(0, reason)
    except Exception:
        pass
    return out

def _route_and_run(url: Optional[str], symbol: Optional[str], address: Optional[str], blurb: Optional[str]) -> Dict[str, Any]:
    if url:     return _bump_for_blurb(check_url(url=url), blurb)
    if address: return _bump_for_blurb(check_contract(address=address), blurb)
    if symbol:  return _bump_for_blurb(check_token(symbol=symbol), blurb)
    raise HTTPException(400, detail="Provide at least one of url | symbol | address | blurb")

@router.post("/check", dependencies=[Depends(require_bearer)])
def risk_check(payload: RiskCheckIn):
    url, symbol, address, blurb = map(_norm, [payload.url, payload.symbol, payload.address, payload.blurb])
    result_json = _route_and_run(url, symbol, address, blurb)

    history_out = _history_probe_and_merge(result_json)
    try: history_log(result_json)
    except Exception: pass

    summary_prompt = (
        "Format the following risk findings into a short summary.\n"
        "Include: Risk Level, Score, Reasons, and Recommended Actions.\n\n"
        f"{json.dumps(result_json, ensure_ascii=False)}"
    )
    summary, _ = _generate_with_retry(risk_agent, summary_prompt)
    return {"agent":"RiskGuard","raw":result_json,"summary":summary,"history":history_out}

# -------------------------
# Health (under /risk/*)
# -------------------------
def _startup_checks() -> dict:
    out = {
        "ETHERSCAN_API_KEY_set": bool(os.getenv("ETHERSCAN_API_KEY")),
        "COINMARKETCAP_API_KEY_set": bool(os.getenv("COINMARKETCAP_API_KEY")),
        "GOOGLE_SAFE_BROWSING_API_KEY_set": bool(os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")),
        "WEB3_RPC_URL_set": bool(os.getenv("WEB3_RPC_URL")),
        "web3_connected": False,
        "chain_id": None,
        "web3_error": None,
    }
    try:
        w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_RPC_URL", "")))
        out["web3_connected"] = w3.is_connected()
        if out["web3_connected"]:
            out["chain_id"] = w3.eth.chain_id
            _ = w3.eth.block_number
    except Exception as e:
        out["web3_error"] = str(e)
    return out

@router.get("/health")
def health():
    return {"ok": True, "service": "crypto-agents-api"}

@router.get("/health/keys")
def health_keys():
    c = _startup_checks()
    return {
        "ETHERSCAN_API_KEY_set": c["ETHERSCAN_API_KEY_set"],
        "COINMARKETCAP_API_KEY_set": c["COINMARKETCAP_API_KEY_set"],
        "GOOGLE_SAFE_BROWSING_API_KEY_set": c["GOOGLE_SAFE_BROWSING_API_KEY_set"],
        "WEB3_RPC_URL_set": c["WEB3_RPC_URL_set"],
    }

@router.get("/health/chain")
def health_chain():
    c = _startup_checks()
    return {"web3_connected": c["web3_connected"], "chain_id": c["chain_id"], "web3_error": c["web3_error"]}

@router.get("/ping")
def ping():
    return {"ok": True}

# -------------------------
# Debug (under /risk/debug/*)
# -------------------------
@router.get("/debug/etherscan/{address}", dependencies=[Depends(require_bearer)])
def debug_etherscan(address: str):
    return etherscan_contract_source(address)

@router.get("/debug/gsb", dependencies=[Depends(require_bearer)])
def debug_gsb(url: str = Query(..., description="URL to check with Google Safe Browsing")):
    return google_safe_browsing_check(url)
