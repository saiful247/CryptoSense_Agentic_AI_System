from fastapi import APIRouter, Depends, HTTPException
from app.auth.deps import require_bearer
from app.schemas.risk import BlockchainIn
from app.agents.blockchain_agent import create_blockchain_agent

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])

agent = create_blockchain_agent()

def _looks_like_evm(addr: str) -> bool:
    return isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42

@router.post("/analyze", dependencies=[Depends(require_bearer)])
def analyze(payload: BlockchainIn):
    if not _looks_like_evm(payload.address):
        raise HTTPException(status_code=400, detail="Invalid EVM address format")
    raw = agent.generate_reply(messages=[{
        "role":"user",
        "content": f"Run analyze_onchain(address='{payload.address}') and return JSON."
    }])
    if isinstance(raw, dict) and "content" in raw:
        return raw["content"]
    return raw
