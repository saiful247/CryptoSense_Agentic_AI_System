import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("COINMARKETCAP_API_KEY")

url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
headers = {
    "X-CMC_PRO_API_KEY": api_key
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("✅ CoinMarketCap API is working!")
else:
    print("❌ Failed. Status code:", response.status_code)
