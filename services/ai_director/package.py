"""DirectorPackage assembly — the executive creative brief for one item."""

from __future__ import annotations

from datetime import datetime, timezone

from services.ai_director.decisions import (
    build_camera_plan,
    build_character_plan,
    build_editing_plan,
    build_expected_runtime,
    build_music_plan,
    build_narration_plan,
    build_optimization_hints,
    build_orchestration_notes,
    build_pacing,
    build_production_strategy,
    build_quality_targets,
    build_shot_plan,
    build_asset_requirements,
    select_animation_style,
    select_creative_style,
    select_format,
    select_orientation,
    select_platforms,
    select_production_priority,
    select_visual_style,
)
from services.ai_director.models import (
    AI_DIRECTOR_ENGINE_VERSION,
    DIRECTOR_PACKAGE_VERSION,
)
from services.ai_director.policies import get_policies
from services.ai_director.quality import validate_director_package


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_director_items(context: dict) -> "tuple[list, str]":
    """Items this run should direct — same collection order as other stages."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas", "candidates"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def build_director_package(item: dict, context: dict | None = None) -> dict:
    """One complete DirectorPackage for one content item."""
    context = context or {}
    policies = get_policies()

    fmt = select_format(item, context, policies)
    platforms = select_platforms(item, context, fmt, policies)
    orientation = select_orientation(item, fmt, platforms, policies)

    strategy = build_production_strategy(item, context, fmt, orientation)
    creative_style = select_creative_style(item, fmt)
    visual_style = select_visual_style(item, creative_style, fmt)
    animation_style = select_animation_style(fmt, strategy["visual_complexity"])
    camera_plan = build_camera_plan(fmt, orientation, strategy["emotional_intensity"])
    pacing = build_pacing(fmt, item, context)
    shot_plan = build_shot_plan(item, pacing, fmt)
    character_plan = build_character_plan(item, fmt)
    music_plan = build_music_plan(fmt, strategy["emotional_intensity"])
    narration_plan = build_narration_plan(item, fmt)
    editing_plan = build_editing_plan(fmt, orientation, strategy["caption_strategy"])
    optimization_hints = build_optimization_hints(item, context)
    asset_requirements = build_asset_requirements(fmt, strategy["visual_complexity"], shot_plan)
    expected_runtime = build_expected_runtime(fmt, pacing, platforms)
    quality_targets = build_quality_targets(item)
    production_priority = select_production_priority(item, context)
    orchestration_notes = build_orchestration_notes(strategy, fmt)

    package = {
        "director_package_version": DIRECTOR_PACKAGE_VERSION,
        "engine_version": AI_DIRECTOR_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "production_strategy": strategy,
        "target_platforms": platforms,
        "creative_style": creative_style,
        "visual_style": visual_style,
        "animation_style": animation_style,
        "camera_plan": camera_plan,
        "pacing": pacing,
        "shot_plan": shot_plan,
        "character_plan": character_plan,
        "music_plan": music_plan,
        "narration_plan": narration_plan,
        "editing_plan": editing_plan,
        "optimization_hints": optimization_hints,
        "asset_requirements": asset_requirements,
        "expected_runtime": expected_runtime,
        "quality_targets": quality_targets,
        "production_priority": production_priority,
        "orchestration_notes": orchestration_notes,
        "upstream_alignment": {},
        "validation": {},
        "director_diagnostics": {
            "policy_version": policies.get("version"),
            "format_selected": fmt,
            "score_used": max(
                int(item.get("opportunity_score", 0) or 0),
                int(item.get("quality_score", 0) or 0),
            ),
            "context_keys_used": [
                key for key in (
                    "opportunity_recommendations", "market_opportunities",
                    "trend_intelligence_report", "psychology_report",
                )
                if context.get(key)
            ],
        },
        "generated_at": _now_iso(),
    }

    validation = validate_director_package(item, package, policies)
    package["validation"] = validation
    return package


def direct_items(items: list, context: dict) -> list:
    """Build DirectorPackages for a list of items."""
    return [build_director_package(item, context) for item in items]
