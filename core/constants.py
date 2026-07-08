"""Shared constants for Generational."""

APP_VERSION = "1.1.0"

MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
DEFAULT_MODEL = "gpt-4o-mini"

IDEAS_PER_BATCH = 10

NICHE_KEYWORDS = {
    "Psychology": ["psychology", "psychological", "mindset", "mind", "behavior"],
    "AI & Future Tech": ["ai ", " ai", "future tech", "technology", "tech ", "robot", "artificial intelligence"],
    "Dark History": ["dark history", "history", "historical", "war", "ancient"],
    "Space": ["space", "nasa", "universe", "astronomy", "galaxy", "planet"],
    "Finance": ["finance", "money", "invest", "wealth", "budget", "stocks"],
    "Health": ["health", "fitness", "wellness", "nutrition", "diet"],
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
    ("🐦", "X (Twitter)"),
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
