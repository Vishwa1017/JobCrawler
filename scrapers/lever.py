"""
Lever ATS scraper.
Lever exposes a public JSON API for every company's postings — no auth required.
API: https://api.lever.co/v0/postings/{company}?mode=json
"""

import time
import requests
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION
from companies import LEVER_COMPANIES

BASE_URL = "https://api.lever.co/v0/postings/{company}?mode=json&commitment=Full-time"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobCrawler/1.0)"}


def _matches_role(title: str) -> bool:
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def _matches_location(categories: dict) -> bool:
    location = (categories.get("location") or "").lower()
    remote = (categories.get("commitment") or "").lower()
    return (
        LOCATION.lower() in location
        or "remote" in location
        or "remote" in remote
    )


def fetch_jobs() -> list[dict]:
    results = []

    for company in LEVER_COMPANIES:
        try:
            resp = requests.get(
                BASE_URL.format(company=company),
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 404:
                continue
            if not resp.ok:
                print(f"[lever] {company}: HTTP {resp.status_code}")
                continue

            jobs = resp.json()
            if not isinstance(jobs, list):
                continue

            for job in jobs:
                title = job.get("text", "")
                categories = job.get("categories", {})

                if not _matches_role(title):
                    continue
                if not _matches_location(categories):
                    continue

                location = categories.get("location") or LOCATION
                results.append({
                    "id": f"lever_{job['id']}",
                    "title": title,
                    "company": company.replace("-", " ").title(),
                    "location": location,
                    "url": job.get("hostedUrl", ""),
                    "source": "Lever",
                    "level": "",
                })

        except requests.RequestException as e:
            print(f"[lever] {company}: {e}")

        time.sleep(0.3)

    return results
