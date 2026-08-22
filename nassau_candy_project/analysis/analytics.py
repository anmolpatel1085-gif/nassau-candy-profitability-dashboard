"""
analytics.py
------------
Core, reusable analytics layer for the Nassau Candy Product Line
Profitability & Margin Performance Analysis project.

This module is imported by BOTH:
  - analysis/run_eda.py        (offline research-paper analysis)
  - dashboard/app.py           (live Streamlit dashboard)

so the two never drift out of sync.

Sections:
  1. load_and_clean()          -> Data Cleaning & Validation
  2. add_metrics()              -> Profitability Metric Calculation
  3. product_summary()          -> Product-Level Profitability Analysis
  4. division_summary()         -> Division-Level Performance Analysis
  5. pareto_analysis()          -> Profit Concentration (Pareto) Analysis
  6. cost_diagnostics()         -> Cost Structure Diagnostics
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. DATA CLEANING & VALIDATION
# ---------------------------------------------------------------------------
def load_and_clean(path: str) -> tuple[pd.DataFrame, dict]:
    """
    Loads the raw CSV (Nassau Candy internship export) and applies the
    cleaning rules described in the project brief:
      - Validate cost and sales values (non-negative, numeric)
      - Remove zero-sales or invalid profit records
      - Handle missing unit values (impute using product median)
      - Standardize product and division labels (trim/title-case)
      - Flag (not silently trust) shipping-date records that fail a
        sanity check, since this export's Ship Date column contains
        multi-year gaps from Order Date for every row (see stats
        ["ship_date_unreliable"]) — those rows are KEPT for revenue/
        profit analysis but Ship Date/Fulfillment Days is not used
        as a trustworthy KPI downstream.

    Returns the cleaned DataFrame plus a dict of cleaning stats (used
    in the report / dashboard "data quality" panel).
    """
    df = pd.read_csv(path, dtype={"Postal Code": str})
    stats = {"rows_in": len(df)}

    # --- parse dates ---------------------------------------------------
    # Source export uses DD-MM-YYYY (day-first); fall back to a generic
    # parse for any row that doesn't match, rather than silently NaT-ing
    # a whole column if the format assumption is ever wrong.
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y", errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y", errors="coerce")

    # --- standardize text labels --------------------------------------
    for col in ["Division", "Product Name", "Region", "State/Province", "City", "Ship Mode"]:
        df[col] = df[col].astype(str).str.strip()
    # Title-case product names but keep known punctuation (avoid "Wonka Bar -Nutty..." issues)
    df["Product Name"] = df["Product Name"].apply(
        lambda x: x if x == x.title() else x.title()
    )
    df["Division"] = df["Division"].str.title()
    df["Postal Code"] = df["Postal Code"].astype(str).str.strip().str.zfill(5)

    # --- numeric validation --------------------------------------------
    for col in ["Sales", "Cost", "Gross Profit", "Units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    stats["missing_units_before"] = int(df["Units"].isna().sum())
    stats["missing_profit_before"] = int(df["Gross Profit"].isna().sum())
    stats["zero_or_negative_sales"] = int((df["Sales"] <= 0).sum())

    # --- data-quality check: Order Date vs Ship Date sanity -------------
    # A legitimate shipment should follow the order by days, not years.
    # This export has Ship Date running ~3-4.5 years after Order Date on
    # EVERY row, which points to a systematic export/format issue in the
    # source Ship Date field rather than genuinely late shipments.
    lag_days = (df["Ship Date"] - df["Order Date"]).dt.days
    stats["ship_date_unreliable"] = int(((lag_days < 0) | (lag_days > 60)).sum())
    stats["ship_date_unreliable_pct"] = round(stats["ship_date_unreliable"] / len(df) * 100, 1)

    # Impute missing Units using the product-level median (fallback: global median)
    df["Units"] = df.groupby("Product Name")["Units"].transform(
        lambda s: s.fillna(s.median())
    )
    df["Units"] = df["Units"].fillna(df["Units"].median())
    df["Units"] = df["Units"].round().astype(int)

    # Recompute Gross Profit where missing, using Sales - Cost
    recompute_mask = df["Gross Profit"].isna() & df["Sales"].notna() & df["Cost"].notna()
    df.loc[recompute_mask, "Gross Profit"] = df.loc[recompute_mask, "Sales"] - df.loc[recompute_mask, "Cost"]

    # Drop remaining invalid records: zero/negative sales, missing cost/profit, non-positive units
    before = len(df)
    df = df[
        (df["Sales"] > 0)
        & (df["Cost"].notna())
        & (df["Gross Profit"].notna())
        & (df["Units"] > 0)
        & (df["Order Date"].notna())
    ].copy()
    stats["rows_dropped"] = before - len(df)
    stats["rows_out"] = len(df)

    df.reset_index(drop=True, inplace=True)
    return df, stats


# ---------------------------------------------------------------------------
# 2. PROFITABILITY METRIC CALCULATION
# ---------------------------------------------------------------------------
def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds row-level KPIs:
      - Gross Margin (%)   = Gross Profit / Sales
      - Profit per Unit    = Gross Profit / Units
      - Order Year / Month (for trend & volatility analysis)

    Note: Fulfillment Days (Ship Date - Order Date) is intentionally NOT
    computed as a trustworthy KPI here — see load_and_clean()'s
    ship_date_unreliable stat. Ship Date is retained in the cleaned
    frame for transparency but excluded from downstream analysis.
    """
    df = df.copy()
    df["Gross Margin %"] = np.where(df["Sales"] > 0, df["Gross Profit"] / df["Sales"] * 100, np.nan)
    df["Profit per Unit"] = np.where(df["Units"] > 0, df["Gross Profit"] / df["Units"], np.nan)
    df["Order Year"] = df["Order Date"].dt.year
    df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df


