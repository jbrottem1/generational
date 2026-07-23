"""Environment Construction System — structured world data for existing render/world layers.

Architecture frozen. Not a renderer. Packages are contracts; MP4 inspection is the quality gate.
"""

from __future__ import annotations

from services.environment_department.definition import GMRI_LAB_A, resolve_environment
from services.environment_department.package import build_environment_package
from services.environment_department.validation import (
    rendered_environment_inspection_template,
    validate_environment_package,
)
from services.environment_department.world_systems import atmospheric_falloff, weather_state

__all__ = [
    "GMRI_LAB_A",
    "atmospheric_falloff",
    "build_environment_package",
    "rendered_environment_inspection_template",
    "resolve_environment",
    "validate_environment_package",
    "weather_state",
]
