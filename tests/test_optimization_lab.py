"""Tests for Autonomous Optimization & Experimentation Engine V4.0."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.executive_orchestrator.stages import STAGE_ENGINES
from services.optimization_lab import (
    OPTIMIZATION_PASS_THRESHOLD,
    build_optimization_package,
    generate_variants,
)
from services.optimization_lab.continuous import measurable_improvement_signal
from services.production_qa.models import PQA_CATEGORIES, REVISION_OWNERS


def _candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "platform": "youtube_shorts",
        "hook": "AI is already changing your life.",
        "psychology": {
            "viral_score": 82,
            "dimensions": {
                "first_3_second_hook": 80,
                "curiosity_gap": 84,
                "retention_potential": 78,
                "share_likelihood": 72,
            },
        },
        "viewer_retention_package": {
            "overall_score": 96,
            "quality_scores": {"retention": 95, "narration": 94},
            "passed": True,
        },
        "studio_render_package": {"overall_score": 97, "passed": True},
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {"scene_id": "s1", "narration": "AI is already changing your life."},
                {"scene_id": "s2", "narration": "Notice this tiny chip learning patterns."},
                {"scene_id": "s3", "narration": "Factories track robot arms."},
                {"scene_id": "s4", "narration": "One billion people use AI daily."},
            ],
        },
    }


def test_engine_graduated_and_ready():
    engine = registry.get_engine("optimization_lab")
    assert engine is not None
    assert engine.is_ready()
    assert engine.version.startswith("4.")


def test_wired_into_workflows_and_orchestrator():
    assert "optimization_lab" in WORKFLOWS["intelligence"]
    assert "optimization_lab" in WORKFLOWS["full_content"]
    assert "optimization_lab" in WORKFLOWS["media_production"]
    intel = WORKFLOWS["intelligence"]
    assert intel.index("studio_render") < intel.index("optimization_lab")
    assert intel.index("optimization_lab") < intel.index("production_qa")
    assert "optimization_lab" in STAGE_ENGINES["export"]


def test_pqa_optimization_category():
    assert "optimization" in PQA_CATEGORIES
    assert "optimization_lab" in REVISION_OWNERS["optimization"]


def test_generates_five_variants_with_axis_differences():
    variants = generate_variants(_candidate(), count=5)
    assert len(variants) == 5
    labels = [v["label"] for v in variants]
    assert labels == ["A", "B", "C", "D", "E"]
    hooks = {v["axes"]["hook"] for v in variants}
    titles = {v["axes"]["title"] for v in variants}
    assert len(hooks) >= 2
    assert len(titles) >= 2


def test_package_picks_winner_revises_and_improves():
    package, updated = build_optimization_package(
        _candidate(),
        variant_count=5,
        record_history=True,
    )
    data = package.to_dict()
    assert len(data["variants"]) == 5
    assert data["leaderboard"][0]["rank"] == 1
    assert data["winner"]["label"]
    assert data["overall_score"] >= OPTIMIZATION_PASS_THRESHOLD
    assert data["passed"] is True
    assert data["predictions"]["ctr_pct"] > 0
    assert data["human_review"]["recommended_winner"]
    assert data["experiment_id"]
    assert updated.get("optimized_hook") or updated.get("hook")
    assert data["improvements_vs_baseline"].get("overall", 0) >= 0


def test_engine_run_attaches_package():
    engine = registry.get_engine("optimization_lab")
    result = engine.run({"candidates": [_candidate()]})
    assert result["optimization_summary"]["average_score"] >= 90
    assert result["optimization_report"]["runs"]
    assert result["candidates"][0]["optimization_package"]["version"] == "4.0.0"


def test_continuous_improvement_signal_api():
    # After recording at least one experiment above, signal API should return a dict
    signal = measurable_improvement_signal()
    assert "improving" in signal
    assert "delta" in signal