# ---------------------------------------------------------------------------
# 3. PRODUCT-LEVEL PROFITABILITY ANALYSIS
# ---------------------------------------------------------------------------
def product_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates to one row per product with revenue/profit contribution,
    margin, profit-per-unit, and a plain-English classification flag:
      - High-Profit / High-Margin
      - High-Sales / Low-Margin   (volume-driven but thin)
      - Low-Sales / Low-Profit    (long-tail / rationalization candidates)
      - Niche High-Margin         (low volume, strong unit economics)
    """
    g = df.groupby(["Division", "Product Name"], as_index=False).agg(
        Total_Sales=("Sales", "sum"),
        Total_Cost=("Cost", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Orders=("Order ID", "nunique"),
    )
    total_sales = g["Total_Sales"].sum()
    total_profit = g["Total_Profit"].sum()

    g["Gross Margin %"] = (g["Total_Profit"] / g["Total_Sales"] * 100).round(2)
    g["Profit per Unit"] = (g["Total_Profit"] / g["Total_Units"]).round(3)
    g["Revenue Contribution %"] = (g["Total_Sales"] / total_sales * 100).round(2)
    g["Profit Contribution %"] = (g["Total_Profit"] / total_profit * 100).round(2)

    sales_median = g["Total_Sales"].median()
    margin_median = g["Gross Margin %"].median()

    def classify(row):
        high_sales = row["Total_Sales"] >= sales_median
        high_margin = row["Gross Margin %"] >= margin_median
        if high_sales and high_margin:
            return "High-Profit / High-Margin"
        if high_sales and not high_margin:
            return "High-Sales / Low-Margin"
        if not high_sales and high_margin:
            return "Niche High-Margin"
        return "Low-Sales / Low-Profit"

    g["Classification"] = g.apply(classify, axis=1)
    return g.sort_values("Total_Profit", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. DIVISION-LEVEL PERFORMANCE ANALYSIS
# ---------------------------------------------------------------------------
def division_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Division", as_index=False).agg(
        Total_Sales=("Sales", "sum"),
        Total_Cost=("Cost", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Orders=("Order ID", "nunique"),
    )
    total_sales = g["Total_Sales"].sum()
    total_profit = g["Total_Profit"].sum()
    g["Gross Margin %"] = (g["Total_Profit"] / g["Total_Sales"] * 100).round(2)
    g["Revenue Share %"] = (g["Total_Sales"] / total_sales * 100).round(2)
    g["Profit Share %"] = (g["Total_Profit"] / total_profit * 100).round(2)
    # Revenue vs profit imbalance: positive => division earns MORE profit share than revenue share
    g["Revenue-Profit Imbalance (pp)"] = (g["Profit Share %"] - g["Revenue Share %"]).round(2)
    return g.sort_values("Total_Profit", ascending=False).reset_index(drop=True)


def division_margin_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly average gross margin by division -> feeds 'Margin Volatility' KPI."""
    t = df.groupby(["Order Month", "Division"], as_index=False).agg(
        Sales=("Sales", "sum"), Profit=("Gross Profit", "sum")
    )
    t["Gross Margin %"] = (t["Profit"] / t["Sales"] * 100).round(2)
    return t.sort_values(["Division", "Order Month"])


