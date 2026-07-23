"""Creative Performance Lab — evidence feedback loop over existing systems.

Extends Optimization Lab, Publishing Intelligence, analytics, Voice Studio,
and human review. Does not add engines or auto-publish.
"""

from __future__ import annotations

from services.creative_performance_lab.dashboard import build_creative_performance_board
from services.creative_performance_lab.evaluation import (
    attach_published_video,
    evaluate_experiment,
    refresh_analytics,
)
from services.creative_performance_lab.experiment import create_experiment
from services.creative_performance_lab.guidance import guidance_for_production
from services.creative_performance_lab.human_review import record_human_review
from services.creative_performance_lab.knowledge import promote_experiment_learning, search_learnings
from services.creative_performance_lab.lab import get_experiment, run_controlled_experiment

__all__ = [
    "attach_published_video",
    "build_creative_performance_board",
    "create_experiment",
    "evaluate_experiment",
    "get_experiment",
    "guidance_for_production",
    "promote_experiment_learning",
    "record_human_review",
    "refresh_analytics",
    "run_controlled_experiment",
    "search_learnings",
]
