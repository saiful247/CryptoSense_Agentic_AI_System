# app/agents/portfolio_agent/portfolioAgent.py
import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
from .utils import (
    fetch_coin_catalog,
    resolve_to_id,
    calculate_portfolio_value,
    format_report,
)

# ─────────────────────────────
# Load Environment Variables
# ─────────────────────────────
load_dotenv()
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")

credentials = None

# Initialize Vertex AI
vertexai.init(project=project_id, location=location, credentials=credentials)

model = GenerativeModel("gemini-2.5-flash")

# ─────────────────────────────
# Gemini Summary
# ─────────────────────────────


def summarize_portfolio(total, breakdown, by_id):
    """
    Ask Gemini to analyze and summarize the portfolio.
    """
    report = format_report(total, breakdown, by_id)
    prompt = f"""
    You are a financial assistant.
    Here is the user's crypto portfolio report:

    {report}

    Please summarize with:
    1. Main holdings and their share of total value
    2. Risk insights (diversification, concentration)
    3. Simple investment-style advice in plain English
    """

    try:
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            print("✅ Gemini summary generated successfully.")
            return response.text

        # Some Gemini models return .candidates instead of .text
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content"):
                parts = getattr(candidate.content, "parts", [])
                if parts and hasattr(parts[0], "text"):
                    print("✅ Gemini candidate summary generated.")
                    return parts[0].text

        print("⚠️ Gemini returned no usable text response.")
        return "No summary generated."
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return "Error generating summary."


# ─────────────────────────────
# Main Entry Function
# ─────────────────────────────
def run_portfolio_agent(holdings_text: str):
    """
    Parse holdings text, compute portfolio value, and summarize.
    """
    by_id, by_symbol, by_name = fetch_coin_catalog()
    portfolio = {}

    for line in holdings_text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        # symbol = parts[0].replace(":", "").strip()
        # amount = parts[1]

        # symbol = symbol.strip().upper()
        symbol, amount = parts
        cid = resolve_to_id(symbol, by_id, by_symbol, by_name)
        print(f"Resolved {symbol} to ID: {cid}")
        if not cid:
            continue
        try:
            amt = float(amount)
            if amt < 0:
                continue
        except ValueError:
            continue
        portfolio[cid] = portfolio.get(cid, 0.0) + amt

    print("Resolved portfolio:", portfolio)

    if not portfolio:
        return {"error": "No valid holdings entered."}

    total, breakdown = calculate_portfolio_value(portfolio)
    report = format_report(total, breakdown, by_id)
    summary = summarize_portfolio(total, breakdown, by_id)

    return {
        "report": report,
        "summary": summary,
        "total_value": total,
        "breakdown": breakdown,
    }
