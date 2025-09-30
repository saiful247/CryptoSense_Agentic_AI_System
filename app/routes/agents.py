import json
from fastapi import APIRouter, HTTPException, Request, status, Depends
from app.agents.graphDownloadAgent import getCryptoStats
from app.agents.cryptoPriceAgent import getCoinPriceData
from app.auth.auth import get_current_user

from app.schemas.schemas import CryptoAdvicerResponse, UserRequest, CryptoAdvice, EstimatedReturns
from app.agents.graph import build_graph

router = APIRouter()

graph_executor = build_graph()


@router.post("/get-finance-advice")
async def get_finance_advice(request: UserRequest, current_user: dict = Depends(get_current_user)):
    print("***Entering to get get-finance-advice...***")
    state = {"input": request.dict()}

    print("Initial State in get-finance-advice: ", state)

    result = await graph_executor.ainvoke(state)
    print("Final Result in get-finance-advice: ", result)

    final_advice_raw = result.get("final_advice", {})
    final_return_amount_raw = result.get("estimated_return_usd", {})

    try:
        final_advice = CryptoAdvice(**final_advice_raw)
        estimated_returns = EstimatedReturns(**final_return_amount_raw)

    except Exception as e:
        print("Error in parsing to pydantic model: ", str(e))
        final_advice_raw = {"Error": str(e)}

    return CryptoAdvicerResponse(
        advice=final_advice,
        estimated_returns=estimated_returns
    )


@router.post("/get-crypto-graph")
async def get_crypto_graph(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query parameter is required")

    try:
        image_url = getCryptoStats(query)
        return {"status": "success", "image_url": image_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/get-crypto-price")
async def get_crypto_price(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query parameter is required")

    try:
        price_data = getCoinPriceData(query)
        # The response is coming as a JSON string, so we need to parse it
        if isinstance(price_data, str):
            price_data = json.loads(price_data)
        return price_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
