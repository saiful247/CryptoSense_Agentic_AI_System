from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from autogen.coding import LocalCommandLineCodeExecutor
import tempfile
from cryptoPriceAgent import getCryptoPrice

load_dotenv()

temp_dir = tempfile.TemporaryDirectory()

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


codeExecuterAgentInstructions="""
You are an agent that executes code to create price change charts.
you will get the data from 
Here is the code you must execute:
```
price_data = content
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
```
after succesfully executing the code you must respond with "SAVED_SUCCESSFULLY"
"""

code_executor= LocalCommandLineCodeExecutor(
    timeout=10,
    work_dir=temp_dir.name,
)

codeExecuterAgent= ConversableAgent(
    "codeExecuterAgent",
    system_message=codeExecuterAgentInstructions,
    llm_config=False,
    code_execution_config={
        "executor": code_executor},
    human_input_mode="NEVER",    
    is_termination_msg=lambda msg: msg.get(
        "content") is not None and "SAVED_SUCCESSFULLY" in msg["content"],
)

cryptoData=getCryptoPrice("I need the price of bitcoin")

print("Crypto Data in Graph Executor: ", cryptoData)

price_data=cryptoData.get("all_price", {})
print("Price Data for Graph: ", price_data)

# crypto_parsed=json.loads(cryptoData)

str_price_data=str(price_data)

# Example initiation
result = codeExecuterAgent.generate_reply(
    messages=[{"role": "user", "content": str_price_data}]
)

# print("Chat History: ", result.chat_history)
