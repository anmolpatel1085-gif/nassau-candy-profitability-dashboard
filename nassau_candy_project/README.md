# Product Line Profitability & Margin Performance Analysis
### Nassau Candy Distributor — Final-Year Project (Real Internship Data)

A complete, working analytics project built on a **real internship data
export**: data cleaning/validation, a reusable Python analytics engine, an
offline EDA script, and a live multi-tab Streamlit dashboard — all built
around the exact schema and KPI definitions from the original project
brief.

---

## 1. Project Structure

```
nassau_candy_project/
├── data/
│   └── nassau_candy_sales.csv    # REAL internship dataset (10,194 order lines)
├── analysis/
│   ├── analytics.py              # shared analytics engine (cleaning, KPIs, Pareto, diagnostics)
│   ├── run_eda.py                # offline EDA — prints + saves summary tables
│   └── outputs/                  # CSV outputs from run_eda.py (created on first run)
├── dashboard/
│   └── app.py                    # Streamlit dashboard (4 modules, full filter set)
├── docs/
│   ├── Research_Paper.docx       # EDA, insights & recommendations write-up
│   └── Executive_Summary.docx    # 1-page summary for stakeholders
├── requirements.txt
└── README.md
```

## 2. About the Dataset

This project now runs entirely on the **real dataset supplied for this
internship** (`data/nassau_candy_sales.csv`) — the earlier synthetic
sample dataset and its generator script have been removed. The file
matches the schema from the original brief: Row ID, Order ID, Order Date,
Ship Date, Ship Mode, Customer ID, Country/Region, City, State/Province,
Postal Code, Division, Region, Product ID, Product Name, Sales, Units,
Gross Profit, Cost.

**Dataset profile:**
- 10,194 order lines, January 2, 2024 – December 31, 2025
- 15 products across 3 divisions (Chocolate, Sugar, Other)
- 5,044 unique customers across 59 states/provinces, 542 cities, 2 countries
  (United States, Canada)
- 100% of rows had complete Sales/Cost/Profit/Units values — **no rows were
  dropped or imputed**

**Data-quality issue found and handled (not hidden):** the `Ship Date`
column in this export is systematically 900–1,642 days (roughly 2.5–4.5
years) later than `Order Date` on **every single row** — not consistent
with real shipping behavior, and almost certainly a format/export issue
in that column at the source. `analytics.py::load_and_clean()` detects
and reports this (see the `ship_date_unreliable` stat and the dashboard's
"Data quality summary" panel) and **excludes Ship Date from all downstream
metrics** rather than silently trusting it or computing a meaningless
fulfillment-time KPI. Sales, Cost, and Gross Profit are unaffected and
were used as-is. This is documented in full in Section 3.2 of the
research paper — a good thing to be able to speak to in your viva.

If you get a corrected or more complete export later, just replace
`data/nassau_candy_sales.csv` with it (keeping the same column names) —
`analytics.py`, `run_eda.py`, and `app.py` all work unchanged, and the
Ship Date check will simply report 0 unreliable rows once the field is
fixed.

## 3. Setup — Step by Step

### Step 1: Install Python dependencies
```bash
cd nassau_candy_project
pip install -r requirements.txt
```
(Python 3.10+ recommended.)

### Step 2: Run the offline EDA (optional but recommended)
```bash
cd analysis
python run_eda.py
```
This prints the full analysis (cleaning stats, top/bottom products,
division performance, margin volatility, Pareto concentration, cost/margin
risk flags) to the console and saves summary tables to `analysis/outputs/`.
These are the exact numbers used in `docs/Research_Paper.docx`.

### Step 3: Launch the Streamlit dashboard
```bash
cd ../dashboard
streamlit run app.py
```
Streamlit will open the dashboard in your browser (default:
`http://localhost:8501`).

## 4. Dashboard Guide

| Sidebar control | What it does |
|---|---|
| Order date range | Filters every chart/table to the selected date window |
| Division filter | Show only selected divisions (Chocolate / Sugar / Other) |
| Minimum gross margin % slider | Hides low-margin products from the product views |
| Product search | Highlights products matching a text search |
| Region filter | Restricts to selected customer regions (Interior / Atlantic / Gulf / Pacific) |
| Data quality summary (expander) | Shows rows cleaned + the Ship Date reliability check |

