# \# FrontierAtlas

# 

# \*\*AI-Powered Startup, Product, Research and Market Intelligence Pipeline\*\*

# 

# FrontierAtlas is an end-to-end data intelligence project that collects information from the AI ecosystem, extracts structured insights using Large Language Models (LLMs), and resolves extracted entities against a canonical dataset.

# 

# The platform brings together startup profiles, AI products, research publications, GitHub repository information, AI-related news, and job opportunities.

# 

# \## Key Features

# 

# \- \*\*Multi-source data collection:\*\* Collects startup, product, research, news and job information from external sources and APIs.

# \- \*\*Asynchronous crawling:\*\* Uses Python asyncio and aiohttp for concurrent data collection.

# \- \*\*Research enrichment:\*\* Identifies GitHub repositories associated with research papers and retrieves repository star counts.

# \- \*\*LLM-powered extraction:\*\* Extracts structured entities, industries, technologies and key facts from collected content.

# \- \*\*Entity resolution:\*\* Uses RapidFuzz similarity matching to map extracted entities to canonical startup and product records.

# \- \*\*Data quality:\*\* Normalizes records, handles failures and maintains source attribution.

# \- \*\*Data export:\*\* Exports processed datasets into CSV files for Google Sheets analysis.

# 

# \## System Architecture

# 

# ```text

# &#x20;      EXTERNAL DATA SOURCES

# &#x20;               |

# &#x20;               v

# &#x20;      ASYNCHRONOUS CRAWLERS

# &#x20;               |

# &#x20;               v

# &#x20;      DATA NORMALIZATION

# &#x20;               |

# &#x20;               v

# &#x20;         JSON DATASETS

# &#x20;               |

# &#x20;               v

# &#x20;       LLM EXTRACTION

# &#x20;               |

# &#x20;               v

# &#x20;       ENTITY RESOLUTION

# &#x20;               |

# &#x20;               v

# &#x20;        CSV EXPORT

# &#x20;               |

# &#x20;               v

# &#x20;         GOOGLE SHEETS

# ```

# 

# The current implementation uses local JSON files as its primary storage layer. PostgreSQL, distributed workers and specialized search infrastructure are proposed future enhancements for production-scale deployment.

# 

# \## Technology Stack

# 

# | Component | Technologies |

# |---|---|

# | Programming language | Python |

# | Asynchronous collection | asyncio, aiohttp |

# | Web parsing | BeautifulSoup, Trafilatura |

# | Feed processing | feedparser |

# | Research collection | arXiv API |

# | Repository enrichment | GitHub REST API |

# | LLM extraction | Groq API |

# | Data validation | Pydantic |

# | Entity resolution | RapidFuzz |

# | Data processing | pandas |

# | Export | CSV, Google Sheets import |

# 

# \## Data Sources

# 

# | Dataset | Source / approach |

# |---|---|

# | Startups | Y Combinator company dataset mirror |

# | AI Products | TiorAI and Harpd product directories |

# | Research Papers | arXiv API |

# | GitHub Metrics | GitHub REST API |

# | AI News | TechCrunch, The Verge, Ars Technica, MIT Technology Review and OpenAI RSS feeds |

# | AI Jobs | Arbeitnow, Remote OK, Himalayas, Jobicy and Remotive APIs |

# 

# External sources may occasionally be unavailable or return incomplete responses. Collection failures are handled where possible and should be considered when interpreting dataset counts.

# 

# \## Current Collection Results

# 

# The following figures are from recorded collection runs:

# 

# | Dataset | Records |

# |---|---:|

# | Startups | 6,249 |

# | AI Products | 1,711 |

# | Research Papers | 1,000 |

# | Research papers linked to verified GitHub repositories | 69 |

# | AI News | 7 in the latest recorded 24-hour run |

# | AI Jobs | 82 in the latest recorded 24-hour run |

# 

# News and job counts represent time-windowed snapshots and will change as the sources are refreshed.

# 

# \### LLM Extraction and Entity Resolution

# 

# A recorded extraction run processed 118 records:

# 

# \- Successful extractions: 95

# \- Failed extractions: 23

# 

# The entity resolution stage processed 529 extracted entities:

# 

# \- Automatically matched: 23

# \- Flagged for manual review: 10

# \- Unmatched: 496

# 

# Unmatched entities are retained as unmatched rather than being assigned incorrect canonical identities.

# 

# \## Project Structure

# 

# ```text

# FrontierAtlas/

# │

# ├── src/

# │   ├── crawlers/

# │   │   ├── startup\_crawler.py

# │   │   ├── product\_crawler.py

# │   │   ├── research\_crawler.py

# │   │   ├── github\_enricher.py

# │   │   ├── news\_crawler.py

# │   │   └── jobs\_crawler.py

# │   │

# │   ├── extraction/

# │   │   └── llm\_extractor.py

# │   │

# │   ├── resolution/

# │   │   └── entity\_resolver.py

# │   │

