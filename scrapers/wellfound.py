"""
Wellfound (AngelList) startup jobs scraper.
Uses the public job search page filtered for Canada + relevant roles.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION

SEARCH_URL = (
    "https://wellfound.com/jobs"
    "?role=engineer&remote=true&location_type=remote&q={query}"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
    "machine+learning",
    "backend+engineer",
    "generative+ai",
]


def _matches_role(title: str) -> bool:
    title_lower = title.lower()
    if any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def fetch_jobs() -> list[dict]:
    results = []
    seen_ids: set[str] = set()

    for query in QUERIES:
        try:
            url = SEARCH_URL.format(query=query)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if not resp.ok:
                print(f"[wellfound] HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # Wellfound job cards have data-test="StartupResult" or similar
            # Try multiple selectors as they change their markup
            cards = soup.find_all("div", attrs={"data-test": re.compile("JobListing|job-listing")})
            if not cards:
                # Fallback: look for links with /jobs/ in href
                cards = soup.find_all("a", href=re.compile(r"/jobs/\d+"))

            for card in cards:
                if isinstance(card, str):
                    continue

                # Try to get job URL
                href = card.get("href", "") if card.name == "a" else ""
                if not href:
                    link = card.find("a", href=re.compile(r"/jobs/\d+"))
                    href = link.get("href", "") if link else ""

                job_id_match = re.search(r"/jobs/(\d+)", href)
                if not job_id_match:
                    continue

                job_id = job_id_match.group(1)
                if job_id in seen_ids:
                    continue

                title_tag = card.find(["h2", "h3", "span"], class_=re.compile("title|position|role", re.I))
                company_tag = card.find(["span", "div"], class_=re.compile("company|startup", re.I))

                title = title_tag.get_text(strip=True) if title_tag else card.get_text(strip=True)[:80]
                company = company_tag.get_text(strip=True) if company_tag else "Startup"

                if not _matches_role(title):
                    continue

                seen_ids.add(job_id)
                results.append({
                    "id": f"wellfound_{job_id}",
                    "title": title,
                    "company": company,
                    "location": "Remote / Canada",
                    "url": f"https://wellfound.com{href}",
                    "source": "Wellfound",
                    "level": "Entry/Mid",
                })

        except requests.RequestException as e:
            print(f"[wellfound] {query}: {e}")

    return results
