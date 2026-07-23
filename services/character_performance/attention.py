"""Attention targets and eye→head→body response order."""

from __future__ import annotations

from typing import Any


ATTENTION_TYPES = [
    "character",
    "camera",
    "object",
    "display",
    "sound",
    "moving_subject",
    "thought_or_memory",
    "offscreen_event",
    "environment",
    "none",
]


def build_attention(
    *,
    target_id: str,
    target_type: str = "object",
    priority: float = 0.8,
    distance_meters: float = 2.0,
    screen_position: list[float] | None = None,
    duration_seconds: float = 2.0,
    head_follow_required: bool | None = None,
    body_follow_required: bool = False,
) -> dict[str, Any]:
    t = str(target_type if target_type in ATTENTION_TYPES else "object")
    dist = float(distance_meters)
    # Eyes lead; head follows when outside comfortable eye range (~±15°)
    if head_follow_required is None:
        head_follow_required = dist < 1.2 or t in {"camera", "character", "moving_subject"} or priority >= 0.85
    return {
        "attention_target_id": target_id,
        "target_type": t,
        "priority": max(0.0, min(1.0, float(priority))),
        "distance_meters": dist,
        "screen_position": screen_position or [0.5, 0.45],
        "duration_seconds": float(duration_seconds),
        "head_follow_required": bool(head_follow_required),
        "body_follow_required": bool(body_follow_required),
        "response_order": [
            "eyes_detect",
            "eyes_shift",
            "eyelids_adjust",
            "head_follows",
            "shoulders_or_torso_if_required",
            "expression_changes_by_meaning",
        ],
        "forbid_simultaneous_identical_eye_head_speed": True,
    }


def infer_attention_from_scene(
    scene: dict[str, Any],
    *,
    character_id: str,
    address_audience: bool = False,
) -> dict[str, Any]:
    subject = str(scene.get("subject") or scene.get("prop") or "").strip()
    narration = str(scene.get("narration") or "").lower()
    if address_audience or "you" in narration.split()[:8]:
        return build_attention(
            target_id="camera",
            target_type="camera",
            priority=0.9,
            distance_meters=1.5,
            duration_seconds=float(scene.get("length_sec") or 3.0) * 0.5,
            head_follow_required=True,
        )
    if subject:
        return build_attention(
            target_id=subject.replace(" ", "_").lower(),
            target_type="object",
            priority=0.88,
            distance_meters=1.8,
            screen_position=[0.68, 0.42],
            duration_seconds=float(scene.get("length_sec") or 3.0) * 0.55,
            head_follow_required=True,
        )
    return build_attention(
        target_id=f"{character_id}_environment",
        target_type="environment",
        priority=0.55,
        distance_meters=4.0,
        duration_seconds=float(scene.get("length_sec") or 3.0) * 0.4,
        head_follow_required=False,
    )
