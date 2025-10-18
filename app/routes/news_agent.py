from fastapi import APIRouter
from app.agents.news_agent import run_news_agent

router = APIRouter()

@router.get("/news")
def get_news(query: str):
    return run_news_agent(query)

