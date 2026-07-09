"""CreativeProductionPackage assembly — the studio's single deliverable.

`build_creative_package()` turns one ContentPackage-style item into one
complete visual production blueprint (CREATIVE_PACKAGE_FIELDS): learning
guidance → Director blueprint → storyboard → shot list → world/animation/
character/environment/motion plans → Camera Director → color & lighting →
asset planning → platform adaptations → thumbnail concepts → continuity
report → quality control → production readiness. `design_items()` runs it
across everything in the context and writes each item's
`creative_package` slot (Agent 12's write zone — no other slot is mutated).
"""

from __future__ import annotations

from datetime import datetime, timezone

from providers.creative import provider_plan
from services.creative_studio.animation import build_animation_plan
from services.creative_studio.assets import build_asset_plan
from services.creative_studio.camera import build_camera_plan
from services.creative_studio.characters import cast_characters
from services.creative_studio.color_lighting import build_color_lighting_plan
from services.creative_studio.continuity import track_continuity
from services.creative_studio.director import build_blueprint
from services.creative_studio.environments import get_environment
from services.creative_studio.guidance import apply_guidance_to_item, derive_creative_guidance
from services.creative_studio.models import (
    CREATIVE_ENGINE_VERSION,
    CREATIVE_PACKAGE_VERSION,
)
from services.creative_studio.platforms import build_platform_adaptations
from services.creative_studio.production_types import select_production_type
from services.creative_studio.quality import production_readiness, validate_package
from services.creative_studio.storyboard import (
    build_asset_requirements,
    build_shot_list,
    build_storyboard,
)
from services.creative_studio.styles import get_style
from services.creative_studio.worlds import get_world


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _world_plan(blueprint: dict, storyboard: "list[dict]") -> dict:
    """The persistent world staging this production and how scenes live in it."""
    world = get_world(blueprint.get("world_id", "")) or {}
    return {
        "world": world,
        "staging_rules": [
            "every scene inherits the world's lighting, mood, and camera language",
            "environments used must belong to the world (or be registered into it)",
            "the world persists across productions — do not redesign it per video",
        ],
        "scene_staging": [
            {
                "scene_id": scene["scene_id"],
                "environment": scene.get("background", ""),
                "weather": world.get("weather", ""),
                "mood": world.get("mood", ""),
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
    guidance = derive_creative_guidance(context or {})
    guided_item = apply_guidance_to_item(item, guidance)

    blueprint = build_blueprint(guided_item)
    production_type = select_production_type(guided_item)
    characters = cast_characters(guided_item, production_type)
    storyboard = build_storyboard(guided_item, blueprint, characters)
    shot_list = build_shot_list(storyboard)
    base_requirements = build_asset_requirements(storyboard, blueprint, characters)
    requirements = build_asset_plan(storyboard, blueprint, characters, base_requirements, guided_item)
    style = get_style(blueprint["visual_style"]) or {}

    package = {
        "creative_package_version": CREATIVE_PACKAGE_VERSION,
        "engine_version": CREATIVE_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "production_type": production_type,
        "creative_blueprint": blueprint,
        "storyboard": storyboard,
        "shot_list": shot_list,
        "animation_plan": build_animation_plan(storyboard, blueprint, characters),
        "character_plan": _character_plan(characters, storyboard),
        "environment_plan": _environment_plan(storyboard),
        "motion_plan": _motion_plan(blueprint, storyboard),
        "camera_plan": build_camera_plan(storyboard, blueprint),
        "asset_requirements": requirements,
        "thumbnail_concepts": _thumbnail_concepts(item, blueprint, storyboard),
        "continuity_report": track_continuity(storyboard, blueprint, characters),
        "provider_plan": provider_plan(sorted({req["asset_type"] for req in requirements})),
        "generated_at": _now_iso(),
        "world_plan": _world_plan(blueprint, storyboard),
        "color_lighting_plan": build_color_lighting_plan(storyboard, blueprint, style, guided_item),
        "platform_adaptations": build_platform_adaptations(guided_item, storyboard),
        "creative_memory": {"entries": [], "recorded": False},
        "learning_adaptations": guidance,
    }

    validation = validate_package(package)
    package["validation"] = validation
    package["production_readiness"] = production_readiness(package, validation)
    package["creative_diagnostics"] = _diagnostics(blueprint, storyboard, requirements)
    return package


def design_items(
    items: "list[dict]", context: "dict | None" = None, record_memory: bool = False
) -> "list[dict]":
    """Design every item: writes each item's `creative_package` slot and
    returns the packages. Only Agent 12's slot is mutated — script, visual,
    audio, render, seo, publishing, analytics slots are read, never written.

    With `record_memory=True` (the engine's mode) each production is also
    remembered in the persistent creative memory."""
    from services.creative_studio.memory import record_production

    packages = []
    for item in items:
        package = build_creative_package(item, context)
        if record_memory:
            entries = record_production(package, item)
            package["creative_memory"] = {
                "entries": [
                    {"entry_id": entry["entry_id"], "kind": entry["kind"], "key": entry["key"]}
                    for entry in entries
                ],
                "recorded": bool(entries),
            }
        item["creative_package"] = package
        packages.append(package)
    return packages
