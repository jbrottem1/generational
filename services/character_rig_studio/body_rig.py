"""Reusable body skeleton + body mechanics contracts."""

from __future__ import annotations

from typing import Any

from services.character_rig_studio.models import (
    BODY_CAPABILITIES,
    MECHANICS_ENSURE,
    MECHANICS_FORBID,
    SKELETON_HIERARCHY,
)


def build_body_rig(
    character_id: str,
    *,
    height_cm: float = 175,
    body_type: str = "adult",
    existing_skeleton: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = str(character_id).upper()
    scale = float(height_cm) / 175.0
    if "child" in body_type.lower() or height_cm < 150:
        scale = float(height_cm) / 132.0 * 0.75

    hierarchy = list(SKELETON_HIERARCHY)
    # Merge any known joints from existing DOCTOR skeleton without dropping fingers
    if existing_skeleton and isinstance(existing_skeleton.get("hierarchy"), list):
        for joint in existing_skeleton["hierarchy"]:
            if joint not in hierarchy:
                hierarchy.append(str(joint))

    return {
        "character_id": cid,
        "rig_type": "generational_body_rig_v1",
        "hierarchy": hierarchy,
        "joint_count": len(hierarchy),
        "scale": round(scale, 4),
        "height_cm": height_cm,
        "capabilities": list(BODY_CAPABILITIES),
        "rules": list((existing_skeleton or {}).get("rules") or [])
        or [
            "movement_originates_from_skeleton",
            "weight_through_pelvis",
            "head_stabilizes_via_spine",
            "hands_never_float",
            "feet_contact_ground",
            "no_limb_length_drift",
        ],
        "joint_constraints_defaults": list(
            (existing_skeleton or {}).get("joint_constraints_defaults") or []
        ),
        "existing_skeleton_ref": "SKELETON_PROFILE.json" if existing_skeleton else None,
        "reusable": True,
        "regenerate_per_scene": False,
    }


def build_body_mechanics(character_id: str) -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "forbid": list(MECHANICS_FORBID),
        "ensure": list(MECHANICS_ENSURE),
        "foot_ik": True,
        "ground_contact_required": True,
        "hip_leads_turns": True,
        "secondary_motion": ["coat_sway", "hair_follow", "soft_tissue_micro"],
        "balance_solver": "pelvis_com_projection",
        "no_pose_teleport": True,
    }
