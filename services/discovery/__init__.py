"""Discovery Engine package — content opportunity intelligence before production."""

from __future__ import annotations

from services.discovery.breaking_news import gate_for_production, is_breaking_candidate, verify_topic
from services.discovery.models import (
    DiscoveryScore,
    PlatformPackage,
    QueueItem,
    SeriesRecommendation,
    VerificationReport,
)
from services.discovery.platform_meta import build_platform_packages
from services.discovery.queue import load_queue, top_queue, upsert_items
from services.discovery.scoring import rank_discovery_opportunities, score_discovery_opportunity
from services.discovery.script_handoff import brief_to_script_context, queue_item_to_script_context
from services.discovery.series import detect_series


def run_discovery(*args, **kwargs):
    from services.discovery.engine import run_discovery as _run

    return _run(*args, **kwargs)


__all__ = [
    "DiscoveryScore",
    "PlatformPackage",
    "QueueItem",
    "SeriesRecommendation",
    "VerificationReport",
    "build_platform_packages",
    "detect_series",
    "gate_for_production",
    "is_breaking_candidate",
    "load_queue",
    "rank_discovery_opportunities",
    "run_discovery",
    "score_discovery_opportunity",
    "brief_to_script_context",
    "queue_item_to_script_context",
    "top_queue",
    "upsert_items",
    "verify_topic",
]