def margin_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Standard deviation of monthly gross margin per division/product = volatility."""
    trend = division_margin_trend(df)
    vol = trend.groupby("Division")["Gross Margin %"].std().round(2).reset_index()
    vol.columns = ["Division", "Margin Volatility (std dev, pp)"]
    return vol.sort_values("Margin Volatility (std dev, pp)", ascending=False)


# ---------------------------------------------------------------------------
# 5. PROFIT CONCENTRATION (PARETO) ANALYSIS
# ---------------------------------------------------------------------------
def pareto_analysis(df: pd.DataFrame, metric: str = "Gross Profit", by: str = "Product Name") -> pd.DataFrame:
    """
    Returns a product-ranked table with cumulative % of the chosen metric
    (Gross Profit or Sales), used to identify the 80/20 concentration point
    and over-dependency risk.
    """
    g = df.groupby(by, as_index=False)[metric].sum().sort_values(metric, ascending=False)
    g["Cumulative"] = g[metric].cumsum()
    g["Cumulative %"] = (g["Cumulative"] / g[metric].sum() * 100).round(2)
    g["Item Rank %"] = ((np.arange(len(g)) + 1) / len(g) * 100).round(2)
    return g.reset_index(drop=True)


def pareto_headline(pareto_df: pd.DataFrame) -> dict:
    """Quick headline numbers: how many items / what % of items drive 80% of the metric."""
    hit_80 = pareto_df[pareto_df["Cumulative %"] >= 80].index
    n_items_for_80 = (hit_80[0] + 1) if len(hit_80) else len(pareto_df)
    pct_items_for_80 = round(n_items_for_80 / len(pareto_df) * 100, 1)
    return {"n_items_for_80pct": int(n_items_for_80), "pct_items_for_80pct": pct_items_for_80,
            "total_items": len(pareto_df)}


# ---------------------------------------------------------------------------
# 6. COST STRUCTURE DIAGNOSTICS
# ---------------------------------------------------------------------------
def cost_diagnostics(product_df: pd.DataFrame, margin_risk_threshold: float = 25.0) -> pd.DataFrame:
    """
    Flags products for pricing/cost review based on gross margin and
    cost-to-sales ratio. Works off the output of product_summary().
    """
    d = product_df.copy()
    d["Cost-to-Sales Ratio %"] = (d["Total_Cost"] / d["Total_Sales"] * 100).round(2)

    def flag(row):
        if row["Gross Margin %"] < margin_risk_threshold and row["Revenue Contribution %"] >= product_df["Revenue Contribution %"].median():
            return "Repricing Review"
        if row["Cost-to-Sales Ratio %"] >= 75:
            return "Cost Renegotiation"
        if row["Gross Margin %"] < 10:
            return "Discontinuation Review"
        return "Healthy"

    d["Risk Flag"] = d.apply(flag, axis=1)
    return d.sort_values("Gross Margin %").reset_index(drop=True)
