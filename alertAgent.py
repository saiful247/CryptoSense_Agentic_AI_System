from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import requests
import json
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration 
config_list = [
    {
        "model": "gemini-2.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google"
    }
]
coinMarketCap_api_key = os.getenv("COINMARKETCAP_API_KEY")
url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
headers = {"X-CMC_PRO_API_KEY": coinMarketCap_api_key}

# Database setup for storing price history
def init_db():
    conn = sqlite3.connect('crypto_alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto TEXT,
            price REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Fetch crypto price from CoinMarketCap
def get_crypto_price(crypto: str) -> float | None:
    params = {"symbol": crypto.upper(), "convert": "USD"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        result_json = response.json()
        if 'data' in result_json and crypto.upper() in result_json['data']:
            return result_json['data'][crypto.upper()]['quote']['USD']['price']
        return None
    except Exception as e:
        logging.error(f"Error fetching price for {crypto}: {e}")
        return None

# Store price in database for history
def store_price(crypto: str, price: float):
    conn = sqlite3.connect('crypto_alerts.db')
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('INSERT INTO price_history (crypto, price, timestamp) VALUES (?, ?, ?)',
                  (crypto, price, timestamp))
    conn.commit()
    conn.close()

# Get previous price from database
def get_previous_price(crypto: str) -> float | None:
    conn = sqlite3.connect('crypto_alerts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT price FROM price_history WHERE crypto = ? ORDER BY timestamp DESC LIMIT 1 OFFSET 1',
                  (crypto,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Check price and trigger alerts based on threshold
def check_price_alerts(crypto: str, threshold: float = 0.1) -> str:

    current_price = get_crypto_price(crypto)
    if current_price is None:
        return "Error fetching price."

    store_price(crypto, current_price)
    previous_price = get_previous_price(crypto)

    if previous_price is None:
        return f"Initial price recorded for {crypto.upper()}: ${current_price:.2f}"

    percent_change = ((current_price - previous_price) / previous_price) * 100
    if abs(percent_change) >= threshold:
        if percent_change > 0:
            message = f"🚀 {crypto.upper()} price increased by {percent_change:.2f}%! Now at ${current_price:.2f}"
        else:
            message = f"📉 {crypto.upper()} price decreased by {abs(percent_change):.2f}%! Now at ${current_price:.2f}"
        return message
    return f"No significant change for {crypto.upper()} (change: {percent_change:.2f}%)."

# Agent configuration and setup
alert_agent_instruction = """
You are a crypto price alert agent. You monitor cryptocurrency prices and notify users of significant changes (>5% by default).
Use the check_price_alerts tool to check prices and provide alerts. Reply TERMINATE when the task is done or no alerts are needed.
If an error occurs, inform the user and suggest trying again later. Ignore empty messages and continue monitoring.
"""

alert_agent = ConversableAgent(
    "crypto_alert_agent",
    system_message=alert_agent_instruction,
    llm_config={"config_list": config_list},
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
)

# Register the alert function with agent instances
register_function(
    check_price_alerts,
    caller=alert_agent,
    executor=user_proxy,
    name="check_price_alerts",
    description="Monitors crypto prices and alerts on significant changes (>5% by default)"
)

# Schedule price checks
def schedule_alerts():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: user_proxy.initiate_chat(alert_agent, message=f"Check alerts for BTC"),
                     'interval', minutes=5)
    scheduler.start()

if __name__ == "__main__":
    init_db()
    schedule_alerts()
    user_proxy.initiate_chat(alert_agent, message="Check alerts for BTC")
    while True:
        time.sleep(60)  # Keep script