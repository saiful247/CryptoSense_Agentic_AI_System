from fastapi import APIRouter, Depends
from app.auth.deps import require_bearer
from app.schemas.risk import LearnIn
from app.agents.learning_agent import create_learning_agent

router = APIRouter(prefix="/learn", tags=["Learning"])

agent = create_learning_agent()

@router.post("/explain", dependencies=[Depends(require_bearer)])
def explain(payload: LearnIn):
    prompt = f"Explain {payload.topic} at {payload.level} level with examples={payload.examples}."
    reply = agent.generate_reply(messages=[{"role":"user","content":prompt}])
    return {"agent":"LearningAgent","result": str(reply)}
