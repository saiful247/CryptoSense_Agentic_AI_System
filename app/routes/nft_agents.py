import json
from fastapi import APIRouter, HTTPException, Request, status, Depends

from app.auth.auth import get_current_user

from app.agents.nft_agents.nft_graph import buildNftGraph
from app.schemas.schemas import NFTRequest, NFTResponse

from app.db.nft_firestore import create_nft_data
from app.db.nft_firestore import create_nft_data, get_nft_data_by_user, delete_nft_data


router = APIRouter()

nft_graph_executer = buildNftGraph()


@router.post("/get-nft-content", response_model=NFTResponse)
async def get_nft_content(request: NFTRequest, current_user: dict = Depends(get_current_user)):
    print("enterin to get nft content...")
    state = {"input": request.dict()}

    print("Initial State in get-nft-content: ", state)

    result = await nft_graph_executer.ainvoke(state)
    print("Final Result in get-nft-content: ", result)

    # return NFTResponse(
    #     nftPrompt=result.get("nftPrompt", ""),
    #     nftURL=result.get("nftURL", ""),
    #     nftMetaData=result.get("nftMetaData", {}),
    #     nftSocialMediaPost=result.get("nftSocialMediaPost", {})
    # )
    nft_response = NFTResponse(
        nftPrompt=result.get("nftPrompt", ""),
        nftURL=result.get("nftURL", ""),
        nftMetaData=result.get("nftMetaData", {}),
        nftSocialMediaPost=result.get("nftSocialMediaPost", {})
    )

    # --- Save to Firestore ---
    try:
        create_nft_data(current_user["user_id"], nft_response.dict())
        print(f"NFT data saved for user {current_user['email']}")
    except Exception as e:
        print(f"Error saving NFT data: {e}")

    return nft_response


@router.get("/my-nfts")
async def get_my_nfts(current_user: dict = Depends(get_current_user)):
    """
    Retrieve all NFT data created by the authenticated user.
    """
    try:
        user_id = current_user["user_id"]
        nft_list = get_nft_data_by_user(user_id)
        return {"user_id": user_id, "count": len(nft_list), "nfts": nft_list}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving NFT data: {str(e)}"
        )


@router.delete("/nft/{nft_id}")
async def delete_nft(nft_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a specific NFT record by its ID (only if it belongs to the current user).
    """
    try:
        # Optional: verify ownership before deletion
        user_nfts = get_nft_data_by_user(current_user["user_id"])
        nft_ids = [n["nft_id"] for n in user_nfts]
        if nft_id not in nft_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this NFT record."
            )

        success = delete_nft_data(nft_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete NFT record."
            )

        return {"message": f"NFT record {nft_id} deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting NFT data: {str(e)}"
        )
