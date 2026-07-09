"""Evergreen engine — which opportunities keep earning for months or years?

Assigns every opportunity ONE content nature:

    trending | seasonal | evergreen | educational | news | reference

building on the discovery-layer classifier (Agent 11's
`services/trend_intelligence/classifier.py`) and refining its
evergreen/topical buckets into the strategy-level six-way split the
roadmap and queues consume.
"""

from __future__ import annotations

from services.trend_intelligence.classifier import classify_opportunity
from services.trends.models import Opportunity

# Topic markers for the strategy-level natures.
EDUCATIONAL_MARKERS = (
    "how to", "explained", "guide", "tutorial", "learn", "beginner",
    "course", "lesson", "science behind", "why does", "what is",
)
REFERENCE_MARKERS = (
    "list of", "top 10", "top ten", "comparison", "vs ", "cheat sheet",
    "glossary", "timeline of", "facts about", "history of",
)
NEWS_MARKERS = (
    "breaking", "announced", "launch", "release", "update", "just happened",
    "report", "leak",
)


def _blob(trend) -> str:
    return " ".join([trend.topic.lower(), *[k.lower() for k in trend.keywords]])


def content_nature(opportunity: Opportunity, classification: "dict | None" = None) -> str:
    """The single strategy-level nature of one opportunity."""
    trend = opportunity.trend
    classification = classification or classify_opportunity(opportunity)
    blob = _blob(trend)

    if trend.category.lower() == "news" or any(m in blob for m in NEWS_MARKERS):
        return "news"
    if classification.get("content_type") == "seasonal":
        return "seasonal"
    if any(m in blob for m in REFERENCE_MARKERS):
        return "reference"
    if any(m in blob for m in EDUCATIONAL_MARKERS) or trend.category.lower() == "education":
        return "educational"
    if classification.get("content_type") == "evergreen":
        return "evergreen"
    return "trending"


# Natures that keep earning long after publication — the evergreen queue.
LONG_LIVED_NATURES = ("evergreen", "educational", "reference")


def is_long_lived(nature: str) -> bool:
    return nature in LONG_LIVED_NATURES


def split_by_nature(opportunities: "list[dict]") -> "dict[str, list[dict]]":
    """Group enriched opportunity dicts by their content nature."""
    groups: "dict[str, list[dict]]" = {}
    for opportunity in opportunities:
        groups.setdefault(opportunity.get("content_nature", "trending"), []).append(opportunity)
    return groups
