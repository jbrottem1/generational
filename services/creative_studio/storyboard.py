"""Storyboard Engine — professional storyboards from a blueprint + script.

Executes the Creative Director's blueprint: every narration beat becomes
one fully specified StoryboardScene (STORYBOARD_SCENE_FIELDS) with camera
work, lighting, palette, animation style, motion instructions,
transitions, background, props, characters, overlays, duration, asset
requirements, and production notes. A flat shot list and per-scene asset
requirements are derived from the board.

Deterministic: scene N of the same input is always the same scene.
"""

from __future__ import annotations

from services.creative_studio.characters import character_prompt_fragment
from services.creative_studio.director import _split_script
from services.creative_studio.environments import select_environments
from services.creative_studio.models import StoryboardScene
from services.creative_studio.production_types import get_production_type
from services.creative_studio.styles import get_style

# Camera coverage cycle — professional shot progression repeated across the
# board (establish → develop → emphasize), with the hook and payoff pinned.
_CAMERA_CYCLE = (
    {"angle": "wide establishing", "movement": "slow push-in"},
    {"angle": "medium", "movement": "static with subtle drift"},
    {"angle": "close-up", "movement": "slow push-in"},
    {"angle": "medium over-shoulder", "movement": "lateral track"},
    {"angle": "detail insert", "movement": "static macro"},
)

_HOOK_CAMERA = {"angle": "dramatic close-up", "movement": "fast push-in"}
_PAYOFF_CAMERA = {"angle": "wide hero shot", "movement": "slow pull-back"}

# Scene purposes across the arc.
_PURPOSES = ("hook", "setup", "development", "escalation", "revelation", "payoff")


def _scene_purpose(index: int, total: int) -> str:
    if index == 0:
        return "hook"
    if index == total - 1:
        return "payoff"
    if total <= 3:
        return "development"
    position = index / max(total - 1, 1)
    if position < 0.35:
        return "setup"
    if position < 0.65:
        return "development"
    if position < 0.85:
        return "escalation"
    return "revelation"


def _scene_emotion(purpose: str, curve: "list[str]") -> str:
    mapping = {
        "hook": "curiosity",
        "setup": "interest",
        "development": "engagement",
        "escalation": "tension",
        "revelation": "surprise",
        "payoff": "satisfaction",
    }
    emotion = mapping.get(purpose, "engagement")
    return emotion if emotion else (curve[0] if curve else "curiosity")


def _camera_for(index: int, total: int) -> dict:
    if index == 0:
        return dict(_HOOK_CAMERA)
    if index == total - 1 and total > 1:
        return dict(_PAYOFF_CAMERA)
    return dict(_CAMERA_CYCLE[(index - 1) % len(_CAMERA_CYCLE)])


def _transitions(index: int, total: int, blueprint: dict) -> dict:
    grammar = blueprint.get("cinematic_language", {}).get("transition_grammar", "")
    signature = "dissolve" if "dissolve" in grammar else "match cut"
    return {
        "in": "none" if index == 0 else ("hard cut" if index % 3 else signature),
        "out": "fade to brand endcard" if index == total - 1 else "hard cut",
    }


def _estimated_duration(narration: str, pacing: dict) -> float:
    """Narration length drives duration (~2.6 words/sec), clamped around
    the blueprint's per-scene target so pacing stays intentional."""
    words = len(narration.split())
    spoken = words / 2.6 if words else 0.0
    target = float(pacing.get("scene_target_sec", 4.0))
    return round(min(max(spoken, target * 0.5), target * 2.0), 1) if spoken else target