# │   ├── processing/

# │   │   ├── run\_extraction.py

# │   │   ├── export\_csv.py

# │   │   └── create\_architecture\_pdf.py

# │   │

# │   └── main.py

# │

# ├── data/

# │   ├── startups.json

# │   ├── products.json

# │   ├── research\_papers.json

# │   ├── research\_papers\_enriched.json

# │   ├── news.json

# │   ├── jobs.json

# │   ├── canonical\_entities.json

# │   ├── extraction\_results.json

# │   ├── entity\_mapping\_log.json

# │   └── google\_sheets\_export/

# │

# ├── tests/

# ├── architecture.pdf

# ├── requirements.txt

# ├── .env.example

# ├── .gitignore

# └── README.md

# ```

# 

# \## Installation and Setup

# 

# \### 1. Clone the repository

# 

# ```bash

# git clone https://github.com/kiran162005/FrontierAtlas.git

# cd FrontierAtlas

# ```

# 

# \### 2. Create a virtual environment

# 

# ```bash

# python -m venv venv

# ```

# 

# Activate it on Windows PowerShell:

# 

# ```powershell

# .\\venv\\Scripts\\Activate.ps1

# ```

# 

# \### 3. Install dependencies

# 

# ```bash

# pip install -r requirements.txt

# ```

# 

# \### 4. Configure environment variables

# 

# Copy `.env.example` to `.env` and provide your own API credentials.

# 

# ```powershell

# Copy-Item .env.example .env

# ```

# 

# Required credentials depend on the modules being executed.

# 

# \## Running the Pipeline

# 

# Run individual modules when needed:

# 

# ```bash

# python -m src.crawlers.startup\_crawler

# python -m src.crawlers.product\_crawler

# python -m src.crawlers.research\_crawler

# python -m src.crawlers.github\_enricher

# python -m src.crawlers.news\_crawler

# python -m src.crawlers.jobs\_crawler

# ```

# 

# Run LLM extraction:

# 

# ```bash

# python -m src.processing.run\_extraction

# ```

# 

# Run entity resolution:

# 

# ```bash

# python -m src.resolution.entity\_resolver

# ```

# 

# Export datasets to CSV:

# 

# ```bash

# python -m src.processing.export\_csv

# ```

# 

# Generate architecture documentation:

# 

# ```bash

# python -m src.processing.create\_architecture\_pdf

# ```

# 

# The integrated orchestrator can be started using:

# 

# ```bash

# python -m src.main

# ```

# 

# \*\*Note:\*\* The integrated pipeline invokes collection and processing stages. It can take considerable time and may make external API requests. Existing collected data should be backed up before rerunning it.

# 

# \## Google Sheets Integration

# 

# CSV exports are generated in:

# 

# ```text

# data/google\_sheets\_export/

# ```

# 

# The export contains six datasets:

# 

# \- startups.csv

# \- products.csv

# \- research\_papers.csv

# \- jobs.csv

# \- news.csv

# \- entity\_mapping\_log.csv

# 

# These files can be imported into separate tabs in a Google Spreadsheet.

# 

# \## Reliability and Data Quality

# 

# The project incorporates:

# 

# \- Asynchronous requests for concurrent data collection.

# \- Retry handling and backoff for transient API errors.

# \- Text chunking for large LLM extraction inputs.

# \- Structured output validation using Pydantic.

# \- Fuzzy matching with configurable similarity thresholds.

# \- Record-level success and failure tracking.

# \- Source URLs and collection metadata for traceability.

# 

# \## Current Limitations

# 

# FrontierAtlas is a working prototype, with several production enhancements remaining:

# 

# \- Complete multi-provider LLM fallback across Gemini, Groq and DeepSeek.

# \- Database-backed persistence using PostgreSQL.

# \- Distributed queues and worker orchestration.

# \- More comprehensive automated testing and monitoring.

# \- Improved reliability across external data providers.

# \- Production deployment and scheduled incremental ingestion.

# 

# \## Future Scalability

# 

# The proposed production architecture targets 500,000+ records through:

# 

# \- PostgreSQL for structured data and relational queries.

# \- Redis Streams or RabbitMQ for task distribution.

# \- Horizontally scalable crawler and extraction workers.

# \- Object storage for raw documents and snapshots.

# \- Vector search for semantic retrieval.

# \- Optional graph storage for entity relationships.

# \- Monitoring, alerting, checkpointing and automated recovery.

# 

# The architecture document is available in `architecture.pdf`.

# 

# \## Responsible Data Collection

# 

# FrontierAtlas prioritizes official APIs, RSS feeds and accessible public datasets. Collection should respect source terms, robots.txt policies, rate limits and access controls. Browser automation should only be used where permitted.

# 

# \## Author

# 

# \*\*Kiran Raj\*\*

# 

# GitHub: https://github.com/kiran162005

# 

# \---

# 

# \*FrontierAtlas — Building structured intelligence from the AI ecosystem.\*

