import json
from fastapi import APIRouter, Request
from app.agents.news_portfolio.NewsAgent import cryptoNewsTool
from app.agents.news_portfolio.portfolioAgent import run_portfolio_agent
from app.schemas.schemas import NewsRequest, PortfolioRequest

router = APIRouter()


@router.post("/news")
async def get_news(query: NewsRequest):
    data = cryptoNewsTool(query.query)
    return data


@router.post("/portfolio")
async def portfolio_endpoint(request: Request):
    try:
        # Try to parse JSON
        data = await request.json()
        if isinstance(data, dict):
            # Convert JSON to plain text lines
            holdings_text = "\n".join([f"{k} {v}" for k, v in data.items()])
        else:
            holdings_text = str(data)
    except Exception:
        # If JSON parsing fails, assume raw text input
        holdings_text = await request.body()
        holdings_text = holdings_text.decode("utf-8")

    result = run_portfolio_agent(holdings_text)
    return result
