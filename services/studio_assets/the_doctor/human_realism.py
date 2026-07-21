"""The Doctor — gold-standard Human Realism reference (inherits shared framework)."""

from __future__ import annotations

from typing import Any

from services.human_realism import materialize_character, resolve_character
from services.studio_assets.the_doctor.profile import ASSET_ID

REQUIRED_REALISM_FILES = [
    "CHARACTER_IDENTITY.json",
    "SKELETON_PROFILE.json",
    "MUSCLE_PROFILE.json",
    "FACE_RIG_PROFILE.json",
    "GAIT_PROFILE.json",
    "GESTURE_LIBRARY.json",
    "EMOTION_LIBRARY.json",
    "HAIR_PROFILE.json",
    "WARDROBE_PROFILE.json",
    "CHARACTER_CONTINUITY_RULES.md",
    "HUMAN_REALISM_INDEX.json",
]


def write_human_realism_package(asset_root: Any, write_json, write_md) -> dict[str, bool]:
    """Materialize Doctor Human Realism profiles (legacy CHAR-0001 path + alias)."""
    del write_json, write_md  # materialize writes directly
    # Canonical gold standard is DOCTOR_001; legacy package keeps alias profiles.
    materialize_character("DOCTOR_001", also_to=None)
    materialize_character(ASSET_ID, also_to=asset_root)
    # Shared performance plan schema copy for local asset consumers
    from services.human_realism.base import base_framework
    import json
    from pathlib import Path

    root = Path(asset_root)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "generational://CHAR-0001/PERFORMANCE_PLAN.schema.json",
        "title": "PerformancePlan",
        "required": base_framework()["performance_plan_required_fields"],
    }
    (root / "PERFORMANCE_PLAN.schema.json").write_text(
        json.dumps(schema, indent=2) + "\n", encoding="utf-8"
    )
    (root / "HUMAN_REALISM" / "PERFORMANCE_PLAN.schema.json").write_text(
        json.dumps(schema, indent=2) + "\n", encoding="utf-8"
    )
    return {name: (root / name).exists() for name in REQUIRED_REALISM_FILES}


def doctor_resolved() -> dict[str, Any]:
    return resolve_character(ASSET_ID)
