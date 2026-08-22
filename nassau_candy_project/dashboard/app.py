"""
Nassau Candy Distributor — Product Line Profitability & Margin Performance Dashboard
--------------------------------------------------------------------------------------
Run with:
    streamlit run app.py
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "analysis"))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    load_and_clean, add_metrics, product_summary, division_summary,
    division_margin_trend, margin_volatility, pareto_analysis,
    pareto_headline, cost_diagnostics
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nassau_candy_sales.csv")

FACTORY_COORDS = {
    "Lot's O' Nuts":     (32.881893, -111.768036),
    "Wicked Choccy's":   (32.076176, -81.088371),
    "Sugar Shack":       (48.11914, -96.18115),
    "Secret Factory":    (41.446333, -90.565487),
    "The Other Factory": (35.1175, -89.971107),
}
PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack", "Sweetarts": "Sugar Shack", "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack", "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory", "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory", "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory",
}

st.set_page_config(
    page_title="Nassau Candy | Profitability & Margin Analysis",
    page_icon="🍬",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data():
    df, stats = load_and_clean(DATA_PATH)
    df = add_metrics(df)
    return df, stats

df_full, clean_stats = get_data()

# ---------------------------------------------------------------------------
# Sidebar — global filters (User Capabilities)
# ---------------------------------------------------------------------------
st.sidebar.title("🍬 Nassau Candy")
st.sidebar.caption("Product Line Profitability & Margin Performance Analysis")
st.sidebar.divider()

min_date, max_date = df_full["Order Date"].min(), df_full["Order Date"].max()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date.date(), max_date.date()

divisions = sorted(df_full["Division"].unique())
selected_divisions = st.sidebar.multiselect("Division filter", divisions, default=divisions)

margin_threshold = st.sidebar.slider(
    "Minimum gross margin % (product view)", 0, 100, 0, step=5,
    help="Hide products below this margin in the product tables/charts."
)

product_search = st.sidebar.text_input("Product search", placeholder="e.g. Nerds, Gobstopper...")

regions = sorted(df_full["Region"].unique())
selected_regions = st.sidebar.multiselect("Region (optional)", regions, default=regions)

st.sidebar.divider()
with st.sidebar.expander("Data quality summary"):
    st.write(f"Rows loaded (raw): **{clean_stats['rows_in']:,}**")
    st.write(f"Rows after cleaning: **{clean_stats['rows_out']:,}**")
    st.write(f"Dropped (invalid/zero-sales): **{clean_stats['rows_dropped']:,}**")
    st.write(f"Missing units imputed: **{clean_stats['missing_units_before']:,}**")
    st.write(f"Missing profit recomputed: **{clean_stats['missing_profit_before']:,}**")
    st.write(f"Ship Date records failing sanity check: **{clean_stats['ship_date_unreliable']:,} "
             f"({clean_stats['ship_date_unreliable_pct']}%)**")
    st.caption("Ship Date in this export lags Order Date by multiple years on every "
               "affected row — a source data-quality issue, not late shipping. "
               "Ship Date / fulfillment-time metrics are excluded from this dashboard "
               "as a result; Sales, Cost, and Gross Profit are unaffected.")

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
mask = (
    (df_full["Order Date"].dt.date >= start_date)
    & (df_full["Order Date"].dt.date <= end_date)
    & (df_full["Division"].isin(selected_divisions))
    & (df_full["Region"].isin(selected_regions))
)
df = df_full[mask].copy()

if product_search:
    df_search_hit = df[df["Product Name"].str.contains(product_search, case=False, na=False)]
else:
    df_search_hit = df

if df.empty:
    st.warning("No records match the current filters. Adjust the sidebar filters.")
    st.stop()

prod = product_summary(df)
prod = prod[prod["Gross Margin %"] >= margin_threshold]
div = division_summary(df)
vol = margin_volatility(df)
trend = division_margin_trend(df)
diag = cost_diagnostics(product_summary(df))  # unfiltered by margin slider, for risk view

# ---------------------------------------------------------------------------
# Header KPIs
# ---------------------------------------------------------------------------
st.title("Product Line Profitability & Margin Performance Analysis")
st.caption("Nassau Candy Distributor — live analytics dashboard")

total_sales = df["Sales"].sum()
total_profit = df["Gross Profit"].sum()
overall_margin = total_profit / total_sales * 100 if total_sales else 0
total_units = df["Units"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Gross Profit", f"${total_profit:,.0f}")
k3.metric("Overall Gross Margin", f"{overall_margin:.1f}%")
k4.metric("Total Units Sold", f"{total_units:,.0f}")
k5.metric("Active Products", f"{df['Product Name'].nunique()}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Product Profitability",
    "🏭 Division Performance",
    "⚠️ Cost vs Margin Diagnostics",
    "📈 Profit Concentration (Pareto)",
])

# ---------------------------------------------------------------------------
# TAB 1 — Product Profitability Overview
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Product-level margin leaderboard")
    left, right = st.columns([3, 2])

    with left:
        sort_metric = st.radio(
            "Rank products by", ["Total_Profit", "Gross Margin %", "Total_Sales"],
            horizontal=True, format_func=lambda x: {
                "Total_Profit": "Gross Profit", "Gross Margin %": "Gross Margin %",
                "Total_Sales": "Sales"}[x]
        )
        board = prod.sort_values(sort_metric, ascending=False)
        fig = px.bar(
            board, x=sort_metric, y="Product Name", color="Division", orientation="h",
            hover_data=["Gross Margin %", "Total_Sales", "Total_Profit", "Classification"],
            title=None,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("**Product classification mix**")
        class_counts = prod["Classification"].value_counts().reset_index()
        class_counts.columns = ["Classification", "Count"]
        fig2 = px.pie(class_counts, names="Classification", values="Count", hole=0.45)
        fig2.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Profit contribution share**")
        fig3 = px.treemap(
            prod, path=["Division", "Product Name"], values="Total_Profit",
            color="Gross Margin %", color_continuous_scale="RdYlGn",
        )
        fig3.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**Full product table**")
    show_cols = ["Product Name", "Division", "Total_Sales", "Total_Units", "Total_Cost",
                 "Total_Profit", "Gross Margin %", "Profit per Unit",
                 "Revenue Contribution %", "Profit Contribution %", "Classification"]
    st.dataframe(
        prod[show_cols].style.format({
            "Total_Sales": "${:,.0f}", "Total_Cost": "${:,.0f}", "Total_Profit": "${:,.0f}",
            "Gross Margin %": "{:.1f}%", "Profit per Unit": "${:,.2f}",
            "Revenue Contribution %": "{:.1f}%", "Profit Contribution %": "{:.1f}%",
        }),
        use_container_width=True, hide_index=True,
    )

    if product_search and not df_search_hit.empty:
        st.info(f"🔎 {df_search_hit['Product Name'].nunique()} product(s) match '{product_search}' "
                f"within the current filters.")

# ---------------------------------------------------------------------------
# TAB 2 — Division Performance Dashboard
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Revenue vs profit comparison by division")
    c1, c2 = st.columns([3, 2])

    with c1:
        div_melt = div.melt(id_vars="Division", value_vars=["Revenue Share %", "Profit Share %"],
                             var_name="Metric", value_name="Share %")
        figd = px.bar(div_melt, x="Division", y="Share %", color="Metric", barmode="group",
                      text_auto=".1f")
        figd.update_layout(height=420)
        st.plotly_chart(figd, use_container_width=True)
        st.caption(
            "A positive **Revenue-Profit Imbalance** means a division earns a larger share of "
            "profit than its share of revenue (efficient); negative means the opposite "
            "(revenue-heavy but margin-light)."
        )

    with c2:
        figg = go.Figure(go.Bar(
            x=div["Revenue-Profit Imbalance (pp)"], y=div["Division"], orientation="h",
            marker_color=np.where(div["Revenue-Profit Imbalance (pp)"] >= 0, "#2e7d32", "#c62828"),
        ))
        figg.update_layout(title="Revenue-Profit Imbalance (pp)", height=420,
                            xaxis_title="Percentage points")
        st.plotly_chart(figg, use_container_width=True)

    st.subheader("Margin distribution by division")
    c3, c4 = st.columns([3, 2])
    with c3:
        figbox = px.box(df, x="Division", y="Gross Margin %", color="Division", points="outliers")
        figbox.update_layout(height=420, showlegend=False)
        st.plotly_chart(figbox, use_container_width=True)
    with c4:
        st.markdown("**Margin volatility (std. dev. of monthly margin)**")
        st.dataframe(vol, use_container_width=True, hide_index=True)
        st.caption("Higher values indicate a division whose margin swings more month-to-month — "
                   "a signal of pricing or cost instability worth investigating.")

    st.subheader("Monthly gross margin trend")
    figtrend = px.line(trend, x="Order Month", y="Gross Margin %", color="Division", markers=True)
    figtrend.update_layout(height=380)
    st.plotly_chart(figtrend, use_container_width=True)

    st.markdown("**Division summary table**")
    st.dataframe(
        div.style.format({
            "Total_Sales": "${:,.0f}", "Total_Cost": "${:,.0f}", "Total_Profit": "${:,.0f}",
            "Gross Margin %": "{:.1f}%", "Revenue Share %": "{:.1f}%", "Profit Share %": "{:.1f}%",
            "Revenue-Profit Imbalance (pp)": "{:+.1f}",
        }),
        use_container_width=True, hide_index=True,
    )

# ---------------------------------------------------------------------------
# TAB 3 — Cost vs Margin Diagnostics
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Cost vs sales scatter — margin risk view")
    figsc = px.scatter(
        diag, x="Total_Sales", y="Total_Cost", size="Total_Units", color="Risk Flag",
        hover_name="Product Name",
        color_discrete_map={
            "Healthy": "#2e7d32", "Repricing Review": "#f9a825",
            "Cost Renegotiation": "#ef6c00", "Discontinuation Review": "#c62828",
        },
        hover_data=["Division", "Gross Margin %", "Cost-to-Sales Ratio %"],
    )
    # 1:1 reference line = 0% margin
    max_val = max(diag["Total_Sales"].max(), diag["Total_Cost"].max()) * 1.05
    figsc.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                     line=dict(dash="dot", color="gray"))
    figsc.update_layout(height=480)
    st.plotly_chart(figsc, use_container_width=True)
    st.caption("Points near the dotted line have costs approaching sales value (thin/near-zero margin). "
               "Bubble size = total units sold.")

    st.subheader("Margin risk flags")
    flag_counts = diag["Risk Flag"].value_counts().reset_index()
    flag_counts.columns = ["Risk Flag", "Products"]
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(flag_counts, use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(
            diag[diag["Risk Flag"] != "Healthy"][
                ["Product Name", "Division", "Gross Margin %", "Cost-to-Sales Ratio %", "Risk Flag"]
            ].style.format({"Gross Margin %": "{:.1f}%", "Cost-to-Sales Ratio %": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
        )

    st.markdown("**Recommended actions**")
    action_map = {
        "Repricing Review": "High revenue contribution but below-median margin — evaluate a targeted price increase or portion-size adjustment.",
        "Cost Renegotiation": "Cost-to-sales ratio ≥ 75% — renegotiate supplier/factory input costs or review manufacturing efficiency.",
        "Discontinuation Review": "Gross margin below 10% — assess whether the product should be discontinued or fundamentally repositioned.",
    }
    for flag, note in action_map.items():
        n = (diag["Risk Flag"] == flag).sum()
        if n:
            st.write(f"- **{flag}** ({n} product{'s' if n != 1 else ''}): {note}")

# ---------------------------------------------------------------------------
# TAB 4 — Profit Concentration (Pareto) Analysis
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Pareto analysis — profit concentration")
    metric_choice = st.radio("Metric", ["Gross Profit", "Sales"], horizontal=True)
    pareto_df = pareto_analysis(df, metric=metric_choice, by="Product Name")
    headline = pareto_headline(pareto_df)

    st.info(
        f"**{headline['n_items_for_80pct']} of {headline['total_items']} products "
        f"({headline['pct_items_for_80pct']}%)** generate 80% of total {metric_choice.lower()}."
    )

    figp = go.Figure()
    figp.add_bar(x=pareto_df["Product Name"], y=pareto_df[metric_choice], name=metric_choice)
    figp.add_trace(go.Scatter(x=pareto_df["Product Name"], y=pareto_df["Cumulative %"],
                               name="Cumulative %", yaxis="y2", mode="lines+markers",
                               line=dict(color="#c62828")))
    figp.add_hline(y=80, line_dash="dot", line_color="gray", yref="y2")
    figp.update_layout(
        height=480,
        yaxis=dict(title=metric_choice),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        xaxis=dict(tickangle=-40),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(figp, use_container_width=True)

    st.subheader("Geographic / factory dependency")
    st.caption("Profit concentration by sourcing factory — an over-dependency risk indicator.")
    df_fact = df.copy()
    df_fact["Factory"] = df_fact["Product Name"].map(PRODUCT_FACTORY)
    fact_profit = df_fact.groupby("Factory", as_index=False)["Gross Profit"].sum().sort_values(
        "Gross Profit", ascending=False)
    fact_profit["Share %"] = (fact_profit["Gross Profit"] / fact_profit["Gross Profit"].sum() * 100).round(1)
    c1, c2 = st.columns([2, 3])
    with c1:
        st.dataframe(fact_profit, use_container_width=True, hide_index=True)
    with c2:
        figf = px.pie(fact_profit, names="Factory", values="Gross Profit", hole=0.4)
        figf.update_layout(height=340, margin=dict(t=10, b=10))
        st.plotly_chart(figf, use_container_width=True)

    st.markdown("**Ranked contribution table**")
    st.dataframe(
        pareto_df.style.format({metric_choice: "${:,.0f}", "Cumulative": "${:,.0f}",
                                 "Cumulative %": "{:.1f}%", "Item Rank %": "{:.1f}%"}),
        use_container_width=True, hide_index=True,
    )

st.divider()
st.caption(
    "Data is synthetically generated for academic/demo purposes but structured to match "
    "Nassau Candy Distributor's real order-level schema and Division→Product→Factory mapping. "
    "Built with Streamlit, Pandas, and Plotly."
)
