"""Shot planning — decide every scene before Animation Engine executes."""

from __future__ import annotations

from typing import Any

from services.animation_engine.cinematic import (
    detect_emotion,
    detect_lighting_mood,
)
from services.animation_engine.intent import (
    detect_characters,
    detect_world_type,
    narration_text,
)
from services.virtual_film_director.models import (
    ANIMATION_PRIORITIES,
    CAMERA_ANGLES,
    EMOTIONAL_BEATS,
    LENS_STYLES,
    SHOT_LANGUAGE,
    SHOT_SIZE_FROM_LANGUAGE,
    SHOT_TO_AE_CAMERA,
    SHOT_TO_TRUE_MOTION,
)
from services.virtual_film_director.questions import answer_director_questions


def _purpose(scene: dict[str, Any]) -> str:
    return str(scene.get("purpose") or scene.get("segment_type") or "story_beat").lower()


def _emotional_beat(scene: dict[str, Any], *, index: int, total: int, emotion: str) -> str:
    purpose = _purpose(scene)
    if purpose == "hook" or index == 0:
        return "curiosity"
    if purpose == "payoff" or index >= max(0, total - 1):
        return "payoff"
    # Alternate rhythm across the middle
    cycle = ["discovery", "explanation", "wonder", "scale", "surprise", "relief"]
    beat = cycle[index % len(cycle)]
    if emotion == "awe":
        return "wonder" if "wonder" in EMOTIONAL_BEATS else beat
    if emotion == "tension":
        return "surprise"
    return beat if beat in EMOTIONAL_BEATS else "explanation"


def choose_shot_language(
    scene: dict[str, Any],
    *,
    emotion: str,
    index: int,
    used: set[str],
) -> str:
    purpose = _purpose(scene)
    text = narration_text(scene).lower()

    preferred: list[str] = []
    if purpose == "hook":
        preferred = ["reveal_shot", "close_up", "push_in", "hero_shot"]
    elif purpose == "payoff":
        preferred = ["hero_shot", "push_in", "epic_establishing", "orbit_shot"]
    elif any(w in text for w in ("wide", "landscape", "world", "across", "map", "skyline", "forest", "ireland")):
        preferred = ["epic_establishing", "wide_landscape", "drone_shot", "crane_shot"]
    elif any(w in text for w in ("look", "detail", "notice", "label", "eye", "read", "close")):
        preferred = ["extreme_close_up", "rack_focus", "close_up"]
    elif emotion == "awe":
        preferred = ["crane_shot", "epic_establishing", "parallax", "reveal_shot"]
    elif emotion == "tension":
        preferred = ["pov", "tracking_shot", "action_follow", "close_up"]
    elif emotion == "curiosity":
        preferred = ["orbit_shot", "reveal_shot", "parallax", "tracking_shot"]
    else:
        preferred = [
            "medium_dialogue",
            "push_in",
            "parallax",
            "tracking_shot",
            SHOT_LANGUAGE[index % len(SHOT_LANGUAGE)],
        ]

    pick = next((s for s in preferred if s not in used), None)
    if pick is None:
        pick = next((s for s in SHOT_LANGUAGE if s not in used), preferred[0])
    return pick


def choose_lens(shot_language: str, emotion: str) -> str:
    if shot_language in {"epic_establishing", "wide_landscape", "drone_shot", "crane_shot"}:
        return "wide_24mm"
    if shot_language in {"extreme_close_up", "close_up", "rack_focus"}:
        return "close_85mm"
    if shot_language == "hero_shot" or emotion == "awe":
        return "anamorphic_feel"
    if shot_language in {"pov", "over_the_shoulder"}:
        return "standard_35mm"
    return "portrait_50mm" if "portrait_50mm" in LENS_STYLES else LENS_STYLES[0]


def choose_angle(shot_language: str, emotion: str) -> str:
    if shot_language == "hero_shot" or emotion in {"clarity", "payoff"}:
        return "low_angle_hero"
    if emotion == "tension" or shot_language == "pov":
        return "high_angle_vulnerable"
    if shot_language in {"drone_shot", "crane_shot"}:
        return "overhead"
    if shot_language in {"epic_establishing", "wide_landscape"}:
        return "eye_level"
    return "eye_level" if "eye_level" in CAMERA_ANGLES else CAMERA_ANGLES[0]


def plan_world_direction(world_env: str, emotion: str, beat: str) -> dict[str, Any]:
    """World is another actor — motion intensifies with dramatic beats."""
    base = {
        "forest": ["canopy_sway", "mist_roll", "birds_overhead", "insect_near_ground", "wet_rock_sheen"],
        "ocean": ["wave_set", "spray", "horizon_haze", "light_caustics"],
        "countryside": ["grass_sway", "cloud_drift", "birds", "mist", "wind"],
        "city": ["traffic_band", "window_glow", "weather", "pedestrian_life"],
        "laboratory": ["monitor_pulse", "dust_motes", "practical_glow"],
        "space": ["star_drift", "nebula_wash"],
        "interior": ["curtain_sway", "dust_motes", "practical_lamp"],
        "generic": ["ambient_life", "cloud_drift", "light_drift"],
    }.get(world_env, ["ambient_life", "cloud_drift"])
    intensifiers = []
    if beat in {"surprise", "scale", "payoff"} or emotion in {"awe", "tension"}:
        intensifiers = ["wind_increase", "lighting_shift", "fog_clear_on_reveal"]
    if beat == "discovery":
        intensifiers.append("god_ray_break")
    return {
        "environment": world_env,
        "ambient_motion": base,
        "dramatic_response": intensifiers,
        "continues_without_narration": True,
        "purpose": "Support story emotion — never decorative noise",
    }


