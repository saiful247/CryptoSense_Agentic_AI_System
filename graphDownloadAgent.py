from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import requests
import json

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

# testParams = {
#     "symbol": "ETH",
# }

# testResponse = requests.get(url, headers=headers, params=testParams)

# print("Test Request Status code: ", testResponse.status_code)

# result = testResponse.json()
# print(result)


def cryptoPriceTool(coinSymbol: str) -> str:
    """This agent is used to get the price info about a specific coin"""
    print("Coin Symbol: ", coinSymbol)

    params = {
        "symbol": coinSymbol,
    }

    response = requests.get(url, headers=headers, params=params)

    print("Response status: ", response.status_code)

    if response.status_code != 200:
        print(f"Error fetching crypto price data to {coinSymbol}")
        return "ERRROR"

    print("Parsing to JSON...")
    result = response.json()

    print("Parsed JSON: ", result)

    return result


statsAgentInstruction = """
You are an agent that provide information about cryptocurrency statistics by using the tools available to you, and using that
data you need to create a graph that displays the price changes over time and you should download that graph as a .png file for
the user.
Here the main steps:
 - first you need to change the user input cryptocurrency name to standard symbol
 - using that symbol you can use the cryptoPriceTool to fetch the price of that coin.
 - then you need to fetch the historical price data for that symbol
 - after that you need to create a graph from the historical data
 - finally, you need to save the graph as a .png file and provide it to the user
"""


statsAgent = ConversableAgent(
    "crypto_stat_agent",
    system_message=statsAgentInstruction,
    llm_config={
        "config_list": config_list
    },
    max_consecutive_auto_reply=1,
)


user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "TERMINATE" in msg["content"],
)

register_function(
    cryptoPriceTool,
    caller=statsAgent,
    executor=user_proxy,
    name="crypto_stat_tool",
    description="Uses CoinMarketCap API to fetch coin data"
)

user_proxy.initiate_chat(
    statsAgent,
    message="Give me all the details about Bitcoin"
)
