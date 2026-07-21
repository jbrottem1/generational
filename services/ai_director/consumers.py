"""Apply Production Blueprint onto candidates so downstream engines follow direction."""

from __future__ import annotations

from typing import Any


def apply_blueprint_to_candidate(candidate: dict, blueprint: dict, director_package: dict | None = None) -> dict:
    """Additive overrides — never strip existing research/script packages."""
    updated = dict(candidate)
    updated["production_blueprint"] = blueprint
    if director_package is not None:
        updated["director_package"] = director_package

    style = blueprint.get("style_library_entry") or {}
    updated["production_style_id"] = blueprint.get("production_style_id") or style.get("style_id")
    updated["visual_style"] = style.get("opt_visual_style") or blueprint.get("visual_style")
    updated["narration_style"] = blueprint.get("narration_style")
    updated["music_mood"] = blueprint.get("music_style")
    updated["preferred_camera_moves"] = list(blueprint.get("camera_style") or [])
    updated["color_palette"] = blueprint.get("color_palette")
    updated["thumbnail_layout"] = (blueprint.get("thumbnail_strategy") or {}).get("layout")
    updated["hook_strategy"] = blueprint.get("hook_strategy") or updated.get("hook_strategy")
    updated["shareability_direction"] = blueprint.get("shareability_direction")
    updated["music_direction"] = blueprint.get("music_direction")
    updated["narration_direction"] = blueprint.get("narration_direction")
    updated["editing_style"] = blueprint.get("editing_style")
    updated["platform"] = blueprint.get("platform") or updated.get("platform")
    updated["duration_sec"] = blueprint.get("video_length_sec") or updated.get("duration_sec")
    updated["audience"] = blueprint.get("primary_audience")
    updated["target_age"] = blueprint.get("target_age")
    updated["knowledge_level"] = blueprint.get("knowledge_level")
    updated["educational_goal"] = blueprint.get("educational_goal")
    updated["entertainment_goal"] = blueprint.get("entertainment_goal")

    # Bridge for studio_render LUT selection
    if style.get("grade_profile"):
        updated["color_grade_profile"] = style["grade_profile"]

    # Bridge for creative_studio style_id
    updated["creative_style_id"] = style.get("style_id")
    updated["director_version"] = "5.0.0"

    # Platform strategy for SEO / publishing consumers
    updated["platform_strategy"] = blueprint.get("platform_strategy")
    updated["competitor_analysis"] = blueprint.get("competitor_analysis")
    updated["retention_targets"] = blueprint.get("retention_targets")
    updated["emotion_curve"] = blueprint.get("emotion_curve")
    updated["curiosity_curve"] = blueprint.get("curiosity_curve")

    # Expected metrics for optimization / learning
    updated["director_expectations"] = {
        "ctr": blueprint.get("expected_ctr"),
        "watch_time_sec": blueprint.get("expected_watch_time_sec"),
        "completion_rate": blueprint.get("expected_completion_rate"),
        "competition": blueprint.get("expected_competition"),
        "difficulty": blueprint.get("expected_difficulty"),
    }
    return updated


def blueprint_consistency_score(candidates: list[dict]) -> dict[str, Any]:
    """Measure whether directed candidates share a unified vision (not mechanical clones)."""
    if not candidates:
        return {"score": 0, "unique_styles": 0, "has_blueprints": 0}
    styles = {
        str((c.get("production_blueprint") or {}).get("production_style_id") or c.get("production_style_id") or "")
        for c in candidates
    }
    styles.discard("")
    with_bp = sum(1 for c in candidates if c.get("production_blueprint"))
    # High consistency within a topic run is good; diversity across topics is handled per-item
    score = 100 if with_bp == len(candidates) else int(100 * with_bp / len(candidates))
    return {
        "score": score,
        "unique_styles": len(styles),
        "has_blueprints": with_bp,
        "total": len(candidates),
        "unified_vision": with_bp == len(candidates),
    }
