"""
LinkedIn Jobs scraper using the public guest API (no login required).
Fetches jobs posted in the last 15 minutes using f_TPR=r900.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION

SEARCH_QUERIES = [
    "backend software engineer machine learning",
    "backend engineer generative ai",
    "ml engineer python canada",
    "genai backend engineer",
    "llm engineer canada",
]

GUEST_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/siteMapJobPostings/"
    "?keywords={keywords}&location={location}&f_TPR=r900&f_E=2%2C3&start={start}&count=25"
)

JOB_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _matches_role(title: str) -> bool:
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def _extract_job_id(urn: str) -> str | None:
    # urn format: urn:li:jobPosting:1234567890
    match = re.search(r"(\d{8,})", urn)
    return match.group(1) if match else None


def fetch_jobs() -> list[dict]:
    results = []
    seen_ids: set[str] = set()

    for query in SEARCH_QUERIES:
        for start in range(0, 50, 25):  # 2 pages per query
            try:
                url = GUEST_SEARCH_URL.format(
                    keywords=requests.utils.quote(query),
                    location=requests.utils.quote(LOCATION),
                    start=start,
                )
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if not resp.ok:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.find_all("li")

                if not cards:
                    break

                for card in cards:
                    urn = card.get("data-entity-urn", "")
                    job_id = _extract_job_id(urn)
                    if not job_id or job_id in seen_ids:
                        continue

                    title_tag = card.find("h3") or card.find(class_=re.compile("job-result-card__title|base-search-card__title"))
                    company_tag = card.find("h4") or card.find(class_=re.compile("job-result-card__subtitle|base-search-card__subtitle"))
                    location_tag = card.find(class_=re.compile("job-result-card__location|job-search-card__location"))

                    title = title_tag.get_text(strip=True) if title_tag else ""
                    company = company_tag.get_text(strip=True) if company_tag else "Unknown"
                    location = location_tag.get_text(strip=True) if location_tag else LOCATION

                    if not title or not _matches_role(title):
                        continue

                    seen_ids.add(job_id)
                    results.append({
                        "id": f"linkedin_{job_id}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                        "source": "LinkedIn",
                        "level": "Entry/Mid",
                    })

            except requests.RequestException as e:
                print(f"[linkedin] query='{query}' start={start}: {e}")
                break

    return results
