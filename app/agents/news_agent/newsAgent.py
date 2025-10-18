import os
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# ──────────────────────────────────────────────
# Environment setup
# ──────────────────────────────────────────────
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")

# ──────────────────────────────────────────────
# Core Tool
# ──────────────────────────────────────────────
def cryptoNewsTool(query: str):
    """
    Fetch and summarize recent cryptocurrency news using Tavily + Gemini.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY missing in .env"}

    # Step 1: Fetch news from Tavily
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"latest cryptocurrency news about {query}",
        "search_depth": "advanced",
        "topic": "news",
        "max_results": 5,
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        return {"error": f"Tavily API error: {e}"}

    if not results:
        return {"error": f"No news found for '{query}'"}

    # Step 2: Format the news
    news_items = [{"title": r.get("title"), "url": r.get("url")} for r in results if r.get("title")]
    headlines_text = "\n".join([f"- {n['title']}" for n in news_items])

    # Step 3: Ask Gemini for analysis
    prompt = f"""
    Summarize the following cryptocurrency news headlines for '{query}'.

    Headlines:
    {headlines_text}

    Return ONLY valid JSON with:
    {{
        "key_themes": ["theme1", "theme2"],
        "summary": "4–6 sentence overview of the market sentiment.",
        "sentiment": "Positive" or "Negative" or "Neutral"
    }}
    """

    parsed = {}
    try:
        g_resp = model.generate_content(prompt)
        text = g_resp.text.strip() if g_resp else ""
        cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        parsed = json.loads(cleaned)
    except Exception as e:
        parsed = {"summary": f"Gemini summarization error: {e}"}

    return {
        "topic": query,
        "headlines": news_items,
        "key_themes": parsed.get("key_themes", []),
        "summary": parsed.get("summary", "No summary available."),
        "sentiment": parsed.get("sentiment", "Neutral"),
        "timestamp": datetime.utcnow().isoformat(),
    }

# ──────────────────────────────────────────────
# Runner function for route integration
# ──────────────────────────────────────────────
def run_news_agent(query: str):
    """
    Wrapper function used by FastAPI route.
    Handles validation and calls cryptoNewsTool().
    """
    if not query or not isinstance(query, str):
        return {"error": "Invalid or missing query parameter."}

    result = cryptoNewsTool(query)
    return {"news_report": result}
