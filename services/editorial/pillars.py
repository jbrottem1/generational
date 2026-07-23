"""Content pillars for motivational productions."""

from __future__ import annotations

MOTIVATION_NICHE = "Motivation"

# Ordered pillar catalog — used for channel config, ideation bias, and SEO.
CONTENT_PILLARS = (
    "discipline",
    "consistency",
    "delayed_gratification",
    "leadership",
    "purpose",
    "personal_responsibility",
    "confidence",
    "resilience",
    "mental_toughness",
    "self_respect",
    "sacrifice",
    "character",
    "integrity",
    "excellence",
    "long_term_thinking",
    "overcoming_adversity",
    "failure_as_education",
    "building_habits",
    "productivity",
    "courage",
    "service",
    "legacy",
)

DEFAULT_MOTIVATION_PILLARS = (
    "discipline",
    "resilience",
    "personal_responsibility",
    "mental_toughness",
    "building_habits",
    "courage",
)

PILLAR_KEYWORDS = {
    "discipline": ["discipline", "disciplined", "self-control", "routine"],
    "consistency": ["consistency", "consistent", "every day", "showing up"],
    "delayed_gratification": ["delayed gratification", "patience", "long game"],
    "leadership": ["leadership", "leader", "lead others"],
    "purpose": ["purpose", "meaning", "meaningful life", "why you"],
    "personal_responsibility": ["responsibility", "accountable", "own it", "no excuses"],
    "confidence": ["confidence", "self-belief", "believe in yourself"],
    "resilience": ["resilience", "resilient", "bounce back", "get back up"],
    "mental_toughness": ["mental toughness", "mentally strong", "tough mind"],
    "self_respect": ["self-respect", "self respect", "standards"],
    "sacrifice": ["sacrifice", "give up", "trade-offs"],
    "character": ["character", "who you become"],
    "integrity": ["integrity", "honest", "do the right thing"],
    "excellence": ["excellence", "mastery", "craft"],
    "long_term_thinking": ["long-term", "long term", "compound", "years from now"],
    "overcoming_adversity": ["adversity", "hardship", "struggle", "setback"],
    "failure_as_education": ["failure", "fail", "lesson from"],
    "building_habits": ["habit", "habits", "daily practice"],
    "productivity": ["productivity", "focus", "deep work"],
    "courage": ["courage", "brave", "fear", "act anyway"],
    "service": ["service", "serve others", "contribute"],
    "legacy": ["legacy", "what you leave", "remembered for"],
}


def is_motivational_niche(niche: str) -> bool:
    """True when the niche is Motivation or a close synonym."""
    normalized = (niche or "").strip().lower()
    return normalized in {"motivation", "motivational", "self-improvement", "self improvement"}


def pillar_keywords(pillars: "list[str] | tuple[str, ...] | None" = None) -> list[str]:
    """Flatten keyword lists for the selected pillars (or all pillars)."""
    selected = pillars or CONTENT_PILLARS
    words: list[str] = []
    for pillar in selected:
        words.extend(PILLAR_KEYWORDS.get(pillar, [pillar.replace("_", " ")]))
    return words
