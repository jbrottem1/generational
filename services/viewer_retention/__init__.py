"""Viewer Retention & Cinematic Excellence Engine (V2.0).

Unifies hook selection, visual pacing, cinematic camera, narration craft,
sound design, captions, visual ranking, retention simulation, production
polish, and quality reporting — then auto-improves until overall ≥ 98.
"""

from __future__ import annotations

from services.viewer_retention.camera import build_camera_plan, choose_cinematic_motion
from services.viewer_retention.excellence import build_excellence_package
from services.viewer_retention.hooks import generate_hook_candidates_v2, select_best_hook
from services.viewer_retention.models import (
    CINEMATIC_MOTIONS_V2,
    EXCELLENCE_PASS_THRESHOLD,
    ExcellenceReport,
)
from services.viewer_retention.pacing import build_pacing_plan
from services.viewer_retention.quality_report import build_quality_report
from services.viewer_retention.retention import simulate_retention

__all__ = [
    "CINEMATIC_MOTIONS_V2",
    "EXCELLENCE_PASS_THRESHOLD",
    "ExcellenceReport",
    "build_camera_plan",
    "build_excellence_package",
    "build_pacing_plan",
    "build_quality_report",
    "choose_cinematic_motion",
    "generate_hook_candidates_v2",
    "select_best_hook",
    "simulate_retention",
]
