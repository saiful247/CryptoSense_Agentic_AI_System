# app/services/threatintel_adapter.py

#“The Threat Intel Adapter connects to public scam databases like CryptoScamDB and OpenPhish. 
# It checks whether a website or wallet address is already reported as fraudulent and returns that information to the RiskGuard or Blockchain agents.
#  This helps the system flag known phishing sites and scam tokens instantly.”

import os, time, csv, io, re, requests
from typing import Dict, Any, Optional

CSDB_DOMAINS_URL = os.getenv("CSDB_DOMAINS_URL", "https://cryptoscamdb.org/api/scams")  # JSON index (fallback if changed)
OPENPHISH_FEED_URL = os.getenv("OPENPHISH_FEED_URL", "https://openphish.com/feed.txt")

_cache: Dict[str, Any] = {"csdb": {"ts": 0, "domains": set(), "addresses": set()},
                          "openphish": {"ts": 0, "domains": set()}}

def _domain_from_url(url: str) -> Optional[str]:
    try:
        m = re.search(r"https?://([^/]+)", url, re.IGNORECASE)
        host = m.group(1).lower() if m else url.lower()
        return host.split(":")[0]
    except Exception:
        return None

def _refresh_csdb(force=False):
    now = time.time()
    if not force and now - _cache["csdb"]["ts"] < 3600:
        return
    try:
        r = requests.get(CSDB_DOMAINS_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
        domains, addrs = set(), set()
        # CryptoScamDB API formats have varied over time; try best-effort parse
        # Expect items under "result" or "scams"
        items = data.get("result") or data.get("scams") or data
        if isinstance(items, list):
            for it in items:
                for d in (it.get("domain") or it.get("domains") or []):
                    domains.add(str(d).lower())
                for a in (it.get("addresses") or []):
                    for chain, arr in a.items():
                        for addr in arr:
                            addrs.add(str(addr).lower())
        elif isinstance(items, dict):
            # sometimes keyed by id
            for _, it in items.items():
                for d in (it.get("domain") or it.get("domains") or []):
                    domains.add(str(d).lower())
                for a in (it.get("addresses") or []):
                    for chain, arr in a.items():
                        for addr in arr:
                            addrs.add(str(addr).lower())
        _cache["csdb"] = {"ts": now, "domains": domains, "addresses": addrs}
    except Exception:
        # keep old cache
        pass

def _refresh_openphish(force=False):
    now = time.time()
    if not force and now - _cache["openphish"]["ts"] < 1800:
        return
    try:
        r = requests.get(OPENPHISH_FEED_URL, timeout=20)
        r.raise_for_status()
        domains = set()
        for line in r.text.splitlines():
            d = _domain_from_url(line.strip())
            if d:
                domains.add(d)
        _cache["openphish"] = {"ts": now, "domains": domains}
    except Exception:
        pass

def ti_check_url(url: str) -> Dict[str, Any]:
    out = {"hits": [], "sources": []}
    d = _domain_from_url(url or "")
    if not d:
        return out
    _refresh_csdb(); _refresh_openphish()
    if d in _cache["csdb"]["domains"]:
        out["hits"].append({"source": "CryptoScamDB", "domain": d})
        out["sources"].append("cryptoscamdb")
    if d in _cache["openphish"]["domains"]:
        out["hits"].append({"source": "OpenPhish", "domain": d})
        out["sources"].append("openphish")
    return out

def ti_check_address(addr: str) -> Dict[str, Any]:
    out = {"hits": [], "sources": []}
    _refresh_csdb()
    a = (addr or "").lower()
    if a in _cache["csdb"]["addresses"]:
        out["hits"].append({"source": "CryptoScamDB", "address": a})
        out["sources"].append("cryptoscamdb")
    return out
