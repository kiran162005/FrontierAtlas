
import json
import time
import logging
from pathlib import Path

from src.extraction.llm_extractor import extract_intelligence

DATASETS = {
    "startups": "data/startups.json",
    "products": "data/products.json",
    "research_papers": "data/research_papers_enriched.json",
    "news": "data/news.json",
    "jobs": "data/jobs.json",
}

OUTPUT_FILE = Path("data/extraction_results.json")

# Keep the initial workload small to protect API quota.
MAX_RECORDS_PER_DATASET = 10
DELAY_SECONDS = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")

    return data


def get_text(dataset, record):
    if dataset == "startups":
        return (
            f"Startup: {record.get('startup_name', '')}\n"
            f"Description: {record.get('description', '')}\n"
            f"Industry: {record.get('industry', '')}\n"
            f"Location: {record.get('location', '')}"
        )

    if dataset == "products":
        return (
            f"Product: {record.get('product_name', '')}\n"
            f"Description: {record.get('description', '')}\n"
            f"Category: {record.get('category', '')}"
        )

    if dataset == "research_papers":
        return (
            f"Paper title: {record.get('title', '')}\n"
            f"Abstract: {record.get('abstract', '')}\n"
            f"Authors: {record.get('authors', '')}"
        )

    if dataset == "news":
        return (
            f"Article title: {record.get('title', '')}\n"
            f"Article text: {record.get('full_text', '')}\n"
            f"Summary: {record.get('summary', '')}"
        )

    if dataset == "jobs":
        return (
            f"Job title: {record.get('job_title', '')}\n"
            f"Company: {record.get('company', '')}\n"
            f"Description: {record.get('description', '')}\n"
            f"Location: {record.get('location', '')}"
        )

    return ""


def get_source_url(dataset, record):
    if dataset == "news":
        return record.get("article_url", "")

    if dataset == "jobs":
        return record.get("job_url", "")

    if dataset == "research_papers":
        return record.get("source_url", "")

    return record.get("source_url") or record.get("website", "")


def save_results(results):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = OUTPUT_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    temporary_file.replace(OUTPUT_FILE)


def main():
    print("\nFRONTIERATLAS - BATCH EXTRACTION")
    print("=" * 50)

    if OUTPUT_FILE.exists():
        results = load_json(OUTPUT_FILE)
    else:
        results = []

    # Successful records are never extracted again.
    successful = {
        (item.get("dataset"), item.get("source_url"))
        for item in results
        if item.get("extraction_status") == "success"
    }

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for dataset, file_path in DATASETS.items():
        path = Path(file_path)

        if not path.exists():
            logging.warning("%s not found. Skipping.", file_path)
            continue

        records = load_json(path)

        print(f"\nProcessing {dataset}: {len(records)} records")

        candidates = []

        for record in records:
            source_url = get_source_url(dataset, record)
            key = (dataset, source_url)

            if not source_url:
                total_skipped += 1
                continue

            if key not in successful:
                candidates.append(record)

        batch = candidates[:MAX_RECORDS_PER_DATASET]

        print(f"Pending records: {len(candidates)}")
        print(f"Selected for extraction: {len(batch)}")

        for index, record in enumerate(batch, start=1):
            text = get_text(dataset, record).strip()
            source_url = get_source_url(dataset, record)

            if len(text) < 20:
                logging.warning("Insufficient text: %s", source_url)
                total_skipped += 1
                continue

            print(f"\n[{index}/{len(batch)}] {dataset}")
            print(f"Source: {source_url}")

            try:
                result = extract_intelligence(
                    text=text,
                    source_url=source_url,
                    content_type=dataset
                )

                result["dataset"] = dataset

                # Remove any previous failed attempt for this record.
                results = [
                    item for item in results
                    if not (
                        item.get("dataset") == dataset
                        and item.get("source_url") == source_url
                    )
                ]

                results.append(result)
                successful.add((dataset, source_url))

                total_success += 1
                print("Extraction successful")

            except Exception as error:
                logging.error("Extraction failed: %s", error)

                # Keep only the latest failure for this source.
                results = [
                    item for item in results
                    if not (
                        item.get("dataset") == dataset
                        and item.get("source_url") == source_url
                    )
                ]

                results.append({
                    "dataset": dataset,
                    "source_url": source_url,
                    "provider": "Groq",
                    "extraction_status": "failed",
                    "error": str(error)
                })

                total_failed += 1

            # Checkpoint after every record.
            save_results(results)

            time.sleep(DELAY_SECONDS)

    previous_successes = sum(
        1 for item in results
        if item.get("extraction_status") == "success"
    )

    previous_failures = sum(
        1 for item in results
        if item.get("extraction_status") == "failed"
    )

    print("\n" + "=" * 50)
    print("EXTRACTION SUMMARY")
    print("=" * 50)
    print(f"Successful this run: {total_success}")
    print(f"Failed this run: {total_failed}")
    print(f"Skipped this run: {total_skipped}")
    print(f"Total successful records: {previous_successes}")
    print(f"Total failed records: {previous_failures}")
    print(f"Total saved records: {len(results)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
