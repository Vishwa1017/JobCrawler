"""
JobCrawler — main entry point.
Runs all scrapers, finds new jobs, sends Telegram alerts, updates seen_jobs.json.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scrapers.greenhouse import fetch_jobs as greenhouse_jobs
from scrapers.lever import fetch_jobs as lever_jobs
from scrapers.linkedin import fetch_jobs as linkedin_jobs
from scrapers.indeed import fetch_jobs as indeed_jobs
from scrapers.wellfound import fetch_jobs as wellfound_jobs
from notifier import send_job_alert, send_summary

SEEN_JOBS_PATH = Path(__file__).parent / "data" / "seen_jobs.json"
RETENTION_DAYS = 30  # Remove entries older than this to keep file small


def load_seen_jobs() -> dict:
    if SEEN_JOBS_PATH.exists():
        try:
            return json.loads(SEEN_JOBS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_seen_jobs(seen: dict) -> None:
    SEEN_JOBS_PATH.write_text(
        json.dumps(seen, indent=2),
        encoding="utf-8",
    )


def purge_old_entries(seen: dict) -> dict:
    """Remove jobs seen more than RETENTION_DAYS ago to keep the file manageable."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    return {
        job_id: ts
        for job_id, ts in seen.items()
        if datetime.fromisoformat(ts) > cutoff
    }


def run_all_scrapers() -> list[dict]:
    all_jobs = []

    scrapers = [
        ("Greenhouse", greenhouse_jobs),
        ("Lever", lever_jobs),
        ("LinkedIn", linkedin_jobs),
        ("Indeed", indeed_jobs),
        ("Wellfound", wellfound_jobs),
    ]

    for name, scraper_fn in scrapers:
        print(f"[main] Running {name} scraper...")
        try:
            jobs = scraper_fn()
            print(f"[main] {name}: {len(jobs)} matching job(s) found")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[main] {name} scraper failed: {e}")

    return all_jobs


def main() -> None:
    print(f"[main] Starting crawl at {datetime.now(timezone.utc).isoformat()}")

    seen = load_seen_jobs()
    seen = purge_old_entries(seen)

    all_jobs = run_all_scrapers()

    new_count = 0
    now_str = datetime.now(timezone.utc).isoformat()

    for job in all_jobs:
        job_id = job["id"]
        if job_id in seen:
            continue  # Already notified

        print(f"[main] NEW: {job['title']} @ {job['company']} ({job['source']})")
        success = send_job_alert(job)

        if success:
            seen[job_id] = now_str
            new_count += 1
        else:
            print(f"[main] Failed to send alert for {job_id}")

    save_seen_jobs(seen)
    print(f"[main] Done. {new_count} new job(s) sent.")

    # Only send summary message when running in CI (GitHub Actions)
    if os.environ.get("GITHUB_ACTIONS"):
        send_summary(new_count)


if __name__ == "__main__":
    main()
