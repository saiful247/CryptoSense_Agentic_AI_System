import os
import json
from dotenv import load_dotenv
import requests
import re

import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.oauth2 import service_account

from app.schemas.schemas import NFTMetadata

load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")


if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
else:
    raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env")

# Initialize Vertex AI
vertexai.init(project=project_id, location=location, credentials=credentials)


# model = GenerativeModel("gemini-2.0-pro-vision")
model = GenerativeModel("gemini-2.5-flash")


def generateNftMetadata():

    def nft_metadata_function(state):
        nftName = state.get("input", {}).get("nftName", "unnamed_nft")
        nftCollectionName = state.get("input", {}).get(
            "nftCollectionName", "default_collection")
        nftURL = state.get("nftURL", "")

        instructions = f"""
        You are a NFT metadata generation agent.
        you will get the nft name {nftName}, nft collection name {nftCollectionName}, and nft image url {nftURL}.
        Return metadata in JSON using ERC-721 format with these fields:
        - name: The name of the NFT, which is {nftName}
        - description (concise but creative)
        - image ({nftURL})
        - attributes (trait_type/value pairs like Style, Color, Mood, Background, etc.)
        """

        # Fetch image bytes from URL
        try:
            image_response = requests.get(nftURL)
            image_response.raise_for_status()  # Raise error for bad responses
            image_bytes = image_response.content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image: {e}")
            exit(1)

        image_part = Part.from_data(
            mime_type="image/png",
            data=image_bytes
        )

        try:
            response = model.generate_content([image_part, instructions])

            content = response.text.strip()
            print("Generated NFT Metadata: ", content)

            # clean json
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            print("Cleaned JSON: ", content)

        except Exception as e:
            print("Error in Gemini API call: ", str(e))
            return state

        try:
            parsed_json = json.loads(content)
            print("Parsed JSON before NFT Metadata init:",
                  json.dumps(parsed_json, indent=2))

            final_output = NFTMetadata(**parsed_json)

            print("Pydantic Schema successfully parsed: ", final_output)

            state["nftMetaData"] = final_output.dict()

        except Exception as e:
            print("Error in parsing JSON: ", str(e))
            state["nftMetaData"] = {}
            return state

        return state
    return nft_metadata_function
