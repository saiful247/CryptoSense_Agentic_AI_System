from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd

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


def createPriceChangeChart(price_data: str) -> str:
    """Create a bar chart of price changes from the current data and save as PNG."""
    try:
        data = json.loads(price_data)
        changes = {
            '1h': data.get('percent_change_1h', 0),
            '24h': data.get('percent_change_24h', 0),
            '7d': data.get('percent_change_7d', 0),
            '30d': data.get('percent_change_30d', 0),
            '60d': data.get('percent_change_60d', 0),
            '90d': data.get('percent_change_90d', 0)
        }
        df = pd.DataFrame(list(changes.items()), columns=['Period', 'Change'])

        plt.figure(figsize=(10, 5))
        plt.bar(df['Period'], df['Change'], color='skyblue')
        plt.xlabel('Time Period')
        plt.ylabel('Percent Change (%)')
        plt.title('Current Price Changes')
        plt.grid(True)

        chart_path = 'price_changes.png'
        plt.savefig(chart_path)
        plt.close()

        return os.path.abspath(chart_path)
    except Exception as e:
        return f"Error creating chart: {str(e)}"


statsAgentInstruction = """
You are an agent that provides information about cryptocurrency statistics by using the tools available to you, and using that
data you need to create a graph that displays the current price changes and you should save that graph as a .png file for
the user.
Here are the main steps:
 - First, you need to change the user input cryptocurrency name to standard symbol (e.g., Bitcoin to BTC).
 - Using that symbol, use the cryptoPriceTool to fetch the current price data of that coin.
 - Then, use the createPriceChangeChart tool to create a bar chart from the current price change data (e.g., percent changes over 1h, 24h, etc.).
 - Finally, save the graph as a .png file and provide the file path to the user in your response.
"""

statsAgent = ConversableAgent(
    "crypto_stat_agent",
    system_message=statsAgentInstruction,
    llm_config={
        "config_list": config_list
    },
    max_consecutive_auto_reply=1,  # Increased for multi-step
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
    name="cryptoPriceTool",
    description="Uses CoinMarketCap API to fetch current coin data"
)

register_function(
    createPriceChangeChart,
    caller=statsAgent,
    executor=user_proxy,
    name="createPriceChangeChart",
    description="Creates a bar chart of price changes from current data and saves as PNG"
)

# Example initiation
user_proxy.initiate_chat(
    statsAgent,
    message="Give me price graph about Bitcoin"
)
