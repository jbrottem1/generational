"""Discovery Engine — continuous educational content opportunity ranking.

Stage runs before research/script. Outputs a real-time production queue,
series recommendations, and deferred breaking-news items.
"""

from __future__ import annotations

from core import parsing
from core.log import get_logger, log_event
from engines.base import Engine

logger = get_logger(__name__)

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


class DiscoveryEngine(Engine):
    key = "discovery"
    label = "Trend Intelligence & Discovery"
    icon = "🧭"
    description = "Discover, verify, score, and queue educational content opportunities."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        from services.discovery.engine import run_discovery

        command = context.get("command", "") or context.get("subject", "")
        niche = parsing.detect_niche(command) if command else "Science"
        subject = (
            parsing.detect_subject(command, fallback=niche.lower())
            if command
            else "science education"
        )
        category = NICHE_CATEGORIES.get(niche, context.get("trend_category") or "science")
        persist = bool(context.get("persist_discovery_queue", True))

        result = run_discovery(
            subject=subject,
            category=category,
            country=str(context.get("country") or "US"),
            language=str(context.get("language") or "en"),
            limit_per_provider=int(context.get("limit_per_provider") or 2),
            top_n=int(context.get("discovery_top_n") or 25),
            persist=persist,
        )
        log_event(
            logger,
            "discovery_engine.completed",
            subject=subject,
            ready=result.get("ready"),
            deferred=result.get("deferred_count"),
        )
        return {
            "discovery": result,
            "discovery_queue": result.get("queue") or [],
            "discovery_series": result.get("series") or [],
            "discovery_top": result.get("top"),
            "discovery_script_handoff": result.get("script_handoff"),
            "youtube_search_intelligence": result.get("youtube_search_intelligence"),
            "audience_intelligence": result.get("audience_intelligence"),
            "human_attention_score": result.get("human_attention_score"),
            "trend_subject": subject,
            "trend_category": category,
        }
