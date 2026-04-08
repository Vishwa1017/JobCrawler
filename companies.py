# Companies using Greenhouse ATS — public API, no auth needed
# API: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
GREENHOUSE_COMPANIES = [
    # Big Tech / Fortune 500 adjacent
    "airbnb", "coinbase", "databricks", "datadog", "discord",
    "doordash", "dropbox", "figma", "github", "gitlab",
    "hashicorp", "hubspot", "instacart", "lyft", "mongodb",
    "notion", "pagerduty", "palantir", "pinterest", "plaid",
    "roblox", "snap", "stripe", "twilio", "twitch",
    "unity", "zendesk", "zoom", "cloudflare", "confluent",
    "elastic", "postman", "amplitude", "airtable", "lattice",
    "carta", "checkr", "benchling", "retool", "loom",
    "faire", "whatnot", "brex", "gusto", "asana",
    "squarespace", "affirm", "chime", "rippling",
    # AI / GenAI companies
    "openai", "anthropic", "scale-ai", "huggingface",
    "perplexity", "runway", "adept", "together",
    # Canadian companies
    "cohere", "1password", "ada", "coveo", "lightspeed",
    "wealthsimple", "hootsuite", "applyboard",
]

# Companies using Lever ATS — public API, no auth needed
# API: https://api.lever.co/v0/postings/{slug}?mode=json
LEVER_COMPANIES = [
    # Big names
    "netflix", "reddit", "duolingo", "flexport", "deel",
    "remote", "mercury", "anyscale", "mistral",
    # AI / ML
    "cohere", "together-ai", "huggingface",
    # Startups with Canadian presence
    "linear", "dbt-labs", "census", "hightouch",
    "prefect", "dagster", "modal", "replicate",
    "fixie", "vectara", "weaviate", "pinecone",
]
