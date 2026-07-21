"""Build INTERACTION_PACKAGE — one believable physical interaction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from services.physics_interaction.models import (
    ENGINE_ID,
    PACKAGE_TYPE,
    PACKAGE_VERSION,
    PHYSICS_STATES,
    SUPPORTED_INTERACTIONS,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_CONTACT: dict[str, list[str]] = {
    "walking": ["foot_left", "foot_right"],
    "running": ["foot_left", "foot_right"],
    "stopping": ["foot_left", "foot_right"],
    "turning": ["foot_plant", "pelvis"],
    "jumping": ["feet", "pelvis"],
    "sitting": ["pelvis", "thighs", "feet"],
    "standing": ["feet", "pelvis"],
    "leaning": ["hand_or_hip", "feet"],
    "opening_doors": ["hand_right", "door_handle"],
    "closing_doors": ["hand_right", "door_handle"],
    "picking_up_objects": ["hand_right", "object_grasp"],
    "putting_objects_down": ["hand_right", "object_release", "surface"],
    "holding_objects": ["hand_right", "object_grip"],
    "writing": ["hand_right", "pen", "surface"],
    "typing": ["fingers_both", "keys"],
    "pointing": ["index_right", "target_ray"],
    "pressing_buttons": ["index_right", "button"],
    "touching_screens": ["index_right", "screen_surface"],
    "handshakes": ["hand_right", "other_hand"],
    "hugging": ["torso", "arms_both"],
    "medical_examinations": ["hands_both", "patient_zone"],
    "using_microscopes": ["hands_both", "eyepiece", "focus_knob"],
    "using_tools": ["hand_right", "tool_grip"],
    "reading_books": ["hands_both", "book"],
    "turning_pages": ["thumb_index", "page_edge"],
    "looking_through_windows": ["eyes", "window_plane"],
}

_ANIM: dict[str, list[str]] = {
    "walking": ["walk_cycle", "foot_plant", "arm_swing"],
    "running": ["run_cycle", "foot_plant"],
    "stopping": ["decelerate", "plant"],
    "turning": ["hip_rotate", "foot_pivot"],
    "jumping": ["crouch", "launch", "land"],
    "sitting": ["approach", "lower", "settle"],
    "standing": ["rise", "balance"],
    "leaning": ["shift_weight", "contact"],
    "opening_doors": ["reach", "grasp_handle", "pull_or_push", "release"],
    "closing_doors": ["reach", "grasp_handle", "close", "release"],
    "picking_up_objects": ["reach", "grasp", "lift"],
    "putting_objects_down": ["lower", "release", "retract"],
    "holding_objects": ["grip_maintain", "arm_stabilize"],
    "writing": ["grip_pen", "stroke"],
    "typing": ["home_row", "key_strikes"],
    "pointing": ["raise_arm", "extend_index", "hold"],
    "pressing_buttons": ["aim", "press", "release"],
    "touching_screens": ["aim", "touch", "retract"],
    "handshakes": ["extend", "grasp", "shake", "release"],
    "hugging": ["approach", "encircle", "release"],
    "medical_examinations": ["approach", "gentle_contact", "observe"],
    "using_microscopes": ["approach", "adjust", "look", "focus"],
    "using_tools": ["grasp", "align", "operate"],
    "reading_books": ["hold_open", "eye_track"],
    "turning_pages": ["pinch", "flip", "smooth"],
    "looking_through_windows": ["approach", "gaze_through"],
}


def normalize_interaction_type(raw: str) -> str:
    t = str(raw or "").lower().strip().replace(" ", "_").replace("-", "_")
    aliases = {
        "walk": "walking",
        "run": "running",
        "stop": "stopping",
        "turn": "turning",
        "jump": "jumping",
        "sit": "sitting",
        "stand": "standing",
        "lean": "leaning",
        "open_door": "opening_doors",
        "close_door": "closing_doors",
        "pick_up": "picking_up_objects",
        "put_down": "putting_objects_down",
        "hold": "holding_objects",
        "write": "writing",
        "type": "typing",
        "point": "pointing",
        "press": "pressing_buttons",
        "touch_screen": "touching_screens",
        "handshake": "handshakes",
        "hug": "hugging",
        "examine": "medical_examinations",
        "microscope": "using_microscopes",
        "tool": "using_tools",
        "read": "reading_books",
        "turn_page": "turning_pages",
        "window": "looking_through_windows",
        "look_through_microscope": "using_microscopes",
        "touch_display": "touching_screens",
        "open_door_verb": "opening_doors",
    }
    if t in SUPPORTED_INTERACTIONS:
        return t
    if t in aliases:
        return aliases[t]
    for s in SUPPORTED_INTERACTIONS:
        if t in s or s in t:
            return s
    return "pointing"


def build_interaction_package(
    *,
    actor: str,
    target: str,
    interaction_type: str,
    interaction_id: str | None = None,
    physics_state: str = "approaching",
    constraints: dict[str, Any] | None = None,
    world_id: str | None = None,
    t_start: float = 0.0,
    t_end: float | None = None,
) -> dict[str, Any]:
    itype = normalize_interaction_type(interaction_type)
    state = physics_state if physics_state in PHYSICS_STATES else "approaching"
    iid = interaction_id or f"ix_{itype}_{uuid4().hex[:8]}"
    contacts = list(_CONTACT.get(itype) or ["hand_right", "target"])
    anims = list(_ANIM.get(itype) or ["reach", "contact"])

    package = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "interaction_id": iid,
        "actor": str(actor).upper(),
        "target": str(target),
        "interaction_type": itype,
        "contact_points": [
            {"id": c, "required": True, "must_reach": True} for c in contacts
        ],
        "physics_state": state,
        "constraints": {
            "no_float": True,
            "no_clip": True,
            "no_teleport": True,
            "ground_contact_if_locomotion": itype
            in {"walking", "running", "stopping", "turning", "jumping", "standing", "sitting"},
            "hand_must_hit_target": itype
            not in {"walking", "running", "stopping", "turning", "jumping", "looking_through_windows"},
            **(constraints or {}),
        },
        "animation_requirements": anims,
        "completion_state": {
            "success_when": "physics_state==complete",
            "required_final_state": "complete",
            "failed_if": [
                "hand_misses_target",
                "foot_slide",
                "clip_detected",
                "actor_float",
            ],
        },
        "timing": {
            "t_start": float(t_start),
            "t_end": float(t_end) if t_end is not None else float(t_start) + 1.2,
        },
        "world_id": world_id,
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "not_a_world_builder": True,
        },
    }
    return package


def plan_interactions_from_scene(
    *,
    actor: str,
    scene: dict[str, Any],
    stage_world: dict[str, Any] | None = None,
    scene_index: int = 0,
) -> list[dict[str, Any]]:
    """Derive INTERACTION_PACKAGEs from CPE / stage cues."""
    packages: list[dict[str, Any]] = []
    world_id = None
    if stage_world:
        world_id = stage_world.get("world_id") or (stage_world.get("scene_ref") or {}).get(
            "world_id"
        )

    # Locomotion baseline — every scene walks or plants
    packages.append(
        build_interaction_package(
            actor=actor,
            target="nav_mesh",
            interaction_type="walking",
            interaction_id=f"scene_{scene_index:03d}_walk",
            physics_state="manipulating",
            world_id=world_id,
            t_start=0.0,
            t_end=float(scene.get("length_sec") or 3.0) * 0.55,
        )
    )

    # From CPE interaction events
    cpe = scene.get("character_performance_package") or {}
    events = (cpe.get("interactions") or scene.get("actor_interactions") or {}).get(
        "events"
    ) or []
    for i, ev in enumerate(events):
        verb = str(ev.get("verb") or "point")
        target = str(ev.get("target") or "prop")
        packages.append(
            build_interaction_package(
                actor=actor,
                target=target,
                interaction_type=verb,
                interaction_id=f"scene_{scene_index:03d}_ev_{i}",
                physics_state="contacting",
                world_id=world_id,
                t_start=float(ev.get("t") or 1.0),
            )
        )

    # From stage interaction points (sample one primary)
    points = []
    if stage_world:
        points = (stage_world.get("interaction_points") or {}).get("points") or []
        if not points and isinstance(stage_world.get("points"), list):
            points = stage_world["points"]
    if points and len(packages) < 3:
        pt = points[min(scene_index, len(points) - 1)]
        action = (pt.get("actions") or ["inspect"])[0]
        packages.append(
            build_interaction_package(
                actor=actor,
                target=str(pt.get("target_id") or pt.get("id")),
                interaction_type=str(action),
                interaction_id=f"scene_{scene_index:03d}_stage",
                physics_state="approaching",
                world_id=world_id,
                t_start=1.2,
            )
        )

    # Always end grounded
    packages.append(
        build_interaction_package(
            actor=actor,
            target="floor",
            interaction_type="standing",
            interaction_id=f"scene_{scene_index:03d}_stand",
            physics_state="complete",
            world_id=world_id,
            t_start=max(0.0, float(scene.get("length_sec") or 3.0) - 0.6),
            t_end=float(scene.get("length_sec") or 3.0),
        )
    )
    return packages
