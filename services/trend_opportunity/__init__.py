"""Trend & Opportunity Intelligence — decide what Generational produces next."""

from __future__ import annotations

from services.trend_opportunity.brief import (
    build_content_strategy,
    build_production_brief,
    to_studio_brief_kwargs,
)
from services.trend_opportunity.engine import run_trend_opportunity
from services.trend_opportunity.handoff import (
    handoff_pipeline,
    handoff_to_research,
    handoff_to_studio_ops,
    verify_brief_ready,
)
from services.trend_opportunity.learning import predict_performance, record_actual_performance
from services.trend_opportunity.library import DB_PATH, list_opportunities, upsert_opportunity
from services.trend_opportunity.providers import list_provider_interfaces
from services.trend_opportunity.scoring import score_opportunity_card
from services.trend_opportunity.validate import validate_opportunity

__all__ = [
    "DB_PATH",
    "build_content_strategy",
    "build_production_brief",
    "handoff_pipeline",
    "handoff_to_research",
    "handoff_to_studio_ops",
    "list_opportunities",
    "list_provider_interfaces",
    "predict_performance",
    "record_actual_performance",
    "run_trend_opportunity",
    "score_opportunity_card",
    "to_studio_brief_kwargs",
    "upsert_opportunity",
    "validate_opportunity",
    "verify_brief_ready",
]
