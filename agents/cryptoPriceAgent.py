import re
from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel

class CryptoPrice(BaseModel):
    current_price: float
    percent_change_1h: float
    percent_change_24h: float
    percent_change_7d: float
    percent_change_30d: float
    market_cap: float
    volume_24h: float

class CryptoPriceAgentResponse(BaseModel):
    summary: str
    all_price: CryptoPrice

load_dotenv()

config_list = [
    {
        "model": "gemini-2.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google"
    }
]

coinMarketCap_api_key = os.getenv("COINMARKETCAP_API_KEY")

url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
headers = {
    "X-CMC_PRO_API_KEY": coinMarketCap_api_key
}


def cryptoPriceTool(coinSymbol: str) -> str:
    """This agent is used to get the price info about a specific coin"""
    print("Coin Symbol: ", coinSymbol)

    params = {
        "symbol": coinSymbol,
    }

    response = requests.get(url, headers=headers, params=params)

    print("Response status: ", response.status_code)

    if response.status_code != 200:
        print(f"Error fetching crypto price data for {coinSymbol}")
        return "ERROR"

    print("Parsing to JSON...")
    result = response.json()

    print("Parsed JSON: ", result)

    coin_usd = result["data"][coinSymbol][0]["quote"]["USD"]

    # Return as JSON string for easier parsing in chart tool
    print("Coin USD Data: ", coin_usd)
    return json.dumps(coin_usd)


instruction = """
You are a crypto price agent. You have acces to Price fetching tool.
steps to follow:
1. first you need to convert the user query into a coin symbol. for example if user query is "give me price of bitcoin" then the coin symbol is "BTC"
2. then you need to call the cryptoPriceTool with the coin symbol to get the price.
3. then cryptoPriceTool will return a JSON string with the price data.
4. then you need to parse the JSON string and extract the following fields:
   - current_price
   - percent_change_1h
   - percent_change_24h
   - percent_change_7d
   - percent_change_30d
5. the you need to give the price to the user like below JSON format:
    {{
        summary: "The current price of Bitcoin is $4342.08, with a 1-hour change of 0.14%, a 24-hour change of -3.41%, and a 7-day change of -9.47%. The market cap is $524119084067.21 and the volume in the last 24 hours is $46773360124.46.",
        all_price: {{
            "current_price": 4342.08,
            "percent_change_1h": 0.14,
            "percent_change_24h": -3.41,
            "percent_change_7d": -9.47,
            "percent_change_30d": 13.83,
            "market_cap": 524119084067.21,
            "volume_24h": 46773360124.46
        }}
    }}
6.After the JSON, output a single line: TERMINATE
"""

cryptoPriceAgent = ConversableAgent(
    "cryptoPriceAgent",
    system_message=instruction,
    llm_config={
        'config_list': config_list
    },
    max_consecutive_auto_reply=2,
    # This setting tells the agent how many back-to-back replies it’s allowed 
    # to generate automatically
    # (without human input) before the framework forces the conversation to stop.
    # Prevents infinite loops where two agents keep talking endlessly.
    # if is_termination_msg met within the autoreply it stops.
    human_input_mode="NEVER",

)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "TERMINATE" in msg["content"],  #if the message(reply) from CryptoPriceAgent contains TERMINATE, then stop
)

register_function(
    f=cryptoPriceTool,
    caller=cryptoPriceAgent,
    executor=user_proxy, #this agent is responsible for actually running the Python code.
    description="Fetches the latest price and market data for a specified cryptocurrency symbol (e.g., BTC for Bitcoin, ETH for Ethereum)."
)

"""
when register function, the function signature is automatically converted to JSON schema like below:
so that the LLM can understand what parameters to pass.
so thats why the cryptoPriceAgent responss to user_proxy as. this is why the respoonse exactly
conatining the same parameter name.
Arguments:
{"coinSymbol": "BTC"}

{
  "name": "cryptoPriceTool",
  "description": "Fetches the latest price and market data for a specified cryptocurrency symbol (e.g., BTC for Bitcoin, ETH for Ethereum).",
  "parameters": {
    "type": "object",
    "properties": {
      "coinSymbol": {
        "type": "string",
        "description": ""
      }
    },
    "required": ["coinSymbol"]
  }
}

"""


result = user_proxy.initiate_chat(
    cryptoPriceAgent, message="give me price of bitcoin")


final_text= result.chat_history[3].get("content","")
print("Final Result 007: ", final_text)

try:
    final_text = re.sub(r"^```json\s*","", final_text)
    final_text = re.sub(r"\s*```\s*","", final_text)
    final_text = re.sub(r"\s*TERMINATE\s*$","", final_text)
    print("After cleaning: ", final_text)
    final_result = json.loads(final_text)
    try: 
        print("Final Result XX str: ", final_result)
        final_output=CryptoPriceAgentResponse(**final_result)
        print("Pydantic Schema successfully parsed: ", final_output)
    except Exception as e:
        print("Error in parsing to pydantic model: ", str(e))
        final_output=final_result
        print("Final Result 008: ", final_output)
except Exception as e:
    final_result = {"raw": final_text}
    print("Error in processing final result: ", str(e))

