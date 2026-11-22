
import asyncio
import aiohttp
import json

from pathlib import Path
from datetime import datetime, timezone


API_URL = "https://yc-oss.github.io/api/companies/all.json"

OUTPUT_FILE = Path("data/startups.json")


async def fetch_startups(session):
    for attempt in range(3):
        try:
            async with session.get(API_URL) as response:
                response.raise_for_status()
                return await response.json(content_type=None)

        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            if attempt == 2:
                raise

            wait_time = 5 * (2 ** attempt)
            print(f"Request failed: {error}")
            print(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)


def normalize_startup(company):
    """Convert source company data into our standard schema."""

    name = company.get("name")
    description = (
        company.get("long_description")
        or company.get("one_liner")
    )

    if not name or not description:
        return None

    return {
        "startup_name": name.strip(),
        "description": description.strip(),
        "website": company.get("website"),
        "industry": company.get("industry"),
        "subindustry": company.get("subindustry"),
        "location": company.get("all_locations"),
        "tags": company.get("tags", []),
        "batch": company.get("batch"),
        "status": company.get("status"),
        "team_size": company.get("team_size"),
        "source": "Y Combinator",
        "source_url": company.get("url"),
        "source_dataset_url": API_URL,
        "collected_at": datetime.now(timezone.utc).isoformat()
    }


async def main():
    print("Starting startup data collection...")
    print("Source: Y Combinator public company directory mirror")

    timeout = aiohttp.ClientTimeout(
        total=180,
        connect=30,
        sock_read=150
    )

    headers = {
        "User-Agent": "FrontierAtlas/1.0 (startup research project)"
    }

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        companies = await fetch_startups(session)

    print(f"Companies received from source: {len(companies)}")

    startups = []
    seen_names = set()

    for company in companies:
        startup = normalize_startup(company)

        if not startup:
            continue

        # Basic duplicate prevention
        normalized_name = startup["startup_name"].casefold()

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)
        startups.append(startup)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            startups,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nStartup collection completed!")
    print(f"Valid unique startups: {len(startups)}")
    print(f"Output: {OUTPUT_FILE.resolve()}")

    if len(startups) < 1000:
        print("WARNING: Fewer than 1,000 valid startups collected.")
    else:
        print("Target of 1,000 startups achieved!")

    print("\nSample records:")

    for startup in startups[:3]:
        print(
            startup["startup_name"],
            "|",
            startup["industry"],
            "|",
            startup["website"]
        )


if __name__ == "__main__":
    asyncio.run(main())
