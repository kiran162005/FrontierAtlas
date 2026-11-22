
import csv
import json
from pathlib import Path

DATASETS = {
    "Startups": "data/startups.json",
    "Products": "data/products.json",
    "Research Papers": "data/research_papers_enriched.json",
    "Jobs": "data/jobs.json",
    "News": "data/news.json",
    "Entity Mapping Log": "data/entity_mapping_log.json",
}

OUTPUT_DIR = Path("data/google_sheets_export")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}")

    return data


def normalize_value(value):
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return value


def export_dataset(name, source_path):
    path = Path(source_path)

    if not path.exists():
        print(f"SKIPPED: {name} - source file not found")
        return

    records = load_json(path)

    if not records:
        print(f"SKIPPED: {name} - no records")
        return

    # Build columns from all records, preserving their first-seen order.
    headers = []
    seen = set()

    for record in records:
        if not isinstance(record, dict):
            continue

        for key in record:
            if key not in seen:
                headers.append(key)
                seen.add(key)

    output_file = OUTPUT_DIR / f"{name.lower().replace(' ', '_')}.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=headers,
            extrasaction="ignore"
        )

        writer.writeheader()

        for record in records:
            if isinstance(record, dict):
                row = {
                    key: normalize_value(record.get(key))
                    for key in headers
                }
                writer.writerow(row)

    print(f"EXPORTED: {name}")
    print(f"Records: {len(records)}")
    print(f"Columns: {len(headers)}")
    print(f"File: {output_file}")
    print("-" * 45)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nFRONTIERATLAS - GOOGLE SHEETS CSV EXPORT")
    print("=" * 45)

    for name, source_path in DATASETS.items():
        export_dataset(name, source_path)

    print("\nCSV EXPORT COMPLETED")
    print(f"Output folder: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
