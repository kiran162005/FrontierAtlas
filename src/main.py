
import asyncio
import logging
import time
from datetime import datetime, timezone

from src.crawlers import (
    startup_crawler,
    product_crawler,
    research_crawler,
    github_enricher,
    news_crawler,
    jobs_crawler,
)

from src.processing import run_extraction
from src.resolution import entity_resolver


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("FrontierAtlas")


async def run_async_step(name, function):
    """Run an asynchronous pipeline step with error handling."""

    logger.info("Starting: %s", name)
    start = time.time()

    try:
        await function()

        elapsed = round(time.time() - start, 2)
        logger.info("Completed: %s (%.2f seconds)", name, elapsed)

        return {
            "step": name,
            "status": "success",
            "duration_seconds": elapsed,
        }

    except Exception as error:
        elapsed = round(time.time() - start, 2)

        logger.exception("Failed: %s", name)

        return {
            "step": name,
            "status": "failed",
            "duration_seconds": elapsed,
            "error": str(error),
        }


def run_sync_step(name, function):
    """Run a synchronous pipeline step with error handling."""

    logger.info("Starting: %s", name)
    start = time.time()

    try:
        function()

        elapsed = round(time.time() - start, 2)
        logger.info("Completed: %s (%.2f seconds)", name, elapsed)

        return {
            "step": name,
            "status": "success",
            "duration_seconds": elapsed,
        }

    except Exception as error:
        elapsed = round(time.time() - start, 2)

        logger.exception("Failed: %s", name)

        return {
            "step": name,
            "status": "failed",
            "duration_seconds": elapsed,
            "error": str(error),
        }


async def main():

    pipeline_start = time.time()

    logger.info("=" * 60)
    logger.info("FRONTIERATLAS - AI INTELLIGENCE PIPELINE")
    logger.info("=" * 60)

    results = []

    # Phase I: Data collection

    crawlers = [
        ("Startup Collection", startup_crawler.main),
        ("Product Collection", product_crawler.main),
        ("Research Paper Collection", research_crawler.main),
        ("GitHub Repository Enrichment", github_enricher.main),
        ("AI News Collection", news_crawler.main),
        ("AI Job Collection", jobs_crawler.main),
    ]

    for name, function in crawlers:
        result = await run_async_step(name, function)
        results.append(result)

        # Do not run downstream processing if a crawler failed.
        # Continue collecting from the other sources.

    # Phase III: LLM extraction

    extraction_result = run_sync_step(
        "LLM Entity and Intelligence Extraction",
        run_extraction.main,
    )
    results.append(extraction_result)

    # Phase IV: Entity resolution

    if extraction_result["status"] == "success":
        resolution_result = run_sync_step(
            "Deterministic Entity Resolution",
            entity_resolver.main,
        )
        results.append(resolution_result)

    # Final execution report

    total_time = round(time.time() - pipeline_start, 2)

    successful = sum(
        item["status"] == "success" for item in results
    )

    failed = sum(
        item["status"] == "failed" for item in results
    )

    report = {
        "pipeline": "FrontierAtlas",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "total_steps": len(results),
        "successful_steps": successful,
        "failed_steps": failed,
        "total_duration_seconds": total_time,
        "steps": results,
    }

    import json
    from pathlib import Path

    output_path = Path(__file__).resolve().parents[1] / "data"
    output_path.mkdir(exist_ok=True)

    report_file = output_path / "pipeline_report.json"

    with open(report_file, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    logger.info("=" * 60)
    logger.info("FRONTIERATLAS PIPELINE FINISHED")
    logger.info("Successful steps: %s", successful)
    logger.info("Failed steps: %s", failed)
    logger.info("Total duration: %s seconds", total_time)
    logger.info("Report: %s", report_file)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
