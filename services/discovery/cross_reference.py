"""Cross-provider topic confidence boosting for discovery.

When multiple independent providers discuss the same topic cluster,
raise Trend.confidence so SEO / psychology / production gates get a
stronger multi-source signal.
"""

from __future__ import annotations

import re
from typing import Any

from services.trends.models import Trend

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def _stem(token: str) -> str:
    t = token.lower()
    if len(t) > 4 and t.endswith("ing"):
        return t[:-3]
    if len(t) > 3 and t.endswith("es"):
        return t[:-2]
    if len(t) > 3 and t.endswith("s"):
        return t[:-1]
    return t


def _topic_tokens(trend: Trend) -> frozenset[str]:
    tokens = set(_TOKEN_RE.findall((trend.topic or "").lower()))
    for kw in trend.keywords or []:
        tokens.update(_TOKEN_RE.findall(str(kw).lower()))
    return frozenset(_stem(t) for t in tokens)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


def agreeing_sources_for_topic(topic: str, trends: list[Trend], *, similarity: float = 0.35) -> dict[str, Any]:
    """Summarize which providers discuss a topic (News / Trends / Reddit / Wiki / YT)."""
    tokens = frozenset(_stem(t) for t in _TOKEN_RE.findall((topic or "").lower()))
    sources: list[str] = []
    for trend in trends:
        other = _topic_tokens(trend)
        token_hit = bool(tokens) and (
            _jaccard(tokens, other) >= similarity
            or len(tokens & other) >= 2
            or any(t in (trend.topic or "").lower() for t in list(tokens)[:3])
        )
        if token_hit and trend.source and trend.source not in sources:
            sources.append(trend.source)
    return {
        "topic": topic,
        "sources": sources,
        "agreeing_sources": len(sources),
        "has_google_news": "google_news" in sources,
        "has_youtube": any(s.startswith("youtube") for s in sources),
        "has_reddit": "reddit_trends" in sources,
        "has_wikipedia": "wikipedia_trending" in sources,
        "has_google_trends": "google_trends" in sources,
    }


def boost_multi_source_confidence(
    trends: list[Trend],
    *,
    max_boost: float = 0.18,
    similarity: float = 0.4,
) -> list[Trend]:
    """Increase confidence when ≥2 distinct sources share a topic cluster.

    Mutates and returns the same list for convenience.
    """
    if len(trends) < 2:
        return trends

    token_sets = [_topic_tokens(t) for t in trends]
    boosts = [0.0] * len(trends)

    for i, trend_i in enumerate(trends):
        partners: set[str] = set()
        for j, trend_j in enumerate(trends):
            if i == j:
                continue
            if trend_i.source == trend_j.source:
                continue
            if _jaccard(token_sets[i], token_sets[j]) >= similarity:
                partners.add(trend_j.source)
        if partners:
            boosts[i] = min(max_boost, 0.06 * len(partners) + 0.04)

    for trend, boost in zip(trends, boosts):
        if boost > 0:
            trend.confidence = min(1.0, float(trend.confidence) + boost)
    return trends
