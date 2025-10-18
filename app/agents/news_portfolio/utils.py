# app/agents/portfolio_agent/utils.py
import requests
from functools import lru_cache

COINGECKO_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


@lru_cache(maxsize=1)
def fetch_coin_catalog():
    """Retrieve and cache the list of all available coins."""
    r = requests.get(COINGECKO_LIST_URL, timeout=30)
    r.raise_for_status()
    data = r.json()

    by_id = {c["id"].lower(): c for c in data}
    by_symbol, by_name = {}, {}
    for c in data:
        by_symbol.setdefault(c["symbol"].lower(), c)
        by_name.setdefault(c["name"].lower(), c)
    return by_id, by_symbol, by_name


def resolve_to_id(token, by_id, by_symbol, by_name):
    """Convert a user-entered coin name/symbol to its CoinGecko ID."""
    print("Entering to resolve token:", token)
    # print("by_id: ", by_id)
    print("by_symbol: ", by_symbol)
    print("by_name: ", by_name)

    t = token.strip().lower()
    print("Normalized token:", t)
    if t in by_id:
        return by_id[t]["id"]
    if t in by_symbol:
        return by_symbol[t]["id"]
    if t in by_name:
        return by_name[t]["id"]
    t_dash = t.replace(" ", "-")
    return by_id.get(t_dash, {}).get("id")


def fetch_prices(coin_ids):
    """Fetch current USD prices for a list of coin IDs."""
    params = {"ids": ",".join(coin_ids), "vs_currencies": "usd"}
    r = requests.get(COINGECKO_PRICE_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def calculate_portfolio_value(portfolio):
    """Compute total USD value and per-coin breakdown."""
    if not portfolio:
        return 0.0, {}
    prices = fetch_prices(list(portfolio.keys()))
    total_value = 0.0
    breakdown = {}
    for coin_id, amount in portfolio.items():
        price = float(prices.get(coin_id, {}).get("usd", 0.0))
        value = price * float(amount)
        breakdown[coin_id] = {
            "amount": float(amount),
            "price": price,
            "value": value,
        }
        total_value += value
    return total_value, breakdown


def format_report(total, breakdown, by_id):
    """Generate a human-readable text summary of the portfolio."""
    lines = []
    for cid, row in breakdown.items():
        name = by_id.get(cid, {}).get("name", cid).title()
        lines.append(
            f"- {name}: {row['amount']} @ ${row['price']:.4f} → ${row['value']:,.2f}"
        )
    summary = "\n".join(lines)
    return f"{summary}\n\n💰 Total Portfolio Value: ${total:,.2f}\n"
