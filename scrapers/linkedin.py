"""
LinkedIn Jobs scraper using the public guest API — no login required.
f_TPR=r3600 filters for jobs posted in the last hour.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
    "backend software engineer machine learning",
    "backend engineer generative ai",
    "ml engineer canada",
    "llm engineer",
    "genai software engineer",
]

GUEST_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/siteMapJobPostings/"
    "?keywords={kw}&location={loc}&f_TPR=r3600&f_E=2%2C3&start={start}&count=25"
)


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def fetch_jobs() -> list[dict]:
    results = []
    seen: set[str] = set()

    for query in QUERIES:
        for start in [0, 25]:
            try:
                url = GUEST_URL.format(
                    kw=requests.utils.quote(query),
                    loc=requests.utils.quote(LOCATION),
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
                    match = re.search(r"(\d{8,})", urn)
                    if not match:
                        continue

                    job_id = match.group(1)
                    if job_id in seen:
                        continue

                    title_tag = card.find("h3")
                    company_tag = card.find("h4")
                    loc_tag = card.find(class_=re.compile(r"job-search-card__location|job-result-card__location"))

                    title = title_tag.get_text(strip=True) if title_tag else ""
                    if not title or not _matches_role(title):
                        continue

                    seen.add(job_id)
                    results.append({
                        "id": f"linkedin_{job_id}",
                        "title": title,
                        "company": company_tag.get_text(strip=True) if company_tag else "Unknown",
                        "location": loc_tag.get_text(strip=True) if loc_tag else LOCATION,
                        "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                        "posted": "",
                        "source": "LinkedIn",
                    })

            except requests.RequestException as e:
                print(f"[linkedin] {query} start={start}: {e}")
                break

    return results
