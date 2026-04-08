"""
Greenhouse ATS scraper.
Greenhouse exposes a public JSON API for every company's job board — no auth required.
API: https://boards-api.greenhouse.io/v1/boards/{company}/jobs
"""

import time
import requests
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION
from companies import GREENHOUSE_COMPANIES

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobCrawler/1.0)"}


def _matches_role(title: str) -> bool:
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def _matches_location(location_str: str) -> bool:
    loc = location_str.lower()
    return LOCATION.lower() in loc or "remote" in loc


def fetch_jobs() -> list[dict]:
    results = []

    for company in GREENHOUSE_COMPANIES:
        try:
            resp = requests.get(
                BASE_URL.format(company=company),
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 404:
                # Company slug doesn't exist on Greenhouse — skip silently
                continue
            if not resp.ok:
                print(f"[greenhouse] {company}: HTTP {resp.status_code}")
                continue

            data = resp.json()
            jobs = data.get("jobs", [])

            for job in jobs:
                title = job.get("title", "")
                location = job.get("location", {}).get("name", "")

                if not _matches_role(title):
                    continue
                if not _matches_location(location):
                    continue

                results.append({
                    "id": f"greenhouse_{job['id']}",
                    "title": title,
                    "company": company.replace("-", " ").title(),
                    "location": location or LOCATION,
                    "url": job.get("absolute_url", ""),
                    "source": "Greenhouse",
                    "level": "",
                })

        except requests.RequestException as e:
            print(f"[greenhouse] {company}: {e}")

        time.sleep(0.3)  # be polite

    return results
