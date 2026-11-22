
import json
import re
from pathlib import Path
from datetime import datetime, timezone

from rapidfuzz import fuzz


BASE_DIR = Path(__file__).resolve().parents[2]

CANONICAL_FILE = BASE_DIR / "data" / "canonical_entities.json"
EXTRACTION_FILE = BASE_DIR / "data" / "extraction_results.json"
OUTPUT_FILE = BASE_DIR / "data" / "entity_mapping_log.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_name(name):
    name = str(name or "").lower().strip()
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return " ".join(name.split())


def compatible_types(extracted_type, canonical_type):
    extracted_type = str(extracted_type or "").lower()
    canonical_type = str(canonical_type or "").lower()

    company_types = {"company", "startup", "organization"}
    product_types = {"product", "software", "tool"}

    if canonical_type == "company":
        return extracted_type in company_types

    if canonical_type == "product":
        return extracted_type in product_types

    return extracted_type == canonical_type


def find_best_match(entity, canonical_entities):
    name = entity.get("name", "")
    entity_type = entity.get("entity_type", "")

    if not name:
        return None, 0, "none"

    best_match = None
    best_score = 0
    best_method = "none"

    normalized_name = normalize_name(name)

    for canonical in canonical_entities:

        if not compatible_types(
            entity_type,
            canonical.get("entity_type")
        ):
            continue

        candidates = [canonical["canonical_name"]]
        candidates.extend(canonical.get("aliases", []))

        for candidate in candidates:

            normalized_candidate = normalize_name(candidate)

            if normalized_name == normalized_candidate:
                score = 100
                method = "exact"
            else:
                score = fuzz.WRatio(
                    normalized_name,
                    normalized_candidate
                )
                method = "fuzzy"

            if score > best_score:
                best_score = score
                best_match = canonical
                best_method = method

    if best_match is None:
        return None, 0, "none"

    return best_match, round(best_score, 2), best_method


def main():

    canonical_entities = load_json(CANONICAL_FILE)
    extraction_records = load_json(EXTRACTION_FILE)

    mapping_log = []

    successful_records = 0
    failed_records = 0
    total_entities = 0

    for record in extraction_records:

        if record.get("extraction_status") != "success":
            failed_records += 1
            continue

        successful_records += 1

        extraction = record.get("extraction", {})

        if not isinstance(extraction, dict):
            continue

        entities = extraction.get("entities", [])

        for entity in entities:

            if not isinstance(entity, dict):
                continue

            total_entities += 1

            match, score, method = find_best_match(
                entity,
                canonical_entities
            )

            if match and score >= 92:
                status = "auto_matched"

            elif match and score >= 85:
                status = "review_required"

            else:
                status = "unmatched"
                match = None
                method = "none"

            mapping_log.append({
                "dataset": record.get("dataset"),
                "source_url": record.get("source_url"),
                "extracted_entity": entity.get("name"),
                "extracted_type": entity.get("entity_type"),
                "canonical_id": (
                    match["canonical_id"] if match else None
                ),
                "canonical_name": (
                    match["canonical_name"] if match else None
                ),
                "match_score": score,
                "match_status": status,
                "match_method": method,
                "mapped_at": datetime.now(timezone.utc).isoformat()
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(mapping_log, file, indent=2, ensure_ascii=False)

    auto_matched = sum(
        item["match_status"] == "auto_matched"
        for item in mapping_log
    )

    review_required = sum(
        item["match_status"] == "review_required"
        for item in mapping_log
    )

    unmatched = sum(
        item["match_status"] == "unmatched"
        for item in mapping_log
    )

    print("\nENTITY RESOLUTION COMPLETE")
    print("--------------------------")
    print(f"Total extraction records: {len(extraction_records)}")
    print(f"Successful records: {successful_records}")
    print(f"Failed records skipped: {failed_records}")
    print(f"Entities processed: {total_entities}")
    print(f"Automatically matched: {auto_matched}")
    print(f"Require manual review: {review_required}")
    print(f"Unmatched: {unmatched}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
