"""Tests for AI Studio Director V5.0 — Production Blueprint before production."""

from __future__ import annotations

import engines  # noqa: F401
from engines import registry
from core.workflows import WORKFLOWS
from services.ai_director import (
    AI_DIRECTOR_ENGINE_VERSION,
    PRODUCTION_BLUEPRINT_FIELDS,
    STYLE_LIBRARY,
    apply_blueprint_to_candidate,
    blueprint_consistency_score,
    build_director_package,
    build_production_blueprint,
    choose_production_style,
    list_styles,
)
from services.executive_orchestrator.stages import EXECUTIVE_STAGES, STAGE_ENGINES


def _candidate(**overrides):
    base = {
        "project_id": "dir_v5_1",
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "niche": "technology",
        "platform": "youtube_shorts",
        "hook": "AI is already changing your life.",
        "quality_score": 82,
        "audience_intelligence": {
            "primary_audience": "Curious adults 18–45",
            "target_age": "18-45",
            "knowledge_level": "beginner",
            "human_attention_score": 78,
        },
        "psychology": {
            "viral_score": 80,
            "dimensions": {"curiosity_gap": 85, "emotional_intensity": 70},
        },
    }
    base.update(overrides)
    return base


def test_engine_is_v5_ready():
    engine = registry.get_engine("ai_director")
    assert engine is not None
    assert engine.is_ready()
    assert engine.version == "5.0.0"
    assert AI_DIRECTOR_ENGINE_VERSION == "5.0.0"
    assert "production-blueprint" in engine.capabilities
    assert "style-library" in engine.capabilities


def test_wired_before_script_and_production():
    for wf in ("intelligence", "full_content"):
        steps = WORKFLOWS[wf]
        assert "ai_director" in steps
        assert steps.index("audience_intelligence") < steps.index("ai_director")
        assert steps.index("ai_director") < steps.index("script_generation")
        assert steps.index("ai_director") < steps.index("visual_intelligence")
        assert steps.index("ai_director") < steps.index("studio_render")
    assert WORKFLOWS["media_production"][0] == "ai_director"
    assert "direction" in EXECUTIVE_STAGES
    assert EXECUTIVE_STAGES.index("research") < EXECUTIVE_STAGES.index("direction")
    assert EXECUTIVE_STAGES.index("direction") < EXECUTIVE_STAGES.index("script")
    assert STAGE_ENGINES["direction"] == ["ai_director"]


def test_style_library_covers_required_styles():
    required = {
        "modern_documentary",
        "minimal_whiteboard",
        "science_documentary",
        "kurzgesagt_inspired",
        "vox_inspired",
        "apple_keynote",
        "history_channel",
        "national_geographic",
        "technology_review",
        "space_documentary",
        "medical_animation",
        "corporate_explainer",
    }
    assert required.issubset(set(STYLE_LIBRARY))
    styles = list_styles()
    assert len(styles) >= 12
    for entry in styles:
        for key in ("motion", "typography", "transitions", "music", "narration", "colors", "camera", "graphics"):
            assert key in entry, key


def test_style_selection_is_topic_aware_not_identical():
    ai = choose_production_style(_candidate(topic="artificial intelligence chips"))
    space = choose_production_style(_candidate(topic="nasa space telescope orbit", title="Space"))
    history = choose_production_style(_candidate(topic="ancient roman empire history", title="Rome"))
    assert ai["style_id"] == "technology_review"
    assert space["style_id"] == "space_documentary"
    assert history["style_id"] == "history_channel"
    assert len({ai["style_id"], space["style_id"], history["style_id"]}) == 3


def test_production_blueprint_has_all_required_fields():
    bp = build_production_blueprint(_candidate())
    for field in PRODUCTION_BLUEPRINT_FIELDS:
        assert field in bp, field
    assert bp["blueprint_version"] == "5.0"
    assert bp["platform"] == "youtube_shorts"
    assert bp["video_length_sec"] <= 60
    assert bp["narration_style"]
    assert bp["music_style"]
    assert bp["visual_direction"]["modality"]
    assert bp["competitor_analysis"]["top_creators"]
    assert bp["production_plan"]["engines_must_follow_blueprint"] is True
    assert bp["expected_ctr"] > 0
    assert bp["expected_watch_time_sec"] > 0
    assert bp["expected_completion_rate"] > 0


def test_director_package_embeds_blueprint():
    pkg = build_director_package(_candidate())
    assert pkg["engine_version"] == "5.0.0"
    assert pkg["director_package_version"] == "5.0"
    bp = pkg["production_blueprint"]
    assert bp["production_style_id"]
    assert pkg["creative_style"]["style_id"] == bp["production_style_id"]
    assert pkg["music_plan"]["direction"] == bp["music_style"]
    assert pkg["narration_plan"]["delivery_style"] == bp["narration_style"]


def test_engine_applies_blueprint_to_candidates():
    item = _candidate()
    result = registry.get_engine("ai_director").run({"candidates": [item]})
    assert result["ai_director_summary"]["blueprints"] == 1
    assert item["production_blueprint"]["production_style_id"]
    assert item["director_package"]["production_blueprint"]
    assert item["visual_style"]
    assert item["narration_style"]
    assert item["music_mood"]
    assert item["director_expectations"]["ctr"]


def test_blueprint_improves_cross_engine_consistency():
    """Directed candidates share a complete vision; undirected do not."""
    undirected = [_candidate(title=f"undirected {i}") for i in range(3)]
    directed = []
    for i, topic in enumerate(("ai chips", "nasa orbit", "roman empire")):
        c = _candidate(title=f"directed {i}", topic=topic)
        pkg = build_director_package(c)
        directed.append(apply_blueprint_to_candidate(c, pkg["production_blueprint"], pkg))

    undirected_score = blueprint_consistency_score(undirected)
    directed_score = blueprint_consistency_score(directed)
    assert undirected_score["has_blueprints"] == 0
    assert directed_score["unified_vision"] is True
    assert directed_score["score"] == 100
    assert directed_score["unique_styles"] >= 2  # not mechanically identical


def test_determinism():
    c = _candidate()
    a = build_production_blueprint(c)
    b = build_production_blueprint(c)
    assert a["production_style_id"] == b["production_style_id"]
    assert a["narration_style"] == b["narration_style"]
    assert a["color_palette"] == b["color_palette"]
    assert a["editing_style"]["average_cut_length_sec"] == b["editing_style"]["average_cut_length_sec"]