def build_storyboard(item: dict, blueprint: dict, characters: "list[dict]") -> "list[dict]":
    """The full professional storyboard for one item — one scene per beat."""
    beats = _split_script(item) or [str(item.get("hook") or item.get("topic") or "Untitled")]
    style = get_style(blueprint["visual_style"]) or {}
    environments = select_environments(item)
    curve = blueprint.get("script_interpretation", {}).get("emotional_curve", [])
    pacing = blueprint.get("pacing", {})
    project_id = str(item.get("project_id", "proj"))
    character_ids = [character["character_id"] for character in characters]
    on_screen = [
        character["character_id"]
        for character in characters
        if "voice-only" not in character.get("visual_signature", "")
    ]

    total = len(beats)
    scenes = []
    for index, narration in enumerate(beats):
        purpose = _scene_purpose(index, total)
        camera = _camera_for(index, total)
        environment = environments[index % len(environments)]
        cast_fragments = [character_prompt_fragment(cid) for cid in on_screen]

        visual_description = " — ".join(
            part
            for part in (
                f"{environment['label']}: {narration[:120]}",
                style.get("texture", ""),
                ", ".join(fragment for fragment in cast_fragments if fragment),
            )
            if part
        )

        scene = StoryboardScene(
            scene_id=f"cs_{project_id}_{index + 1:03d}",
            purpose=purpose,
            emotion=_scene_emotion(purpose, curve),
            narration=narration,
            visual_description=visual_description,
            camera_angle=camera["angle"],
            camera_movement=camera["movement"],
            lighting=style.get("lighting", environment.get("lighting", "")),
            color_palette=style.get("color_palette", environment.get("color_palette", "")),
            animation_style=blueprint.get("production_type", ""),
            motion_instructions=(
                f"{style.get('motion_language', 'natural motion')}; "
                f"intensity {'high' if purpose in ('hook', 'escalation') else 'medium'}"
            ),
            transitions=_transitions(index, total, blueprint),
            background=environment["environment_id"],
            props=list(environment.get("props", []))[:3],
            characters=list(character_ids),
            overlay_graphics=(
                ["hook text overlay"] if purpose == "hook"
                else ["cta endcard"] if purpose == "payoff"
                else []
            ),
            estimated_duration_sec=_estimated_duration(narration, pacing),
            asset_requirements=[f"asset_{project_id}_{index + 1:03d}"],
            production_notes=(
                f"{purpose} beat — {blueprint.get('storytelling_style', '')}; "
                f"hold brand consistency ({style.get('style_id', blueprint['visual_style'])})"
            ),
        )
        scenes.append(scene.to_dict())
    return scenes


def build_shot_list(storyboard: "list[dict]") -> "list[dict]":
    """The flat, numbered shot list production crews (and providers) execute."""
    shots = []
    for number, scene in enumerate(storyboard, start=1):
        shots.append(
            {
                "shot_id": f"shot_{number:03d}",
                "scene_id": scene["scene_id"],
                "shot_number": number,
                "shot_type": scene["camera_angle"],
                "camera_angle": scene["camera_angle"],
                "camera_movement": scene["camera_movement"],
                "subject": scene["visual_description"][:100],
                "duration_sec": scene["estimated_duration_sec"],
                "notes": scene["production_notes"],
            }
        )
    return shots


def build_asset_requirements(
    storyboard: "list[dict]", blueprint: dict, characters: "list[dict]"
) -> "list[dict]":
    """Every creative asset the production needs, provider-ready.

    One primary visual per scene (typed by the production medium) plus one
    reusable reference asset per on-screen character — the reference is what
    keeps a character identical across scenes and future productions.
    """
    production_type = get_production_type(blueprint.get("production_type", "")) or {}
    asset_types = production_type.get("asset_types") or ["ai_image"]
    primary_type = asset_types[0]
    requirements = []

    for scene in storyboard:
        asset_id = scene["asset_requirements"][0]
        requirements.append(
            {
                "asset_id": asset_id,
                "scene_id": scene["scene_id"],
                "asset_type": primary_type,
                "description": scene["visual_description"],
                "prompt": (
                    f"{scene['visual_description']}, {scene['lighting']}, "
                    f"{scene['color_palette']}, {scene['camera_angle']}"
                ),
                "style": blueprint["visual_style"],
                "priority": "required",
                "reusable": False,
                "status": "planned",
            }
        )

    for character in characters:
        if "voice-only" in character.get("visual_signature", ""):
            continue
        requirements.append(
            {
                "asset_id": f"charref_{character['character_id']}",
                "scene_id": "",
                "asset_type": "ai_image",
                "description": f"Character reference sheet: {character['name']}",
                "prompt": (
                    f"character reference sheet, {character_prompt_fragment(character['character_id'])}, "
                    f"front and side views, neutral background"
                ),
                "style": blueprint["visual_style"],
                "priority": "required",
                "reusable": True,
                "status": "planned",
            }
        )
    return requirements
