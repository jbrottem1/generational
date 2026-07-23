"""Build per-scene PerformancePlan bindings from character Human Realism packages."""

from __future__ import annotations

from typing import Any

from services.human_realism.resolve import resolve_character

_EMOTION_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("compassion", ("care", "help", "heal", "safe", "reassure", "together")),
    ("concern", ("risk", "danger", "warning", "infection", "disease", "careful")),
    ("curiosity", ("how", "why", "wonder", "discover", "look", "question")),
    ("joy", ("delight", "celebrate", "amazing", "wonderful", "fun")),
    ("determination", ("must", "will", "solve", "build", "fix")),
    ("confidence", ("know", "clear", "explain", "understand", "simple")),
    ("surprise", ("suddenly", "unexpected", "wow")),
    ("contemplation", ("think", "consider", "pause", "reflect")),
]


def _infer_emotion(text: str, bias: dict[str, Any] | None) -> str:
    t = (text or "").lower()
    for emotion, keys in _EMOTION_KEYWORDS:
        if any(k in t for k in keys):
            return emotion
    bias = bias or {}
    if any(w in t for w in ("teach", "learn", "because", "means")):
        return str(bias.get("teaching_primary") or "confidence")
    return str(bias.get("default_primary") or "curiosity")


def _infer_objective(narration: str, expression: str) -> str:
    n = (narration or "").strip()
    if not n:
        return f"perform_{expression or 'presence'}"
    # First clause / short objective
    chunk = n.split(".")[0].strip()
    if len(chunk) > 90:
        chunk = chunk[:87] + "..."
    return chunk or f"communicate_{expression or 'idea'}"


def build_performance_plan(
    *,
    character_id: str,
    scene: dict[str, Any],
    scene_index: int = 0,
    host: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct a scene PerformancePlan soft-binding (no new renderer)."""
    cid = str(character_id or (host or {}).get("id") or "CHAR-UNKNOWN").upper()
    resolved = resolve_character(cid)
    narration = str(scene.get("narration") or scene.get("dialogue") or "")
    expression = str(
        scene.get("studio_expression")
        or (host or {}).get("facial_range", ["focus"])[0]
        or "focus"
    )
    emotion_name = _infer_emotion(narration + " " + expression, resolved.get("emotion_bias") or {})
    favorites = list(
        ((resolved.get("gestures") or {}).get("favorites"))
        or (host or {}).get("favorite_gestures")
        or ["open_palm_teach"]
    )
    gesture_type = favorites[scene_index % len(favorites)]
    gait = resolved.get("gait") or {}
    breath_modes = (resolved.get("breathing") or {}).get("modes") or {}
    teach_breath = breath_modes.get("teaching") or breath_modes.get("calm") or {"rate_bpm": 12}
    camera = resolved.get("camera_awareness") or {}
    address = bool(camera.get("teaching_may_address_audience"))
    gaze_target = "camera" if address and scene_index % 2 == 0 else "subject_or_environment"

    face_recipes = (resolved.get("face") or {}).get("recipes") or {}
    facial = dict(face_recipes.get(emotion_name) or face_recipes.get("teaching") or {"eye_focus": 0.5})

    scene_id = str(
        scene.get("scene_id")
        or scene.get("id")
        or f"scene_{int(scene.get('scene_number') or scene_index + 1):03d}"
    )

    plan = {
        "character_id": cid,
        "scene_id": scene_id,
        "objective": _infer_objective(narration, expression),
        "emotion": {
            "primary": emotion_name,
            "intensity": 0.62,
            "transition_from": "neutral",
            "transition_duration_seconds": 0.6,
        },
        "gaze": {
            "target": gaze_target,
            "duration_seconds": float(scene.get("length_sec") or 3.0) * 0.45,
        },
        "body_language": {
            "stance": "open" if emotion_name in {"compassion", "joy", "confidence"} else "attentive",
            "weight_distribution": {"left": 0.48, "right": 0.52},
            "posture": "professional_open",
        },
        "gesture": {
            "type": gesture_type,
            "cadence": "measured",
            "start_time": 0.4,
            "peak_time": 1.1,
            "end_time": 1.8,
        },
        "walking_style": gait.get("personality_walk") or "professional",
        "breathing": {
            "mode": "teaching" if "teach" in emotion_name or address else "calm",
            "rate_bpm": teach_breath.get("rate_bpm", 12),
            "intensity": 0.35 if emotion_name != "fear" else 0.7,
        },
        "facial_performance": {
            "expression": expression,
            "channels": facial,
            "micro_expression_before_speech": True,
        },
        "interaction_targets": list(
            filter(
                None,
                [
                    scene.get("subject"),
                    scene.get("prop"),
                    "audience" if gaze_target == "camera" else None,
                ],
            )
        )
        or ["environment"],
        "camera_awareness": {
            "mode": "address_audience" if gaze_target == "camera" else "diegetic_world",
            "lens_lock_eyes": gaze_target == "camera",
        },
        "environmental_reactions": {
            "respond_to_ambient_life": True,
            "shared_world_wind": True,
            "contact_shadows": True,
        },
        "foot_contact_required": True,
        "cloth_simulation": True,
        "hair_simulation": bool(((resolved.get("visual_identity") or {}).get("hair") or {}).get("has_organic_hair")),
        "framework_id": resolved.get("framework_id"),
        "true_motion_hint": gait.get("true_motion_hint")
        or (host or {}).get("true_motion_performance")
        or "walk_explain",
    }
    return plan


def attach_performance_plans(
    scenes: list[dict[str, Any]],
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Ensure every scene binding carries a performance_plan."""
    hosts_by_id = hosts_by_id or {}
    out: list[dict[str, Any]] = []
    for i, scene in enumerate(scenes):
        row = dict(scene)
        cid = str(row.get("studio_character_id") or "")
        host = hosts_by_id.get(cid.upper()) if cid else None
        if not row.get("performance_plan"):
            row["performance_plan"] = build_performance_plan(
                character_id=cid,
                scene=row,
                scene_index=i,
                host=host,
            )
        # Convenience mirrors for animation layers
        plan = row["performance_plan"]
        row["studio_emotion"] = (plan.get("emotion") or {}).get("primary")
        row["studio_gaze_target"] = (plan.get("gaze") or {}).get("target")
        row["studio_body_language"] = plan.get("body_language")
        row["studio_walking_style"] = plan.get("walking_style")
        row["studio_breathing"] = plan.get("breathing")
        out.append(row)
    return out
