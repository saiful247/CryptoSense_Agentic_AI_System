from fastapi import APIRouter, HTTPException
from app.schemas.schemas import AdviseRequest
from app.agents.defi_agent.defi_agent import resolve_and_fetch

router = APIRouter(prefix="/api/defi", tags=["defi"])

def _build_prompt(p: AdviseRequest) -> str:
    days = int((p.duration_months or 3) * 30)
    parts = [
        f"risk {p.risk}",
        f"{days} days",
        f"chain {p.chain}",
        f"token {p.coin}",
        f"minimum tvl {p.min_tvl_usd}",
        "include rewards" if p.include_rewards else "no rewards",
        f"compare {p.compare_protocols[0]} vs {p.compare_protocols[1]}",
    ]
    return " ".join(parts)

def _project_value(amount_usd: float, apy: float, days: int) -> float:
    return round(amount_usd * ((1 + apy) ** (days / 365.0)), 2)

@router.post("/advise")
def advise(req: AdviseRequest):
    try:
        prompt = _build_prompt(req)
        data = resolve_and_fetch(prompt)  # dict, already in your desired JSON shape

        # Optional: projections if amount provided
        if req.amount_usd and data.get("top_options"):
            days = int((req.duration_months or 3) * 30)
            for opt in data["top_options"]:
                apy = float(opt.get("apy_annual", 0.0))
                opt["projected_value_usd"] = _project_value(req.amount_usd, apy, days)

        return {"ok": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"advisor_error: {e}")