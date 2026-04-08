"""
Glassdoor scraper using Playwright headless browser.
Glassdoor has Cloudflare + login walls — Playwright handles it better than requests.
Note: Glassdoor may still block intermittently. Jobs here are a bonus on top of other sources.
"""

import re
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION

QUERIES = [
    "backend engineer machine learning",
    "backend engineer generative ai",
    "ml engineer",
]

SEARCH_URL = (
    "https://www.glassdoor.com/Job/canada-{query}-jobs-SRCH_IL.0,6_IN3_KO7,{end}.htm"
    "?sortBy=date&fromAge=1"
)


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def _build_url(query: str) -> str:
    slug = query.replace(" ", "-")
    end = 7 + len(slug)
    return SEARCH_URL.format(query=slug, end=end)


def fetch_jobs() -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("[glassdoor] playwright not installed — skipping")
        return []

    results = []
    seen: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-CA",
        )
        page = context.new_page()

        for query in QUERIES:
            try:
                url = _build_url(query)
                page.goto(url, timeout=20000, wait_until="domcontentloaded")

                # Dismiss any login/signup modal if it appears
                try:
                    page.click('[alt="Close"], .modal_closeIcon, [data-test="modal-close"]', timeout=3000)
                except PWTimeout:
                    pass

                page.wait_for_selector('[data-test="jobListing"], .JobCard_jobCardContainer__arQlW, li[data-id]', timeout=10000)

                cards = page.query_selector_all('[data-test="jobListing"], .JobCard_jobCardContainer__arQlW, li[data-id]')

                for card in cards:
                    # Extract job ID from link
                    link = card.query_selector("a[href*='/job-listing/']")
                    if not link:
                        link = card.query_selector("a[href*='glassdoor.com/job']")
                    if not link:
                        continue

                    href = link.get_attribute("href") or ""
                    id_match = re.search(r"jobListingId=(\d+)|/(\d+)\.htm", href)
                    if not id_match:
                        continue

                    job_id = id_match.group(1) or id_match.group(2)
                    if job_id in seen:
                        continue

                    title_el = card.query_selector('[data-test="job-title"], .JobCard_jobTitle__GLyJ1, a.jobLink')
                    company_el = card.query_selector('[data-test="employer-name"], .EmployerProfile_compactEmployerName__9MGcV')
                    location_el = card.query_selector('[data-test="emp-location"], .JobCard_location__Ds1fM')

                    title = title_el.inner_text().strip() if title_el else ""
                    if not title or not _matches_role(title):
                        continue

                    full_url = href if href.startswith("http") else f"https://www.glassdoor.com{href}"
                    seen.add(job_id)
                    results.append({
                        "id": f"glassdoor_{job_id}",
                        "title": title,
                        "company": company_el.inner_text().strip() if company_el else "Unknown",
                        "location": location_el.inner_text().strip() if location_el else LOCATION,
                        "url": full_url,
                        "posted": "",
                        "source": "Glassdoor",
                    })

            except PWTimeout:
                print(f"[glassdoor] Timeout on query: {query}")
            except Exception as e:
                print(f"[glassdoor] {query}: {e}")

        browser.close()

    return results
