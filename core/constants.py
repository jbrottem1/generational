"""Shared constants for Generational."""

APP_VERSION = "7.6.0"

MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

IDEAS_PER_BATCH = 10
CANDIDATE_IDEAS = 20  # candidates generated before ranking selects the best
SCRIPT_VARIANTS_PER_IDEA = 3  # stylistic script variants generated per candidate
DEFAULT_PUBLISH_THRESHOLD = 70

RESEARCH_PROVIDERS = [
    "wikipedia",
    "pubmed",
    "arxiv",
    "crossref",
    "news",
    "trends",
    "youtube",
    "reddit",
    "tiktok",
]

RESEARCH_PROVIDER_LABELS = {
    "wikipedia": "Wikipedia (live)",
    "pubmed": "PubMed (live)",
    "arxiv": "arXiv (live)",
    "crossref": "Crossref (live)",
    "news": "News (placeholder)",
    "trends": "Google Trends (placeholder)",
    "youtube": "YouTube Trends (placeholder)",
    "reddit": "Reddit (placeholder)",
    "tiktok": "TikTok Trends (placeholder)",
}

RESEARCH_DEPTH_OPTIONS = ["shallow", "moderate", "deep"]

DEFAULT_RESEARCH_SETTINGS = {
    "enabled_providers": list(RESEARCH_PROVIDERS),
    "cache_ttl_hours": 24,
    "max_sources": 20,
    "min_confidence": 0.4,
    "research_depth": "moderate",
    "science_medical_strict": False,
    "citation_required": True,
    "research_confidence_threshold": 0.45,
    "max_unsupported_claims": 2,
    "min_claim_confidence": 0.5,
}

NICHE_KEYWORDS = {
    "Psychology": ["psychology", "psychological", "mindset", "mind", "behavior"],
    "AI & Future Tech": ["ai ", " ai", "future tech", "technology", "tech ", "robot", "artificial intelligence"],
    "Dark History": ["dark history", "history", "historical", "war", "ancient"],
    "Space": ["space", "nasa", "universe", "astronomy", "galaxy", "planet"],
    "Finance": ["finance", "money", "invest", "wealth", "budget", "stocks"],
    "Health": ["health", "fitness", "wellness", "nutrition", "diet"],
    "Science": ["science", "physics", "biology", "chemistry", "experiment", "quantum", "scientific"],
}

WORD_NUMBERS = {
    "a week": 7,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

EXAMPLE_COMMANDS = [
    "Create 10 psychology shorts about procrastination",
    "Generate 5 AI future tech video ideas",
    "Make a week of content for dark history",
    "Create 3 finance shorts about money habits",
]

PUBLISHING_PLATFORMS = [
    ("▶️", "YouTube Shorts"),
    ("🎵", "TikTok"),
    ("📸", "Instagram Reels"),
    ("📘", "Facebook Reels"),
    ("🐦", "X (Twitter)"),
    ("🎬", "YouTube Long-form"),
]

PUBLISHING_COMING_SOON = [
    ("🎙️", "AI Voice Generation"),
    ("🎬", "AI Video Creation"),
    ("📤", "Auto Posting"),
]

ANALYTICS_COMING_SOON = [
    ("📊", "Analytics Dashboard"),
    ("🔍", "SEO Optimizer"),
]
