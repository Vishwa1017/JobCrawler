"""
Indeed Canada scraper.
Uses the public search page with date-sorted results.
Parses the embedded JSON job data from the page source.
"""

import re
import json
import requests
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS

SEARCH_QUERIES = [
    "backend software engineer machine learning",
    "backend engineer generative ai",
    "ml engineer python",
    "genai engineer",
    "llm engineer",
]

BASE_URL = (
    "https://ca.indeed.com/jobs"
    "?q={query}&l=Canada&sort=date&fromage=1&limit=25&start={start}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _matches_role(title: str) -> bool:
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def _extract_jobs_from_html(html: str) -> list[dict]:
    """Indeed embeds job data as JSON in window.mosaic.providerData."""
    jobs = []

    # Try the structured JSON blob first
    pattern = r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return jobs

    try:
        data = json.loads(match.group(1))
        job_cards = (
            data.get("metaData", {})
                .get("mosaicProviderJobCardsModel", {})
                .get("results", [])
        )
    except (json.JSONDecodeError, AttributeError):
        return jobs

    for card in job_cards:
        title = card.get("title", "")
        company = card.get("company", "Unknown")
        location = card.get("formattedLocation", "Canada")
        job_key = card.get("jobkey", "")
        job_url = f"https://ca.indeed.com/viewjob?jk={job_key}"

        if not _matches_role(title):
            continue

        jobs.append({
            "id": f"indeed_{job_key}",
            "title": title,
            "company": company,
            "location": location,
            "url": job_url,
            "source": "Indeed Canada",
            "level": "",
        })

    return jobs


def fetch_jobs() -> list[dict]:
    results = []
    seen_ids: set[str] = set()

    for query in SEARCH_QUERIES:
        for start in range(0, 50, 25):
            try:
                url = BASE_URL.format(
                    query=requests.utils.quote(query),
                    start=start,
                )
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if not resp.ok:
                    print(f"[indeed] HTTP {resp.status_code} for query='{query}'")
                    break

                jobs = _extract_jobs_from_html(resp.text)
                if not jobs:
                    break

                for job in jobs:
                    if job["id"] not in seen_ids:
                        seen_ids.add(job["id"])
                        results.append(job)

            except requests.RequestException as e:
                print(f"[indeed] query='{query}' start={start}: {e}")
                break

    return results
