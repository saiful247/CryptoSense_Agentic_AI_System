import os, requests
from typing import Dict, Any, Optional

CMC_BASE = "https://pro-api.coinmarketcap.com/v1"
CMC_KEY = os.getenv("COINMARKETCAP_API_KEY", "")

class PriceAdapter:
    def cmc_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not CMC_KEY:
            return None
        try:
            r = requests.get(
                f"{CMC_BASE}/cryptocurrency/quotes/latest",
                params={"symbol": symbol.upper()},
                headers={"X-CMC_PRO_API_KEY": CMC_KEY},
                timeout=15
            )
            r.raise_for_status()
            j = r.json().get("data", {}).get(symbol.upper())
            if not j:
                return None
            q = j.get("quote", {}).get("USD", {})
            return {
                "price": q.get("price"),
                "market_cap": q.get("market_cap"),
                "volume_24h": q.get("volume_24h"),
                "name": j.get("name"),
                "symbol": j.get("symbol"),
                "source": "coinmarketcap"
            }
        except Exception:
            return None
