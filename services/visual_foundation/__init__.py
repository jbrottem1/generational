"""Generational Visual Foundation V1 — permanent visual constitution (not a renderer)."""

from __future__ import annotations

from services.visual_foundation.gate import review_visual_foundation
from services.visual_foundation.standards import FOUNDATION_VERSION, load_foundation, visual_target

__all__ = [
    "FOUNDATION_VERSION",
    "load_foundation",
    "review_visual_foundation",
    "visual_target",
]
