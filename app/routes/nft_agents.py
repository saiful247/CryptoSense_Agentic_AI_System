import json
from fastapi import APIRouter, HTTPException, Request, status, Depends

from app.auth.auth import get_current_user

from app.agents.nft_agents.nft_graph import buildNftGraph
from app.schemas.schemas import NFTRequest, NFTResponse

router = APIRouter()

nft_graph_executer = buildNftGraph()


@router.post("/get-nft-content", response_model=NFTResponse)
async def get_nft_content(request: NFTRequest, current_user: dict = Depends(get_current_user)):
    print("enterin to get nft content...")
    state = {"input": request.dict()}

    print("Initial State in get-nft-content: ", state)

    result = await nft_graph_executer.ainvoke(state)
    print("Final Result in get-nft-content: ", result)

    # final_output = {
    #     "nftPrompt": result.get("nftPrompt", ""),
    #     "nftURL": result.get("nftURL", ""),
    #     "nftMetaData": result.get("nftMetaData", ""),
    #     "nftSocialMediaPost": result.get("nftSocialMediaPost", "")
    # }

    return NFTResponse(
        nftPrompt=result.get("nftPrompt", ""),
        nftURL=result.get("nftURL", ""),
        nftMetaData=result.get("nftMetaData", {}),
        nftSocialMediaPost=result.get("nftSocialMediaPost", {})
    )
