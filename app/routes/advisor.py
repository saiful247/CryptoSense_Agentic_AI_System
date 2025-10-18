from fastapi import APIRouter, Depends
from app.auth.deps import require_bearer
from app.schemas.risk import AdvisorIn
from app.agents.advisor_agent import advise_next_steps, create_advisor_agent

router = APIRouter(prefix="/advisor", tags=["Advisor"])

_ = create_advisor_agent()

@router.post("/advise", dependencies=[Depends(require_bearer)])
def advise(payload: AdvisorIn):
    combined = {
        "riskguard": payload.riskguard or {},
        "blockchain": payload.blockchain or {},
    }
    return advise_next_steps(combined)
