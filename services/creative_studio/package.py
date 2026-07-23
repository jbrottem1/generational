"""CreativeProductionPackage assembly — the studio's single deliverable.

`build_creative_package()` turns one ContentPackage-style item into one
complete visual production blueprint (CREATIVE_PACKAGE_FIELDS): Director
blueprint → storyboard → shot list → animation/character/environment/
motion/camera plans → asset requirements → thumbnail concepts → continuity
report → quality control → production readiness. `design_items()` runs it
across everything in the context and writes each item's
`creative_package` slot (Agent 12's write zone — no other slot is mutated).
"""

from __future__ import annotations

from datetime import datetime, timezone

from providers.creative import provider_plan
from services.creative_studio.characters import cast_characters
from services.creative_studio.continuity import track_continuity
from services.creative_studio.director import build_blueprint
from services.creative_studio.environments import get_environment
from services.creative_studio.models import (
    CREATIVE_ENGINE_VERSION,
    CREATIVE_PACKAGE_VERSION,
)
from services.creative_studio.production_types import get_production_type, select_production_type
from services.creative_studio.quality import production_readiness, validate_package
from services.creative_studio.storyboard import (
    build_asset_requirements,
    build_shot_list,
    build_storyboard,
)
from services.creative_studio.styles import get_style


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _animation_plan(blueprint: dict, storyboard: "list[dict]") -> dict:
    production_type = get_production_type(blueprint["production_type"]) or {}
    return {
        "animation_style": blueprint["production_type"],
        "techniques": list(production_type.get("techniques", [])),
        "complexity": blueprint["production_complexity"],
        "scenes": [
            {
                "scene_id": scene["scene_id"],
                "motion_instructions": scene["motion_instructions"],
                "transitions": scene["transitions"],
            }
            for scene in storyboard
        ],
    }


def _character_plan(characters: "list[dict]", storyboard: "list[dict]") -> dict:
    return {
        "cast": [dict(character) for character in characters],
        "consistency_rules": [
            "embed each character's visual_signature verbatim in every prompt featuring them",
            "keep each character's color_anchor identical in every scene",
            "generate one reusable reference sheet per on-screen character before scene assets",
        ],
        "appearances": {
            character["character_id"]: [
                scene["scene_id"]
                for scene in storyboard
                if character["character_id"] in scene.get("characters", [])
            ]
            for character in characters
        },
    }


def _environment_plan(storyboard: "list[dict]") -> dict:
    used: "list[str]" = []
    for scene in storyboard:
        if scene["background"] and scene["background"] not in used:
            used.append(scene["background"])
    return {
        "environments": [get_environment(env_id) or {"environment_id": env_id} for env_id in used],
        "continuity_rules": [
            "reuse the registered environment preset for every scene staged in it",
            "keep environment lighting and palette identical across its scenes",
        ],
        "scene_map": {scene["scene_id"]: scene["background"] for scene in storyboard},
    }


def _motion_plan(blueprint: dict, storyboard: "list[dict]") -> dict:
    style = get_style(blueprint["visual_style"]) or {}
    return {
        "motion_language": style.get("motion_language", ""),
        "pacing": blueprint["pacing"],
        "scenes": [
            {
                "scene_id": scene["scene_id"],
                "camera_movement": scene["camera_movement"],
                "motion_instructions": scene["motion_instructions"],
                "duration_sec": scene["estimated_duration_sec"],
            }
            for scene in storyboard
        ],
    }


def _camera_plan(blueprint: dict, shot_list: "list[dict]") -> dict:
    return {
        "cinematic_language": blueprint["cinematic_language"],
        "aspect_ratio": blueprint["aspect_ratio"],
        "shots": [
            {
                "shot_id": shot["shot_id"],
                "scene_id": shot["scene_id"],
                "angle": shot["camera_angle"],
                "movement": shot["camera_movement"],
                "duration_sec": shot["duration_sec"],
            }
            for shot in shot_list
        ],
    }


