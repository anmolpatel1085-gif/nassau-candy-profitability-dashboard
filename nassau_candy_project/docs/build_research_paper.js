const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, PageBreak,
  Header, Footer, PageNumber, LevelFormat,
} = require("docx");
const fs = require("fs");

const PAGE = { size: { width: 12240, height: 15840 } }; // US Letter

const NAVY = "1F3864";
const ACCENT = "C0392B";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({ text, ...opts })],
  });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 80 } });
}

function cell(text, { header = false, width, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: NAVY } : undefined,
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold: header, color: header ? "FFFFFF" : "000000", size: header ? 19 : 18 })],
    })],
  });
}

function dataTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((h, i) => cell(h, { header: true, width: widths[i] })) }),
      ...rows.map((r) => new TableRow({
        children: r.map((val, i) => cell(String(val), { width: widths[i], align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT })),
      })),
    ],
  });
}

// ---------------------------------------------------------------------------
// Data pulled from analysis/outputs after running analysis/run_eda.py on the
// real internship export (data/nassau_candy_sales.csv). Regenerate these
// numbers by re-running run_eda.py if the dataset changes.
// ---------------------------------------------------------------------------
const divisionRows = [
  ["Chocolate", "$131,692.90", "$88,824.62", "67.5%", "92.9%", "95.1%", "+2.18"],
  ["Other", "$9,663.25", "$4,333.45", "44.8%", "6.8%", "4.6%", "-2.18"],
  ["Sugar", "$427.48", "$284.73", "66.6%", "0.3%", "0.3%", "0.00"],
];

const topProductRows = [
  ["Wonka Bar - Scrumdiddlyumptious", "Chocolate", "$27,874.80", "$19,357.50", "69.4%", "High-Profit / High-Margin"],
  ["Wonka Bar - Triple Dazzle Caramel", "Chocolate", "$28,485.00", "$18,610.20", "65.3%", "High-Profit / High-Margin"],
  ["Wonka Bar - Milk Chocolate", "Chocolate", "$26,867.75", "$17,443.37", "64.9%", "High-Profit / High-Margin"],
  ["Wonka Bar - Nutty Crunch Surprise", "Chocolate", "$23,574.95", "$16,819.95", "71.4%", "High-Profit / High-Margin"],
  ["Wonka Bar - Fudge Mallows", "Chocolate", "$24,890.40", "$16,593.60", "66.7%", "High-Profit / High-Margin"],
];

const bottomProductRows = [
  ["Kazookles", "Other", "$1,205.75", "7.7%", "High-Sales / Low-Margin"],
  ["Fun Dip", "Sugar", "$12.00", "40.0%", "Low-Sales / Low-Profit"],
  ["Nerds", "Sugar", "$15.00", "46.7%", "Low-Sales / Low-Profit"],
  ["SweeTARTS", "Sugar", "$61.50", "46.7%", "Low-Sales / Low-Profit"],
  ["Lickable Wallpaper", "Other", "$7,860.00", "50.0%", "High-Sales / Low-Margin"],
];

const riskRows = [
  ["Kazookles", "Other", "7.7%", "92.3%", "Repricing Review"],
];

const volatilityRows = [
  ["Sugar", "11.08 pp*"],
  ["Other", "10.17 pp*"],
  ["Chocolate", "0.24 pp"],
];

