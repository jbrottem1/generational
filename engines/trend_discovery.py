"""Trend Discovery engine — stage 0 of the intelligence pipeline.

The front door of the operating system: before any research or content
generation, it queries every registered trend provider and normalizes the
signals into the universal Trend model. Downstream stages consume only
that model.
"""

from __future__ import annotations

from core import parsing
from core.log import get_logger, log_event
from engines.base import Engine
from services.trends.manager import get_trend_manager

logger = get_logger(__name__)

# Map research niches onto trend categories used by the opportunity scorer.
NICHE_CATEGORIES = {
    "Psychology": "psychology",
    "AI & Future Tech": "technology",
    "Dark History": "history",
    "Space": "space",
    "Finance": "finance",
    "Health": "health",
    "Science": "science",
    "General Content": "general",
}


class TrendDiscoveryEngine(Engine):
    key = "trend_discovery"
    label = "Trend Discovery"
    icon = "📡"
    description = "Discover trending opportunities across all trend providers."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        command = context.get("command", "")
        niche = parsing.detect_niche(command)
        subject = parsing.detect_subject(command, fallback=niche.lower())
        category = NICHE_CATEGORIES.get(niche, "general")

        manager = get_trend_manager()
        trends = manager.discover(subject, category=category)

        log_event(
            logger,
            "trend_discovery.completed",
            subject=subject,
            category=category,
            trends=len(trends),
        )
        return {
            "trends": [trend.to_dict() for trend in trends],
            "trend_category": category,
            "trend_subject": subject,
        }
