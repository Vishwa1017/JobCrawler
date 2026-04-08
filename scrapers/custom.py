"""
Custom company career sites scraper.
Auto-detects ATS type from the URL and uses the right method.
  - Greenhouse → hits their public API
  - Lever      → hits their public API
  - Workday    → Playwright scrape
  - Other      → Playwright scrape (generic)
"""

import re
import requests
from config import ROLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS, LOCATION
from custom_companies import CUSTOM_COMPANIES


def _matches_role(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_TITLE_KEYWORDS):
        return False
    return any(kw in t for kw in ROLE_KEYWORDS)


def _matches_location(location_str: str) -> bool:
    loc = location_str.lower()
    return LOCATION.lower() in loc or "remote" in loc


def _scrape_greenhouse(company_name: str, url: str) -> list[dict]:
    slug_match = re.search(r"greenhouse\.io/v1/boards/([^/]+)", url) or \
                 re.search(r"boards\.greenhouse\.io/([^/]+)", url)
    if not slug_match:
        return []
    slug = slug_match.group(1)
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = requests.get(api_url, timeout=10)
        if not resp.ok:
            return []
        jobs = []
        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            if _matches_role(title) and _matches_location(location):
                jobs.append({
                    "id": f"custom_greenhouse_{job['id']}",
                    "title": title,
                    "company": company_name,
                    "location": location or LOCATION,
                    "url": job.get("absolute_url", ""),
                    "posted": job.get("updated_at", ""),
                    "source": f"{company_name} (Careers)",
                })
        return jobs
    except Exception:
        return []


def _scrape_lever(company_name: str, url: str) -> list[dict]:
    slug_match = re.search(r"lever\.co/([^/?]+)", url)
    if not slug_match:
        return []
    slug = slug_match.group(1)
    api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(api_url, timeout=10)
        if not resp.ok:
            return []
        jobs = []
        for job in resp.json():
            title = job.get("text", "")
            categories = job.get("categories", {})
            location = categories.get("location", "")
            if _matches_role(title) and _matches_location(location):
                jobs.append({
                    "id": f"custom_lever_{job['id']}",
                    "title": title,
                    "company": company_name,
                    "location": location or LOCATION,
                    "url": job.get("hostedUrl", ""),
                    "posted": "",
                    "source": f"{company_name} (Careers)",
                })
        return jobs
    except Exception:
        return []


def _scrape_playwright(company_name: str, url: str) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return []

    results = []
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
            )
        )
        page = context.new_page()
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Generic: collect all text that looks like a job title from links
            links = page.query_selector_all("a[href]")
            seen_titles: set[str] = set()

            for link in links:
                title = link.inner_text().strip()
                href = link.get_attribute("href") or ""

                if not title or len(title) < 5 or len(title) > 120:
                    continue
                if not _matches_role(title):
                    continue
                if title in seen_titles:
                    continue

                full_url = href if href.startswith("http") else f"{url.rstrip('/')}/{href.lstrip('/')}"
                seen_titles.add(title)
                results.append({
                    "id": f"custom_{company_name.lower().replace(' ', '_')}_{abs(hash(href))}",
                    "title": title,
                    "company": company_name,
                    "location": LOCATION,
                    "url": full_url,
                    "posted": "",
                    "source": f"{company_name} (Careers)",
                })

        except PWTimeout:
            print(f"[custom] Timeout: {company_name}")
        except Exception as e:
            print(f"[custom] {company_name}: {e}")
        finally:
            browser.close()

    return results


def fetch_jobs() -> list[dict]:
    if not CUSTOM_COMPANIES:
        return []

    results = []
    for entry in CUSTOM_COMPANIES:
        name = entry.get("name", "Unknown")
        url = entry.get("url", "")
        if not url:
            continue

        print(f"[custom] Scanning {name}...")

        if "greenhouse.io" in url:
            jobs = _scrape_greenhouse(name, url)
        elif "lever.co" in url:
            jobs = _scrape_lever(name, url)
        else:
            jobs = _scrape_playwright(name, url)

        print(f"[custom] {name}: {len(jobs)} matching job(s)")
        results.extend(jobs)

    return results
