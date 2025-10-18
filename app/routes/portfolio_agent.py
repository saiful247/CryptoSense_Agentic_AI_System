# routes/portfolio_agents.py
from fastapi import APIRouter, Request
from app.agents.portfolio_agent import run_portfolio_agent

router = APIRouter()

@router.post("/portfolio")
async def analyze_portfolio(request: Request):
    """
    Endpoint to analyze user's crypto portfolio.
    Expects a JSON body like:
      { "holdings": "BTC 1\nETH 2\nADA 100" }
    """
    body = await request.json()
    holdings_text = body.get("holdings", "")
    result = run_portfolio_agent(holdings_text)
    return result
