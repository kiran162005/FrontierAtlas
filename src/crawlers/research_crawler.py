
import asyncio
import aiohttp
import feedparser
import json

from pathlib import Path
from datetime import datetime, timezone


ARXIV_API = "https://export.arxiv.org/api/query"
OUTPUT_FILE = Path("data/research_papers.json")


async def fetch_batch(session, start, batch_size):
    params = {
        "search_query": "cat:cs.AI",
        "start": start,
        "max_results": batch_size,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    for attempt in range(3):
        try:
            async with session.get(
                ARXIV_API,
                params=params
            ) as response:

                response.raise_for_status()
                xml_data = await response.text()

            feed = feedparser.parse(xml_data)

            if feed.bozo and not feed.entries:
                raise ValueError("Invalid arXiv response")

            papers = []

            for entry in feed.entries:
                paper = {
                    "title": " ".join(entry.title.split()),
                    "authors": [
                        author.name for author in entry.authors
                    ],
                    "abstract": " ".join(entry.summary.split()),
                    "published_date": entry.published,
                    "updated_date": entry.updated,
                    "source": "arXiv",
                    "source_url": entry.link,
                    "arxiv_id": entry.id.split("/abs/")[-1],
                    "github_url": None,
                    "github_stars": None,
                    "collected_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }

                papers.append(paper)

            return papers

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError
        ) as error:

            if attempt == 2:
                raise RuntimeError(
                    f"Failed to fetch batch starting at {start}: {error}"
                ) from error

            wait_time = 5 * (2 ** attempt)

            print(
                f"Request failed: {error}. "
                f"Retrying in {wait_time} seconds..."
            )

            await asyncio.sleep(wait_time)


def save_papers(papers):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )


async def main():
    target_count = 1000
    batch_size = 100

    # Load previously collected records
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open("r", encoding="utf-8") as file:
            all_papers = json.load(file)
    else:
        all_papers = []

    # Use arXiv IDs to prevent duplicates
    existing_ids = {
        paper["arxiv_id"] for paper in all_papers
    }

    timeout = aiohttp.ClientTimeout(
        total=180,
        connect=30,
        sock_read=150
    )

    headers = {
        "User-Agent": "FrontierAtlasResearchCrawler/1.0"
    }

    print("Starting arXiv research paper collection...")
    print(f"Target: {target_count} papers")

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        for start in range(0, target_count, batch_size):

            print(
                f"\nFetching batch: "
                f"{start + 1} to "
                f"{min(start + batch_size, target_count)}"
            )

            batch = await fetch_batch(
                session,
                start,
                batch_size
            )

            new_papers = [
                paper for paper in batch
                if paper["arxiv_id"] not in existing_ids
            ]

            all_papers.extend(new_papers)

            for paper in new_papers:
                existing_ids.add(paper["arxiv_id"])

            # Save after every successful batch
            save_papers(all_papers)

            print(
                f"Retrieved: {len(batch)} | "
                f"New records: {len(new_papers)} | "
                f"Total saved: {len(all_papers)}"
            )

            # Respect arXiv request rate limits
            if start + batch_size < target_count:
                await asyncio.sleep(3)

    print("\nResearch paper collection completed!")
    print(f"Total unique papers saved: {len(all_papers)}")
    print(f"Output file: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
