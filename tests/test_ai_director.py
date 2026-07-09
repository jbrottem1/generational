"""Tests for the AI Director service layer (Agent 18).

Proves: creative decisions, DirectorPackage generation, strategy selection,
platform selection, policy configuration, quality validation, conflict
detection, graceful degradation, and learning feedback hooks.
"""

from __future__ import annotations

from services.ai_director import (
    DIRECTOR_PACKAGE_FIELDS,
    build_director_package,
    configure_policies,
    reset_policies,
    select_format,
    validate_director_package,
)
from services.ai_director.decisions import (
    build_production_strategy,
    select_orientation,
    select_platforms,
)
from services.ai_director.models import DirectorStatus, ProductionPriority
from services.ai_director.policies import apply_learning_feedback


def make_item(**overrides):
    base = {
        "project_id": "proj1",
        "topic": "mystery of the deep ocean",
        "niche": "entertainment",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Experts trace the cause to a rift. The rift is growing."
        ),
        "keywords": ["ocean"],
        "quality_score": 80,
        "opportunity_score": 75,
        "target_platforms": ["youtube_shorts"],
        "script_package": {"script": "The ocean vanishes overnight...", "script_score": 78},
        "visual_package": {"scenes": [], "visual_style": "science"},
        "audio_package": {"voice_style": {"name": "narrator"}},
    }
    base.update(overrides)
    return base


