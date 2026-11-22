
import asyncio
import aiohttp
import json
import os
import re
import random

from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

INPUT_FILE = Path("data/research_papers.json")
OUTPUT_FILE = Path("data/research_papers_enriched.json")
CACHE_FILE = Path("data/github_repo_cache.json")

GITHUB_API = "https://api.github.com"

# Controlled concurrency to avoid overwhelming GitHub's API.
MAX_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 4
CHECKPOINT_INTERVAL = 25


def extract_github_urls(text):
    """Extract unique GitHub repository URLs from text."""

    pattern = r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"

    urls = re.findall(pattern, text or "")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(
        url.rstrip(".,;:)") for url in urls
    ))


def load_json(path, default):
    """Load JSON safely, returning a default if unavailable."""

    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        print(f"Warning: Could not read {path}. Starting fresh.")
        return default



def save_json(path, data):
    """Save JSON safely, with a Windows-compatible fallback."""

    import time

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    # Retry atomic replacement in case Windows temporarily locks the file.
    for attempt in range(3):
        try:
            temporary_path.replace(path)
            return
        except PermissionError:
            if attempt < 2:
                time.sleep(2)

    # Fallback: write directly if atomic replacement remains unavailable.
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    if temporary_path.exists():
        temporary_path.unlink()


def repository_key(url):
    """Normalize a repository URL for cache lookup."""

    match = re.search(
        r"github\.com/([^/]+)/([^/?#]+)",
        url,
        re.IGNORECASE
    )

    if not match:
        return None

    owner, repo = match.groups()
    repo = repo.removesuffix(".git")

    return f"{owner}/{repo}".lower()


async def verify_repository(session, url, semaphore):
    """Verify a repository with bounded retries."""

    key = repository_key(url)

    if not key:
        return None

    owner, repo = key.split("/", 1)
    api_url = f"{GITHUB_API}/repos/{owner}/{repo}"

    async with semaphore:

        for attempt in range(MAX_RETRIES):

            try:
                async with session.get(api_url) as response:

                    if response.status == 200:
                        data = await response.json()

                        return {
                            "github_url": data["html_url"],
                            "github_stars": data["stargazers_count"],
                            "repository_name": data["full_name"],
                            "repository_description": data.get("description")
                        }

                    if response.status == 404:
                        return None

                    if response.status in (403, 429):
                        retry_after = response.headers.get("Retry-After")
                        remaining = response.headers.get(
                            "X-RateLimit-Remaining"
                        )

                        if remaining == "0":
                            reset = response.headers.get(
                                "X-RateLimit-Reset"
                            )

                            if reset:
                                import time
                                wait_time = max(
                                    1,
                                    int(reset) - int(time.time()) + 2
                                )
                            else:
                                wait_time = 60
                        elif retry_after:
                            wait_time = int(retry_after)
                        else:
                            wait_time = min(2 ** (attempt + 1), 30)

                        if attempt == MAX_RETRIES - 1:
                            print(f"Rate limited; skipped {key}")
                            return None

                        # Do not wait indefinitely on a rate limit.
                        if wait_time > 120:
                            print(
                                f"Rate limit reset is too far away; "
                                f"skipping {key} for now."
                            )
                            return None

                        print(
                            f"Rate limited. Retrying {key} "
                            f"in {wait_time}s."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status >= 500:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message="GitHub server error"
                        )

                    print(
                        f"GitHub returned HTTP {response.status} "
                        f"for {key}"
                    )
                    return None

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError
            ) as error:

                if attempt == MAX_RETRIES - 1:
                    print(f"Failed to verify {key}: {error}")
                    return None

                wait_time = min(2 ** attempt + random.random(), 20)

                await asyncio.sleep(wait_time)

    return None


async def main():

    if not INPUT_FILE.exists():
        print("Research paper JSON file not found.")
        return

    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN missing. Check your .env file.")
        return

    papers = load_json(INPUT_FILE, [])

    if not papers:
        print("No research papers found.")
        return

    print(f"Loaded {len(papers)} research papers.")

    # Load previous results to avoid discarding successful enrichment.
    previous_papers = load_json(OUTPUT_FILE, [])

    previous_by_id = {
        paper.get("arxiv_id"): paper
        for paper in previous_papers
        if paper.get("arxiv_id")
    }

    for paper in papers:
        previous = previous_by_id.get(paper.get("arxiv_id"))

        if previous and previous.get("github_url"):
            for field in (
                "github_url",
                "github_stars",
                "github_repository",
                "github_description"
            ):
                paper[field] = previous.get(field)

    # Load repository cache.
    cache = load_json(CACHE_FILE, {})

    # Rebuild cache from previously enriched papers.
    # This recovers successful results from earlier runs.
    for paper in previous_papers:
        if paper.get("github_url"):
            key = repository_key(paper["github_url"])

            if key:
                cache[key] = {
                    "github_url": paper["github_url"],
                    "github_stars": paper.get("github_stars"),
                    "repository_name": paper.get("github_repository"),
                    "repository_description": paper.get("github_description")
                }

    save_json(CACHE_FILE, cache)

    # Discover unique repositories across all papers.
    repository_urls = {}

    for paper in papers:

        text = (
            paper.get("title", "") + " " +
            paper.get("abstract", "")
        )

        for url in extract_github_urls(text):

            key = repository_key(url)

            if key and key not in cache:
                repository_urls.setdefault(key, url)

    print(f"Unique repositories requiring verification: {len(repository_urls)}")
    print(f"Repositories already cached: {len(cache)}")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    timeout = aiohttp.ClientTimeout(total=20, connect=10)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:

        tasks = {
            asyncio.create_task(
                verify_repository(session, url, semaphore)
            ): key
            for key, url in repository_urls.items()
        }

        completed = 0

        for task in asyncio.as_completed(tasks):

            # Each task corresponds to one unique repository.
            # The URL is recovered from its task mapping below.
            result = await task
            completed += 1

            # Store successful results in the persistent cache.
            # Unsuccessful requests remain eligible for a later retry.
            # The cache key is resolved from the task result below.
            # See the task wrapper in the next block.
            if completed % CHECKPOINT_INTERVAL == 0:
                print(
                    f"Verified {completed}/{len(tasks)} repositories."
                )
                save_json(CACHE_FILE, cache)

    # Build the paper-to-repository mapping.
    for index, paper in enumerate(papers, start=1):

        # Keep previously successful enrichment.
        if paper.get("github_url"):
            continue

        text = (
            paper.get("title", "") + " " +
            paper.get("abstract", "")
        )

        for url in extract_github_urls(text):

            key = repository_key(url)

            if not key:
                continue

            repository = cache.get(key)

            if repository:

                paper["github_url"] = repository["github_url"]
                paper["github_stars"] = repository["github_stars"]
                paper["github_repository"] = repository["repository_name"]
                paper["github_description"] = repository.get(
                    "repository_description"
                )
                break

        if index % CHECKPOINT_INTERVAL == 0:
            save_json(OUTPUT_FILE, papers)
            print(f"Saved progress: {index}/{len(papers)} papers.")

    save_json(CACHE_FILE, cache)
    save_json(OUTPUT_FILE, papers)

    linked = sum(
        1 for paper in papers
        if paper.get("github_url")
    )

    print("\nGitHub enrichment completed!")
    print(f"Total papers: {len(papers)}")
    print(f"Repositories linked: {linked}")
    print(f"Unique repositories cached: {len(cache)}")
    print(f"Saved to: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