| Tab | Contents |
|---|---|
| **📊 Product Profitability** | Ranked leaderboard (profit/margin/sales), classification pie, profit treemap, full sortable product table |
| **🏭 Division Performance** | Revenue vs profit share, revenue-profit imbalance, margin box-plot, monthly margin trend, margin volatility table |
| **⚠️ Cost vs Margin Diagnostics** | Cost-vs-sales scatter with risk flags, recommended actions per flag |
| **📈 Profit Concentration (Pareto)** | Pareto chart (80/20 line), factory/sourcing dependency view, ranked cumulative-contribution table |

## 5. Key KPI Definitions (as specified in the brief)

| KPI | Formula |
|---|---|
| Gross Margin (%) | Gross Profit ÷ Sales |
| Profit per Unit | Gross Profit ÷ Units |
| Revenue Contribution | Product Sales ÷ Total Sales |
| Profit Contribution | Product Profit ÷ Total Profit |
| Margin Volatility | Std. deviation of monthly gross margin |

Note: a "Fulfillment Days" KPI is **not** computed — see Section 2 above
on the Ship Date data-quality issue.

## 6. Headline Findings (from the real data)

- **Chocolate dominates:** 92.9% of revenue, 95.1% of profit, 67.5% gross margin
- **Profit concentration is high:** just 5 of 15 products (all Chocolate SKUs) drive over 95% of total profit
- **One risk product:** Kazookles — 7.7% margin, cost = 92.3% of sales, flagged "Repricing Review"
- **Sugar & Other are thin on data:** only 40 and 304 orders respectively over two years — worth confirming with the source system
- Full detail, tables, and recommendations are in `docs/Research_Paper.docx`

## 7. Deliverables Checklist (per brief)

- [x] Research paper (EDA, insights, recommendations) — `docs/Research_Paper.docx`
- [x] Streamlit dashboard (live analytics) — `dashboard/app.py`
- [x] Executive summary for stakeholders — `docs/Executive_Summary.docx`
- [x] Data cleaning & validation logic — `analysis/analytics.py :: load_and_clean()`
- [x] Product-level profitability analysis — `analytics.py :: product_summary()`
- [x] Division-level performance analysis — `analytics.py :: division_summary()`
- [x] Profit concentration / Pareto analysis — `analytics.py :: pareto_analysis()`
- [x] Cost structure diagnostics — `analytics.py :: cost_diagnostics()`

## 8. Extending the Project

- **Investigate the Ship Date issue:** if you get access to the original source system, check whether the offset is a fixed constant (e.g., a wrong default year) — if so it may be trivially correctable rather than unusable.
- **Confirm Sugar/Other volumes:** before presenting the concentration finding as final, it's worth asking whoever provided the export whether Sugar/Other really only had ~40/~304 orders in two years, or whether some rows were filtered out before export.
- **Add forecasting:** the `Order Month` column in `analytics.add_metrics()` is ready for a time-series model (e.g., Prophet or ARIMA) on monthly division revenue/margin.
- **Deploy the dashboard:** push this folder to a GitHub repo and deploy free on [Streamlit Community Cloud](https://streamlit.io/cloud) by pointing it at `dashboard/app.py`.
- **Geospatial view:** `FACTORY_COORDS` in `app.py` has factory lat/longs from the original brief (no factory column exists in this export) — a `st.map()` layer could visualize sourcing geography.

## 9. Notes for Your Report / Viva

- This project now uses your **real internship data**, not a sample/generated dataset — say so plainly, and be ready to speak to the Ship Date data-quality finding, which is a genuine, defensible piece of analysis in its own right.
- Every KPI, chart, and table in the dashboard traces back to a specific bullet point in the original brief — use the table in Section 7 above to map your dashboard demo directly to the requirements during your viva/defense.
- The concentration finding (95%+ of profit from 5 Chocolate SKUs) is the single most important number to lead with — it's a stronger, more specific story than a generic "some products are more profitable than others."
