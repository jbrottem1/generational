"""Tests for Viewer Retention & Cinematic Excellence Engine V2.0."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.executive_orchestrator.stages import STAGE_ENGINES
from services.production_qa.models import PQA_CATEGORIES, REVISION_OWNERS
from services.viewer_retention import (
    EXCELLENCE_PASS_THRESHOLD,
    build_excellence_package,
    choose_cinematic_motion,
    generate_hook_candidates_v2,
    select_best_hook,
)
from services.viewer_retention.pacing import build_pacing_plan, pacing_variety_score
from services.viewer_retention.retention import simulate_retention


def _rich_candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "hook": "AI is already changing your life.",
        "psychology": {
            "viral_score": 78,
            "dimensions": {
                "first_3_second_hook": 72,
                "curiosity_gap": 80,
                "retention_potential": 75,
                "emotional_intensity": 70,
                "information_density": 82,
                "share_likelihood": 68,
            },
        },
        "script_retention": {"retention_score": 62},
        "research": {"statistics": ["Over 1 billion people use AI features every day."]},
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "Artificial Intelligence is already changing your life — and most people don't even realize it.",
                    "expected_attention_score": 78,
                    "source_url": "https://commons.wikimedia.org/wiki/File:Integrated_circuit.jpg",
                    "license": "CC-BY-SA",
                    "confidence": 96,
                    "concepts": ["chip", "ai"],
                },
                {
                    "scene_id": "s2",
                    "narration": "Notice this tiny chip — it learns patterns from oceans of data.",
                    "expected_attention_score": 74,
                    "source_url": "https://www.nasa.gov/",
                    "license": "NASA",
                    "confidence": 98,
                    "concepts": ["nasa", "data"],
                },
                {
                    "scene_id": "s3",
                    "narration": "Factories track robot arms that assemble with machine precision.",
                    "expected_attention_score": 70,
                    "source_url": "https://commons.wikimedia.org/",
                    "license": "CC-BY-SA",
                    "confidence": 94,
                    "concepts": ["robot", "factory"],
                },
                {
                    "scene_id": "s4",
                    "narration": "Language models train on supercomputers and rewrite how we write.",
                    "expected_attention_score": 72,
                    "confidence": 93,
                    "concepts": ["supercomputer"],
                },
                {
                    "scene_id": "s5",
                    "narration": "The surprising part: the ideas behind AI are older than you think.",
                    "expected_attention_score": 80,
                    "confidence": 95,
                    "concepts": ["history"],
                },
            ],
        },
        "cinematography_plan": {
            "scenes": [
                {"scene_id": "s1", "movement": "slow_push_in", "reason": "Hook push"},
                {"scene_id": "s2", "movement": "macro_push_in", "reason": "Detail"},
            ],
            "overall_attention_score": 88,
        },
        "cinematography_attention_score": 88,
        "seo": {"title": "AI Explained in 60 Seconds", "tags": ["ai", "shorts", "education"], "score": 90},
    }


def test_engine_registered_and_ready():
    engine = registry.get_engine("viewer_retention")
    assert engine is not None
    assert engine.is_ready()
    assert engine.version.startswith("2.")


def test_wired_into_workflows_and_orchestrator():
    assert "viewer_retention" in WORKFLOWS["intelligence"]
    assert "viewer_retention" in WORKFLOWS["full_content"]
    intel = WORKFLOWS["intelligence"]
    assert intel.index("cinematography") < intel.index("viewer_retention")
    assert intel.index("viewer_retention") < intel.index("voice_audio")
    assert "viewer_retention" in STAGE_ENGINES["animation"]
    assert STAGE_ENGINES["animation"].index("cinematography") < STAGE_ENGINES["animation"].index(
        "viewer_retention"
    )


def test_pqa_retention_category_and_revision_owners():
    assert "retention" in PQA_CATEGORIES
    assert "viewer_retention" in REVISION_OWNERS["retention"]
    assert "viewer_retention" in REVISION_OWNERS["cinematography"]


def test_hook_engine_generates_at_least_five_and_picks_best():
    hooks = generate_hook_candidates_v2(_rich_candidate())
    assert len(hooks) >= 5
    ranked = select_best_hook(_rich_candidate())
    assert ranked["count"] >= 5
    assert ranked["selected"]["score"] >= ranked["candidates"][1]["score"]
    assert ranked["selected"]["text"]


def test_camera_motion_matches_narration_not_random():
    a = choose_cinematic_motion("Notice this tiny chip on the board.")
    b = choose_cinematic_motion("Notice this tiny chip on the board.")
    assert a == b
    assert a[0] == "macro_push"
    orbit, _ = choose_cinematic_motion("The Earth tilts and orbits the Sun.")
    assert orbit == "orbit"


def test_pacing_varies_and_avoids_long_static():
    plan = build_pacing_plan(_rich_candidate())
    assert len(plan) >= 4
    assert all(p.duration_sec <= 6.0 or p.pacing_label == "dramatic_pause" for p in plan)
    assert pacing_variety_score(plan) >= 50


def test_excellence_improves_over_baseline_and_targets_98():
    candidate = _rich_candidate()
    baseline_overall = 58  # typical pre-V2 floor from excellence._baseline_scores
    report = build_excellence_package(candidate)
    data = report.to_dict()
    assert data["overall_score"] >= baseline_overall
    assert data["quality_scores"]["hook"] > 58
    assert data["quality_scores"]["retention"] > 55
    assert len(data["hook_candidates"]) >= 5
    assert data["predictions"]["completion_rate_pct"] > 0
    # Strong fixture should reach excellence bar after polish
    assert data["overall_score"] >= EXCELLENCE_PASS_THRESHOLD
    assert data["passed"] is True
    # Measurable improvement vs baseline
    assert data["improvements_vs_baseline"].get("overall", 0) > 0 or data["overall_score"] > 90


def test_retention_simulation_checkpoints():
    candidate = _rich_candidate()
    hook = select_best_hook(candidate)
    pacing = build_pacing_plan(candidate)
    sim = simulate_retention(
        duration_sec=60,
        hook=hook,
        pacing=pacing,
        narration_score=90,
        visual_score=90,
        psychology=candidate["psychology"]["dimensions"],
    )
    labels = [c["label"] for c in sim["checkpoints"]]
    assert labels == ["3s", "10s", "20s", "40s", "ending"]
    # Survival should generally decline or hold
    probs = [c["retention_probability"] for c in sim["checkpoints"]]
    assert probs[0] >= probs[-1]


def test_engine_run_attaches_package():
    engine = registry.get_engine("viewer_retention")
    result = engine.run({"candidates": [_rich_candidate()], "subject": "AI"})
    assert result["viewer_retention_summary"]["average_score"] >= 90
    cand = result["candidates"][0]
    assert cand["viewer_retention_package"]["version"] == "2.0.0"
    assert cand.get("v2_selected_hook") or cand.get("hook")
