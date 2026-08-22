"""
run_eda.py
----------
Runs the full offline analysis pipeline described in the project brief and
prints a findings summary. Use this to regenerate the numbers quoted in the
research paper / executive summary after any change to the dataset.

Run:
    python run_eda.py
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
from analytics import (
    load_and_clean, add_metrics, product_summary, division_summary,
    division_margin_trend, margin_volatility, pareto_analysis,
    pareto_headline, cost_diagnostics
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nassau_candy_sales.csv")

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)


def main():
    print("=" * 80)
    print("NASSAU CANDY DISTRIBUTOR — PRODUCT LINE PROFITABILITY & MARGIN ANALYSIS")
    print("=" * 80)

    # 1. Clean
    df, stats = load_and_clean(DATA_PATH)
    print("\n[1] DATA CLEANING & VALIDATION")
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # 2. Metrics
    df = add_metrics(df)

    # 3. Product-level
    prod = product_summary(df)
    print("\n[2] TOP 5 PRODUCTS BY TOTAL PROFIT")
    print(prod[["Product Name", "Division", "Total_Sales", "Total_Profit",
                "Gross Margin %", "Classification"]].head(5).to_string(index=False))

    print("\n[3] BOTTOM 5 PRODUCTS BY GROSS MARGIN %")
    print(prod.sort_values("Gross Margin %").head(5)[
        ["Product Name", "Division", "Total_Sales", "Gross Margin %", "Classification"]
    ].to_string(index=False))

    print("\n[4] CLASSIFICATION COUNTS")
    print(prod["Classification"].value_counts().to_string())

    # 4. Division-level
    div = division_summary(df)
    print("\n[5] DIVISION PERFORMANCE")
    print(div.to_string(index=False))

    vol = margin_volatility(df)
    print("\n[6] MARGIN VOLATILITY BY DIVISION (higher = less stable margins)")
    print(vol.to_string(index=False))

    # 5. Pareto
    pareto_profit = pareto_analysis(df, metric="Gross Profit")
    headline = pareto_headline(pareto_profit)
    print("\n[7] PROFIT CONCENTRATION (PARETO)")
    print(f"    {headline['n_items_for_80pct']} of {headline['total_items']} products "
          f"({headline['pct_items_for_80pct']}%) generate 80% of total gross profit.")

    pareto_sales = pareto_analysis(df, metric="Sales")
    headline_sales = pareto_headline(pareto_sales)
    print(f"    {headline_sales['n_items_for_80pct']} of {headline_sales['total_items']} products "
          f"({headline_sales['pct_items_for_80pct']}%) generate 80% of total revenue.")

    # 6. Cost diagnostics
    diag = cost_diagnostics(prod)
    print("\n[8] COST / MARGIN RISK FLAGS")
    print(diag["Risk Flag"].value_counts().to_string())
    print("\n    Products flagged for review:")
    print(diag[diag["Risk Flag"] != "Healthy"][
        ["Product Name", "Division", "Gross Margin %", "Cost-to-Sales Ratio %", "Risk Flag"]
    ].to_string(index=False))

    # Save key tables for reuse in the report
    out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(out_dir, exist_ok=True)
    prod.to_csv(os.path.join(out_dir, "product_summary.csv"), index=False)
    div.to_csv(os.path.join(out_dir, "division_summary.csv"), index=False)
    diag.to_csv(os.path.join(out_dir, "cost_diagnostics.csv"), index=False)
    pareto_profit.to_csv(os.path.join(out_dir, "pareto_profit.csv"), index=False)
    print(f"\nSaved summary tables to: {out_dir}")


if __name__ == "__main__":
    main()
