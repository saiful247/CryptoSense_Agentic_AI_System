import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta


def estimate_crypto_return_with_csv():
    def estimate_crypto_return_with_csv_function(
        state,
        csv_path: str = "http/avarageMonthlyInflationRate.csv"
    ):
        print("Entering estimate_crypto_return_with_csv_function...State: ", state)
        finance_metrics = state["finance_metrics"]
        # Convert percentages → decimals
        cagr = finance_metrics.get("cagr") / 100
        annual_volatility = finance_metrics.get("volatility") / 100
        max_drawdown = finance_metrics.get("max_drawdown") / 100

        invest_amount = state["input"]["amountUSD"]
        duration_months = state["input"]["investmentDurationMonths"]
        start_date = state["input"]["investmentStartDate"]

        # Load inflation rates from CSV
        df = pd.read_csv(csv_path)
        infl_map = {row["month_num"]: row["inflation_rate"]
                    for _, row in df.iterrows()}

        # Monthly CAGR growth
        monthly_growth = (1 + cagr) ** (1/12) - 1

        # Initialize
        nominal_value = invest_amount
        real_value = invest_amount
        date = datetime.strptime(start_date, "%Y-%m-%d")

        records = []

        for i in range(duration_months):
            month_num = (date.month + i - 1) % 12 + 1   # loop through 1–12
            infl_rate = infl_map[month_num] / 100.0     # % → decimal

            # Apply growth
            nominal_value *= (1 + monthly_growth)

            # Apply inflation adjustment
            real_value = nominal_value / (1 + infl_rate)

            records.append({
                "month": (date + relativedelta(months=i)).strftime("%Y-%m"),
                "nominal_value": round(nominal_value, 2),
                "inflation_rate": infl_rate,
                "real_value": round(real_value, 2)
            })

        print("Estimated Return Records: ", records)

        # Risk scenarios
        years = duration_months / 12
        fv_best = invest_amount * ((1 + (cagr + annual_volatility)) ** years)
        fv_worst = invest_amount * ((1 + (cagr - annual_volatility)) ** years)
        fv_drawdown = invest_amount * (1 + max_drawdown)

        print("Final Estimates - Nominal: ", nominal_value,
              "Real: ", real_value)
        print("Final Estimates - Best Case: ", fv_best,
              "Worst Case: ", fv_worst, "Drawdown Floor: ", fv_drawdown)

        # state["estimated_return_usd"] = {
        #     "timeline": records,
        #     "final_estimates": {
        #         "future_value_nominal_usd": round(nominal_value, 2),
        #         "future_value_real_usd": round(real_value, 2),
        #         "best_case_volatility_usd": round(fv_best, 2),
        #         "worst_case_volatility_usd": round(fv_worst, 2),
        #         "drawdown_floor_usd": round(fv_drawdown, 2)
        #     }
        # }
        state["estimated_return_usd"] = {
            "future_value_nominal_usd": round(nominal_value, 2),
            "future_value_real_usd": round(real_value, 2),
            "best_case_volatility_usd": round(fv_best, 2),
            "worst_case_volatility_usd": round(fv_worst, 2),
            "drawdown_floor_usd": round(fv_drawdown, 2)
        }
        return state
    return estimate_crypto_return_with_csv_function
