
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import aiohttp


SOURCES = [
    {
        "name": "TiorAI",
        "url": "https://raw.githubusercontent.com/tioraicom/ai-tools-dataset/main/data/ai-tools.json",
    },
    {
        "name": "Harpd",
        "url": "https://raw.githubusercontent.com/harpd-dev/harpd-ai-datasets/main/data/products/products.json",
    },
]

OUTPUT_FILE = Path("data/products.json")


def extract_records(payload):
    """Handle JSON arrays and common dataset wrappers."""
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("products", "tools", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    return []


def first_value(record, keys):
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def normalize_product(record, source_name, dataset_url):
    if not isinstance(record, dict):
        return None

    name = first_value(record, ["name", "title", "product_name"])
    if not name:
        return None

    website = first_value(
        record,
        ["website", "official_url", "url", "link", "vendor_url"]
    )

    # Some directories use "url" for their own listing page.
    # Prefer a separate official/vendor website when available.
    listing_url = first_value(
        record,
        ["source_url", "review_url", "listing_url", "url"]
    )

    description = first_value(
        record,
        ["description", "summary", "short_description", "tagline"]
    )

    category = first_value(
        record,
        ["primary_category", "category", "categoryName", "category_name"]
    )

    pricing = first_value(
        record,
        ["pricing_model", "pricing", "pricingModel"]
    )

    if isinstance(category, list):
        category = ", ".join(str(x) for x in category)

    if isinstance(pricing, list):
        pricing = ", ".join(str(x) for x in pricing)

    if not website and listing_url:
        website = listing_url

    if not website:
        return None

    return {
        "product_name": str(name).strip(),
        "description": str(description).strip() if description else None,
        "website": str(website).strip(),
        "category": str(category).strip() if category else None,
        "pricing_model": str(pricing).strip() if pricing else None,
        "source": source_name,
        "source_url": str(listing_url or dataset_url),
        "source_dataset_url": dataset_url,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_source(session, source):
    print(f"\nFetching: {source['name']}")

    async with session.get(source["url"]) as response:
        response.raise_for_status()
        payload = await response.json(content_type=None)

    records = extract_records(payload)
    print(f"Records received: {len(records)}")

    products = []

    for record in records:
        product = normalize_product(
            record,
            source["name"],
            source["url"]
        )
        if product:
            products.append(product)

    print(f"Valid products: {len(products)}")
    return products


async def main():
    print("Starting AI product collection...")

    os.makedirs("data", exist_ok=True)

    timeout = aiohttp.ClientTimeout(total=90)

    headers = {
        "User-Agent": "FrontierAtlasResearch/1.0"
    }

    all_products = []

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        for source in SOURCES:
            try:
                products = await fetch_source(session, source)
                all_products.extend(products)

            except Exception as error:
                print(f"Source failed: {source['name']}")
                print(f"Reason: {error}")

    # Deduplicate by normalized product name.
    unique = {}

    for product in all_products:
        key = re.sub(
            r"[^a-z0-9]",
            "",
            product["product_name"].lower()
        )

        if not key:
            continue

        existing = unique.get(key)

        # Prefer the record with a description.
        if (
            existing is None
            or (
                not existing.get("description")
                and product.get("description")
            )
        ):
            unique[key] = product

    final_products = list(unique.values())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(final_products, file, indent=2, ensure_ascii=False)

    print("\n========== COLLECTION SUMMARY ==========")
    print(f"Total fetched: {len(all_products)}")
    print(f"Unique products: {len(final_products)}")
    print(f"Missing descriptions: {sum(not p['description'] for p in final_products)}")
    print(f"Missing websites: {sum(not p['website'] for p in final_products)}")
    print(f"Output: {OUTPUT_FILE}")

    if len(final_products) >= 1000:
        print("SUCCESS: 1000+ unique products collected.")
    else:
        print("WARNING: Fewer than 1000 unique products collected.")
        print("Do not duplicate records to reach the target.")


if __name__ == "__main__":
    asyncio.run(main())
