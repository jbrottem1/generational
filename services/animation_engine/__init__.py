"""Animation Engine — cinematic enhancement layer (V2)."""

from __future__ import annotations

from services.animation_engine.package import attach_animation_package, build_animation_package
from services.animation_engine.score import animation_excellence, quality_gate

__all__ = [
    "attach_animation_package",
    "build_animation_package",
    "animation_excellence",
    "quality_gate",
]
