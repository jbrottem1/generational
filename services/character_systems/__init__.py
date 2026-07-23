"""Character Systems — identity consistency, libraries, production validation."""

from __future__ import annotations

from services.character_systems.validation import (
    FORBIDDEN_PROFESSOR_GESTURES,
    PROFESSOR_CHARACTER_ID,
    PROFESSOR_LOCKED_PALETTE,
    ConsistencyError,
    load_character,
    load_character_systems_registry,
    validate_attire,
    validate_gesture_for_character,
    validate_production_character,
    validate_proportions,
    validate_palette,
)

__all__ = [
    "FORBIDDEN_PROFESSOR_GESTURES",
    "PROFESSOR_CHARACTER_ID",
    "PROFESSOR_LOCKED_PALETTE",
    "ConsistencyError",
    "load_character",
    "load_character_systems_registry",
    "validate_attire",
    "validate_gesture_for_character",
    "validate_production_character",
    "validate_proportions",
    "validate_palette",
]
