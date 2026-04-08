"""
Greenhouse ATS — direct company career page API.
Stripe careers, OpenAI careers, Airbnb careers etc. all run on Greenhouse.
Only returns jobs posted/updated in the last 1 hour.
"""

import time
import requests
from datetime import datetime, timezone, timedelta
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION
from companies import GREENHOUSE_COMPANIES

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobCrawler/1.0)"}
CUTOFF = timedelta(hours=1)


def _is_recent(updated_at: str) -> bool:
    try:
        posted = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - posted <= CUTOFF
    except Exception:
        return False


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


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
                continue
            if not resp.ok:
                continue

            for job in resp.json().get("jobs", []):
                title = job.get("title", "")
                location = job.get("location", {}).get("name", "")
                updated_at = job.get("updated_at", "")

                if not _is_recent(updated_at):
                    continue
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
                    "posted": updated_at,
                    "source": "Greenhouse",
                })

        except requests.RequestException:
            pass

        time.sleep(0.3)

    return results
