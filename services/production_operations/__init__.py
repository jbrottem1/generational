"""Production Operations Layer — Agent 0 AI Studio command center.

    from services.production_operations import run_studio_ops, enqueue_production

INPUT: topic, platform, style, duration, optional constraints
OUTPUT: monitored production + report + history + export package
"""

from __future__ import annotations

from services.production_operations.brief import StudioBrief, build_studio_brief, brief_to_context
from services.production_operations.history import search_history, store_production
from services.production_operations.orchestrator import run_studio_ops
from services.production_operations.queue import (
    enqueue_batch,
    enqueue_production,
    ensure_ops_queue_handler,
    queue_summary,
    recover_failed_jobs,
)
from services.production_operations.report import build_production_report
from services.production_operations.stages import OPERATIONS_STAGES, STAGE_KEYS, SUPPORTED_PLATFORMS, flat_engine_order
from services.production_operations.status import build_live_dashboard, load_ops_status, status_path

__all__ = [
    "OPERATIONS_STAGES",
    "STAGE_KEYS",
    "SUPPORTED_PLATFORMS",
    "StudioBrief",
    "brief_to_context",
    "build_live_dashboard",
    "build_production_report",
    "build_studio_brief",
    "enqueue_batch",
    "enqueue_production",
    "ensure_ops_queue_handler",
    "flat_engine_order",
    "load_ops_status",
    "queue_summary",
    "recover_failed_jobs",
    "run_studio_ops",
    "search_history",
    "status_path",
    "store_production",
]
