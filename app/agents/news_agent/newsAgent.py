import os, re, json, requests
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")  # ✅ Stable model version


def run_news_agent(query: str):
    """Fetch and summarize recent crypto news using Tavily + Gemini."""
    if not TAVILY_API_KEY:
        return {"error": "Missing TAVILY_API_KEY in .env"}

    # Step 1️⃣ — Fetch news from Tavily API
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
        return {"error": f"Tavily API error: {str(e)}"}

    if not results:
        return {"error": f"No news found for '{query}'."}

    news_items = [{"title": r.get("title"), "url": r.get("url")} for r in results if r.get("title")]
    headlines_text = "\n".join([f"- {n['title']}" for n in news_items])

    # Step 2️⃣ — Ask Gemini for structured summary
    prompt = f"""
    Summarize the following cryptocurrency news headlines for "{query}".

    Headlines:
    {headlines_text}

    Return ONLY valid JSON with:
    {{
      "key_themes": ["Theme1", "Theme2"],
      "summary": "4-6 sentence summary",
      "sentiment": "Positive" | "Negative" | "Neutral"
    }}
    """

    parsed = {}
    try:
        g_resp = model.generate_content(prompt)
        text = g_resp.text.strip() if g_resp else ""
        cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        parsed = json.loads(cleaned)
    except Exception as e:
        parsed = {"summary": f"Gemini API error: {str(e)}"}

    return {
        "topic": query,
        "headlines": news_items,
        "key_themes": parsed.get("key_themes", []),
        "summary": parsed.get("summary", "No summary available."),
        "sentiment": parsed.get("sentiment", "Neutral"),
        "timestamp": datetime.utcnow().isoformat(),
    }
