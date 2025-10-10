import os
import json
import re
from dotenv import load_dotenv


import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

from app.schemas.schemas import NFTMarketingContent

load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")

# if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
#     credentials = service_account.Credentials.from_service_account_file(
#         os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#     )
# else:
#     raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env")
credentials = None

vertexai.init(project=project_id, location=location, credentials=credentials)

model = GenerativeModel("gemini-2.5-flash")


def generateNftMarketingContent():
    def nft_marketing_function(state):

        nftName = state.get("input", {}).get("nftName", "unnamed_nft")
        nftCollectionName = state.get("input", {}).get(
            "nftCollectionName", "default_collection")
        nftURL = state.get("nftURL", "")

        metaData = state.get("nftMetaData", {})

        nftDescription = metaData.get("description", "A beautiful NFT art")
        nft_attributes = metaData.get("attributes", [])
        social_platform = state.get("input", {}).get(
            "socialMediaPlatform", "Twitter")

        instructions = f"""
            You are a creative marketing assistant for NFT projects.
            Given an NFT project name, collection name, and a brief description, generate a catchy marketing tagline and a concise promotional post.
            The tagline should be no more than 10 words, and the promotional post should be around 50 words.
            you will get,
                - nftName: {nftName}
                - nftCollectionName: {nftCollectionName}
                - nftDescription: {nftDescription}
                - nft_attributes: {nft_attributes}
                - nftURL: {nftURL}
                - socialMediaPlatform:{social_platform}

            Guidelines:
            - Write in the tone suitable for {social_platform}.
            - Highlight the unique artistic traits or story of the NFT.
            - Include 3–5 relevant hashtags (like #NFT, #DigitalArt, etc.).
            - Keep it under 280 characters for Twitter, otherwise engaging and concise.

            respond only in JSON format as:
            {{
                "tagline": "Your catchy tagline here",
                "promotional_post": "Your promotional post here"
            }}
        """

        try:
            response = model.generate_content(instructions)

            response_text = response.text.strip()
            print("Raw response text: ", response_text)

            response_text = re.sub(r"^```json\s*", "", response_text)
            response_text = re.sub(r"\s*```\s*", "", response_text)

            print("Cleaned response text: ", response_text)
        except Exception as e:
            print(f"Error generating content: {e}")
            state["nftMarketingContent"] = {}
            return state

        try:
            parsed_json = json.loads(response_text)
            print("Parsed JSON: ", json.dumps(parsed_json, indent=2))

            final_output = NFTMarketingContent(**parsed_json)

            print("Pydantic Schema successfully parsed: ", final_output)

            state["nftSocialMediaPost"] = final_output.dict()

        except Exception as e:
            print("Error parsing JSON or initializing Pydantic model: ", str(e))
            state["nftMarketingContent"] = {}
            return state

        return state

    return nft_marketing_function