const paretoRows = [
  ["Wonka Bar -Scrumdiddlyumptious", "$19,357.50", "20.7%"],
  ["Wonka Bar - Triple Dazzle Caramel", "$18,610.20", "40.6%"],
  ["Wonka Bar - Milk Chocolate", "$17,443.37", "59.3%"],
  ["Wonka Bar - Nutty Crunch Surprise", "$16,819.95", "77.3%"],
  ["Wonka Bar - Fudge Mallows", "$16,593.60", "95.1%"],
];

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 21 } },
    },
  },
  numbering: {
    config: [{
      reference: "bullet-list",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT }],
    }],
  },
  sections: [
    // ---------------- TITLE PAGE ----------------
    {
      properties: { page: { size: PAGE, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [
        new Paragraph({ spacing: { before: 2400 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Product Line Profitability & Margin", bold: true, size: 44, color: NAVY })] }),
        new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Performance Analysis", bold: true, size: 44, color: NAVY })] }),
        new Paragraph({ spacing: { before: 400 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "A Data-Driven Study of Nassau Candy Distributor's Product Portfolio", italics: true, size: 26 })] }),
        new Paragraph({ spacing: { before: 800 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Final-Year Research Paper", size: 24, color: ACCENT, bold: true })] }),
        new Paragraph({ spacing: { before: 2000 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Prepared for: Unified Mentor", size: 22 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Subject: Nassau Candy Distributor", size: 22 })] }),
        new Paragraph({ spacing: { before: 200 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Data Source: Internship dataset export (10,194 order lines, Jan 2024\u2013Dec 2025)", size: 20, color: "555555" })] }),
        new Paragraph({ spacing: { before: 800 }, alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Tools: Python (pandas, NumPy) \u00b7 Streamlit \u00b7 Plotly", size: 20, color: "555555" })] }),
      ],
    },
    // ---------------- MAIN BODY ----------------
    {
      properties: {
        page: { size: PAGE, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "Nassau Candy \u2014 Profitability & Margin Analysis", size: 16, color: "888888" })],
        })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })],
        })] }),
      },
      children: [
        h1("Table of Contents"),
        p("1. Abstract"),
        p("2. Background and Problem Statement"),
        p("3. Data and Methodology"),
        p("   3.1 Data Source"),
        p("   3.2 Data Cleaning and Validation"),
        p("   3.3 KPI Definitions"),
        p("4. Findings"),
        p("   4.1 Division-Level Performance"),
        p("   4.2 Product-Level Profitability"),
        p("   4.3 Profit Concentration (Pareto Analysis)"),
        p("   4.4 Cost Structure Diagnostics and Margin Risk"),
        p("   4.5 Margin Volatility"),
        p("5. Recommendations"),
        p("6. Limitations"),
        p("7. Conclusion"),
        new Paragraph({ children: [new PageBreak()] }),

        // 1. Abstract
        h1("1. Abstract"),
        p("Sales volume alone is a misleading indicator of financial health for a multi-division distributor such as Nassau Candy. This paper analyzes 10,194 order lines from an internship dataset export spanning January 2024 to December 2025, across the Chocolate, Sugar, and Other product divisions, to determine which products and divisions genuinely drive profitability. Using gross margin, profit-per-unit, revenue/profit contribution, profit concentration (Pareto analysis), and cost-structure diagnostics, the study finds that the business is overwhelmingly concentrated in a single division \u2014 Chocolate accounts for 96.6% of all order lines and 95.1% of total gross profit \u2014 and that just five products (all five Chocolate SKUs) generate over 95% of company-wide profit. The study also surfaces a systematic data-quality issue in the source export's Ship Date field, which is documented in full rather than silently corrected or ignored. The accompanying interactive Streamlit dashboard operationalizes these findings for ongoing, self-service decision-making."),

        // 2. Background & Problem Statement
        h1("2. Background and Problem Statement"),
        p("Nassau Candy Distributor currently lacks structured visibility into which product lines deliver the highest gross margin, whether high-sales products are actually profitable, how profitability varies across product divisions, and which products represent margin risk. In the absence of this insight, decisions on pricing, promotions, and product-portfolio rationalization remain reactive and intuition-driven rather than data-driven. This project was undertaken to close that gap using a real internship data export."),
        p("Specifically, the analysis was designed to answer four questions:"),
        bullet("Which product lines deliver the highest gross margin, independent of sales volume?"),
        bullet("Do the organization's best-selling products also rank among its most profitable?"),
        bullet("How does financial efficiency (margin, revenue-to-profit conversion) differ across the Chocolate, Sugar, and Other divisions?"),
        bullet("Which specific products carry cost or margin risk severe enough to warrant repricing, cost renegotiation, or discontinuation review?"),

        // 3. Data & Methodology
        h1("3. Data and Methodology"),
        h2("3.1 Data Source"),
        p("The analysis uses a real order-level transactional export supplied for this project (not a synthetic or sample dataset), structured to Nassau Candy's schema: Row ID, Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Country/Region, City, State/Province, Postal Code, Division, Region, Product ID, Product Name, Sales, Units, Gross Profit, and Cost. The export contains 10,194 order lines covering 15 products across 3 divisions (Chocolate, Sugar, Other), 5,044 unique customers, 59 states/provinces and 542 cities across two countries (United States and Canada), over a two-year window (January 2, 2024 \u2013 December 31, 2025)."),

        h2("3.2 Data Cleaning and Validation"),
        p("Prior to analysis, the dataset was passed through a validation pipeline that:"),
        bullet("Parsed and validated Order Date and Ship Date fields (source format: DD-MM-YYYY)"),
        bullet("Standardized Division and Product Name text labels (trimming whitespace, normalizing case, e.g. \"SweeTARTS\" \u2192 \"Sweetarts\")"),
        bullet("Coerced Sales, Cost, Gross Profit, and Units to numeric types"),
        bullet("Preserved Postal Code as a zero-padded text field rather than a number, to avoid dropping leading zeros"),
        bullet("Checked for missing Units and Gross Profit values, and for zero/negative Sales records"),
        bullet("Cross-checked Order Date against Ship Date for a plausible fulfillment window"),
        p("Unlike the earlier phase of this project (which used a generated sample dataset), this real export required no row-level imputation or deletion: all 10,194 rows had complete Units, Gross Profit, and Sales values, and Gross Profit reconciled exactly to Sales minus Cost in every row. The one substantive data-quality issue found was systematic rather than row-level: the Ship Date field is 900\u20131,642 days (roughly 2.5 to 4.5 years) later than the corresponding Order Date on every single row in the dataset, which is not consistent with genuine shipment behavior for a confectionery distributor and points to a format or export error in that specific column at the source. Rather than silently trusting or discarding this field, it was flagged in the cleaning-stats output (see the dashboard's \"Data quality summary\" panel) and excluded from all downstream KPI calculations \u2014 no fulfillment-time metric is reported anywhere in this study. Sales, Cost, and Gross Profit are unaffected by this issue and were used as-is."),

        h2("3.3 KPI Definitions"),
        dataTable(
          ["KPI", "Formula", "Purpose"],
          [
            ["Gross Margin (%)", "Gross Profit \u00f7 Sales", "Measures profitability efficiency independent of scale"],
            ["Profit per Unit", "Gross Profit \u00f7 Units", "Normalizes profit contribution per item sold"],
            ["Revenue Contribution", "Product Sales \u00f7 Total Sales", "Share of total revenue attributable to a product"],
            ["Profit Contribution", "Product Profit \u00f7 Total Profit", "Share of total profit attributable to a product"],
            ["Margin Volatility", "Std. dev. of monthly gross margin", "Stability of a division's margin over time"],
          ],
          [2400, 3600, 3708],
        ),

        // 4. Findings
        new Paragraph({ children: [new PageBreak()] }),
        h1("4. Findings"),

        h2("4.1 Division-Level Performance"),
        p("Aggregating all 10,194 order lines to the division level reveals a business that is, in this dataset, almost entirely a Chocolate business:"),
        dataTable(
          ["Division", "Total Sales", "Total Profit", "Gross Margin", "Rev. Share", "Profit Share", "Imbalance (pp)"],
          divisionRows,
          [1500, 1600, 1600, 1300, 1200, 1300, 1308],
        ),
        p(""),
        p("Chocolate accounts for 92.9% of total revenue and 95.1% of total gross profit, at a healthy 67.5% gross margin, and converts revenue to profit slightly more efficiently than its revenue share alone would suggest (+2.18 percentage-point imbalance). Other contributes 6.8% of revenue but only 4.6% of profit at a comparatively weak 44.8% margin (-2.18 pp imbalance) \u2014 a real, if small in absolute terms, margin-efficiency gap. Sugar is present in the data but at a scale (0.3% of revenue, $427 total sales across 40 orders) too small to draw reliable conclusions from; its margin figure (66.6%) is directionally healthy but statistically thin."),

        h2("4.2 Product-Level Profitability"),
        p("Ranking all 15 products by total gross profit produces the following leaderboard:"),
        dataTable(
          ["Product", "Division", "Sales", "Profit", "Margin", "Classification"],
          topProductRows,
          [2600, 1400, 1400, 1400, 1000, 1508],
        ),
        p(""),
        p("Every one of the top five products by profit is a Chocolate-division Wonka Bar, each independently classified High-Profit / High-Margin, with gross margins ranging from 64.9% to 71.4%. There is no High-Sales / Low-Margin product among the top performers in this dataset \u2014 the pattern the original problem statement warned about (\"sells in high volume but generates low profit\") is not what is driving Nassau Candy's revenue here. Instead, the risk is concentration: the five Chocolate SKUs together account for 95.1% of all profit generated across the entire 15-product portfolio."),
        p("At the other end of the spectrum, the lowest-margin products are:"),
        dataTable(
          ["Product", "Division", "Sales", "Margin", "Classification"],
          bottomProductRows,
          [2700, 1400, 1600, 1200, 2408],
        ),
        p(""),
        p("Kazookles is the clearest margin-risk product in the portfolio (see Section 4.4). The four other low-margin products (Fun Dip, Nerds, SweeTARTS, Lickable Wallpaper) collectively represent a very small fraction of total sales \u2014 Sugar-division figures here in particular reflect only a handful of orders each and should be read as directional, not conclusive."),

        h2("4.3 Profit Concentration (Pareto Analysis)"),
        p("Ranking products by cumulative contribution to total gross profit shows a much steeper concentration than a generic 80/20 rule would predict: just 5 of the 15 products (33.3%) \u2014 the entire Chocolate lineup \u2014 are required to reach 80% of total gross profit, and in fact reach 95.1% of it."),
        dataTable(
          ["Product", "Gross Profit", "Cumulative %"],
          paretoRows,
          [3900, 2100, 3708],
        ),
        p(""),
        p("This is a materially higher concentration risk than a typical 80/20 pattern. Practically, it means Nassau Candy's profitability \u2014 at least as captured in this export \u2014 is highly dependent on the continued performance of a single product division. A supply disruption, cost shock, or demand shift affecting Chocolate sourcing (per the original brief's factory mapping, primarily \"Lot's O' Nuts\" and \"Wicked Choccy's\") would have an outsized effect on total company profit, in a way that a more evenly distributed portfolio would not."),

        h2("4.4 Cost Structure Diagnostics and Margin Risk"),
        p("Applying the cost-diagnostics rules described in Section 3.3 (margin below 25% combined with above-median revenue contribution \u2192 Repricing Review; cost-to-sales ratio \u2265 75% \u2192 Cost Renegotiation; margin below 10% \u2192 Discontinuation Review) flags one product for management attention:"),
        dataTable(
          ["Product", "Division", "Margin", "Cost-to-Sales", "Flag"],
          riskRows,
          [2600, 1600, 1400, 1800, 1908],
        ),
        p(""),
        p("Kazookles has by far the weakest unit economics in the portfolio: costs consume 92.3% of sales value, leaving only a 7.7% gross margin \u2014 close to break-even and the only product in the dataset crossing both the margin and cost-to-sales risk thresholds. Every other product in the portfolio, including the very low-volume Sugar-division items, clears the \"Healthy\" threshold on a margin basis, even where their absolute revenue contribution is negligible."),

        h2("4.5 Margin Volatility"),
        dataTable(["Division", "Margin Volatility (monthly std. dev.)"], volatilityRows, [4854, 4854]),
        p(""),
        p("*Caution: Sugar and Other's higher volatility figures are computed from only 40 and 304 orders respectively across the two-year window \u2014 several months in this dataset have very few Sugar/Other orders, so month-to-month margin swings are as likely to reflect small-sample noise as genuine pricing instability. Chocolate's volatility figure (0.24 pp), by contrast, is based on 8,205 orders and can be read with much higher confidence as a genuinely stable, well-controlled margin."),

        // 5. Recommendations
        new Paragraph({ children: [new PageBreak()] }),
        h1("5. Recommendations"),
        bullet("Treat Chocolate-division concentration as the primary strategic risk, not a strength to be taken for granted: with 95.1% of profit riding on five SKUs from two factories, Nassau Candy should stress-test what a supply, cost, or demand shock to Chocolate sourcing would do to overall profitability, and consider deliberate investment to grow Sugar and Other as a diversification hedge."),
        bullet("Open a repricing or reformulation review for Kazookles, whose 7.7% margin and 92.3% cost-to-sales ratio make it the only structurally unprofitable product in the current portfolio."),
        bullet("Investigate whether Sugar and Other's low order volumes reflect genuine low demand or a data-completeness gap in this particular export \u2014 40 orders for an entire division over two years is unusually low and is worth confirming against the source system before drawing firm portfolio decisions from it."),
        bullet("Report the Ship Date data-quality finding (Section 3.2) back to whoever maintains the source export \u2014 a systematic multi-year offset in a date field is the kind of issue that quietly breaks fulfillment-time and logistics reporting elsewhere in the organization if it isn't caught and fixed at the source."),
        bullet("Continue monitoring profit concentration on a rolling basis using the dashboard's Pareto module, since the current 33.3% (5-of-15) concentration is a live risk indicator that should be re-checked every reporting period, not just at Kazookles' potential repricing decision."),

        // 6. Limitations
        h1("6. Limitations"),
        bullet("The Sugar and Other divisions are represented by a very small number of orders (40 and 304 respectively) relative to Chocolate's 8,205, so per-product and per-division figures for those two divisions carry much wider uncertainty than the headline numbers suggest."),
        bullet("Ship Date could not be used for any fulfillment-time or logistics analysis due to the systematic data-quality issue documented in Section 3.2; the \"shipping route efficiency\" angle referenced in the original brief's conclusion could not be pursued with this export as-is."),
        bullet("Gross margin as defined here (Sales \u2212 Cost) reflects manufacturing/product cost only; it does not incorporate distribution, shipping, or overhead costs, which would be required for a full net-margin picture."),
        bullet("Factory-level sourcing figures shown in the dashboard's Pareto tab use the Division\u2192Product\u2192Factory mapping supplied in the original project brief, not a field present in this order-level export, since no factory column exists in the source data."),

        // 7. Conclusion
        h1("7. Conclusion"),
        p("This project establishes a clear, data-driven view of product-line profitability for Nassau Candy Distributor using a real internship data export. The headline finding is stronger than a typical margin-optimization story: the business, as captured in this dataset, is almost entirely dependent on five Chocolate products for its profitability, with the Sugar and Other divisions playing a marginal role. Alongside this, the analysis identifies one clear repricing/discontinuation candidate (Kazookles) and documents a systematic data-quality issue in the Ship Date field that should be corrected at the source. The accompanying Streamlit dashboard makes these same metrics available on a self-service, continuously updated basis, replacing reactive, intuition-based portfolio decisions with a repeatable, quantitative process \u2014 and is ready to be re-pointed at a more complete future export if the Sugar/Other volume gap turns out to be a data-completeness issue rather than a true reflection of the business."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Research_Paper.docx", buf);
  console.log("Wrote Research_Paper.docx");
});
