import os, requests
from typing import Dict, Any, Optional

ETHERSCAN = "https://api.etherscan.io/api"
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY", "")

def etherscan_contract_source(address: str) -> Optional[Dict[str, Any]]:
    if not ETHERSCAN_KEY:
        return None
    try:
        r = requests.get(
            ETHERSCAN,
            params={
                "module": "contract",
                "action": "getsourcecode",
                "address": address,
                "apikey": ETHERSCAN_KEY,
            },
            timeout=15
        )
        r.raise_for_status()
        res = r.json().get("result", [])
        if not res:
            return None
        row = res[0]
        return {
            "is_verified": bool(row.get("SourceCode")),
            "compiler": row.get("CompilerVersion"),
            "contract_name": row.get("ContractName"),
            "source_len": len(row.get("SourceCode") or ""),
            "license": row.get("LicenseType"),
            "data_source": "etherscan",
        }
    except Exception:
        return None
