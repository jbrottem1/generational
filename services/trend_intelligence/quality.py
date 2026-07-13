"""Quality control — only trustworthy signals reach scoring and forecasting.

Detects and handles, without ever raising:

- exact duplicates          (same normalized topic — keep the strongest)
- near duplicates           (token-overlap similarity above threshold)
- expired trends            (signal older than the configured max age)
- stale signals             (freshness below the floor)
- spam                      (marker phrases, shouting, junk punctuation)
- low-confidence signals    (below the configured confidence gate)
- conflicting signals       (same topic, wildly divergent growth across
                             sources — kept, flagged, confidence-discounted)

Provider failures are already absorbed upstream by TrendDiscoveryManager;
this module cleans what the providers DID return.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from core.log import get_logger, log_event
from services.trend_intelligence.config import (
    TrendIntelligenceConfig,
    get_trend_intelligence_config,
)
from services.trends.models import Trend

logger = get_logger(__name__)

SPAM_MARKERS = (
    "free money", "click here", "giveaway", "limited offer", "buy now",
    "100% guaranteed", "get rich quick", "dm me", "link in bio",
)

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class QualityReport:
    """What QC kept, what it dropped, and why — JSON-safe."""

    total: int = 0
    kept: int = 0
    dropped: dict = field(default_factory=lambda: {
        "duplicate": 0, "near_duplicate": 0, "expired": 0,
        "stale": 0, "spam": 0, "low_confidence": 0,
    })
    conflicts: list = field(default_factory=list)   # flagged topics (kept, discounted)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "kept": self.kept,
            "dropped": dict(self.dropped),
            "dropped_total": sum(self.dropped.values()),
            "conflicts": list(self.conflicts),
        }


def _normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def _tokens(trend: Trend) -> "set[str]":
    tokens = set(_WORD_RE.findall(trend.topic.lower()))
    for keyword in trend.keywords:
        tokens.update(_WORD_RE.findall(keyword.lower()))
    return tokens


def _similarity(a: "set[str]", b: "set[str]") -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _is_spam(trend: Trend) -> bool:
    text = trend.topic.lower()
    if any(marker in text for marker in SPAM_MARKERS):
        return True
    letters = [c for c in trend.topic if c.isalpha()]
    if len(letters) > 6 and sum(c.isupper() for c in letters) / len(letters) > 0.8:
        return True
    return trend.topic.count("!") >= 3


def _is_expired(trend: Trend, config: TrendIntelligenceConfig) -> bool:
    try:
        seen = datetime.fromisoformat(trend.timestamp)
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return True   # unparseable timestamp = untrustworthy signal
    age_limit = timedelta(hours=config.max_signal_age_hours)
    return datetime.now(timezone.utc) - seen > age_limit


def _flag_conflicts(trends: "list[Trend]", config: TrendIntelligenceConfig, report: QualityReport) -> None:
    """Same topic reported with wildly divergent growth across sources:
    keep the signals but flag the topic and discount every copy's
    confidence — conflicting data is weaker data."""
    by_topic: "dict[str, list[Trend]]" = {}
    for trend in trends:
        by_topic.setdefault(_normalize(trend.topic), []).append(trend)

    for topic, group in by_topic.items():
        if len(group) < 2:
            continue
        growths = [t.growth_pct for t in group]
        spread = max(growths) - min(growths)
        if spread > config.conflict_growth_spread_pct:
            report.conflicts.append({
                "topic": group[0].topic,
                "sources": sorted({t.source for t in group}),
                "growth_spread_pct": round(spread, 1),
            })
            for trend in group:
                trend.confidence = round(trend.confidence * 0.7, 2)


def review_trends(
    trends: "list[Trend]",
    config: "TrendIntelligenceConfig | None" = None,
) -> "tuple[list[Trend], QualityReport]":
    """Filter a raw trend batch down to trustworthy signals.

    Returns (kept_trends, report). Never raises; a malformed trend is
    dropped, not fatal.
    """
    config = config or get_trend_intelligence_config()
    report = QualityReport(total=len(trends))

    gated: "list[Trend]" = []
    for trend in trends:
        if trend.confidence < config.min_confidence:
            report.dropped["low_confidence"] += 1
            continue
        if _is_spam(trend):
            report.dropped["spam"] += 1
            continue
        if _is_expired(trend, config):
            report.dropped["expired"] += 1
            continue
        if trend.freshness < config.min_freshness:
            report.dropped["stale"] += 1
            continue
        gated.append(trend)

    # Conflicts are detected BEFORE deduplication — divergent copies of the
    # same topic are exactly what dedup would otherwise hide.
    _flag_conflicts(gated, config, report)

    kept: "list[Trend]" = []
    seen_topics: "dict[str, int]" = {}   # normalized topic → index into kept
    for trend in gated:
        topic_key = _normalize(trend.topic)
        if topic_key in seen_topics:
            # Exact duplicate — keep whichever copy is more confident.
            index = seen_topics[topic_key]
            if trend.confidence > kept[index].confidence:
                kept[index] = trend
            report.dropped["duplicate"] += 1
            continue

        tokens = _tokens(trend)
        near = next(
            (k for k in kept if _similarity(tokens, _tokens(k)) >= config.near_duplicate_similarity),
            None,
        )
        if near is not None:
            report.dropped["near_duplicate"] += 1
            continue

        seen_topics[topic_key] = len(kept)
        kept.append(trend)

    report.kept = len(kept)
    log_event(
        logger, "trend_intelligence.quality_reviewed",
        total=report.total, kept=report.kept,
        dropped=sum(report.dropped.values()), conflicts=len(report.conflicts),
    )
    return kept, report
