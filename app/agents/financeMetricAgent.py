import yfinance as yf
import numpy as np


def get_finance_metrics():

    def get_finance_metrics_function(state):
        coinSymbol = state["coinSymbol"]
        print("Calculating finance metrics for: ", coinSymbol)

        ticker = f"{coinSymbol}-USD"

        # Define tickers
        coin_ticker = yf.Ticker(ticker)

        # Get last 5 years daily data
        coin_hist = coin_ticker.history(period="1y", interval="1d")
        print(coin_hist.head())

        start_price = coin_hist["Close"].iloc[0]
        end_price = coin_hist["Close"].iloc[-1]

        years = int((coin_hist.index[-1]-coin_hist.index[0]).days/365)
        # print("Years: ", years)

        cagr = (end_price / start_price) ** (1 / years) - 1
        cagr_percent = round(cagr * 100, 2)
        # print("CAGR: ", cagr_percent)

        # Compute daily log returns
        coin_hist["returns"] = np.log(
            coin_hist["Close"] / coin_hist["Close"].shift(1))

        coin_returns = coin_hist["returns"].dropna()

        daily_vol = coin_returns.std()

        # Annualized volatility
        annual_vol = daily_vol * np.sqrt(365)
        annual_vol_percent = round(annual_vol * 100, 2)

        # print("Daily Volatility: ", daily_vol)
        # print("Annualized Volatility: ", annual_vol_percent)

        # Running maximum of Close price
        coin_hist["cummax"] = coin_hist["Close"].cummax()

        # Drawdown at each time
        coin_hist["drawdown"] = (coin_hist["Close"] -
                                 coin_hist["cummax"]) / coin_hist["cummax"]

        # Max Drawdown
        max_drawdown = coin_hist["drawdown"].min()
        max_drawdown_percent = round(max_drawdown * 100, 2)

        # Print all metrics
        print(f"CAGR: {cagr_percent}%")
        print(f"Annualized Volatility: {annual_vol_percent}%")
        print(f"Maximum Drawdown: {max_drawdown_percent}%")

        if "finance_metrics" not in state:
            state["finance_metrics"] = {}

        # print(f"Maximum Drawdown:", max_drawdown_percent)
        state["finance_metrics"]["cagr"] = cagr_percent
        state["finance_metrics"]["volatility"] = annual_vol_percent
        state["finance_metrics"]["max_drawdown"] = max_drawdown_percent

        return state
    return get_finance_metrics_function
