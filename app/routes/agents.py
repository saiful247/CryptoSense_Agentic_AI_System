from fastapi import APIRouter, HTTPException, Request, status
from app.agents.graphDownloadAgent import getCryptoStats

router = APIRouter()


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
