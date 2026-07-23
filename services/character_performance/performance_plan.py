"""Facial Performance Plan builder — structured input for existing animation layers."""

from __future__ import annotations

from typing import Any

from services.character_performance.attention import infer_attention_from_scene
from services.character_performance.blinking import build_blink_profile, plan_blinks_for_duration
from services.character_performance.emotion import blend_emotions
from services.character_performance.expressions import (
    build_expression_curve,
    expression_transition_block,
    plan_micro_expressions,
)
from services.character_performance.face_rig import face_rig_profile
from services.character_performance.gaze import GazeMode, plan_gaze_events
from services.character_performance.speech import build_speech_performance


def _infer_emotions(scene: dict[str, Any], host: dict[str, Any] | None) -> tuple[str, str]:
    narration = str(scene.get("narration") or "").lower()
    expr = str(scene.get("studio_expression") or "").lower()
    bias = ((host or {}).get("emotion_bias") if host else None) or {}
    if any(w in narration for w in ("safe", "reassure", "care", "heal", "together")):
        return "compassion", "confidence"
    if any(w in narration for w in ("risk", "danger", "infection", "warning", "careful")):
        return "concern", "compassion"
    if any(w in narration for w in ("how", "why", "discover", "look")):
        return "curiosity", "teaching"
    if "teach" in expr or "explain" in expr:
        return str(bias.get("teaching_primary") or "teaching"), "confidence"
    return str(bias.get("default_primary") or "confidence"), "compassion"


def build_facial_performance_plan(
    *,
    character_id: str,
    scene: dict[str, Any],
    host: dict[str, Any] | None = None,
    scene_index: int = 0,
    audio_path: str = "",
) -> dict[str, Any]:
    cid = str(character_id or (host or {}).get("id") or "UNKNOWN").upper()
    duration = float(scene.get("length_sec") or 3.0)
    primary, secondary = _infer_emotions(scene, host)
    address = bool((host or {}).get("teaching_may_address_audience")) or cid in {
        "DOCTOR_001",
        "CHAR-0001",
        "CHAR-ATLAS",
    }
    attention = infer_attention_from_scene(scene, character_id=cid, address_audience=address and scene_index % 2 == 0)
    blended = blend_emotions(primary, secondary, primary_weight=0.72)
    gaze_mode = GazeMode.CAMERA_ADDRESS if attention.get("target_type") == "camera" else GazeMode.FIXATION
    arousal = float((blended.get("vector") or {}).get("arousal") or 0.4)

    plan = {
        "character_id": cid,
        "scene_id": str(
            scene.get("scene_id")
            or scene.get("id")
            or f"scene_{int(scene.get('scene_number') or scene_index + 1):03d}"
        ),
        "story_objective": str(scene.get("narration") or scene.get("purpose") or "communicate_clearly")[:160],
        "primary_emotion": primary,
        "secondary_emotion": secondary,
        "emotion_vector": blended.get("vector"),
        "face_controls": blended.get("face_controls"),
        "attention_target": attention,
        "gaze_events": plan_gaze_events(attention, mode=gaze_mode, arousal=arousal),
        "blink_profile": build_blink_profile(
            mode="natural",
            stress_multiplier=0.35 if primary == "concern" else 0.2,
            focus_intensity=float((blended.get("vector") or {}).get("attention") or 0.6),
            sentence_boundary=True,
        ),
        "blink_plan": plan_blinks_for_duration(
            duration,
            stress=0.35 if primary == "concern" else 0.2,
            focus=float((blended.get("vector") or {}).get("attention") or 0.6),
            seed=hash(cid + str(scene_index)) % 10_000,
        ),
        "expression_curve": build_expression_curve(
            primary=primary,
            secondary=secondary,
            duration_seconds=duration,
            intensity=0.65,
        ),
        "emotion_transition": expression_transition_block(primary, trigger="scene_intent"),
        "micro_expressions": plan_micro_expressions(primary, duration),
        "speech_performance": build_speech_performance(
            narration=str(scene.get("narration") or ""),
            duration_seconds=duration,
            emotion_name=primary,
            audio_path=audio_path,
        ),
        "head_motion": {
            "lead_by_eyes": True,
            "follow_attention": attention.get("head_follow_required", True),
            "forbid_rigid_spin": True,
        },
        "breathing_mode": "calm" if primary in {"compassion", "confidence", "teaching"} else "concern",
        "face_rig_ref": face_rig_profile(cid),
        "validation_required": True,
        "quality_caveat": (
            "A complete Facial Performance Plan is an execution contract — "
            "not proof of quality. Final acceptance requires inspecting the rendered MP4 "
            "for gaze direction, blink naturalism, expression continuity, and lip sync."
        ),
        "pipeline": [
            "scene_intent",
            "emotional_state",
            "attention_target",
            "facial_performance_plan",
            "eye_and_head_coordination",
            "expression_blending",
            "speech_and_viseme_animation",
            "micro_expression_layer",
            "rendered_performance_validation",
        ],
    }
    return plan


def attach_facial_performance_plans(
    scenes: list[dict[str, Any]],
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    hosts_by_id = hosts_by_id or {}
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        cid = str(row.get("studio_character_id") or "")
        host = hosts_by_id.get(cid.upper()) if cid else None
        if not row.get("facial_performance_plan"):
            row["facial_performance_plan"] = build_facial_performance_plan(
                character_id=cid,
                scene=row,
                host=host,
                scene_index=i,
                audio_path=str(row.get("narration_audio_path") or ""),
            )
        out.append(row)
    return out
