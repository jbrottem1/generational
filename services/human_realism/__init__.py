"""Human Realism Framework — permanent character performance standard.

Every Generational character inherits BASE_HUMAN_REALISM.
The Doctor (CHAR-0001) is the gold-standard reference implementation.
Architecture frozen: schemas + soft PerformancePlan bindings, not a new renderer.
"""

from __future__ import annotations

from services.human_realism.base import (
    FRAMEWORK_ID,
    FRAMEWORK_VERSION,
    GOLD_STANDARD_CHARACTER_ID,
    base_framework,
)
from services.human_realism.characters import list_character_ids
from services.human_realism.materialize import materialize_character, materialize_framework
from services.human_realism.performance import attach_performance_plans, build_performance_plan
from services.human_realism.resolve import resolve_character
from services.human_realism.validate import validate_performance_plan, validate_scene_bindings

__all__ = [
    "FRAMEWORK_ID",
    "FRAMEWORK_VERSION",
    "GOLD_STANDARD_CHARACTER_ID",
    "attach_performance_plans",
    "base_framework",
    "build_performance_plan",
    "list_character_ids",
    "materialize_character",
    "materialize_framework",
    "resolve_character",
    "validate_performance_plan",
    "validate_scene_bindings",
]
