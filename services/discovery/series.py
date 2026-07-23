"""Series detection — build topical authority, not isolated uploads."""

from __future__ import annotations

import re
from collections import defaultdict

from services.discovery.models import SeriesRecommendation
from services.trends.models import Opportunity, Trend

_STOP = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with",
    "about", "explained", "myths", "debunked", "science", "behind", "what",
    "nobody", "tells", "you", "hidden", "history", "future",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def _subject_key(trend: Trend) -> str:
    toks = _tokens(trend.topic) | _tokens(" ".join(trend.keywords[:4]))
    # Prefer category + strongest keyword
    if trend.keywords:
        primary = trend.keywords[0].lower().strip()
        if primary:
            return f"{trend.category.lower()}::{primary}"
    if toks:
        return f"{trend.category.lower()}::{sorted(toks)[0]}"
    return f"{trend.category.lower()}::misc"


def detect_series(
    opportunities: list[Opportunity] | list[tuple[Opportunity, object]],
    *,
    min_episodes: int = 3,
) -> list[SeriesRecommendation]:
    """Cluster related opportunities into multi-part series recommendations."""
    groups: dict[str, list[Opportunity]] = defaultdict(list)
    for item in opportunities:
        opp = item[0] if isinstance(item, tuple) else item
        groups[_subject_key(opp.trend)].append(opp)

    recommendations: list[SeriesRecommendation] = []
    for key, opps in groups.items():
        if len(opps) < min_episodes:
            # Still suggest companion Shorts when 2 strong evergreen topics share a subject
            if len(opps) == 2 and all(o.trend.category.lower() in ("science", "education", "psychology", "history", "space") for o in opps):
                pass
            else:
                continue
        opps_sorted = sorted(opps, key=lambda o: o.opportunity_score, reverse=True)
        topics = [o.trend.topic for o in opps_sorted[:8]]
        category = opps_sorted[0].trend.category
        subject = key.split("::", 1)[-1].replace("_", " ").title()
        formats = ["multi_part_series", "playlist", "companion_shorts"]
        avg_evergreen = sum(o.factors.get("evergreen_potential", 50) for o in opps_sorted) / len(opps_sorted)
        if avg_evergreen >= 75:
            formats.append("long_form_documentary")
        priority = min(100, int(sum(o.opportunity_score for o in opps_sorted[:3]) / min(3, len(opps_sorted))))
        recommendations.append(
            SeriesRecommendation(
                subject_area=category,
                title=f"{subject}: Generational Deep Dive",
                episode_topics=topics,
                formats=formats,
                rationale=(
                    f"{len(topics)} related trending topics in {category} — "
                    "build topical authority with a series + companion Shorts."
                ),
                priority=priority,
            )
        )
    recommendations.sort(key=lambda s: s.priority, reverse=True)
    return recommendations
