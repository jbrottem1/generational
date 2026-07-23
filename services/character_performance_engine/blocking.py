"""Scene blocking — where everyone is, walks, looks, touches, and ends."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import MAX_STATIONARY_SEC


def plan_blocking(
    *,
    duration_sec: float,
    objective: dict[str, Any],
    scene_index: int = 0,
    shot_size: str = "dynamic_medium",
) -> dict[str, Any]:
    """Answer the blocking questions before any camera move is chosen."""
    dur = max(float(duration_sec or 3.0), 1.0)
    # Stage space in normalized frame coords (0–1). Floor line ~0.72–0.82.
    patterns = (
        {
            "start": {"x": 0.18, "y": 0.52, "facing": "right"},
            "end": {"x": 0.62, "y": 0.50, "facing": "camera"},
            "path_name": "cross_lab_to_hologram",
        },
        {
            "start": {"x": 0.55, "y": 0.48, "facing": "left"},
            "end": {"x": 0.28, "y": 0.50, "facing": "subject"},
            "path_name": "approach_microscope",
        },
        {
            "start": {"x": 0.40, "y": 0.55, "facing": "camera"},
            "end": {"x": 0.72, "y": 0.48, "facing": "right"},
            "path_name": "walk_to_whiteboard",
        },
        {
            "start": {"x": 0.70, "y": 0.50, "facing": "left"},
            "end": {"x": 0.35, "y": 0.52, "facing": "camera"},
            "path_name": "walk_toward_camera",
        },
    )
    pat = patterns[scene_index % len(patterns)]
    mid_t = dur * 0.45
    stop_t = max(0.6, min(MAX_STATIONARY_SEC - 0.2, dur * 0.25))

    looking = _looking_targets(objective)
    touching = _touch_targets(objective)

    return {
        "where_is_everyone": {
            "primary_character": {
                "start": pat["start"],
                "end": pat["end"],
                "floor_contact": True,
                "stage_depth": "midground",
            },
            "extras": [
                {"id": "lab_tech_pass", "path": "bg_left_to_right", "opacity": 0.35},
            ],
        },
        "where_walking": {
            "path_name": pat["path_name"],
            "waypoints": [
                {"t": 0.0, **pat["start"], "action": "plant_and_depart"},
                {"t": mid_t, "x": (pat["start"]["x"] + pat["end"]["x"]) / 2, "y": 0.51, "facing": "path", "action": "walk"},
                {"t": max(mid_t + 0.4, dur - 0.8), **pat["end"], "action": "arrive_and_gesture"},
            ],
            "never_teleport": True,
            "never_slide": True,
            "never_float": True,
        },
        "where_looking": looking,
        "what_touching": touching,
        "what_reacting_to": [
            "environment_life",
            "interaction_target",
            "narration_emphasis",
        ],
        "where_end_shot": {
            "position": pat["end"],
            "pose": "open_teach" if "teach" in str(objective.get("id") or "") else "grounded_presence",
            "hold_sec": min(stop_t, MAX_STATIONARY_SEC),
        },
        "shot_size_hint": shot_size,
        "max_stationary_sec": MAX_STATIONARY_SEC,
        "questions_answered": [
            "where_is_everyone",
            "where_walking",
            "where_looking",
            "what_touching",
            "what_reacting_to",
            "where_end_shot",
        ],
    }


def _looking_targets(objective: dict[str, Any]) -> list[dict[str, Any]]:
    oid = str(objective.get("id") or "")
    if "patient" in oid:
        return [{"t": 0.5, "target": "patient"}, {"t": 2.0, "target": "camera_brief"}]
    if "evidence" in oid or "point" in oid:
        return [{"t": 0.3, "target": "hologram"}, {"t": 1.8, "target": "equipment"}, {"t": 2.8, "target": "camera"}]
    return [
        {"t": 0.2, "target": "environment"},
        {"t": 1.2, "target": "interaction_prop"},
        {"t": 2.4, "target": "camera"},
    ]


def _touch_targets(objective: dict[str, Any]) -> list[dict[str, Any]]:
    oid = str(objective.get("id") or "")
    if "equipment" in oid or "evidence" in oid:
        return [{"t": 1.4, "target": "microscope", "verb": "touch"}, {"t": 2.2, "target": "hologram", "verb": "point"}]
    if "open" in oid:
        return [{"t": 0.8, "target": "door", "verb": "open_door"}]
    return [{"t": 1.6, "target": "display", "verb": "touch_display"}]
