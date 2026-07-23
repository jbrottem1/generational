"""Soft-attach physics profiles and interaction packages onto scenes."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.package import build_scene_physics


def attach_physics_interactions(
    scenes: list[dict[str, Any]],
    *,
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
    location: dict[str, Any] | str | None = None,
) -> list[dict[str, Any]]:
    hosts_by_id = hosts_by_id or {}
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        cid = str(row.get("studio_character_id") or "DOCTOR_001").upper()
        host = hosts_by_id.get(cid)
        if host and host.get("canonical_height_cm"):
            pass  # height resolved inside build_scene_physics via rig
        if not row.get("physics_bundle"):
            row["physics_bundle"] = build_scene_physics(
                character_id=cid,
                scene=row,
                scene_index=i,
                stage_world=row.get("stage_world_package"),
                location=location,
            )
        bundle = row["physics_bundle"]
        row["physics_profile"] = {
            "character_id": cid,
            "scene_ref": bundle.get("scene_ref"),
            "validation": bundle.get("validation"),
            "do_not_float": True,
            "do_not_clip": True,
            "do_not_teleport": True,
        }
        row["interaction_packages"] = bundle.get("interactions") or []
        # Soft constraints for performance engine / true_motion
        tm = dict(row.get("true_motion") or {})
        tm["physics_constrained"] = True
        tm["no_float"] = True
        tm["no_clip"] = True
        tm["no_teleport"] = True
        row["true_motion"] = tm
        # Mirror foot/hand requirements onto CPE-ish fields
        row["physics_constraints"] = {
            "no_float": True,
            "no_clip": True,
            "no_teleport": True,
            "foot_planting": True,
            "hand_must_hit_targets": True,
            "collision_enabled": True,
        }
        out.append(row)
    return out
