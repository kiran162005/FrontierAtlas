
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

OUTPUT_FILE = Path("architecture.pdf")

NAVY = colors.HexColor("#142D4E")
BLUE = colors.HexColor("#2563A6")
LIGHT_BLUE = colors.HexColor("#EAF2F8")
LIGHT_GREY = colors.HexColor("#F2F4F7")
DARK = colors.HexColor("#263445")
GREEN = colors.HexColor("#287A55")


styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="CoverTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=23,
    leading=28,
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=8,
))

styles.add(ParagraphStyle(
    name="SubtitleCustom",
    parent=styles["Normal"],
    fontSize=10,
    leading=15,
    textColor=colors.HexColor("#64748B"),
    alignment=TA_CENTER,
    spaceAfter=16,
))

styles.add(ParagraphStyle(
    name="Section",
    parent=styles["Heading1"],
    fontSize=15,
    leading=19,
    textColor=NAVY,
    spaceBefore=9,
    spaceAfter=7,
))

styles.add(ParagraphStyle(
    name="SubSection",
    parent=styles["Heading2"],
    fontSize=10.5,
    leading=13,
    textColor=BLUE,
    spaceBefore=6,
    spaceAfter=4,
))

styles.add(ParagraphStyle(
    name="BodyCustom",
    parent=styles["BodyText"],
    fontSize=8.5,
    leading=12,
    textColor=DARK,
    spaceAfter=5,
))

styles.add(ParagraphStyle(
    name="SmallCustom",
    parent=styles["BodyText"],
    fontSize=7.5,
    leading=10,
    textColor=DARK,
))

styles.add(ParagraphStyle(
    name="CellHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.white,
))

styles.add(ParagraphStyle(
    name="Cell",
    parent=styles["Normal"],
    fontSize=7.5,
    leading=10,
    textColor=DARK,
))

styles.add(ParagraphStyle(
    name="FlowBox",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=11,
    alignment=TA_CENTER,
    textColor=NAVY,
))


def P(text, style="BodyCustom"):
    return Paragraph(text, styles[style])


def make_table(rows, widths, header=True):
    converted = []
    for r, row in enumerate(rows):
        converted.append([
            P(str(value), "CellHeader" if header and r == 0 else "Cell")
            for value in row
        ])

    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7DEE8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        if len(rows) > 1:
            commands.append(
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY])
            )

    table.setStyle(TableStyle(commands))
    return table


def flow_box(text):
    return Table(
        [[P(text, "FlowBox")]],
        colWidths=[37 * mm],
        rowHeights=[17 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
            ("BOX", (0, 0), (-1, -1), 0.8, BLUE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]),
    )


def footer(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setStrokeColor(colors.HexColor("#D7DEE8"))
    canvas.line(17 * mm, 14 * mm, width - 17 * mm, 14 * mm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(17 * mm, 9 * mm, "FRONTIERATLAS | AI INTELLIGENCE PIPELINE")
    canvas.drawRightString(
        width - 17 * mm, 9 * mm, f"Page {doc.page} of 3"
    )
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT_FILE),
    pagesize=A4,
    rightMargin=17 * mm,
    leftMargin=17 * mm,
    topMargin=15 * mm,
    bottomMargin=20 * mm,
)

story = []

# ==========================================================
# PAGE 1 — SYSTEM ARCHITECTURE
# ==========================================================

story.append(Spacer(1, 5 * mm))
story.append(P("FRONTIERATLAS", "CoverTitle"))
story.append(P(
    "AI-Powered Startup, Product, Research and Market Intelligence Platform",
    "SubtitleCustom",
))

story.append(P("1. System Overview", "Section"))
story.append(P(
    "FrontierAtlas is a modular data intelligence pipeline designed to collect "
    "AI ecosystem information from multiple sources, normalize records, extract "
    "structured entities using LLMs, and identify relationships against a "
    "canonical entity dataset."
))

story.append(P("High-Level Data Flow", "SubSection"))

flow = Table(
    [[
        flow_box("DATA SOURCES"),
        P("→", "Section"),
        flow_box("ASYNC CRAWLERS"),
        P("→", "Section"),
        flow_box("NORMALIZATION"),
        P("→", "Section"),
        flow_box("JSON DATASETS"),
    ]],
    colWidths=[39 * mm, 5 * mm, 39 * mm, 5 * mm, 39 * mm, 5 * mm, 39 * mm],
    hAlign="CENTER",
)
flow.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
]))
story.append(flow)
story.append(Spacer(1, 3 * mm))

