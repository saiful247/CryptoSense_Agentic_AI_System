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

url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
headers = {
    "X-CMC_PRO_API_KEY": coinMarketCap_api_key
}


def cryptoDataTool(coinName: str) -> str:
    """Uses CoinMarketCap API to fetch coin data for a specific cryptocurrency symbol."""

    print(f"Searching data for crypto {coinName}")

    params = {
        "symbol": coinName.upper(),
        "convert": "USD"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result_json = response.json()
        if 'data' in result_json and result_json['data']:
            coin_data = result_json['data'][0]
            usd_quote = coin_data['quote']['USD']
            filtered_result = {
                'name': coin_data['name'],
                'symbol': coin_data['symbol'],
                'percent_change_1h': usd_quote['percent_change_1h'],
                'percent_change_24h': usd_quote['percent_change_24h'],
                'percent_change_7d': usd_quote['percent_change_7d'],
                'market_cap': usd_quote['market_cap'],
                'volume_24h': usd_quote['volume_24h'],
                'circulating_supply': coin_data['circulating_supply']
            }
            return json.dumps(filtered_result, indent=4)
        else:
            return "No data found for the specified coin."
    else:
        return f"Failed to fetch data: {response.status_code} - {response.text}"


cryptoPriceAgent_instruction = """
You are helping to find the latest data of the cryptocurrency.
You have the ability to access real-time crypto data using the cryptoDataTool.
Use that tool to provide the details, including price changes, market cap, volume, and supply.
Reply TERMINATE when the task is done.
"""

crypto_agent = ConversableAgent(
    "crypto_price_tracker_agent",
    system_message=cryptoPriceAgent_instruction,
    llm_config={
        "config_list": config_list
    },
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "TERMINATE" in msg["content"],
)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "TERMINATE" in msg["content"],
)

register_function(
    cryptoDataTool,
    caller=crypto_agent,
    executor=user_proxy,
    name="crypto_data_tool",
    description="Uses CoinMarketCap API to fetch coin data"
)

user_proxy.initiate_chat(
    crypto_agent,
    message="Give me all the details about Bitcoin"
)
