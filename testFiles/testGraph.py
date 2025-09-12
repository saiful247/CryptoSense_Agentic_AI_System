import matplotlib.pyplot as plt

data = {
    "price": 4342.087872309703,
    "volume_24h": 46773360124.45501,
    "volume_change_24h": 17.7647,
    "percent_change_1h": 0.14096949,
    "percent_change_24h": -3.4190724,
    "percent_change_7d": -9.47329805,
    "percent_change_30d": 13.8356476,
    "percent_change_60d": 74.47098115,
    "percent_change_90d": 71.09046013,
    "market_cap": 524119084067.21216,
    "market_cap_dominance": 13.9557,
    "fully_diluted_market_cap": 524119084067.21
}

# ---- Percent Change Line Chart ----
timeframes = ["1h", "24h", "7d", "30d", "60d", "90d"]
percent_changes = [
    data["percent_change_1h"],
    data["percent_change_24h"],
    data["percent_change_7d"],
    data["percent_change_30d"],
    data["percent_change_60d"],
    data["percent_change_90d"]
]

plt.plot(timeframes, percent_changes, marker="o")
plt.title("Ethereum % Change Over Timeframes")
plt.xlabel("Timeframe")
plt.ylabel("Percent Change (%)")
plt.grid(True)
plt.show()
