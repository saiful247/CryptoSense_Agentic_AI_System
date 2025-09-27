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

# Update user progress
def update_progress(user_id: int, correct: bool):
    conn = sqlite3.connect('quiz_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT quizzes_completed, badges FROM user_progress WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        quizzes_completed, badges = result
        quizzes_completed += 1
        new_badges = badges.split(",") if badges else []
        if quizzes_completed == 5 and "Crypto Novice" not in new_badges:
            new_badges.append("Crypto Novice")
        cursor.execute('UPDATE user_progress SET quizzes_completed = ?, badges = ? WHERE user_id = ?',
                      (quizzes_completed, ",".join(new_badges), user_id))
    else:
        cursor.execute('INSERT INTO user_progress (user_id, quizzes_completed, badges) VALUES (?, ?, ?)',
                      (user_id, 1, "Crypto Novice" if correct else ""))
    conn.commit()
    conn.close()

# Conduct quiz with news-based question (avoid repeats)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(Exception))
def conduct_quiz(user_id: int) -> str:
    news_items = fetch_recent_news()
    if not news_items:
        return "No recent news available. Try again later."
    
    conn = sqlite3.connect('quiz_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT news_title FROM asked_questions WHERE user_id = ?', (user_id,))
    asked_titles = [row[0] for row in cursor.fetchall()]
    available_news = [item for item in news_items if item['title'] not in asked_titles]
    if not available_news:
        available_news = news_items  # Reset if all asked
    
    news_item = random.choice(available_news)
    question_data = generate_question_from_news(news_item)
    response = f"News-based Question: {question_data['question']}\nOptions: {', '.join(question_data['options'])}\nBased on recent news: {news_item['title']}\nPlease select A, B, C, or D."
    
    cursor.execute('INSERT INTO asked_questions (user_id, news_title) VALUES (?, ?)', (user_id, news_item['title']))
    conn.commit()
    conn.close()
    
    return json.dumps({"response": response, "question_data": question_data, "news_item": news_item})

# Check answer and provide feedback with news explanation
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(Exception))
def check_answer(user_id: int, answer: str, question_json: str) -> str:
    try:
        data = json.loads(question_json.replace('\\u', 'u').replace('\\', '\\\\'))  # Clean invalid escapes
        question_data = data["question_data"]
        news_item = data["news_item"]
        correct = answer.upper() == question_data['answer']
        update_progress(user_id, correct)
        conn = sqlite3.connect('quiz_progress.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quizzes_completed, badges FROM user_progress WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        quizzes_completed, badges = result if result else (0, "")
        badges_list = badges.split(",") if badges else []
        
        feedback = f"{'Correct!' if correct else f'Incorrect. The correct answer is {question_data['answer']}: {question_data['options'][ord(question_data['answer']) - ord('A')]}'}\n"
        feedback += f"Explanation: {question_data['explanation'].replace('\\n', ' ').replace('\\r', ' ').strip()}\n"
        feedback += f"Full News Context: {news_item['description'].replace('\\n', ' ').replace('\\r', ' ').strip()} (Source: {news_item['url']})\n"
        feedback += f"Quizzes completed: {quizzes_completed}. Badges: {', '.join(badges_list) if badges_list else 'None'}\n"
        feedback += "Would you like another quiz? (Yes/No)"
        return feedback
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
        return f"Error processing your answer. Please try again. Details: {str(e)}\nWould you like another quiz? (Yes/No)"
    except Exception as e:
        logging.error(f"Unexpected error in check_answer: {e}")
        return f"Service unavailable. Please try again later. Details: {str(e)}\nWould you like another quiz? (Yes/No)"

# Agent configuration
quiz_agent_instruction = """
You are a Crypto Educational Quiz Agent. Engage users with quizzes based on current news about cryptocurrency concepts, market trends, and trading basics.
Fetch recent news to generate dynamic questions. Use conduct_quiz to present a news-based question and check_answer to evaluate responses with news-tied explanations.
Track user progress and award badges (e.g., 'Crypto Novice' at 5 quizzes).
Reply TERMINATE when the user declines another quiz or the session ends.
Parse JSON from tools for question data and news context.
Handle errors gracefully with retries and suggest retries if needed.
"""

quiz_agent = ConversableAgent(
    "crypto_quiz_agent",
    system_message=quiz_agent_instruction,
    llm_config={"config_list": config_list},
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
)

user_proxy = ConversableAgent(
    "user_proxy",
    llm_config=False,
    human_input_mode="ALWAYS",  # ALWAYS for interactive answers
    is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
)

# Register functions
register_function(
    conduct_quiz,
    caller=quiz_agent,
    executor=user_proxy,
    name="conduct_quiz",
    description="Generates and presents a news-based cryptocurrency quiz question with options as JSON"
)

register_function(
    check_answer,
    caller=quiz_agent,
    executor=user_proxy,
    name="check_answer",
    description="Evaluates user's answer using JSON-encoded question data and provides news-based feedback"
)

if __name__ == "__main__":
    init_db()
    user_proxy.initiate_chat(quiz_agent, message="Start a quiz for user 1")