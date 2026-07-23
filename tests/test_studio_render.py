"""Tests for Studio Render & Motion Graphics Engine V3.0."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.executive_orchestrator.stages import STAGE_ENGINES
from services.production_qa.models import PQA_CATEGORIES, REVISION_OWNERS
from services.studio_render import (
    RENDER_QUALITY_THRESHOLD,
    build_studio_render_package,
    choose_transition,
)
from services.studio_render.color import choose_grade_profile
from services.studio_render.export_pipeline import choose_primary_preset
from services.studio_render.motion_graphics import build_motion_graphics
from services.studio_render.transitions import build_transitions


def _rich_candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "platform": "youtube_shorts",
        "aspect_ratio": "9:16",
        "hook": "AI is already changing your life.",
        "cinematography_attention_score": 90,
        "animation_handoff": {
            "scenes": [
                {"scene_id": "s1", "camera": {"movement": "slow_push_in"}, "movement": "slow_push_in"},
                {"scene_id": "s2", "camera": {"movement": "macro_push_in"}, "movement": "macro_push_in"},
            ]
        },
        "cinematography_plan": {
            "scenes": [
                {"scene_id": "s1", "movement": "slow_push_in", "reason": "hook"},
                {"scene_id": "s2", "movement": "macro_push_in", "reason": "detail"},
            ],
            "overall_attention_score": 90,
        },
        "viewer_retention_package": {
            "overall_score": 98,
            "selected_hook": {"text": "AI is already changing your life.", "score": 95},
            "pacing_plan": [
                {"scene_id": "s1", "duration_sec": 2.5},
                {"scene_id": "s2", "duration_sec": 3.0},
                {"scene_id": "s3", "duration_sec": 3.2},
                {"scene_id": "s4", "duration_sec": 2.8},
            ],
            "caption_plan": {
                "cues": [
                    {"text": "AI is already changing your life", "start_sec": 0, "end_sec": 2.5, "highlight_indices": [0]},
                ]
            },
            "sound_design": {
                "music_intensity_curve": [{"t": 0, "intensity": 0.3}],
                "events": [{"type": "whoosh", "scene_id": "s1"}],
            },
            "camera_plan": [
                {"scene_id": "s1", "motion": "slow_push"},
                {"scene_id": "s2", "motion": "macro_push"},
            ],
        },
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "AI is already changing your life — and most people don't realize it.",
                    "source_url": "https://commons.wikimedia.org/",
                    "license": "CC-BY-SA",
                    "confidence": 96,
                    "concepts": ["ai", "smartphone"],
                },
                {
                    "scene_id": "s2",
                    "narration": "Notice this tiny chip learning patterns from oceans of data.",
                    "source_url": "https://www.nasa.gov/",
                    "license": "NASA",
                    "confidence": 99,
                    "concepts": ["chip", "nasa"],
                },
                {
                    "scene_id": "s3",
                    "narration": "Factories track robot arms assembling with machine precision.",
                    "license": "CC-BY-SA",
                    "confidence": 94,
                    "concepts": ["robot"],
                },
                {
                    "scene_id": "s4",
                    "narration": "The surprising part: 1 billion people use AI features daily.",
                    "confidence": 95,
                    "concepts": ["statistic"],
                },
            ],
        },
    }


def test_engine_registered():
    engine = registry.get_engine("studio_render")
    assert engine is not None
    assert engine.is_ready()
    assert engine.version.startswith("3.")


def test_wired_into_workflows_and_orchestrator():
    assert "studio_render" in WORKFLOWS["intelligence"]
    assert "studio_render" in WORKFLOWS["full_content"]
    assert "studio_render" in WORKFLOWS["media_production"]
    intel = WORKFLOWS["intelligence"]
    assert intel.index("viewer_retention") < intel.index("studio_render")
    assert intel.index("studio_render") < intel.index("production_qa")
    assert "studio_render" in STAGE_ENGINES["assembly"]
    assert STAGE_ENGINES["assembly"].index("render_package") < STAGE_ENGINES["assembly"].index(
        "studio_render"
    )


def test_pqa_render_quality_category():
    assert "render_quality" in PQA_CATEGORIES
    assert "studio_render" in REVISION_OWNERS["render_quality"]


def test_transitions_context_not_generic_hard_cut():
    a = choose_transition("Suddenly the impact hits.")
    b = choose_transition("Suddenly the impact hits.")
    assert a == b
    assert a[0] == "whip_pan"
    transitions = build_transitions(_rich_candidate())
    assert transitions
    assert all(t["type"] != "hard_cut" for t in transitions)


def test_motion_graphics_follow_narration():
    graphics = build_motion_graphics(_rich_candidate())
    types = {g["type"] for g in graphics}
    assert "highlight_box" in types or "animated_arrow" in types
    assert "popup_statistic" in types


def test_color_profile_for_tech():
    assert choose_grade_profile(_rich_candidate()) == "technology"


def test_export_preset_shorts():
    assert choose_primary_preset(_rich_candidate()) == "youtube_shorts"


def test_package_reaches_98_and_improves():
    report = build_studio_render_package(_rich_candidate())
    data = report.to_dict()
    assert data["overall_score"] >= RENDER_QUALITY_THRESHOLD
    assert data["passed"] is True
    assert data["master_timeline"]["synchronized"] is True
    assert data["motion_graphics"]
    assert data["transitions"]
    assert data["color_grade"]["lut"]
    assert data["camera_choreography"]
    assert data["export_plan"]["primary"]
    assert data["improvements_vs_baseline"].get("overall", 0) > 0
    assert data["typography"]["style"] == "cinematic_kinetic"


def test_engine_run_attaches_package():
    engine = registry.get_engine("studio_render")
    result = engine.run({"candidates": [_rich_candidate()]})
    assert result["studio_render_summary"]["average_score"] >= 90
    cand = result["candidates"][0]
    assert cand["studio_render_package"]["version"] == "3.0.0"
    assert cand.get("master_timeline_v3")