flow2 = Table(
    [[
        flow_box("LLM EXTRACTION"),
        P("→", "Section"),
        flow_box("ENTITY RESOLUTION"),
        P("→", "Section"),
        flow_box("CSV EXPORT"),
        P("→", "Section"),
        flow_box("GOOGLE SHEETS"),
    ]],
    colWidths=[39 * mm, 5 * mm, 39 * mm, 5 * mm, 39 * mm, 5 * mm, 39 * mm],
    hAlign="CENTER",
)
flow2.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
]))
story.append(flow2)

story.append(P("Data Collection Layer", "SubSection"))
story.append(make_table([
    ["Dataset", "Collection approach", "Current collected volume"],
    ["Startups", "YC company dataset crawler", "6,249"],
    ["AI Products", "Product directory crawlers", "1,711"],
    ["Research Papers", "arXiv API crawler", "1,000"],
    ["Research GitHub enrichment", "GitHub REST API verification", "69 papers linked"],
    ["AI News", "Five RSS source integrations", "7 articles in latest run"],
    ["AI Jobs", "Five job-board API integrations", "82 jobs in latest run"],
], [36 * mm, 87 * mm, 48 * mm]))

story.append(P("Technology Stack", "SubSection"))
story.append(P(
    "<b>Language:</b> Python 3.13 &nbsp;&nbsp; "
    "<b>Networking:</b> aiohttp, asyncio &nbsp;&nbsp; "
    "<b>Parsing:</b> BeautifulSoup, Trafilatura, feedparser<br/>"
    "<b>AI extraction:</b> Groq API and Pydantic validation<br/>"
    "<b>Entity matching:</b> RapidFuzz<br/>"
    "<b>Export:</b> CSV and Google Sheets import workflow<br/>"
    "<b>Data format:</b> JSON with source URLs and collection timestamps"
))

story.append(P(
    "The current implementation uses local JSON files as its primary storage "
    "layer. Database-backed storage and distributed processing are proposed "
    "for the production-scale architecture.",
    "SmallCustom",
))

story.append(PageBreak())

# ==========================================================
# PAGE 2 — PROCESSING AND INTELLIGENCE
# ==========================================================

story.append(P("2. Processing and Intelligence", "Section"))

story.append(P("LLM-Based Structured Extraction", "SubSection"))
story.append(P(
    "Collected records are processed through an LLM extraction module. "
    "The extraction prompt identifies organizations, products, technologies, "
    "industries and key facts from source content. Pydantic models validate "
    "the structured response before it is stored."
))

story.append(make_table([
    ["Capability", "Implementation"],
    ["Structured output", "Pydantic extraction schemas and JSON responses"],
    ["Large input handling", "Text chunking with overlap and recursive handling of HTTP 413"],
    ["Rate-limit handling", "Retry logic, request pacing and exponential backoff"],
    ["Output validation", "Schema validation and record-level success/failure tracking"],
    ["Persistence", "Incremental extraction result saving"],
], [42 * mm, 129 * mm]))

story.append(P("Entity Resolution", "SubSection"))
story.append(P(
    "Extracted entities are compared with a canonical seed dataset containing "
    "approximately 50 startup and product entities. Names and aliases are "
    "normalized before fuzzy similarity scoring."
))

story.append(make_table([
    ["Decision", "Similarity score", "Action"],
    ["Automatic match", "92 or higher", "Assign canonical entity"],
    ["Manual review", "85 to below 92", "Flag for human verification"],
    ["Unmatched", "Below 85", "Keep unmatched; do not force a mapping"],
], [42 * mm, 48 * mm, 81 * mm]))

story.append(P("Latest Recorded Entity Resolution Results", "SubSection"))
story.append(make_table([
    ["Metric", "Result"],
    ["Extraction records", "118"],
    ["Successful extraction records", "95"],
    ["Failed extraction records skipped", "23"],
    ["Entities processed", "529"],
    ["Automatically matched", "23"],
    ["Require manual review", "10"],
    ["Unmatched", "496"],
], [85 * mm, 86 * mm]))

story.append(P("Data Quality and Reliability", "SubSection"))
story.append(P(
    "Each collected record retains source attribution, source URL and "
    "collection metadata where available. Crawlers normalize publication "
    "dates and filter news and job records to a 24-hour window. URL-based "
    "deduplication is used in collection workflows, while GitHub repository "
    "verification enriches research records with repository and star data."
))

