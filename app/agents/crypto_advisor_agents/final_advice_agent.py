import re
import os
from dotenv import load_dotenv
import json

from app.schemas.schemas import CryptoAdvice

from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part
import vertexai

load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")


if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
else:
    raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env")

# Initialize Vertex AI
vertexai.init(project=project_id, location=location, credentials=credentials)

model = GenerativeModel("gemini-2.5-flash")


def getFinalAdvice():

    def get_advice_function(state):
        print("Entering Final Advice Agent with state: ", state)
        userInput = state["input"]
        investmentAmountUSD = userInput.get("amountUSD", 1000)
        investmentDurationMonths = userInput.get(
            "investmentDurationMonths", 12)
        coinSymbol = state["coinSymbol"]
        finance_metrics = state["finance_metrics"]
        platform_selection = state["platform_selection"]
        binance_as_platform = platform_selection["platforms"]["Binance"]
        coinbase_as_platform = platform_selection["platforms"]["Coinbase"]

        instruction = f"""
        You are a crypto currency finance advice agent.
        you will get the coin symbol {coinSymbol},investment amount in USD {investmentAmountUSD}, investment duration in months {investmentDurationMonths}, finance metrics {finance_metrics}, and platform selection {platform_selection}.

        IMPORTANT: Finance metrics contains the following information for coin {coinSymbol}:
         - CAGR (Compound Annual Growth Rate) in percentage over the last 5 years {finance_metrics.get("cagr", "")}%.
         - Volatility (Annualized Volatility) in percentage over the last 5 years {finance_metrics.get("volatility", "")}%.
         - Maximum Drawdown (Risk Indicator) in percentage over the last 5 years {finance_metrics.get("max_drawdown", "")}%.
         - using these metrics, provide a concise investment advice for the coin {coinSymbol}.

        IMPORTANT: Platform selection contains the following information:
         - Best Platform to buy the coin {coinSymbol} based on:
            - Price difference across platforms: for now we will consider only two platforms Binance and Coinbase.
                - Binance Price: {binance_as_platform.get("current_price", "")} USD
                - Coinbase Price: {coinbase_as_platform.get("current_price", "")} USD
            - Trading fees on each platform:
                - Binance Trading Fee:
                    - Maker Fee: {binance_as_platform.get("trading_fee", {}).get("maker_fee", "")}%
                    - Taker Fee: {binance_as_platform.get("trading_fee", {}).get("taker_fee", "")}%
                - Coinbase Trading Fee:
                    - Maker Fee: {coinbase_as_platform.get("trading_fee", {}).get("maker_fee", "")}%
                    - Taker Fee: {coinbase_as_platform.get("trading_fee", {}).get("taker_fee", "")}%
            - Trust Score of each platform:
                - Binance Trust Score: {binance_as_platform.get("trust_score", "")} out of 10
                - Coinbase Trust Score: {coinbase_as_platform.get("trust_score", "")} out of 10
            - Average Spread Percentage on each platform:
                - Binance Average Spread Percentage: {binance_as_platform.get("avg_spread_pct", "")}%
                - Coinbase Average Spread Percentage: {coinbase_as_platform.get("avg_spread_pct", "")}%
            - Deposit and Withdrawal Options on each platform:
                - Binance Deposit and Withdrawal Options: {', '.join(binance_as_platform.get("deposit_withdraw_options", []))}
                - Coinbase Deposit and Withdrawal Options: {', '.join(coinbase_as_platform.get("deposit_withdraw_options", []))}
            - using these metrics, provide a concise recommendation on which platform is better to buy the coin {coinSymbol}.
        
        IMPORTANT: Using the investment amount in USD {investmentAmountUSD}, investment duration in months {investmentDurationMonths}, CAGR, Volatility, and Maximum Drawdown, provide a concise estimation of the potential returns and risks associated with investing in the coin {coinSymbol} over the specified duration.

        Finally, combine all the above information and provide a concise final advice on whether to invest in the coin {coinSymbol} or not, and if yes, then which platform is better to buy the coin {coinSymbol}.

        ONLY return a valid JSON object structured EXACTLY like this:

        {{
            "coinSymbol": "{coinSymbol}",
            "current_price"{{
                "Binance": {binance_as_platform.get("current_price", "")},
                "Coinbase": {coinbase_as_platform.get("current_price", "")},
                "cheaper_platform": "Binance or Coinbase based on current price"
            }},
            "final_advice": "Your concise final advice here.",
            "investment_advice": {{
                "should_invest": "Yes or No",
                "reason": "Concise investment advice based on finance metrics."
            }},
            "recommended_platform": {{
                "platform_name": "Binance or Coinbase",
                "reason": "Concise reason for recommendation based on platform selection metrics."
            }},
            "risk_assessment": "Concise risk assessment based on volatility and max drawdown"
        }}

        """

        try:
            print("Calling Gemini API with prompt:")
            response = model.generate_content(instruction)

            content = response.text.strip()
            print(content)

            print("Gemini API response received.")

            # error handling 1 for jason
            content = response.text.strip()

            # remove starting ````
            content = re.sub(r"^```json\s*", "", content)

            # Remove ending ```
            content = re.sub(r"\s*```$", "", content)

            print(content)

        except Exception as e:
            print("Error in Gemini API call: ", str(e))
            return state

        try:
            # without tools: JSON output not valid error
            parsed_json = json.loads(content)

            print("Parsed JSON before FinalItinerary init:",
                  json.dumps(parsed_json, indent=2))

            final_output = CryptoAdvice(**parsed_json)
            print("Pydantic Schema successfully parsed: ", final_output)

            state["final_advice"] = final_output.dict()

        except Exception as e:
            print("Error in parsing JSON: ", str(e))
            state["final_advice"] = {}
            return state

        return state
    return get_advice_function
