"""Production Asset Studio models — renderer-neutral asset contracts."""

from __future__ import annotations

from typing import Any

ENGINE_ID = "production_asset_studio"
PACKAGE_TYPE = "PRODUCTION_ASSET_PACKAGE"
PACKAGE_VERSION = "2.0.0"
PHASE = "II"

# Frozen runtime consumption contract — do not rename without updating AnimationRuntime paths.
RUNTIME_CONTRACT = {
    "character_blend": "DOCTOR_001_SKINNED.blend",
    "world_blend": "GENERATIONAL_MEDICAL_LAB.blend",
    "prop_blend": "SAMPLE_CONTAINER_001.blend",
    "rig_map": "RIG_BONE_MAP.json",
    "asset_origin": "ASSET_ORIGIN.json",
}

REJECTION_RULES = [
    "breaks_runtime",
    "breaks_rig",
    "breaks_animation_compatibility",
    "requires_new_architecture",
    "reduces_performance_unacceptably",
    "replaces_skeletal_with_image_animation",
]

DEPARTMENT_IDS = [
    "character_studio",
    "environment_studio",
    "prop_studio",
    "material_studio",
    "lighting_studio",
    "facial_performance_studio",
    "animation_library",
    "visual_storytelling",
]


def empty_validation() -> dict[str, Any]:
    return {
        "ok": True,
        "rejected": False,
        "rejection_reasons": [],
        "warnings": [],
        "runtime_compatible": True,
        "rig_compatible": True,
        "skeletal_animation_preserved": True,
    }
