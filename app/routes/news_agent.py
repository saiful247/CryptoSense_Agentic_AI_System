from fastapi import APIRouter, HTTPException
from app.agents.news_agent.newsAgent import run_news_agent

router = APIRouter(prefix="/news", tags=["Crypto News Agent"])

@router.post("/")
def get_news(data: dict):
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")

    result = run_news_agent(query)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