story.append(P("Operational Limitations", "SubSection"))
story.append(P(
    "External APIs and RSS feeds can fail or return incomplete data. The latest "
    "integrated run recorded temporary source failures for some news and job "
    "providers. The extraction pipeline also had record-level failures. "
    "These are tracked rather than treated as successful records. The current "
    "prototype uses Groq extraction; a complete Gemini-to-Groq-to-DeepSeek "
    "provider fallback chain is a future enhancement."
))

story.append(PageBreak())

# ==========================================================
# PAGE 3 — PRODUCTION SCALE
# ==========================================================

story.append(P("3. Production Architecture: Scaling to 500K+ Records", "Section"))

story.append(P(
    "The following architecture is a proposed evolution of the current "
    "prototype. It introduces distributed workers, durable queues and "
    "database-backed storage to support larger datasets and continuous updates."
))

story.append(P("Proposed Production Data Flow", "SubSection"))
story.append(make_table([
    ["Layer", "Proposed components", "Responsibility"],
    ["Ingestion", "API clients, RSS, sitemaps, Playwright", "Collect data from authorized sources"],
    ["Queue", "Redis Streams or RabbitMQ", "Buffer tasks and distribute workloads"],
    ["Workers", "Async crawler and extraction workers", "Concurrent collection, parsing and enrichment"],
    ["Processing", "Normalization, hashing, deduplication", "Validate records and prevent duplicates"],
    ["Storage", "PostgreSQL + object storage", "Store metadata, entities and raw documents"],
    ["Search", "Vector database / PostgreSQL vector extension", "Semantic retrieval and similarity search"],
    ["Graph", "Neo4j (optional)", "Explore relationships between companies, products and research"],
    ["Observability", "Prometheus, Grafana, structured logs", "Track failures, latency and data freshness"],
], [30 * mm, 58 * mm, 83 * mm]))

story.append(P("Scalability and Reliability Strategy", "SubSection"))
story.append(P(
    "<b>Horizontal scaling:</b> Run multiple independent crawler and extraction "
    "workers, with queue-based task distribution and configurable concurrency."
))
story.append(P(
    "<b>Incremental ingestion:</b> Schedule source-specific refresh jobs, "
    "use publication timestamps and content hashes, and fetch only new or "
    "changed records whenever source capabilities allow."
))
story.append(P(
    "<b>Deduplication:</b> Enforce unique source identifiers and normalized "
    "URLs in the database. Use content hashes to detect duplicate documents "
    "across different URLs."
))
story.append(P(
    "<b>Resilience:</b> Add bounded retries with exponential backoff and jitter, "
    "dead-letter queues, checkpoints, idempotent workers and recovery from "
    "partial failures."
))
story.append(P(
    "<b>Storage:</b> Use PostgreSQL for structured records and relationships, "
    "object storage for raw documents and snapshots, and optional vector or "
    "graph storage for specialized retrieval."
))

story.append(P("Crawling Policy and Source Protection", "SubSection"))
story.append(P(
    "Prefer official APIs, RSS feeds and sitemaps. Respect robots.txt, provider "
    "terms, rate limits and access controls. Use browser automation only when "
    "JavaScript rendering is required and permitted. Do not bypass CAPTCHAs, "
    "authentication controls or anti-bot protections."
))

story.append(P("Implementation Roadmap", "SubSection"))
story.append(make_table([
    ["Stage", "Priority improvements"],
    ["1. Stabilize", "Improve source reliability, extraction success rate and monitoring"],
    ["2. Persist", "Move JSON datasets to PostgreSQL; add migrations and unique constraints"],
    ["3. Distribute", "Introduce queues, worker pools and scheduled incremental crawls"],
    ["4. Enrich", "Complete multi-provider LLM fallback and add semantic/graph search where needed"],
    ["5. Operate", "Containerize services, add metrics, alerts, backups and deployment automation"],
], [35 * mm, 136 * mm]))

story.append(Spacer(1, 4 * mm))
story.append(P(
    "<b>Design principle:</b> Preserve provenance, make processing idempotent, "
    "and scale each pipeline stage independently.",
    "SmallCustom",
))

doc.build(story, onFirstPage=footer, onLaterPages=footer)

print(f"Architecture PDF created: {OUTPUT_FILE.resolve()}")
print(f"File size: {OUTPUT_FILE.stat().st_size:,} bytes")
