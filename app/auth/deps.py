# app/auth/deps.py
import os
from typing import Optional
from fastapi import Header, HTTPException

def require_bearer(authorization: Optional[str] = Header(None)) -> bool:
    expected = os.getenv("API_BEARER_TOKEN", "").strip()
    if expected:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")
        if authorization.split(" ", 1)[1] != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")
    return True
