"""Breaking News Mode — verify before any production.

Rules:
- Require multiple independent reputable source classes
- Separate confirmed facts from developing claims
- Flag rumor language
- Defer production when confidence is below threshold

Never ship educational explainers on unverified rumors.
"""

from __future__ import annotations

import re
from typing import Any

from services.discovery.models import VerificationReport
from services.trends.models import Trend

MIN_VERIFIED_CONFIDENCE = 0.72
MIN_INDEPENDENT_SOURCES = 2

REPUTABLE_SOURCE_CLASSES = {
    "news_api": "news",
    "rss_feeds": "news",
    "google_news": "news",
    "google_trends": "search",
    "youtube_trending": "video",
    "youtube_search_trends": "video",
    "youtube_data_api": "video",
    "reddit_trends": "social",
    "wikipedia_trending": "reference",
    "academic_publications": "science",
    "scientific_publications": "science",
    "industry_publications": "industry",
}

RUMOR_PATTERNS = re.compile(
    r"\b(rumor|rumour|allegedly|unconfirmed|sources say|leaked|supposedly|"
    r"might be|could be fake|conspiracy|going viral that)\b",
    re.I,
)

BREAKING_CUES = re.compile(
    r"\b(breaking|just in|urgent|developing|live updates|happening now|"
    r"announced today|newly discovered)\b",
    re.I,
)


def is_breaking_candidate(trend: Trend) -> bool:
    blob = f"{trend.topic} {' '.join(trend.keywords)}"
    if BREAKING_CUES.search(blob):
        return True
    if trend.category.lower() == "news" and trend.freshness >= 0.7 and trend.velocity >= 0.55:
        return True
    if trend.freshness >= 0.85 and trend.growth_pct >= 120:
        return True
    return False


def _source_class(source: str) -> str:
    return REPUTABLE_SOURCE_CLASSES.get(source, "other")


def verify_topic(
    topic: str,
    *,
    related_trends: list[Trend] | None = None,
    external_sources: list[dict[str, Any]] | None = None,
    min_confidence: float = MIN_VERIFIED_CONFIDENCE,
) -> VerificationReport:
    """Multi-source verification gate for a candidate topic."""
    related = list(related_trends or [])
    external = list(external_sources or [])
    rumor_flags: list[str] = []
    confirmed: list[str] = []
    developing: list[str] = []

    blob = topic
    for trend in related:
        blob += f" {trend.topic}"
    if RUMOR_PATTERNS.search(blob):
        rumor_flags.append("rumor_language_detected")

    # Aggregate independent source classes from related trends + externals
    classes: set[str] = set()
    sources_out: list[dict[str, Any]] = []
    for trend in related:
        cls = _source_class(trend.source)
        if cls != "other":
            classes.add(cls)
        sources_out.append(
            {
                "source": trend.source,
                "class": cls,
                "platform": trend.platform,
                "confidence": trend.confidence,
                "topic": trend.topic,
            }
        )
        if trend.confidence >= 0.7 and cls in ("news", "science", "reference", "search"):
            confirmed.append(f"{trend.source}: {trend.topic}")
        elif trend.confidence >= 0.45:
            developing.append(f"{trend.source}: {trend.topic}")

    for item in external:
        src = str(item.get("source") or item.get("name") or "external")
        cls = str(item.get("class") or _source_class(src))
        if cls != "other":
            classes.add(cls)
        sources_out.append({"source": src, "class": cls, **{k: v for k, v in item.items() if k not in ("source", "class")}})
        status = str(item.get("status") or "developing")
        claim = str(item.get("claim") or item.get("summary") or src)
        if status == "confirmed":
            confirmed.append(claim)
        else:
            developing.append(claim)
        if item.get("rumor"):
            rumor_flags.append(str(item.get("rumor")))

    # Confidence model
    class_bonus = min(0.35, 0.12 * len(classes))
    confirm_bonus = min(0.25, 0.08 * len(confirmed))
    avg_trend_conf = (
        sum(t.confidence for t in related) / len(related) if related else 0.4
    )
    confidence = min(0.98, 0.35 * avg_trend_conf + class_bonus + confirm_bonus)
    if rumor_flags:
        confidence *= 0.55
    if len(classes) < MIN_INDEPENDENT_SOURCES:
        confidence *= 0.7

    if rumor_flags and len(confirmed) < 2:
        return VerificationReport(
            status="rejected",
            confidence=round(confidence, 3),
            confirmed_facts=confirmed,
            developing_claims=developing,
            rumor_flags=rumor_flags,
            sources=sources_out,
            defer_reason="Unverified rumor language without sufficient confirmed sources.",
        )

    if confidence < min_confidence or len(classes) < MIN_INDEPENDENT_SOURCES:
        return VerificationReport(
            status="deferred",
            confidence=round(confidence, 3),
            confirmed_facts=confirmed,
            developing_claims=developing,
            rumor_flags=rumor_flags,
            sources=sources_out,
            defer_reason=(
                f"Need ≥{MIN_INDEPENDENT_SOURCES} independent reputable source classes "
                f"and confidence ≥{min_confidence:.2f} before production."
            ),
        )

    if developing and not confirmed:
        return VerificationReport(
            status="developing",
            confidence=round(confidence, 3),
            confirmed_facts=confirmed,
            developing_claims=developing,
            rumor_flags=rumor_flags,
            sources=sources_out,
            defer_reason="Story still developing — wait for confirmed facts.",
        )

    return VerificationReport(
        status="verified",
        confidence=round(min(0.98, confidence + 0.05), 3),
        confirmed_facts=confirmed or [f"Corroborated across {len(classes)} source classes"],
        developing_claims=developing,
        rumor_flags=rumor_flags,
        sources=sources_out,
    )


def gate_for_production(trend: Trend, related: list[Trend] | None = None) -> VerificationReport:
    """Convenience: breaking candidates must verify; evergreen educational topics auto-pass lightly."""
    peers = list(related or [])
    if trend not in peers:
        peers = [trend] + peers
    if is_breaking_candidate(trend):
        return verify_topic(trend.topic, related_trends=peers)
    # Non-breaking educational topics: soft verification from signal confidence
    if trend.confidence >= 0.55 and trend.category.lower() not in ("news", "entertainment"):
        return VerificationReport(
            status="verified",
            confidence=round(min(0.95, 0.7 + 0.25 * trend.confidence), 3),
            confirmed_facts=[f"Educational topic with provider confidence {trend.confidence:.2f}"],
            sources=[{"source": trend.source, "class": _source_class(trend.source), "topic": trend.topic}],
        )
    return verify_topic(trend.topic, related_trends=peers)