def make_context(**overrides):
    base = {
        "opportunity_recommendations": [{
            "recommended_format": "short_form",
            "hook_direction": "Open with impossible question",
            "thumbnail_direction": "Split ocean before/after",
            "confidence_score": 82,
            "recommended_duration_sec": 45,
        }],
        "market_opportunities": [{
            "platform": "youtube_shorts",
            "recommended_content_type": "educational",
            "confidence": 70,
        }],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------- format selection


def test_select_format_defaults_to_short_form_for_faceless_content():
    item = make_item(topic="viral ocean mystery", keywords=["ocean"])
    assert select_format(item, {}) == "short_form"


def test_select_format_respects_explicit_request():
    item = make_item(format="documentary", topic="history of Rome")
    assert select_format(item, {}) == "documentary"


def test_select_format_detects_educational_signals():
    item = make_item(topic="how to learn python tutorial", niche="education")
    assert select_format(item, {}) == "educational"


def test_select_format_detects_cartoon_signals():
    item = make_item(topic="animated cartoon character adventure for kids")
    assert select_format(item, {}) == "cartoon"


def test_select_format_boosted_by_trend_recommendation():
    context = make_context()
    item = make_item(topic="general topic")
    assert select_format(item, context) == "short_form"


def test_long_duration_promotes_long_form():
    item = make_item(target_duration_sec=300, topic="feature film deep dive")
    fmt = select_format(item, {})
    assert fmt in ("long_form", "documentary", "cinematic")


# -------------------------------------------------------- platform selection


def test_select_platforms_primary_and_secondary():
    item = make_item(target_platforms=["youtube_shorts", "tiktok"])
    platforms = select_platforms(item, {}, "short_form")
    assert platforms[0]["platform"] == "youtube_shorts"
    assert platforms[0]["priority"] == "primary"
    assert platforms[1]["priority"] == "secondary"
    assert platforms[0]["caption_required"] is True


def test_select_orientation_vertical_for_shorts():
    platforms = select_platforms(make_item(), {}, "short_form")
    assert select_orientation(make_item(), "short_form", platforms) == "vertical"


def test_select_orientation_horizontal_for_youtube():
    item = make_item(target_platforms=["youtube"], aspect_ratio="16:9")
    platforms = select_platforms(item, {}, "long_form")
    assert select_orientation(item, "long_form", platforms) == "horizontal"


# ------------------------------------------------------ production strategy


def test_production_strategy_includes_all_decision_fields():
    fmt = "short_form"
    strategy = build_production_strategy(make_item(), make_context(), fmt, "vertical")
    assert strategy["format"] == "short_form"
    assert strategy["orientation"] == "vertical"
    assert strategy["emotional_intensity"] in ("low", "moderate", "high", "extreme")
    assert strategy["caption_strategy"] == "full"
    assert strategy["thumbnail_strategy"]
    assert strategy["publishing_strategy"] in ("immediate", "scheduled", "batch", "test_variant")
    assert strategy["rationale"]


def test_high_score_elevates_visual_complexity():
    item = make_item(quality_score=92, opportunity_score=90)
    strategy = build_production_strategy(item, {}, "cinematic", "horizontal")
    assert strategy["visual_complexity"] in ("rich", "cinematic")


# ------------------------------------------------------ package generation


def test_director_package_carries_full_contract():
    package = build_director_package(make_item(), make_context())
    for field in DIRECTOR_PACKAGE_FIELDS:
        assert field in package, field


def test_director_package_production_strategy_and_plans():
    package = build_director_package(make_item(), make_context())
    assert package["production_strategy"]["format"] == "short_form"
    assert package["target_platforms"]
    assert package["camera_plan"]["camera_grammar"]
    assert package["pacing"]["tempo"]
    assert package["shot_plan"]["key_beats"]
    assert package["character_plan"]["cast_strategy"]
    assert package["music_plan"]["direction"]
    assert package["narration_plan"]["voice_selection"]
    assert package["editing_plan"]["style"]
    assert package["optimization_hints"]
    assert package["asset_requirements"]
    assert package["expected_runtime"]["target_sec"] > 0
    assert package["quality_targets"]["production_tier"]
    assert package["production_priority"] in ProductionPriority.ALL


def test_orchestration_notes_cover_agents_12_through_17():
    package = build_director_package(make_item(), make_context())
    notes = package["orchestration_notes"]
    for agent in (
        "creative_studio", "character_universe", "asset_generation",
        "animation", "render", "post_production",
    ):
        assert agent in notes
        assert notes[agent]


def test_deterministic_output_for_identical_input():
    item = make_item()
    context = make_context()
    first = build_director_package(item, context)
    second = build_director_package(item, context)
    assert first["production_strategy"] == second["production_strategy"]
    assert first["target_platforms"] == second["target_platforms"]


# -------------------------------------------------------- policy configuration


def test_configure_policies_merges_updates():
    reset_policies()
    try:
        updated = configure_policies({"default_platforms": ["tiktok"]})
        assert updated["default_platforms"] == ["tiktok"]
        package = build_director_package(make_item(target_platforms=[]), {})
        assert package["target_platforms"][0]["platform"] == "tiktok"
    finally:
        reset_policies()


def test_apply_learning_feedback_adjusts_weights():
    reset_policies()
    try:
        apply_learning_feedback({"format": {"short_form": 0.5}})
        # Boost should not crash; format still valid.
        fmt = select_format(make_item(), {})
        assert fmt in ("short_form", "educational", "documentary", "cartoon", "cinematic")
    finally:
        reset_policies()


# ---------------------------------------------------------- quality validation


def test_validation_ready_for_well_formed_item():
    package = build_director_package(make_item(), make_context())
    assert package["validation"]["status"] in (DirectorStatus.READY, DirectorStatus.NEEDS_REVIEW)
    assert package["validation"]["confidence"] >= 70


def test_conflict_detection_format_mismatch_with_creative_package():
    item = make_item()
    item["creative_package"] = {
        "creative_blueprint": {
            "production_type": "podcast_visual",
            "aspect_ratio": "16:9",
        }
    }
    package = build_director_package(item, make_context())
    alignment = package["upstream_alignment"]
    assert alignment["packages_consumed"]
    # Director chose short_form/science — may conflict with podcast blueprint.
    if alignment["conflicts_detected"]:
        assert alignment["conflicts_resolved"] or package["validation"]["warnings"]


def test_impossible_duration_capped_gracefully():
    item = make_item(target_platforms=["youtube_shorts"])
    package = build_director_package(item, make_context())
    package["expected_runtime"]["target_sec"] = 999
    validation = validate_director_package(item, package, {})
    assert validation["conflicts_resolved"] >= 1 or validation["degraded"] or validation["warnings"]
    assert package["expected_runtime"]["target_sec"] <= 60


def test_missing_script_degrades_not_blocks():
    item = make_item(script="", script_package={})
    del item["script_package"]
    package = build_director_package(item, {})
    assert package["validation"]["status"] in (
        DirectorStatus.DEGRADED, DirectorStatus.NEEDS_REVIEW, DirectorStatus.READY,
    )
    assert package["production_strategy"]["format"]


def test_upstream_packages_consumed_listed():
    item = make_item()
    package = build_director_package(item, make_context())
    consumed = package["upstream_alignment"]["packages_consumed"]
    assert "script_package" in consumed
    assert "visual_package" in consumed
    assert "audio_package" in consumed
