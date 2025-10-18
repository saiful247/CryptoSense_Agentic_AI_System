import os
from dotenv import load_dotenv

load_dotenv()

AUTOGEN_CONFIG_LIST = [{
    "model": "gemini-2.5-flash",
    "api_type": "google",
    "api_key": os.environ.get("GEMINI_API_KEY", ""),
}]

def require_env(var: str):
    val = os.getenv(var)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return val

def optional_env(var: str, default: str = ""):
    return os.getenv(var, default)

def sanitize_text(s: str) -> str:
    return (s or "").strip()[:2000]

def clamp(n, lo, hi):
    return max(lo, min(hi, n))
