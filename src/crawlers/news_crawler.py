
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
import feedparser
import trafilatura


SOURCES = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Ars Technica AI": "https://arstechnica.com/ai/feed/",
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "OpenAI News": "https://openai.com/news/rss.xml",
}

OUTPUT_FILE = Path("data/news.json")
LOOKBACK_HOURS = 24
MAX_CONCURRENT_ARTICLES = 8

HEADERS = {
    "User-Agent": "FrontierAtlasResearchBot/1.0 (educational research project)"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def parse_published_date(entry):
    """Convert an RSS publication date into a timezone-aware UTC datetime."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)

        if parsed:
            try:
                from calendar import timegm
                return datetime.fromtimestamp(
                    timegm(parsed),
                    tz=timezone.utc
                )
            except (ValueError, TypeError, OverflowError):
                pass

    return None


async def fetch_feed(session, source_name, feed_url):
    """Fetch and parse one RSS/Atom feed."""
    try:
        async with session.get(feed_url) as response:
            response.raise_for_status()
            content = await response.read()

        parsed_feed = feedparser.parse(content)

        if parsed_feed.bozo and not parsed_feed.entries:
            logging.warning("%s: Feed parsing failed", source_name)
            return []

        logging.info(
            "%s: received %d entries",
            source_name,
            len(parsed_feed.entries)
        )

        return parsed_feed.entries

    except Exception as error:
        logging.error("%s: Feed request failed: %s", source_name, error)
        return []


async def extract_article(session, semaphore, article_url):
    """Download an article and extract its readable text."""
    if not article_url:
        return ""

    async with semaphore:
        for attempt in range(2):
            try:
                async with session.get(article_url) as response:
                    if response.status != 200:
                        return ""

                    html = await response.text(errors="replace")

                extracted = trafilatura.extract(
                    html,
                    url=article_url,
                    include_comments=False,
                    include_tables=True,
                    favor_precision=True
                )

                return extracted or ""

            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt == 0:
                    await asyncio.sleep(2)

            except Exception as error:
                logging.warning(
                    "Article extraction failed for %s: %s",
                    article_url,
                    error
                )
                return ""

    return ""


async def main():
    print("\nStarting FrontierAtlas AI News Crawler...")
    print("Time window: Last 24 hours")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=LOOKBACK_HOURS)

    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=15)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ARTICLES)

    collected = []
    seen_urls = set()
    source_counts = {}

    async with aiohttp.ClientSession(
        headers=HEADERS,
        timeout=timeout,
        connector=connector
    ) as session:

        # Step 1: Fetch all five RSS feeds.
        feed_tasks = [
            fetch_feed(session, name, url)
            for name, url in SOURCES.items()
        ]

        feed_results = await asyncio.gather(*feed_tasks)

        # Step 2: Keep only entries published within the last 24 hours.
        articles_to_extract = []

        for (source_name, feed_url), entries in zip(
            SOURCES.items(),
            feed_results
        ):
            source_counts[source_name] = 0

            for entry in entries:
                published_at = parse_published_date(entry)

                # Do not guess publication dates.
                if published_at is None:
                    continue

                if not (cutoff <= published_at <= now):
                    continue

                article_url = entry.get("link", "").strip()

                if not article_url or article_url in seen_urls:
                    continue

                seen_urls.add(article_url)

                articles_to_extract.append({
                    "title": entry.get("title", "").strip(),
                    "article_url": article_url,
                    "published_at": published_at.isoformat(),
                    "source": source_name,
                    "source_feed_url": feed_url,
                    "summary": entry.get("summary", ""),
                })

        print(
            f"\nArticles published in the last 24 hours: "
            f"{len(articles_to_extract)}"
        )

        # Step 3: Extract full article text concurrently.
        extraction_tasks = [
            extract_article(
                session,
                semaphore,
                article["article_url"]
            )
            for article in articles_to_extract
        ]

        article_texts = await asyncio.gather(*extraction_tasks)

        # Step 4: Build final records.
        for article, full_text in zip(
            articles_to_extract,
            article_texts
        ):
            record = {
                "title": article["title"],
                "source": article["source"],
                "published_at": article["published_at"],
                "article_url": article["article_url"],
                "source_feed_url": article["source_feed_url"],
                "summary": article["summary"],
                "full_text": full_text,
                "full_text_extracted": bool(full_text),
                "collected_at": now.isoformat(),
            }

            collected.append(record)
            source_counts[article["source"]] += 1

    # Step 5: Save records.
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(collected, file, indent=2, ensure_ascii=False)

    print("\n========== NEWS COLLECTION SUMMARY ==========")
    print(f"Sources configured: {len(SOURCES)}")
    print(f"Articles collected: {len(collected)}")
    print(
        "Full-text extraction successes:",
        sum(item["full_text_extracted"] for item in collected)
    )

    print("\nRecords by source:")
    for source, count in source_counts.items():
        print(f"  {source}: {count}")

    print(f"\nOutput: {OUTPUT_FILE}")
    print("News crawler completed.")


if __name__ == "__main__":
    asyncio.run(main())
