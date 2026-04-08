"""
Indeed Canada scraper.
Parses embedded JSON from the search results page.
Filters for jobs posted in the last 24h (Indeed has no hourly filter),
deduplication in main.py handles repeat runs.
"""

import re
import json
import requests
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://ca.indeed.com/",
}

QUERIES = [
    "backend software engineer machine learning",
    "backend engineer generative ai",
    "ml engineer python canada",
    "llm engineer canada",
    "genai software engineer",
]

SEARCH_URL = "https://ca.indeed.com/jobs?q={q}&l=Canada&sort=date&fromage=1&limit=25&start={start}"


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def _parse_jobs(html: str) -> list[dict]:
    jobs = []
    pattern = re.compile(
        r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.+?\});\s*window\.mosaic',
        re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return jobs

    try:
        data = json.loads(match.group(1))
        cards = (
            data.get("metaData", {})
                .get("mosaicProviderJobCardsModel", {})
                .get("results", [])
        )
    except (json.JSONDecodeError, AttributeError):
        return jobs

    for card in cards:
        title = card.get("title", "")
        if not _matches_role(title):
            continue
        job_key = card.get("jobkey", "")
        jobs.append({
            "id": f"indeed_{job_key}",
            "title": title,
            "company": card.get("company", "Unknown"),
            "location": card.get("formattedLocation", "Canada"),
            "url": f"https://ca.indeed.com/viewjob?jk={job_key}",
            "posted": "",
            "source": "Indeed",
        })
    return jobs


def fetch_jobs() -> list[dict]:
    results = []
    seen: set[str] = set()

    for query in QUERIES:
        for start in [0, 25]:
            try:
                url = SEARCH_URL.format(q=requests.utils.quote(query), start=start)
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if not resp.ok:
                    break
                for job in _parse_jobs(resp.text):
                    if job["id"] not in seen:
                        seen.add(job["id"])
                        results.append(job)
            except requests.RequestException as e:
                print(f"[indeed] {query}: {e}")
                break

    return results
