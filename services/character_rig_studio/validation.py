"""Quality gates — reject incomplete or non-reusable actors."""

from __future__ import annotations

from typing import Any

from services.character_rig_studio.models import (
    BODY_CAPABILITIES,
    EYE_CAPABILITIES,
    FACIAL_EMOTIONS,
    HAND_CAPABILITIES,
    PERFORMANCE_CLIPS,
    REJECT_REASONS,
    SKELETON_HIERARCHY,
)


def validate_character_rig(package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_character_rig_package"],
            "rejects": list(REJECT_REASONS),
        }

    failures: list[str] = []
    rejects: list[str] = []

    identity = package.get("identity") or {}
    for field in (
        "character_id",
        "canonical_name",
        "role",
        "age_appearance",
        "body_type",
        "height_cm",
        "proportions",
        "continuity_version",
    ):
        if identity.get(field) in (None, ""):
            failures.append(f"identity_missing_{field}")
            rejects.append("appearance_changes_between_scenes")

    if not identity.get("forbid_regenerate_per_scene"):
        failures.append("identity_allows_regeneration")
        rejects.append("appearance_changes_between_scenes")

    body = package.get("body_rig") or {}
    hierarchy = list(body.get("hierarchy") or [])
    required_joints = {"head", "neck", "pelvis", "spine_01", "hand_left", "hand_right", "foot_left", "foot_right"}
    if not required_joints.issubset(set(hierarchy)):
        failures.append("skeleton_incomplete")
        rejects.append("inconsistent_proportions")
    if len(hierarchy) < len(SKELETON_HIERARCHY) * 0.7:
        failures.append("skeleton_hierarchy_too_small")
    caps = set(body.get("capabilities") or [])
    if not set(BODY_CAPABILITIES).issubset(caps):
        failures.append("body_capabilities_incomplete")
        rejects.append("cannot_perform_natural_walking")

    face = package.get("facial_rig") or {}
    if not face.get("controls") and not face.get("regions_supported"):
        failures.append("facial_rig_missing")
        rejects.append("cannot_perform_expressive_facial_acting")
    emotions = set(face.get("emotions_supported") or [])
    if not set(FACIAL_EMOTIONS).issubset(emotions):
        failures.append("facial_emotions_incomplete")
        rejects.append("cannot_perform_expressive_facial_acting")

    eyes = package.get("eye_system") or {}
    if not set(EYE_CAPABILITIES).issubset(set(eyes.get("capabilities") or [])):
        failures.append("eye_system_incomplete")
        rejects.append("cannot_maintain_eye_contact")

    hands = package.get("hand_system") or {}
    if not set(HAND_CAPABILITIES).issubset(set(hands.get("capabilities") or [])):
        failures.append("hand_system_incomplete")
        rejects.append("cannot_interact_with_objects")

    perf = package.get("performance_system") or {}
    clips = set((perf.get("clips") or {}).keys()) or set(perf.get("required_clips") or [])
    if not set(PERFORMANCE_CLIPS).issubset(clips):
        failures.append("animation_library_incomplete")
        rejects.append("cannot_support_reusable_animation_clips")

    wardrobe = package.get("wardrobe") or {}
    if not wardrobe.get("outfits") or not wardrobe.get("architecture"):
        failures.append("wardrobe_missing")
    if wardrobe.get("architecture") != "clothing_separated_from_body":
        failures.append("wardrobe_not_separated_from_body")

    mechanics = package.get("body_mechanics") or {}
    if not mechanics.get("ground_contact_required") or not mechanics.get("foot_ik"):
        failures.append("body_mechanics_weak")
        rejects.append("cannot_perform_natural_walking")

    materials = package.get("materials") or {}
    if not materials:
        failures.append("materials_missing")

    personality = package.get("personality") or {}
    if not personality.get("traits"):
        failures.append("personality_missing")

    score = max(0, 100 - 8 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "reject_catalog": list(REJECT_REASONS),
        "rule": "Scenes reference the actor. Scenes never recreate the actor.",
        "success": (
            "Permanent cast of digital actors with reusable rigs, animations, "
            "personalities, and performances."
        ),
    }
