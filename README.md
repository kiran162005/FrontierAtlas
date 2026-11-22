# FrontierAtlas

### AI-Powered Startup, Product, Research and Market Intelligence Pipeline

FrontierAtlas is an end-to-end data intelligence project that collects information from across the AI ecosystem, extracts structured insights using Large Language Models (LLMs), and resolves extracted entities against a canonical dataset.

The platform brings together startup profiles, AI products, research publications, GitHub repository information, AI-related news, and job opportunities into structured, analysis-ready datasets.

---

## Key Features

- **Multi-Source Data Collection:** Collects startup, product, research, news, and job information from external sources and APIs.
- **Asynchronous Crawling:** Uses Python `asyncio` and `aiohttp` for concurrent data collection.
- **Research Enrichment:** Identifies GitHub repositories associated with research papers and retrieves repository star counts.
- **LLM-Powered Extraction:** Extracts structured entities, industries, technologies, and key facts from collected content.
- **Entity Resolution:** Uses RapidFuzz similarity matching to map extracted entities to canonical startup and product records.
- **Data Quality:** Normalizes records, handles failures, validates extracted information, and maintains source attribution.
- **Data Export:** Exports processed datasets into CSV files for Google Sheets analysis.

---

## System Architecture

```text
       EXTERNAL DATA SOURCES
                 |
                 v
       ASYNCHRONOUS CRAWLERS
                 |
                 v
        DATA NORMALIZATION
                 |
                 v
           JSON DATASETS
                 |
                 v
          LLM EXTRACTION
                 |
                 v
         ENTITY RESOLUTION
                 |
                 v
            CSV EXPORT
                 |
                 v
           GOOGLE SHEETS
```

The current implementation uses local JSON files as its primary storage layer.

PostgreSQL, distributed workers, and specialized search infrastructure are proposed future enhancements for production-scale deployment.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Programming Language | Python |
| Asynchronous Collection | asyncio, aiohttp |
| Web Parsing | BeautifulSoup, Trafilatura |
| Feed Processing | feedparser |
| Research Collection | arXiv API |
| Repository Enrichment | GitHub REST API |
| LLM Extraction | Groq API |
| Data Validation | Pydantic |
| Entity Resolution | RapidFuzz |
| Data Processing | pandas |
| Data Export | CSV, Google Sheets import |

---

## Data Sources

| Dataset | Source / Approach |
|---|---|
| Startups | Y Combinator company dataset mirror |
| AI Products | TiorAI and Harpd product directories |
| Research Papers | arXiv API |
| GitHub Metrics | GitHub REST API |
| AI News | TechCrunch, The Verge, Ars Technica, MIT Technology Review, and OpenAI RSS feeds |
| AI Jobs | Arbeitnow, Remote OK, Himalayas, Jobicy, and Remotive APIs |

External sources may occasionally be unavailable or return incomplete responses. Collection failures are handled where possible and should be considered when interpreting dataset counts.

---

## Current Collection Results

The following figures are from recorded collection runs.

| Dataset | Records |
|---|---:|
| Startups | 6,249 |
| AI Products | 1,711 |
| Research Papers | 1,000 |
| Research Papers Linked to Verified GitHub Repositories | 69 |
| AI News | 7 |
| AI Jobs | 82 |

**Note:** News and job counts represent time-windowed snapshots from the latest recorded 24-hour run and will change as the sources are refreshed.

### LLM Extraction and Entity Resolution

A recorded extraction run processed 118 records.

**Extraction Results**

| Metric | Count |
|---|---:|
| Total Records Processed | 118 |
| Successful Extractions | 95 |
| Failed Extractions | 23 |

**Entity Resolution Results**

| Metric | Count |
|---|---:|
| Total Extracted Entities | 529 |
| Automatically Matched | 23 |
| Flagged for Manual Review | 10 |
| Unmatched | 496 |

Unmatched entities are retained as unmatched rather than being assigned incorrect canonical identities. This helps prevent unreliable entity associations.

---

## Project Structure

