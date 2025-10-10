import re
import os
from dotenv import load_dotenv
import pandas as pd
import json

from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part
import vertexai

load_dotenv()

# config_list = [
#     {
#         "model": "gemini-2.5-flash",
#         "api_key": os.environ["GEMINI_API_KEY"],
#         "api_type": "google"
#     }
# ]

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

model = GenerativeModel("gemini-2.5-flash")


def getCoinSymbol():
    def get_coin_symbol_function(state):
        coinName = state["input"]["coinName"]
        print("Coin Name: ", coinName)

        instruction = f"""
        You are a crypto currency name to symbol conversion agent.
        user prompt will conatain crypto currency name {coinName}. you need to change this name to Crypto currrency symbol.
        out put only the symbol for example BTC for Bitcoin, ETH for Ethereum, LTC for Litecoin.
        output in json format like {{"coinSymbol": "BTC"}}.
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
            state["coinSymbol"] = ""
            print("Error in processing final result: ", str(e))

        try:
            print("Final Result XX str: ", final_result)
            final_dict = json.loads(final_result)
            print("Final Result XX dict: ", final_dict)
            coinSymbol = final_dict.get("coinSymbol", "")
            print("Coin Symbol: ", coinSymbol)

            state["coinSymbol"] = coinSymbol
        except Exception as e:
            print("Error in parsing to pydantic model: ", str(e))
            state["coinSymbol"] = ""

        return state
    return get_coin_symbol_function
