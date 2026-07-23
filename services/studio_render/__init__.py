"""Studio Render & Motion Graphics Engine (V3.0).

Final visual authority between storyboard and export — master timeline,
motion graphics, transitions, color, VFX, typography, diagrams, B-roll,
camera choreography, export presets, quality ≥98, and Media Library layout.
"""

from __future__ import annotations

from services.studio_render.director import build_studio_render_package
from services.studio_render.export_pipeline import build_export_plan, choose_primary_preset
from services.studio_render.models import (
    EXPORT_PRESETS,
    RENDER_QUALITY_THRESHOLD,
    TRANSITIONS_V3,
    StudioRenderPackage,
)
from services.studio_render.quality import analyze_render_quality
from services.studio_render.transitions import choose_transition

__all__ = [
    "EXPORT_PRESETS",
    "RENDER_QUALITY_THRESHOLD",
    "TRANSITIONS_V3",
    "StudioRenderPackage",
    "analyze_render_quality",
    "build_export_plan",
    "build_studio_render_package",
    "choose_primary_preset",
    "choose_transition",
]
