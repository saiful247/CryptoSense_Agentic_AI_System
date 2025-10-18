import os, requests
from typing import Dict, Any, Optional

GSB_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")
URLSCAN_KEY = os.getenv("URLSCAN_API_KEY", "")

GSB_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

def google_safe_browsing_check(url: str) -> Optional[Dict[str, Any]]:
    if not GSB_KEY:
        return None
    payload = {
        "client": {"clientId": "riskguard", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        r = requests.post(f"{GSB_URL}?key={GSB_KEY}", json=payload, timeout=15)
        r.raise_for_status()
        j = r.json()
        matches = j.get("matches", [])
        if matches:
            return {"flagged": True, "matches": matches, "source": "google_safe_browsing"}
        return {"flagged": False, "source": "google_safe_browsing"}
    except Exception:
        return None

def urlscan_quick_check(url: str) -> Optional[Dict[str, Any]]:
    if not URLSCAN_KEY:
        return None
    try:
        r = requests.post(
            "https://urlscan.io/api/v1/scan/",
            headers={"API-Key": URLSCAN_KEY, "Content-Type": "application/json"},
            json={"url": url, "public": "off"},
            timeout=20
        )
        if r.status_code in (200, 201):
            return {"submitted": True, "source": "urlscan"}
        return {"submitted": False, "source": "urlscan"}
    except Exception:
        return None
