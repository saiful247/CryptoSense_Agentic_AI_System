from autogen import ConversableAgent, register_function
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import logging
import random
import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration
config_list = [
    {
        "model": "gemini-2.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google"
    }
]
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Add to .env: NEWS_API_KEY=your_newsapi_key

# Database setup
def init_db():
    conn = sqlite3.connect('quiz_progress.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER PRIMARY KEY,
            quizzes_completed INTEGER DEFAULT 0,
            badges TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asked_questions (
            user_id INTEGER,
            news_title TEXT,
            PRIMARY KEY (user_id, news_title)
        )
    ''')
    conn.commit()
    conn.close()

# Fetch recent crypto news with retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_recent_news() -> list:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "cryptocurrency OR bitcoin OR ethereum OR defi OR blockchain",
        "apiKey": NEWS_API_KEY,
        "sortBy": "publishedAt",
        "pageSize": 20,
        "language": "en"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        return [{"title": article['title'], "description": article['description'], "url": article['url']} for article in articles if article['description']]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {e}")
        return [
            {"title": "Bitcoin Hits New All-Time High", "description": "BTC surges 10% amid ETF approvals.", "url": "https://example.com/btc-high"},
            {"title": "Ethereum Dencun Upgrade Goes Live", "description": "Reduces fees and improves scalability.", "url": "https://example.com/eth-upgrade"},
            {"title": "DeFi Hacks Rise in Q3", "description": "Security concerns in lending protocols highlighted.", "url": "https://example.com/defi-hacks"}
        ]

# Generate question from a news item
def generate_question_from_news(news_item: dict) -> dict:
    title = news_item['title'].replace('"', '').replace('\\', '')
    description = news_item['description'].replace('"', '').replace('\\', '').replace('\u2026', '...').replace('\u2013', '-').replace('\u2019', "'").replace('\u2018', "'")
    
    mock_questions = [
        {
            "question": f"What is the main event in '{title}'?",
            "options": [f"A) {description[:50]}...", "B) Price drop", "C) Regulatory ban", "D) New exchange launch"],
            "answer": "A",
            "explanation": f"According to the news: {description}. Source: {news_item['url']}"
        },
        {
            "question": f"Which factor is highlighted in '{title}'?",
            "options": ["A) Market crash", f"B) {description[:50]}...", "C) Bull run", "D) Stablecoin adoption"],
            "answer": "B",
            "explanation": f"The news discusses: {description}. Source: {news_item['url']}"
        }
    ]
    return random.choice(mock_questions)