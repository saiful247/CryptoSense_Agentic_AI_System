from fastapi import APIRouter, Request
from app.agents.portfolio_agent.portfolioAgent import run_portfolio_agent

router = APIRouter()

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
