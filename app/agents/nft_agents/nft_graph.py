from langgraph.graph import StateGraph
from typing import TypedDict
from app.schemas.schemas import NFTRequest

from app.agents.nft_agents.prompt_preprocess_agent import nftPromptPreprocess
from app.agents.nft_agents.nft_metadata_agent import generateNftMetadata
from app.agents.nft_agents.nft_marketing_agent import generateNftMarketingContent
from app.agents.nft_agents.nft_generation_agent import generateNftImage


class GraphState(TypedDict):
    input: NFTRequest
    nftPrompt: str
    nftURL: str
    nftMetaData: str
    nftSocialMediaPost: str


def buildNftGraph():
    graph = StateGraph(GraphState)

    prompt_preprocess_fn = nftPromptPreprocess()
    nft_metadata_fn = generateNftMetadata()
    nft_marketing_fn = generateNftMarketingContent()
    nft_image_generation_fn = generateNftImage()

    graph.add_node("nftPrompt", prompt_preprocess_fn)
    graph.add_node("nftImageGen", nft_image_generation_fn)
    graph.add_node("nftMetaData", nft_metadata_fn)
    graph.add_node("nftSocialMediaPost", nft_marketing_fn)

    # build flow
    graph.set_entry_point("nftPrompt")
    graph.add_edge("nftPrompt", "nftImageGen")
    graph.add_edge("nftImageGen", "nftMetaData")
    graph.add_edge("nftMetaData", "nftSocialMediaPost")
    graph.set_finish_point("nftSocialMediaPost")

    return graph.compile()
