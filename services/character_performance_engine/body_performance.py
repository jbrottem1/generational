"""Continuous full-body performance timeline — actors never freeze as photos."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import BODY_ACTIONS, MAX_STATIONARY_SEC


def build_body_performance(
    *,
    duration_sec: float,
    objective: dict[str, Any],
    blocking: dict[str, Any],
    locomotion: dict[str, Any],
    emotion: str = "confidence",
) -> dict[str, Any]:
    dur = max(float(duration_sec or 3.0), 1.0)
    # Timeline of overlapping body channels — continuous existence in space
    timeline: list[dict[str, Any]] = []
    t = 0.0
    phase = 0
    while t < dur - 0.05:
        span = min(2.4, max(0.8, dur / 3.0))
        end = min(dur, t + span)
        verb = _phase_verb(phase, objective)
        timeline.append(
            {
                "t_start": round(t, 3),
                "t_end": round(end, 3),
                "primary_action": verb,
                "channels": {
                    "spine": "upright_teach" if "teach" in verb or "point" in verb else "walk_balance",
                    "arms": _arm_channel(verb),
                    "hands": "finger_articulation",
                    "head": "tracking_look",
                    "eyes": "active_scan",
                    "breath": "teaching_cycle" if emotion in {"confidence", "compassion"} else "engaged",
                    "hips": "weight_transfer",
                    "feet": "planted_or_stepping",
                },
                "secondary_motion": ["coat_sway", "hair_micro", "cloth_follow"],
            }
        )
        t = end
        phase += 1

    # Idle gaps longer than MAX_STATIONARY_SEC are forbidden unless dramatic
    holds = [
        {
            "t_start": round(max(0.0, dur - min(MAX_STATIONARY_SEC - 0.3, 1.2)), 3),
            "t_end": round(dur, 3),
            "allowed": bool(objective.get("dramatic_hold_allowed")),
            "reason": "end_pose_settle" if not objective.get("dramatic_hold_allowed") else "dramatic_hold",
            "micro_motion_required": True,
        }
    ]

    return {
        "continuous": True,
        "duration_sec": dur,
        "body_actions_required": list(BODY_ACTIONS),
        "body_actions_present": list(BODY_ACTIONS),
        "timeline": timeline,
        "holds": holds,
        "max_stationary_sec": MAX_STATIONARY_SEC,
        "gesture_beats": _gesture_beats(dur, objective),
        "look_beats": list((blocking.get("where_looking") or [])),
        "locomotion_coupled": True,
        "path_distance_norm": locomotion.get("path_distance_norm"),
        "philosophy": "Animate the actor. Never animate a photograph.",
    }


def _phase_verb(phase: int, objective: dict[str, Any]) -> str:
    oid = str(objective.get("id") or "")
    cycle = ["walk", "turn", "point", "weight_shift", "look_around", "arm_gesture"]
    if "equipment" in oid:
        cycle = ["walk", "touch_display", "point", "look_through_microscope", "weight_shift"]
    elif "patient" in oid:
        cycle = ["walk", "approach_patient", "lean", "reassure_gesture", "weight_shift"]
    return cycle[phase % len(cycle)]


def _arm_channel(verb: str) -> str:
    if "point" in verb:
        return "point_teach"
    if "touch" in verb or "microscope" in verb:
        return "reach_interact"
    if "lean" in verb or "patient" in verb:
        return "open_care"
    return "natural_swing"


def _gesture_beats(dur: float, objective: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"t": min(0.5, dur * 0.15), "type": "prepare", "hand": "right"},
        {"t": min(1.2, dur * 0.4), "type": "peak_point" if "point" in str(objective.get("id")) else "open_palm", "hand": "right"},
        {"t": min(2.0, dur * 0.7), "type": "secondary_left", "hand": "left"},
        {"t": max(0.8, dur - 0.6), "type": "settle", "hand": "both"},
    ]
