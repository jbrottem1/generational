"""Facial performance validation — plan checks + rendered-MP4 inspection checklist.

Critical rule: JSON plan completeness is NOT quality proof.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


REQUIRED_PLAN_FIELDS = [
    "character_id",
    "scene_id",
    "story_objective",
    "primary_emotion",
    "attention_target",
    "gaze_events",
    "blink_profile",
    "expression_curve",
    "speech_performance",
    "validation_required",
]

RENDERED_INSPECTION_CHECKLIST = [
    "gaze_direction_matches_attention_target",
    "eyes_converge_on_near_objects",
    "no_blank_stare",
    "blinks_are_irregular_not_mechanical",
    "expression_transitions_are_gradual",
    "lips_match_narration_audio",
    "jaw_and_cheeks_support_speech",
    "micro_expressions_readable_not_random",
    "face_identity_stable_frame_to_frame",
    "emotion_readable_without_dialogue",
    "no_mesh_sliding_or_uncanny_deform",
]


def validate_facial_performance_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict) or not plan:
        return {
            "ok": False,
            "failures": ["missing_facial_performance_plan"],
            "warnings": [],
            "plan_only": True,
            "rendered_inspection_required": True,
        }
    for field in REQUIRED_PLAN_FIELDS:
        if field not in plan or plan.get(field) in (None, "", []):
            failures.append(f"missing_{field}")
    if not (plan.get("gaze_events") or []):
        failures.append("no_gaze_events")
    speech = plan.get("speech_performance") if isinstance(plan.get("speech_performance"), dict) else {}
    if speech.get("placeholder_timing"):
        warnings.append("speech_visemes_are_placeholder_until_audio_aligned")
    if not plan.get("validation_required"):
        warnings.append("validation_required_flag_missing")
    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "plan_only": True,
        "rendered_inspection_required": True,
        "rendered_inspection_checklist": list(RENDERED_INSPECTION_CHECKLIST),
        "quality_rule": (
            "Do not treat plan completeness or checklist presence as proof of realism. "
            "Inspect the final MP4."
        ),
    }


def validate_scene_facial_plans(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    for i, scene in enumerate(scenes):
        review = validate_facial_performance_plan(scene.get("facial_performance_plan"))
        for f in review.get("failures") or []:
            failures.append(f"scene_{i}:{f}")
        for w in review.get("warnings") or []:
            warnings.append(f"scene_{i}:{w}")
    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "rendered_inspection_required": True,
        "rendered_inspection_checklist": list(RENDERED_INSPECTION_CHECKLIST),
    }


def rendered_facial_inspection_template(*, mp4_path: str | Path | None = None) -> dict[str, Any]:
    """Human/operator inspection sheet — must be filled after watching the MP4."""
    return {
        "mp4_path": str(mp4_path) if mp4_path else None,
        "status": "PENDING_HUMAN_OR_FRAME_INSPECTION",
        "checklist": {item: None for item in RENDERED_INSPECTION_CHECKLIST},
        "rule": "Null/incomplete checklist means the shot is not quality-approved.",
        "reject_if_any_critical_fail": [
            "eyes_stare_blankly",
            "eyes_point_at_different_targets",
            "mechanical_blinking",
            "instant_expression_switch",
            "lips_mismatch_narration",
            "face_identity_loss",
            "emotion_unreadable",
        ],
    }
