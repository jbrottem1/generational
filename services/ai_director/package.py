"""DirectorPackage assembly — the executive creative brief for one item."""

from __future__ import annotations

from datetime import datetime, timezone

from services.ai_director.blueprint import build_production_blueprint
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
from services.ai_director.styles import choose_production_style


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
    """One complete DirectorPackage + V5 Production Blueprint for one content item."""
    context = context or {}
    policies = get_policies()

    # V5: Production Blueprint first — unified creative vision before downstream work.
    production_blueprint = build_production_blueprint(item, context)
    style_lib = choose_production_style(item, context)

    fmt = select_format(item, context, policies)
    platforms = select_platforms(item, context, fmt, policies)
    orientation = select_orientation(item, fmt, platforms, policies)

    strategy = build_production_strategy(item, context, fmt, orientation)
    # Prefer style-library DNA when available (still keep legacy selectors as base).
    creative_style = select_creative_style(item, fmt)
    creative_style = {
        **creative_style,
        "style_id": style_lib.get("style_id") or creative_style.get("style_id"),
        "label": style_lib.get("label") or creative_style.get("label"),
        "color_direction": (
            ", ".join(f"{k}:{v}" for k, v in (style_lib.get("colors") or {}).items())
            if isinstance(style_lib.get("colors"), dict)
            else (creative_style.get("color_direction") or "")
        ),
        "typography_direction": style_lib.get("typography") or creative_style.get("typography_direction"),
        "mood": style_lib.get("music") or creative_style.get("mood"),
    }
    visual_style = select_visual_style(item, creative_style, fmt)
    visual_style = {
        **visual_style,
        "style_id": style_lib.get("opt_visual_style") or visual_style.get("style_id"),
        "label": style_lib.get("label") or visual_style.get("label"),
        "reference_mood": style_lib.get("motion") or visual_style.get("reference_mood"),
    }
    animation_style = select_animation_style(fmt, strategy["visual_complexity"])
    animation_style = {
        **animation_style,
        "motion_language": style_lib.get("motion") or animation_style.get("motion_language"),
        "transition_style": style_lib.get("transitions") or animation_style.get("transition_style"),
    }
    camera_plan = build_camera_plan(fmt, orientation, strategy["emotional_intensity"])
    if style_lib.get("camera"):
        camera_plan = {
            **camera_plan,
            "dominant_shot_types": list(style_lib.get("camera") or [])[:4],
            "movement_profile": style_lib.get("motion") or camera_plan.get("movement_profile"),
        }
    pacing = build_pacing(fmt, item, context)
    editing = production_blueprint.get("editing_style") or {}
    if editing.get("average_cut_length_sec"):
        pacing = {
            **pacing,
            "scene_target_sec": float(editing["average_cut_length_sec"]),
        }
    shot_plan = build_shot_plan(item, pacing, fmt)
    character_plan = build_character_plan(item, fmt)
    music_plan = build_music_plan(fmt, strategy["emotional_intensity"])
    music_plan = {
        **music_plan,
        "direction": production_blueprint.get("music_style") or music_plan.get("direction"),
    }
    narration_plan = build_narration_plan(item, fmt)
    narration_plan = {
        **narration_plan,
        "delivery_style": production_blueprint.get("narration_style") or narration_plan.get("delivery_style"),
        "voice_selection": production_blueprint.get("narration_style") or narration_plan.get("voice_selection"),
    }
    editing_plan = build_editing_plan(fmt, orientation, strategy["caption_strategy"])
    editing_plan = {
        **editing_plan,
        "transition_grammar": style_lib.get("transitions") or editing_plan.get("transition_grammar"),
        "color_grade_direction": style_lib.get("grade_profile") or editing_plan.get("color_grade_direction"),
        "caption_style": editing.get("caption_frequency") or editing_plan.get("caption_style"),
    }
    optimization_hints = build_optimization_hints(item, context)
    # Competitor differentiation becomes optimization hints
    for tip in (production_blueprint.get("competitor_analysis") or {}).get("differentiation_recommendations") or []:
        optimization_hints.append({
            "dimension": "differentiation",
            "hint": tip,
            "confidence": 80,
            "source": "competitor_analysis",
        })
    asset_requirements = build_asset_requirements(fmt, strategy["visual_complexity"], shot_plan)
    expected_runtime = build_expected_runtime(fmt, pacing, platforms)
    if production_blueprint.get("video_length_sec"):
        length = int(production_blueprint["video_length_sec"])
        expected_runtime = {
            **expected_runtime,
            "target_sec": length,
            "max_sec": max(int(expected_runtime.get("max_sec") or length), length),
        }
    quality_targets = build_quality_targets(item)
    production_priority = select_production_priority(item, context)
    orchestration_notes = build_orchestration_notes(strategy, fmt)
    orchestration_notes = {
        **orchestration_notes,
        "follow_production_blueprint": True,
        "production_style_id": production_blueprint.get("production_style_id"),
        "visual_direction": (production_blueprint.get("visual_direction") or {}).get("modality"),
    }

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
            "production_style_id": production_blueprint.get("production_style_id"),
            "blueprint_version": production_blueprint.get("blueprint_version"),
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
        "production_blueprint": production_blueprint,
        "generated_at": _now_iso(),
    }

    validation = validate_director_package(item, package, policies)
    package["validation"] = validation
    return package


def direct_items(items: list, context: dict) -> list:
    """Build DirectorPackages for a list of items."""
    return [build_director_package(item, context) for item in items]
