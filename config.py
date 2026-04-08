LOCATION = "Canada"

# Jobs must match at least one of these in title or description
ROLE_KEYWORDS = [
    "backend",
    "back-end",
    "back end",
    "software engineer",
    "software developer",
    "machine learning",
    "ml engineer",
    "generative ai",
    "genai",
    "gen ai",
    "ai engineer",
    "llm",
    "large language model",
    "nlp engineer",
    "python engineer",
    "python developer",
    "platform engineer",
    "data engineer",
    "applied scientist",
    "research engineer",
    "inference engineer",
    "foundation model",
]

# Jobs with these in title are too senior — skip
EXCLUDE_TITLE_KEYWORDS = [
    "staff engineer",
    "principal engineer",
    "distinguished engineer",
    "engineering director",
    "director of engineering",
    "vice president",
    "head of engineering",
    "senior staff",
    "engineering manager",
    "vp of",
    "vp,",
]

# How often Actions runs — used to filter "posted recently" on scrapers
CHECK_INTERVAL_MINUTES = 15
