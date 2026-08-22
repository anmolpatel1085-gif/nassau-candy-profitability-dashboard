const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, Header, Footer, PageNumber, LevelFormat,
} = require("docx");
const fs = require("fs");

const PAGE = { size: { width: 12240, height: 15840 } };
const NAVY = "1F3864";
const ACCENT = "C0392B";
const GOOD = "2E7D32";
const WARN = "EF6C00";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 140 }, children: [new TextRun({ text, ...opts })] });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 70 } });
}
function cell(text, { header = false, width, color } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: NAVY } : undefined,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: header, color: header ? "FFFFFF" : (color || "000000"), size: 18 })],
    })],
  });
}
function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((h, i) => cell(h, { header: true, width: widths[i] })) }),
      ...rows.map((r) => new TableRow({ children: r.map((v, i) => cell(String(v), { width: widths[i] })) })),
    ],
  });
}

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  numbering: { config: [{ reference: "bullet-list", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT }] }] },
  sections: [{
    properties: { page: { size: PAGE, margin: { top: 1080, bottom: 1080, left: 1260, right: 1260 } } },
    headers: { default: new Header({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Executive Summary — Nassau Candy Distributor", size: 16, color: "888888" })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })],
    })] }) },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Product Line Profitability & Margin Performance", bold: true, size: 34, color: NAVY })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
        children: [new TextRun({ text: "Executive Summary", bold: true, size: 30, color: ACCENT })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
        children: [new TextRun({ text: "Nassau Candy Distributor · Prepared for Stakeholder Review", italics: true, size: 20, color: "555555" })] }),

      h1("Why This Matters"),
      p("Sales volume alone does not tell us which products make money. This analysis reviewed all 10,194 order lines from a real internship data export across the Chocolate, Sugar, and Other divisions to separate products that genuinely drive profit from products that merely drive revenue — and to flag where pricing or cost action, or a data-quality fix, is needed now."),

      h1("Headline Numbers"),
      table(
        ["Metric", "Value"],
        [
          ["Total Sales Analyzed", "$141,783.63"],
          ["Total Gross Profit", "$93,442.80"],
          ["Overall Gross Margin", "65.9%"],
          ["Products Analyzed", "15, across 3 divisions"],
          ["Order Lines / Customers", "10,194 lines, 5,044 customers"],
          ["Data Quality", "100% of rows clean; 1 systematic field issue found (see below)"],
        ],
        [4700, 4708],
      ),

      h1("Top-Line Findings"),
      bullet("The business is almost entirely a Chocolate business: the division drives 92.9% of revenue and 95.1% of profit, at a strong 67.5% gross margin."),
      bullet("All five top-profit products are Chocolate SKUs — no high-volume product is dragging down margin the way the original problem statement worried about."),
      bullet("This is a concentration risk, not just a strength: just 5 of 15 products supply over 95% of total profit, so a shock to Chocolate sourcing would hit the whole business hard."),
      bullet("Sugar and Other divisions are tiny in this export (40 and 304 orders respectively over two years) — worth confirming with the source system whether that's real or a data gap."),
      bullet("One product needs attention now: Kazookles, at a 7.7% margin with costs eating 92.3% of its sales value."),
      bullet("Data-quality finding: the Ship Date field is 2.5–4.5 years later than Order Date on every row — a source export issue, not real shipping delays. It has been excluded from all metrics; Sales, Cost, and Profit figures are unaffected."),

      h1("Recommended Actions"),
      table(
        ["Action", "Product / Area", "Priority"],
        [
          ["Repricing / reformulation review", "Kazookles", "High"],
          ["Stress-test Chocolate concentration risk", "Chocolate division sourcing", "High"],
          ["Confirm Sugar/Other order volume is accurate", "Sugar, Other divisions", "Medium"],
          ["Report Ship Date field issue to data owner", "Source export / Ship Date column", "Medium"],
        ],
        [3600, 3600, 2208],
      ),

      h1("What's Delivered"),
      bullet("A live, interactive Streamlit dashboard for ongoing self-service analysis (product leaderboard, division performance, cost/margin risk flags, Pareto concentration) — now running on the real internship dataset."),
      bullet("A full research paper documenting methodology, findings, and recommendations in detail, including the Ship Date data-quality investigation."),
      bullet("A reusable Python analytics engine that can be pointed at a future, more complete export with no code changes to the dashboard."),

      new Paragraph({ spacing: { before: 200 }, children: [new TextRun({
        text: "Full methodology, KPI definitions, and detailed findings are available in the accompanying Research Paper.",
        italics: true, size: 19, color: "555555",
      })] }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Executive_Summary.docx", buf);
  console.log("Wrote Executive_Summary.docx");
});
