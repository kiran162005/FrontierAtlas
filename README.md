# FrontierAtlas

**AI-Powered Startup, Product, Research and Market Intelligence Pipeline**

FrontierAtlas is an end-to-end data intelligence project that collects information from the AI ecosystem, extracts structured insights using Large Language Models (LLMs), and resolves extracted entities against a canonical dataset.

The platform brings together startup profiles, AI products, research publications, GitHub repository information, AI-related news, and job opportunities.

## Key Features

- **Multi-source data collection:** Collects startup, product, research, news and job information from external sources and APIs.
- **Asynchronous crawling:** Uses Python `asyncio` and `aiohttp` for concurrent data collection.
- **Research enrichment:** Identifies GitHub repositories associated with research papers and retrieves repository star counts.
- **LLM-powered extraction:** Extracts structured entities, industries, technologies and key facts from collected content.
- **Entity resolution:** Uses RapidFuzz similarity matching to map extracted entities to canonical startup and product records.
- **Data quality:** Normalizes records, handles failures and maintains source attribution.
- **Data export:** Exports processed datasets into CSV files for Google Sheets analysis.

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