def _thumbnail_concepts(item: dict, blueprint: dict, storyboard: "list[dict]") -> "list[dict]":
    """Creative thumbnail directions from the board's strongest beats.

    Visual Intelligence owns scored thumbnail psychology (`thumbnail_plan`);
    these are the studio's production-side concepts — what to actually
    stage, in the production's own style.
    """
    style = get_style(blueprint["visual_style"]) or {}
    hook = storyboard[0] if storyboard else {}
    payoff = storyboard[-1] if storyboard else {}
    concepts = [
        {
            "concept_id": "thumb_hook_frame",
            "source_scene": hook.get("scene_id", ""),
            "direction": f"The hook moment: {hook.get('visual_description', '')[:120]}",
            "style": blueprint["visual_style"],
            "color_strategy": style.get("color_palette", ""),
            "text_overlay": str(item.get("hook", ""))[:40],
        },
        {
            "concept_id": "thumb_payoff_frame",
            "source_scene": payoff.get("scene_id", ""),
            "direction": f"The payoff hero shot: {payoff.get('visual_description', '')[:120]}",
            "style": blueprint["visual_style"],
            "color_strategy": style.get("color_palette", ""),
            "text_overlay": str(item.get("title", item.get("topic", "")))[:40],
        },
        {
            "concept_id": "thumb_character_focus",
            "source_scene": hook.get("scene_id", ""),
            "direction": "Lead character close-up with high-contrast emotional expression",
            "style": blueprint["visual_style"],
            "color_strategy": style.get("color_palette", ""),
            "text_overlay": "",
        },
    ]
    return concepts


def _diagnostics(blueprint: dict, storyboard: "list[dict]", requirements: "list[dict]") -> dict:
    return {
        "scenes": len(storyboard),
        "total_duration_sec": round(
            sum(float(scene.get("estimated_duration_sec", 0) or 0) for scene in storyboard), 1
        ),
        "assets_required": len(requirements),
        "reusable_assets": sum(1 for req in requirements if req.get("reusable")),
        "production_type": blueprint["production_type"],
        "visual_style": blueprint["visual_style"],
        "complexity": blueprint["production_complexity"],
        "environments": sorted({scene["background"] for scene in storyboard if scene.get("background")}),
    }


def build_creative_package(item: dict, context: "dict | None" = None) -> dict:
    """One CreativeProductionPackage for one content item. Never raises."""
    blueprint = build_blueprint(item)
    production_type = select_production_type(item)
    characters = cast_characters(item, production_type)
    storyboard = build_storyboard(item, blueprint, characters)
    shot_list = build_shot_list(storyboard)
    requirements = build_asset_requirements(storyboard, blueprint, characters)

    package = {
        "creative_package_version": CREATIVE_PACKAGE_VERSION,
        "engine_version": CREATIVE_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "production_type": production_type,
        "creative_blueprint": blueprint,
        "storyboard": storyboard,
        "shot_list": shot_list,
        "animation_plan": _animation_plan(blueprint, storyboard),
        "character_plan": _character_plan(characters, storyboard),
        "environment_plan": _environment_plan(storyboard),
        "motion_plan": _motion_plan(blueprint, storyboard),
        "camera_plan": _camera_plan(blueprint, shot_list),
        "asset_requirements": requirements,
        "thumbnail_concepts": _thumbnail_concepts(item, blueprint, storyboard),
        "continuity_report": track_continuity(storyboard, blueprint, characters),
        "provider_plan": provider_plan(sorted({req["asset_type"] for req in requirements})),
        "generated_at": _now_iso(),
    }

    validation = validate_package(package)
    package["validation"] = validation
    package["production_readiness"] = production_readiness(package, validation)
    package["creative_diagnostics"] = _diagnostics(blueprint, storyboard, requirements)
    return package


def design_items(items: "list[dict]", context: "dict | None" = None) -> "list[dict]":
    """Design every item: writes each item's `creative_package` slot and
    returns the packages. Only Agent 12's slot is mutated — script, visual,
    audio, render, seo, publishing, analytics slots are read, never written."""
    packages = []
    for item in items:
        package = build_creative_package(item, context)
        item["creative_package"] = package
        packages.append(package)
    return packages