def plan_character_direction(scene: dict[str, Any], *, topic: str, emotion: str) -> dict[str, Any] | None:
    chars = detect_characters(scene, topic=topic)
    if not chars:
        return None
    return {
        "enabled": True,
        "characters": chars,
        "blocking": "primary subject holds rule-of-thirds; secondary clears look-space",
        "performance": {
            "eye_movement": "track subject of narration",
            "facial_expression": emotion,
            "body_language": "weight_shift + posture settle",
            "walking_speed": "measured" if emotion != "tension" else "urgent",
            "gestures": "point_or_demonstrate when teaching",
            "reaction_timing": "anticipate beat then settle",
            "cloth_hair": "subtle wind response",
        },
        "forbid_mannequin": True,
    }


def plan_shot(
    scene: dict[str, Any],
    *,
    candidate: dict[str, Any],
    topic: str,
    index: int,
    total: int,
    used_shots: set[str],
    prev_shot: dict[str, Any] | None,
) -> dict[str, Any]:
    world_env = detect_world_type(candidate, scene, topic=topic)
    emotion = detect_emotion(scene)
    # Prefer emotional pacing beat for middle scenes
    beat = _emotional_beat(scene, index=index, total=total, emotion=emotion)
    shot_language = choose_shot_language(scene, emotion=emotion, index=index, used=used_shots)
    lighting = detect_lighting_mood(scene, world_env=world_env, emotion=emotion)
    lens = choose_lens(shot_language, emotion)
    angle = choose_angle(shot_language, emotion)
    subject = str(scene.get("subject") or topic or "subject").strip()
    dur = float(scene.get("length_sec") or scene.get("duration_sec") or 3.0)
    if dur <= 0:
        dur = 3.0

    questions = answer_director_questions(
        scene,
        topic=topic,
        emotion=emotion,
        shot_language=shot_language,
        primary_subject=subject,
    )

    transition = "hard_cut" if index == 0 else (
        "seamless_camera_continuation"
        if prev_shot and prev_shot.get("emotional_beat") == beat
        else (
            "lighting_continuity"
            if prev_shot and prev_shot.get("lighting_mood") == lighting
            else ["motion_match_cut", "environmental_continuation", "object_continuation", "natural_reveal"][
                index % 4
            ]
        )
    )

    priorities = list(ANIMATION_PRIORITIES)
    if detect_characters(scene, topic=topic):
        priorities = ["character_performance"] + [p for p in priorities if p != "character_performance"]
    else:
        priorities = ["environment_life", "camera_storytelling"] + [
            p for p in priorities if p not in {"environment_life", "camera_storytelling"}
        ]

    shot = {
        "scene_number": scene.get("scene_number") or index + 1,
        "scene_id": scene.get("scene_id") or scene.get("id") or f"scene_{index:02d}",
        "scene_objective": (questions.get("answers") or {}).get("why_scene_exists"),
        "primary_subject": subject,
        "camera_angle": angle,
        "lens_style": lens,
        "shot_size": SHOT_SIZE_FROM_LANGUAGE.get(shot_language, "dynamic_medium"),
        "shot_language": shot_language,
        "camera_movement": shot_language,
        "camera_begin": (questions.get("answers") or {}).get("camera_begin"),
        "camera_end": (questions.get("answers") or {}).get("camera_end"),
        "character_blocking": plan_character_direction(scene, topic=topic, emotion=emotion),
        "environmental_motion": plan_world_direction(world_env, emotion, beat),
        "lighting_mood": lighting,
        "color_palette": {
            "harmony": "natural",
            "temperature": {
                "golden_hour": "warm",
                "firelight": "warm",
                "moonlight": "cool",
                "storm": "cool",
                "soft_daylight": "neutral",
                "volumetric_sunlight": "warm_neutral",
                "cinematic_contrast": "contrast",
            }.get(lighting, "neutral"),
            "subject_isolation": True,
        },
        "transition_style": transition,
        "emotional_beat": beat,
        "emotion": emotion,
        "educational_goal": (questions.get("answers") or {}).get("what_viewer_learns"),
        "estimated_duration_sec": dur,
        "animation_priority": priorities[:4],
        "director_questions": questions,
        "cinematic_payoff": (questions.get("answers") or {}).get("cinematic_payoff"),
        "muted_story_test": (questions.get("answers") or {}).get("cinematic_payoff"),
        "notice_first": (questions.get("answers") or {}).get("notice_first"),
        # Seeds for Animation Engine execution
        "animation_seed": {
            "true_motion_camera": SHOT_TO_TRUE_MOTION.get(shot_language, "push_in"),
            "ae_camera_move": SHOT_TO_AE_CAMERA.get(shot_language, "slow_cinematic_push"),
            "shot_size": SHOT_SIZE_FROM_LANGUAGE.get(shot_language, "dynamic_medium"),
            "emotion": emotion,
            "lighting_mood": lighting,
            "forbid_purposeless_drift": True,
            "narrative_purpose": (questions.get("answers") or {}).get("why_scene_exists"),
        },
        "composition": {
            "rule_of_thirds": True,
            "leading_lines": world_env in {"city", "forest", "countryside"},
            "negative_space": shot_language in {"close_up", "extreme_close_up", "hero_shot"},
            "fg_mg_bg": True,
            "subject_hierarchy": "clear",
        },
        "ready": bool(questions.get("ready")),
    }
    return shot
