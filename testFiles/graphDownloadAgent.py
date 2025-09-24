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
        print("Data in createPriceChangeChart: ", data)
        print("1h data: ", data.get('percent_change_1h', 0))
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

        chart_path = f'E:\\IRWA\\Project\\CryptoAgent\\cryptoGraph\\price_changes_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(chart_path)
        plt.close()

        return os.path.abspath(chart_path)
    except Exception as e:
        return f"Error creating chart: {str(e)}"


statsAgentInstruction = """
You are an agent that provides cryptocurrency price change graphs.
Here are the main steps, ALL OF WHICH MUST BE COMPLETED IN ORDER:
1. first you need to convert the user query into a coin symbol. for example if user query is "give me price of bitcoin" then the coin symbol is "BTC"
2. then you need to call the cryptoPriceTool with the coin symbol to get the price.
3. then cryptoPriceTool will return a JSON string with the price data.
4. then you need to parse the JSON string and extract the following fields:
   - current_price
   - percent_change_1h
   - percent_change_24h
   - percent_change_7d

   - percent_change_60d
   - percent_change_90d
5.then you need to use the createPriceChangeChart Tool with the above fields to create the chart.
6. Finally, if succesfully created the chart respond as "SAVED_SUCCESSFULLY".

YOU MUST PERFORM ALL STEPS IN SEQUENCE, DO NOT STOP AFTER JUST GETTING THE PRICE DATA.
"""

statsAgent = ConversableAgent(
    "crypto_stat_agent",
    system_message=statsAgentInstruction,
    llm_config={
        "config_list": config_list
    },
    max_consecutive_auto_reply=2,
    human_input_mode="NEVER",
)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "SAVED_SUCCESSFULLY" in msg["content"],
)

register_function(
    f=cryptoPriceTool,
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
result = user_proxy.initiate_chat(
    statsAgent,
    message="Give me price graph about Solana"
)

print("Chat History: ", result.chat_history)
