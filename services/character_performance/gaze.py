"""Gaze: eye pose math, saccades/fixations, head-eye coordination."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from math import atan2, degrees
from typing import Any


Vector3 = tuple[float, float, float]


class GazeMode(str, Enum):
    FIXATION = "fixation"
    SACCADE = "saccade"
    SMOOTH_PURSUIT = "smooth_pursuit"
    ANTICIPATORY_GLANCE = "anticipatory_glance"
    CAMERA_ADDRESS = "camera_address"
    DISTRACTED_SCAN = "distracted_scan"


@dataclass
class EyePose:
    yaw_deg: float
    pitch_deg: float
    convergence_deg: float


EYE_LIMITS = {
    "horizontal_deg": 35.0,
    "vertical_up_deg": 25.0,
    "vertical_down_deg": 30.0,
    "comfortable_horizontal_deg": 15.0,
}


def subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def compute_eye_pose(
    eye_position: Vector3,
    target_position: Vector3,
    interocular_distance: float = 0.063,
) -> EyePose:
    dx, dy, dz = subtract(target_position, eye_position)
    yaw = degrees(atan2(dx, max(abs(dz), 1e-6)))
    pitch = degrees(atan2(dy, max((dx * dx + dz * dz) ** 0.5, 1e-6)))
    target_distance = max((dx * dx + dy * dy + dz * dz) ** 0.5, 1e-6)
    convergence = degrees(2.0 * atan2(interocular_distance / 2.0, target_distance))
    return EyePose(yaw_deg=yaw, pitch_deg=pitch, convergence_deg=convergence)


def clamp_eye_pose(pose: EyePose) -> tuple[EyePose, bool]:
    """Clamp to anatomical limits; return (pose, head_follow_required)."""
    yaw = max(-EYE_LIMITS["horizontal_deg"], min(EYE_LIMITS["horizontal_deg"], pose.yaw_deg))
    pitch = max(
        -EYE_LIMITS["vertical_down_deg"],
        min(EYE_LIMITS["vertical_up_deg"], pose.pitch_deg),
    )
    head_follow = abs(pose.yaw_deg) > EYE_LIMITS["comfortable_horizontal_deg"] or abs(
        pose.pitch_deg
    ) > EYE_LIMITS["comfortable_horizontal_deg"]
    return EyePose(yaw, pitch, pose.convergence_deg), head_follow


def pupil_size(
    normalized_luminance: float,
    emotional_arousal: float,
    near_focus: float,
) -> float:
    light_response = 1.0 - max(0.0, min(1.0, normalized_luminance))
    emotion_response = max(0.0, min(1.0, emotional_arousal)) * 0.25
    focus_response = max(0.0, min(1.0, near_focus)) * 0.10
    return max(0.15, min(0.90, 0.25 + light_response * 0.45 + emotion_response + focus_response))


def head_eye_coordination(
    *,
    target: str,
    eye_start: float = 0.0,
    head_start: float = 0.12,
    shoulder_start: float | None = 0.28,
    torso_start: float | None = None,
    settle_time: float = 0.55,
) -> dict[str, Any]:
    return {
        "gaze_event": {
            "target": target,
            "eye_start": eye_start,
            "head_start": head_start,
            "shoulder_start": shoulder_start,
            "torso_start": torso_start,
            "settle_time": settle_time,
            "rule": "eyes_lead_head",
            "forbid_rigid_whole_body_rotation": True,
        }
    }


def plan_gaze_events(
    attention: dict[str, Any],
    *,
    mode: GazeMode | str = GazeMode.FIXATION,
    arousal: float = 0.4,
) -> list[dict[str, Any]]:
    target = attention.get("attention_target_id") or "environment"
    mode_s = mode.value if isinstance(mode, GazeMode) else str(mode)
    duration = float(attention.get("duration_seconds") or 2.0)
    eye_pos: Vector3 = (0.0, 1.65, 0.0)
    # Approximate target from screen position + distance
    sp = attention.get("screen_position") or [0.5, 0.45]
    dist = float(attention.get("distance_meters") or 2.0)
    target_pos: Vector3 = ((sp[0] - 0.5) * dist, 1.5 + (0.5 - sp[1]) * 0.6, -dist)
    pose, head_follow = clamp_eye_pose(compute_eye_pose(eye_pos, target_pos))
    if attention.get("head_follow_required"):
        head_follow = True

    event = {
        "mode": mode_s,
        "target": target,
        "eye_pose": asdict(pose),
        "pupil_size": round(pupil_size(0.55, arousal, 1.0 if dist < 1.5 else 0.2), 4),
        "micro_motion": mode_s == GazeMode.FIXATION.value,
        "coordination": head_eye_coordination(
            target=str(target),
            head_start=0.12 if head_follow else 0.18,
            shoulder_start=0.28 if head_follow and dist < 2.5 else None,
            settle_time=min(0.7, duration * 0.35),
        )["gaze_event"],
        "duration_seconds": duration,
    }
    events = [event]
    # Anticipatory glance before teaching/pointing beats
    if mode_s in {GazeMode.FIXATION.value, GazeMode.CAMERA_ADDRESS.value}:
        events.insert(
            0,
            {
                "mode": GazeMode.ANTICIPATORY_GLANCE.value,
                "target": target,
                "duration_seconds": 0.18,
                "precede_primary": True,
            },
        )
    return events
