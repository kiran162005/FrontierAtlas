
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup


SOURCES = {
    "Arbeitnow": "https://www.arbeitnow.com/api/job-board-api?page=1",
    "Remote OK": "https://remoteok.com/api",
    "Himalayas": "https://himalayas.app/jobs/api?limit=20",
    "Jobicy": "https://jobicy.com/api/jobs?count=200",
    "Remotive": "https://remotive.com/api/remote-jobs",
}

OUTPUT_FILE = Path("data/jobs.json")
LOOKBACK_HOURS = 24

AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "generative ai", "genai", "llm", "large language model",
    "nlp", "natural language processing", "computer vision",
    "data scientist", "ai engineer", "ml engineer",
    "machine learning engineer", "robotics", "neural network",
    "prompt engineer", "rag", "agentic ai", " MLOps ",
]

HEADERS = {
    "User-Agent": "FrontierAtlasResearchBot/1.0 (educational research project)"
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def clean_text(value):
    """Convert HTML descriptions into readable plain text."""
    if not value:
        return ""

    soup = BeautifulSoup(str(value), "html.parser")
    return re.sub(r"\s+", " ", unescape(soup.get_text(" "))).strip()


def parse_date(value):
    """Normalize ISO, RFC, and Unix timestamps to UTC."""
    if value is None or value == "":
        return None

    try:
        if isinstance(value, (int, float)):
            # Handle seconds or milliseconds.
            if value > 10_000_000_000:
                value = value / 1000
            return datetime.fromtimestamp(value, tz=timezone.utc)

        value = str(value).strip()

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = parsedate_to_datetime(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (ValueError, TypeError, OverflowError, OSError):
        return None


def is_ai_related(job):
    searchable = " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        " ".join(job.get("tags", []))
        if isinstance(job.get("tags"), list) else str(job.get("tags", "")),
        str(job.get("category", "")),
    ]).lower()

    return any(keyword.strip().lower() in searchable for keyword in AI_KEYWORDS)


def extract_jobs(source, payload):
    """Convert each provider's response into a list of job dictionaries."""

    if source == "Arbeitnow":
        return payload.get("data", []) if isinstance(payload, dict) else []

    if source == "Remote OK":
        return payload[1:] if isinstance(payload, list) else []

    if source == "Himalayas":
        return payload.get("jobs", []) if isinstance(payload, dict) else []

    if source == "Jobicy":
        return payload.get("jobs", []) if isinstance(payload, dict) else []

    if source == "Remotive":
        return payload.get("jobs", []) if isinstance(payload, dict) else []

    return []


def normalize_job(source, job):
    """Map provider-specific fields into a common schema."""

    if source == "Arbeitnow":
        published = job.get("created_at")
        url = job.get("url")
        description = job.get("description")
        company = job.get("company_name")
        title = job.get("title")
        location = job.get("location")
        tags = job.get("tags", [])

    elif source == "Remote OK":
        published = job.get("date") or job.get("epoch")
        url = job.get("url")
        description = job.get("description")
        company = job.get("company")
        title = job.get("position")
        location = job.get("location")
        tags = job.get("tags", [])

    elif source == "Himalayas":
        published = (
            job.get("pubDate")
            or job.get("publishedAt")
            or job.get("createdAt")
        )
        url = job.get("applicationLink") or job.get("url")
        description = job.get("description")
        company = job.get("companyName")
        title = job.get("title")
        location = job.get("location") or job.get("locationRestrictions")
        tags = job.get("categories", [])

    elif source == "Jobicy":
        published = (
            job.get("pubDate")
            or job.get("published_at")
            or job.get("date")
        )
        url = job.get("url")
        description = job.get("jobDescription")
        company = job.get("companyName")
        title = job.get("jobTitle")
        location = job.get("jobGeo")
        tags = job.get("jobIndustry", [])

    else:  # Remotive
        published = job.get("publication_date")
        url = job.get("url")
        description = job.get("description")
        company = job.get("company_name")
        title = job.get("title")
        location = job.get("candidate_required_location")
        tags = job.get("tags", [])

    if isinstance(tags, str):
        tags = [tags]

    return {
        "job_title": str(title or "").strip(),
        "company": str(company or "").strip(),
        "location": location if isinstance(location, str) else json.dumps(location),
        "description": clean_text(description),
        "job_url": str(url or "").strip(),
        "published_at": parse_date(published),
        "tags": tags if isinstance(tags, list) else [],
        "source": source,
    }


async def fetch_source(session, source, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)

        jobs = extract_jobs(source, payload)
        logging.info("%s: received %d jobs", source, len(jobs))
        return source, jobs

    except Exception as error:
        logging.error("%s request failed: %s", source, error)
        return source, []


async def main():
    print("\nStarting FrontierAtlas AI Jobs Crawler...")
    print("Time window: Last 24 hours")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=LOOKBACK_HOURS)

    timeout = aiohttp.ClientTimeout(total=45)
    connector = aiohttp.TCPConnector(limit=10)

    collected = []
    seen_urls = set()
    source_counts = {source: 0 for source in SOURCES}

    async with aiohttp.ClientSession(
        headers=HEADERS,
        timeout=timeout,
        connector=connector
    ) as session:

        tasks = [
            fetch_source(session, source, url)
            for source, url in SOURCES.items()
        ]

        results = await asyncio.gather(*tasks)

        for source, jobs in results:
            for raw_job in jobs:
                job = normalize_job(source, raw_job)

                if not job["job_title"] or not job["job_url"]:
                    continue

                if job["job_url"] in seen_urls:
                    continue

                if not job["published_at"]:
                    continue

                if not (cutoff <= job["published_at"] <= now):
                    continue

                if not is_ai_related(job):
                    continue

                seen_urls.add(job["job_url"])

                collected.append({
                    "job_title": job["job_title"],
                    "company": job["company"],
                    "location": job["location"],
                    "description": job["description"],
                    "job_url": job["job_url"],
                    "published_at": job["published_at"].isoformat(),
                    "tags": job["tags"],
                    "source": source,
                    "collected_at": now.isoformat(),
                })

                source_counts[source] += 1

    collected.sort(key=lambda item: item["published_at"], reverse=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(collected, file, indent=2, ensure_ascii=False)

    print("\n========== JOB COLLECTION SUMMARY ==========")
    print(f"Sources configured: {len(SOURCES)}")
    print(f"AI jobs published in last 24 hours: {len(collected)}")
    print(f"Jobs with descriptions: {sum(bool(j['description']) for j in collected)}")

    print("\nRecords by source:")
    for source, count in source_counts.items():
        print(f"  {source}: {count}")

    print(f"\nOutput: {OUTPUT_FILE}")
    print("Jobs crawler completed.")


if __name__ == "__main__":
    asyncio.run(main())
