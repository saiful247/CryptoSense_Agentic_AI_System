import numpy as np
import requests


def get_platform_selection():

    async def get_platform_selection_function(state):
        coinSymbol = state["coinSymbol"]

        current_price_binance, current_price_coinbase = await get_coin_price(
            coinSymbol)

        trustScore_binance, trustScore_coinbase = await get_platform_trust_score()

        spread_binance = await get_avg_spread_binance(coinSymbol)
        spread_coinbase = await get_avg_spread_coinbase(coinSymbol)

        # trading fee
        Coinbase_trading_taker_fee = "0.60%"
        Coinbase_trading_maker_fee = "0.40%"

        Binance_trading_taker_fee = "0.10%"
        Binance_trading_maker_fee = "0.10%"

        # deposit,withdraw options
        deposit_withdraw_options_binance = {
            "deposit_methods": [
                "Bank Transfer",
                "Credit/Debit Card",
                "P2P Trading",
                "Crypto Transfer"
            ],
            "withdrawal_methods": [
                "Bank Transfer",
                "Credit/Debit Card",
                "P2P Trading",
                "Crypto Transfer"
            ]
        }
        deposit_withdraw_options_coinbase = {
            "deposit_methods": [
                "Bank Transfer",
                "PayPal",
                "Credit/Debit Card",
                "Crypto Transfer"
            ],
            "withdrawal_methods": [
                "Bank Transfer",
                "PayPal",
                "Credit/Debit Card",
                "Crypto Transfer"
            ]
        }

        state["platform_selection"] = {
            "platforms": {
                "Binance": {
                    "current_price": current_price_binance,
                    "trust_score": trustScore_binance,
                    "avg_spread_pct": spread_binance,
                    "trading_fees": {
                        "taker_fee": Binance_trading_taker_fee,
                        "maker_fee": Binance_trading_maker_fee
                    },
                    "deposit_withdraw_options": deposit_withdraw_options_binance
                },
                "Coinbase": {
                    "current_price": current_price_coinbase,
                    "trust_score": trustScore_coinbase,
                    "avg_spread_pct": spread_coinbase,
                    "trading_fees": {
                        "taker_fee": Coinbase_trading_taker_fee,
                        "maker_fee": Coinbase_trading_maker_fee
                    },
                    "deposit_withdraw_options": deposit_withdraw_options_coinbase
                }
            }
        }

        return state
    return get_platform_selection_function


# current price
async def get_coin_price(coinSymbol: str):
    url_binance = f"https://api.binance.com/api/v3/ticker/price?symbol={coinSymbol}USDT"
    response_binance = requests.get(url_binance)
    price_binance = float(response_binance.json()['price'])

    url_coinBase = f"https://api.exchange.coinbase.com/products/{coinSymbol}-USD/ticker"
    response_coinbase = requests.get(url_coinBase)
    price_coinbase = float(response_coinbase.json()['price'])

    return price_binance, price_coinbase


# Liquidity (Spread / Volume) : Lower spread = higher liquidity (better execution).
async def get_avg_spread_binance(coinSymbol: str, limit=1000):
    url = "https://api.binance.com/api/v3/depth"
    params = {"symbol": f"{coinSymbol}USDT", "limit": limit}
    data = requests.get(url, params=params).json()

    bids = [float(b[0]) for b in data["bids"][:limit]]
    asks = [float(a[0]) for a in data["asks"][:limit]]

    avg_bid = sum(bids) / len(bids)
    avg_ask = sum(asks) / len(asks)
    mid = (avg_bid + avg_ask) / 2
    spread_pct = (avg_ask - avg_bid) / mid * 100

    return spread_pct


async def get_avg_spread_coinbase(coinSymbol: str, limit=1000):
    url = f"https://api.exchange.coinbase.com/products/{coinSymbol}-USD/book"
    params = {"level": 2}
    data = requests.get(url, params=params).json()

    bids = [float(b[0]) for b in data["bids"][:limit]]
    asks = [float(a[0]) for a in data["asks"][:limit]]

    avg_bid = sum(bids) / len(bids)
    avg_ask = sum(asks) / len(asks)
    mid = (avg_bid + avg_ask) / 2
    spread_pct = (avg_ask - avg_bid) / mid * 100

    return spread_pct


# platform trust score
async def get_platform_trust_score():
    trustScore_binance_url = "https://api.coingecko.com/api/v3/exchanges/binance"
    trustScore_binance_response = requests.get(trustScore_binance_url).json()
    trustScore_binance = trustScore_binance_response['trust_score']
    print(f"Binance Trust Score: {trustScore_binance}")

    trustScore_coinbase = 10

    return trustScore_binance, trustScore_coinbase
