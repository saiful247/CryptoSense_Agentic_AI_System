from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part
import vertexai
import re
import os
from dotenv import load_dotenv
import pandas as pd
import json

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

# Initialize Vertex AI
vertexai.init(project=project_id, location=location, credentials=credentials)

model = GenerativeModel("gemini-2.5-flash")


def nftPromptPreprocess():
    def nft_prompt_preprocess_function(state):
        userPrompt = state["input"]["userPrompt"]
        print("Prompt: ", userPrompt)

        instruction = f"""
        You are a NFT art prompt generation agent.
        user prompt will conatain NFT art description {userPrompt}. you need to change this description to detailed NFT art prompt for AI image generation model.
        output in json format like {{"nftPrompt": "A futuristic neon fox NFT, cyberpunk background, detailed illustration"}}.
        """
        try:
            result = model.generate_content(instruction)
            content = result.text.strip()
            print("Raw content: ", content)

            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```\s*", "", content)

            print("After cleaning: ", content)
            final_result = content

        except Exception as e:
            print("Error in parsing to pydantic model: ", str(e))
            state["nftPrompt"] = ""

        try:
            print("Final Result XX str: ", final_result)
            final_dict = json.loads(final_result)
            print("Final Result XX dict: ", final_dict)
            nftPrompt = final_dict.get("nftPrompt", "")
            print("NFT Prompt: ", nftPrompt)

            state["nftPrompt"] = nftPrompt
        except Exception as e:
            state["nftPrompt"] = ""
            print("Error in processing final result: ", str(e))

        return state
    return nft_prompt_preprocess_function
