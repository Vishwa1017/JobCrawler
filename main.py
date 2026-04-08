"""
JobCrawler — runs every hour via GitHub Actions.
Sources: Greenhouse, Lever (direct APIs) + Indeed, LinkedIn, Glassdoor (scraped).
Only alerts on jobs not seen before. Deduplication via seen_jobs.json.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scrapers.greenhouse import fetch_jobs as greenhouse_jobs
from scrapers.lever import fetch_jobs as lever_jobs
from scrapers.indeed import fetch_jobs as indeed_jobs
from scrapers.linkedin import fetch_jobs as linkedin_jobs
from scrapers.glassdoor import fetch_jobs as glassdoor_jobs
from scrapers.custom import fetch_jobs as custom_jobs
from notifier import send_job_alert, send_summary

SEEN_JOBS_PATH = Path(__file__).parent / "data" / "seen_jobs.json"
RETENTION_DAYS = 7


def load_seen() -> dict:
    if SEEN_JOBS_PATH.exists():
        try:
            return json.loads(SEEN_JOBS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_seen(seen: dict) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    cleaned = {k: v for k, v in seen.items() if datetime.fromisoformat(v) > cutoff}
    SEEN_JOBS_PATH.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")


def main() -> None:
    print(f"[crawler] Starting at {datetime.now(timezone.utc).isoformat()}")

    seen = load_seen()
    new_count = 0
    now_str = datetime.now(timezone.utc).isoformat()

    scrapers = [
        ("Greenhouse",        greenhouse_jobs),
        ("Lever",             lever_jobs),
        ("Indeed",            indeed_jobs),
        ("LinkedIn",          linkedin_jobs),
        ("Glassdoor",         glassdoor_jobs),
        ("Custom Companies",  custom_jobs),
    ]

    for name, fn in scrapers:
        print(f"[crawler] Scanning {name}...")
        try:
            jobs = fn()
            print(f"[crawler] {name}: {len(jobs)} matching job(s)")

            for job in jobs:
                if job["id"] in seen:
                    continue
                ok = send_job_alert(job)
                if ok:
                    seen[job["id"]] = now_str
                    new_count += 1
                    print(f"[crawler] Sent: {job['title']} @ {job['company']}")

        except Exception as e:
            print(f"[crawler] {name} failed: {e}")

    save_seen(seen)
    print(f"[crawler] Done. {new_count} new alert(s) sent.")

    if os.environ.get("GITHUB_ACTIONS"):
        send_summary(new_count)


if __name__ == "__main__":
    main()