```text
FrontierAtlas/
│
├── src/
│   ├── crawlers/
│   │   ├── startup_crawler.py
│   │   ├── product_crawler.py
│   │   ├── research_crawler.py
│   │   ├── github_enricher.py
│   │   ├── news_crawler.py
│   │   └── jobs_crawler.py
│   │
│   ├── extraction/
│   │   └── llm_extractor.py
│   │
│   ├── resolution/
│   │   └── entity_resolver.py
│   │
│   ├── processing/
│   │   ├── run_extraction.py
│   │   ├── export_csv.py
│   │   └── create_architecture_pdf.py
│   │
│   └── main.py
│
├── data/
│   ├── startups.json
│   ├── products.json
│   ├── research_papers.json
│   ├── research_papers_enriched.json
│   ├── news.json
│   ├── jobs.json
│   ├── canonical_entities.json
│   ├── extraction_results.json
│   ├── entity_mapping_log.json
│   └── google_sheets_export/
│
├── tests/
│
├── architecture.pdf
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/kiran162005/FrontierAtlas.git

cd FrontierAtlas
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and provide your own API credentials.

```powershell
Copy-Item .env.example .env
```

Required credentials depend on the modules being executed.

---

## Running the Pipeline

Individual modules can be executed independently.

### Data Collection

```bash
# Collect startup information
python -m src.crawlers.startup_crawler

# Collect AI products
python -m src.crawlers.product_crawler

# Collect research papers
python -m src.crawlers.research_crawler

# Enrich research papers with GitHub metrics
python -m src.crawlers.github_enricher

# Collect AI-related news
python -m src.crawlers.news_crawler

# Collect AI job opportunities
python -m src.crawlers.jobs_crawler
```

### LLM Extraction

```bash
python -m src.processing.run_extraction
```

### Entity Resolution

```bash
python -m src.resolution.entity_resolver
```

### CSV Export

```bash
python -m src.processing.export_csv
```

### Generate Architecture Documentation

```bash
python -m src.processing.create_architecture_pdf
```

### Run the Integrated Pipeline

```bash
python -m src.main
```

**Note:** The integrated pipeline invokes collection and processing stages. It can take considerable time and make external API requests. Existing collected data should be backed up before rerunning it.

---

## Google Sheets Integration

Processed datasets are exported to:

```text
data/google_sheets_export/
```

The export contains six datasets:

- `startups.csv`
- `products.csv`
- `research_papers.csv`
- `jobs.csv`
- `news.csv`
- `entity_mapping_log.csv`

These CSV files can be imported into separate tabs within a Google Spreadsheet for further exploration and analysis.

---

## Reliability and Data Quality

FrontierAtlas incorporates several mechanisms to improve collection reliability and extraction quality:

- Asynchronous requests for concurrent data collection.
- Retry handling and backoff for transient API errors.
- Text chunking for large LLM extraction inputs.
- Structured output validation using Pydantic.
- Fuzzy matching with configurable similarity thresholds.
- Record-level success and failure tracking.
- Source URLs and collection metadata for traceability.
- Conservative entity matching to avoid incorrect canonical associations.

---

## Current Limitations

FrontierAtlas is a working prototype, with several production enhancements remaining:

- Complete multi-provider LLM fallback across Gemini, Groq, and DeepSeek.
- Database-backed persistence using PostgreSQL.
- Distributed queues and worker orchestration.
- More comprehensive automated testing and monitoring.
- Improved reliability across external data providers.
- Production deployment and scheduled incremental ingestion.

---

## Future Scalability

The proposed production architecture targets **500,000+ records** through:

- **PostgreSQL:** Persistent structured storage and relational queries.
- **Redis Streams or RabbitMQ:** Distributed task management and message processing.
- **Horizontally Scalable Workers:** Independent crawler and extraction workers.
- **Object Storage:** Storage for raw documents and historical snapshots.
- **Vector Search:** Semantic retrieval across collected information.
- **Graph Storage:** Optional representation of relationships between startups, products, technologies, and research.
- **Monitoring and Recovery:** Logging, alerting, checkpointing, and automated recovery.

The current architecture documentation is available in `architecture.pdf`.

---

## Responsible Data Collection

FrontierAtlas prioritizes official APIs, RSS feeds, and accessible public datasets.

Data collection should respect source terms of service, `robots.txt` policies, rate limits, and access controls. Browser automation should only be used where permitted.

---

## Author

**Kiran Raj**

GitHub: [github.com/kiran162005](https://github.com/kiran162005)

---

*FrontierAtlas — Building structured intelligence from the AI ecosystem.*
