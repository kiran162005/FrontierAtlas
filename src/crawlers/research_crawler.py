
import asyncio
import aiohttp
import feedparser
import json
from pathlib import Path
from datetime import datetime, timezone


ARXIV_API = "https://export.arxiv.org/api/query"


async def fetch_research_papers(max_results=100):
    params = {
        "search_query": "cat:cs.AI",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            ARXIV_API,
            params=params,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:

            response.raise_for_status()
            xml_data = await response.text()

    feed = feedparser.parse(xml_data)

    papers = []

    for entry in feed.entries:
        paper = {
            "title": " ".join(entry.title.split()),
            "authors": [author.name for author in entry.authors],
            "abstract": " ".join(entry.summary.split()),
            "published_date": entry.published,
            "updated_date": entry.updated,
            "source": "arXiv",
            "source_url": entry.link,
            "arxiv_id": entry.id.split("/abs/")[-1],
            "github_url": None,
            "github_stars": None,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }

        papers.append(paper)

    return papers


async def main():
    print("Fetching research papers from arXiv...")

    papers = await fetch_research_papers(max_results=1000)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "research_papers.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(papers, file, indent=4, ensure_ascii=False)

    print(f"\nSuccessfully collected {len(papers)} papers.")
    print(f"Saved to: {output_file.resolve()}")

    if papers:
        print("\nSample paper:")
        print(json.dumps(papers[0], indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
