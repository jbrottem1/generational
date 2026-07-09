"""Animation Planning — how everything moves, without rendering anything.

Plans character movement, facial animation, camera animation, motion
graphics, scene transitions, timing, lip-sync, and physics notes for one
storyboard (extends the v1.0 animation plan additively). Purely a plan —
the Render Engine and future animation providers execute it.
"""

from __future__ import annotations

# Approximate speech rate used for lip-sync timing windows.
_WORDS_PER_SEC = 2.6


def _character_movement(blueprint: dict, characters: "list[dict]") -> "list[dict]":
    return [
        {
            "character_id": character["character_id"],
            "movement_style": character.get("movement_style", "")
            or f"match the production's {blueprint.get('production_type', '')} motion language",
            "notes": "movement stays in character in every scene — no style breaks",
        }
        for character in characters
    ]


def _facial_animation(scene: dict, on_screen: "list[str]") -> dict:
    return {
        "scene_id": scene.get("scene_id", ""),
        "characters": list(on_screen),
        "expression": scene.get("emotion", ""),
        "notes": (
            "lead with the eyes, expression change lands one beat BEFORE the "
            "narration line that motivates it"
        ),
    }


def _lip_sync(scene: dict) -> dict:
    """Word-window lip-sync timing derived from the narration."""
    words = str(scene.get("narration", "")).split()
    duration = float(scene.get("estimated_duration_sec", 0) or 0)
    spoken = round(min(len(words) / _WORDS_PER_SEC, duration), 1) if words else 0.0
    return {
        "scene_id": scene.get("scene_id", ""),
        "words": len(words),
        "speech_window_sec": spoken,
        "rest_window_sec": round(max(duration - spoken, 0.0), 1),
        "notes": "phoneme-level timing comes from the Voice engine's narration track at render time",
    }


def build_animation_plan(
    storyboard: "list[dict]", blueprint: dict, characters: "list[dict]"
) -> dict:
    """The complete animation plan for one production (plan only)."""
    from services.creative_studio.production_types import get_production_type

    production_type = get_production_type(blueprint.get("production_type", "")) or {}
    on_screen = [
        character["character_id"]
        for character in characters
        if "voice-only" not in character.get("visual_signature", "")
    ]

    return {
        # v1.0 fields (kept identical for downstream consumers).
        "animation_style": blueprint.get("production_type", ""),
        "techniques": list(production_type.get("techniques", [])),
        "complexity": blueprint.get("production_complexity", "standard"),
        "scenes": [
            {
                "scene_id": scene.get("scene_id", ""),
                "motion_instructions": scene.get("motion_instructions", ""),
                "transitions": scene.get("transitions", {}),
            }
            for scene in storyboard
        ],
        # v1.1 additive extension.
        "character_movement": _character_movement(blueprint, characters),
        "facial_animation": [_facial_animation(scene, on_screen) for scene in storyboard],
        "camera_animation": [
            {
                "scene_id": scene.get("scene_id", ""),
                "movement": scene.get("camera_movement", ""),
                "easing": "ease-out into holds, ease-in out of holds — no linear camera",
            }
            for scene in storyboard
        ],
        "motion_graphics": [
            {
                "scene_id": scene.get("scene_id", ""),
                "overlays": list(scene.get("overlay_graphics", [])),
                "timing": "overlays enter after the visual beat lands, exit before the cut",
            }
            for scene in storyboard
            if scene.get("overlay_graphics")
        ],
        "timing": {
            "tempo": blueprint.get("pacing", {}).get("tempo", "dynamic"),
            "cuts_per_minute": blueprint.get("pacing", {}).get("cuts_per_minute", 15),
            "rule": "every move resolves before its scene's transition begins",
        },
        "lip_sync": [_lip_sync(scene) for scene in storyboard],
        "physics_notes": (
            "weight is real even in stylized media: heavier subjects accelerate "
            "slower, settle longer; cloth and hair trail one beat behind the body"
        ),
    }
