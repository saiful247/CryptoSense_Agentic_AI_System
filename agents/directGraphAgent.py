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


def process_crypto_request(crypto_name):
    # Map common crypto names to their symbols
    crypto_map = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "litecoin": "LTC",
        "dogecoin": "DOGE",
        # Add more mappings as needed
    }
    
    # Convert to lowercase for case-insensitive matching
    crypto_name_lower = crypto_name.lower()
    
    # Get the symbol (or use the input if not in our map)
    symbol = crypto_map.get(crypto_name_lower, crypto_name.upper())
    
    print(f"Processing request for {crypto_name} (Symbol: {symbol})")
    
    # Step 1: Get price data
    price_data = cryptoPriceTool(symbol)
    if price_data == "ERROR":
        return f"Failed to get price data for {crypto_name}"
    
    # Step 2: Create chart
    chart_path = createPriceChangeChart(price_data)
    
    return f"Created price change chart for {crypto_name} at: {chart_path}"


statsAgentInstruction = """
You are an agent that provides information about cryptocurrency statistics.
Your role is to interpret user requests about crypto price graphs and call the appropriate
processing function.
"""

statsAgent = ConversableAgent(
    "crypto_stat_agent",
    system_message=statsAgentInstruction,
    llm_config={
        "config_list": config_list
    },
)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
)

def handle_crypto_graph_request(message: str) -> str:
    # Extract the crypto name from the message
    # This is a simple implementation - in a real app you might want more sophisticated NLP
    if "bitcoin" in message.lower():
        return process_crypto_request("Bitcoin")
    elif "ethereum" in message.lower():
        return process_crypto_request("Ethereum")
    elif "litecoin" in message.lower():
        return process_crypto_request("Litecoin")
    elif "dogecoin" in message.lower():
        return process_crypto_request("Dogecoin")
    else:
        # Default to Bitcoin if no specific crypto mentioned
        return process_crypto_request("Bitcoin")

register_function(
    handle_crypto_graph_request,
    caller=statsAgent,
    executor=user_proxy,
    name="handleCryptoGraphRequest",
    description="Processes a request for a cryptocurrency price graph"
)

# Example initiation
user_proxy.initiate_chat(
    statsAgent,
    message="Give me price graph about Bitcoin"
)
