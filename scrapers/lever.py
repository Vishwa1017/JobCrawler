"""
Lever ATS — direct company career page API.
Netflix careers, Cohere careers, Reddit careers etc. all run on Lever.
Only returns jobs posted in the last 1 hour.
"""

import time
import requests
from datetime import datetime, timezone, timedelta
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION
from companies import LEVER_COMPANIES

BASE_URL = "https://api.lever.co/v0/postings/{company}?mode=json&commitment=Full-time"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobCrawler/1.0)"}
CUTOFF_MS = 60 * 60 * 1000  # 1 hour in milliseconds


def _is_recent(created_at_ms: int) -> bool:
    try:
        now_ms = datetime.now(timezone.utc).timestamp() * 1000
        return (now_ms - created_at_ms) <= CUTOFF_MS
    except Exception:
        return False


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def _matches_location(categories: dict) -> bool:
    location = (categories.get("location") or "").lower()
    return LOCATION.lower() in location or "remote" in location


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
                continue

            jobs = resp.json()
            if not isinstance(jobs, list):
                continue

            for job in jobs:
                title = job.get("text", "")
                categories = job.get("categories", {})
                created_at = job.get("createdAt", 0)

                if not _is_recent(created_at):
                    continue
                if not _matches_role(title):
                    continue
                if not _matches_location(categories):
                    continue

                location = categories.get("location") or LOCATION
                posted_dt = datetime.fromtimestamp(
                    created_at / 1000, tz=timezone.utc
                ).isoformat()

                results.append({
                    "id": f"lever_{job['id']}",
                    "title": title,
                    "company": company.replace("-", " ").title(),
                    "location": location,
                    "url": job.get("hostedUrl", ""),
                    "posted": posted_dt,
                    "source": "Lever",
                })

        except requests.RequestException:
            pass

        time.sleep(0.3)

    return results
