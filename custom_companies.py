# Drop company names and their careers page URL here.
# The scraper will visit each URL and look for matching jobs.
#
# Format:
# {
#     "name": "Company Name",
#     "url": "https://company.com/careers",  # their careers/jobs page
# }
#
# Supported ATS (auto-detected from URL):
#   - Greenhouse  → boards.greenhouse.io or careers page powered by Greenhouse
#   - Lever       → jobs.lever.co
#   - Workday     → company.wd5.myworkdayjobs.com
#   - Generic     → any other careers page (scraped with Playwright)

CUSTOM_COMPANIES = [
    # Add companies here — example:
    # {"name": "Google",    "url": "https://careers.google.com/jobs/results/?q=backend+engineer&location=Canada&sort_by=date"},
    # {"name": "Amazon",    "url": "https://www.amazon.jobs/en/search?base_query=backend+engineer&loc_query=Canada&sort=recent"},
    # {"name": "Microsoft", "url": "https://jobs.microsoft.com/en-us/search?q=backend+engineer&l=Canada&exp=Entrylevel%2CMidlevel"},
    # {"name": "Apple",     "url": "https://jobs.apple.com/en-ca/search?search=backend+engineer&sort=newest"},
    # {"name": "Meta",      "url": "https://www.metacareers.com/jobs?q=backend+engineer&locations%5B0%5D=Canada&sort_by_new=true"},
    # {"name": "Shopify",   "url": "https://www.shopify.com/careers/search?keywords=backend+engineer&sort=newest"},
]
