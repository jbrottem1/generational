"""Learning integration — historical performance feeds future rankings.

The Knowledge Base `performance` category is the system's memory of how
published content actually performed (the Analytics & Continuous Learning
Engine — Agent 9 — writes it; this module only reads). Each entry's
content/metadata may carry a `category` (or `niche`) and a normalized
`performance` score (0-1) or a raw `score` (0-100).

`historical_performance_for(category)` distills that history into the 0-1
factor `services/trends/scorer.py` already accepts — so every ranking run
automatically gets better as real performance data accumulates. With no
history yet it returns the neutral 0.5 the scorer defaults to.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.knowledge import CATEGORY, KnowledgeBase, get_knowledge_base

logger = get_logger(__name__)

NEUTRAL_PERFORMANCE = 0.5
_MAX_ENTRIES = 200   # most recent entries considered


def _entry_category(entry: dict) -> str:
    content = entry.get("content")
    metadata = entry.get("metadata") or {}
    if isinstance(content, dict):
        found = content.get("category") or content.get("niche")
        if found:
            return str(found).lower()
    return str(metadata.get("category") or metadata.get("niche") or "").lower()


def _entry_performance(entry: dict) -> "float | None":
    """Normalized 0-1 performance from an entry, if it carries one."""
    content = entry.get("content")
    sources = [content if isinstance(content, dict) else {}, entry.get("metadata") or {}]
    for source in sources:
        for key, scale in (("performance", 1.0), ("score", 100.0)):
            value = source.get(key)
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value) / scale))
    return None


def historical_performance_for(
    category: str,
    knowledge_base: "KnowledgeBase | None" = None,
) -> float:
    """0-1 average historical performance for a trend category.

    Neutral (0.5) when no matching history exists — the ranking behaves
    exactly as before learning data arrives. Never raises.
    """
    kb = knowledge_base or get_knowledge_base()
    category = (category or "").lower()
    try:
        entries = kb.list_entries(CATEGORY.PERFORMANCE, limit=_MAX_ENTRIES)
    except Exception as exc:  # noqa: BLE001 - learning must never break discovery
        log_event(logger, "trend_intelligence.history_read_failed", level=30, error=str(exc))
        return NEUTRAL_PERFORMANCE

    scores = [
        performance
        for entry in entries
        if (performance := _entry_performance(entry)) is not None
        and (not category or _entry_category(entry) in ("", category))
    ]
    if not scores:
        return NEUTRAL_PERFORMANCE
    return round(sum(scores) / len(scores), 3)
