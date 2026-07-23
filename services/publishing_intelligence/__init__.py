"""Continuous Learning & Publishing Intelligence V2.0

Thin orchestration over frozen architecture — no new engines.

Phases:
  1. Publishing Pipeline
  2. Analytics Collection
  3. Prediction Calibration
  4. Creative Learning
  5. Continuous Improvement
  6. Executive Dashboard
  7. Business Intelligence
"""

from __future__ import annotations

from services.publishing_intelligence.business_intel import estimate_business_metrics
from services.publishing_intelligence.calibration import build_calibration_report, recalibrate_priors
from services.publishing_intelligence.creative_library import (
    recommend_creative_patterns,
    update_creative_library,
)
from services.publishing_intelligence.dashboard import build_studio_intelligence_dashboard
from services.publishing_intelligence.improvement import recommend_highest_impact_improvement
from services.publishing_intelligence.pipeline import build_complete_publish_packages
from services.publishing_intelligence.system import run_intelligence_cycle

__all__ = [
    "build_calibration_report",
    "build_complete_publish_packages",
    "build_studio_intelligence_dashboard",
    "estimate_business_metrics",
    "recalibrate_priors",
    "recommend_creative_patterns",
    "recommend_highest_impact_improvement",
    "run_intelligence_cycle",
    "update_creative_library",
]
