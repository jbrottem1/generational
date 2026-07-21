"""Tests for Continuous Learning & Self-Improvement Engine."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.learning import (
    PRODUCTION_RECORD_FIELDS,
    build_learning_brief,
    build_learning_dashboard,
    consult_context,
    for_discovery,
    for_psychology,
    for_script,
    get_knowledge_graph,
    get_optimization_api,
    get_production_memory,
    predict_performance,
    record_productions_from_context,
)
from services.learning.experiments import EXPERIMENT_KINDS


def test_production_memory_records_all_fields(tmp_path, monkeypatch):
    import services.learning.productions as productions

    monkeypatch.setattr(productions, "_DEFAULT_DIR", str(tmp_path))
    memory = get_production_memory(str(tmp_path))
    ctx = {
        "subject": "infrared cameras",
        "target_platform": "youtube_shorts",
        "target_runtime_sec": 60,
        "selected_ideas": [
            {
                "id": "idea1",
                "title": "Why cameras see infrared",
                "script": "Infrared light is invisible…",
                "psychology_score": 88,
                "seo_score": 90,
                "visual_score": 92,
                "pqa_score": 94,
                "pqa_decision": "APPROVE",
                "human_attention_score": 91,
            }
        ],
    }
    saved = record_productions_from_context(ctx, pipeline_used="executive", run_id="run1")
    assert len(saved) == 1
    row = saved[0]
    for field in PRODUCTION_RECORD_FIELDS:
        assert field in row
    assert memory.count() == 1
    similar = memory.find_similar("infrared")
    assert similar


def test_knowledge_graph_expands(tmp_path, monkeypatch):
    import services.learning.graph as graph_mod

    monkeypatch.setattr(graph_mod, "_DEFAULT_DIR", str(tmp_path))
    g = get_knowledge_graph(str(tmp_path))
    g.expand_from_production(
        {"topic": "black holes", "platform": "youtube", "visual_score": 95, "psychology_score": 90, "animation_score": 88}
    )
    snap = g.snapshot()
    assert snap["node_count"] >= 2
    assert snap["edge_count"] >= 1


def test_consult_before_script():
    brief = build_learning_brief("black holes", platform="youtube", runtime_sec=720)
    assert "suggested_improvements" in brief
    assert "predictions" in brief
    assert "engine_guidance" in brief
    ctx = consult_context("black holes", platform="youtube", runtime_sec=720)
    assert ctx["learning_consulted"] is True
    assert "learning_recommendations" in ctx
    assert "learning_predictions" in ctx


def test_predictions_have_confidence_intervals():
    pred = predict_performance(topic="infrared", platform="youtube_shorts", runtime_sec=60, qa_score=95)
    assert "expected_views" in pred
    assert "expected_ctr" in pred
    assert "expected_virality_score" in pred
    assert "confidence_intervals" in pred
    assert pred["confidence"] >= 25


def test_self_optimization_api():
    api = get_optimization_api()
    assert "winning_hooks" in api.for_script("seasons")
    assert "preferred_strategies" in for_psychology("seasons")
    assert "question" in for_script("seasons")
    assert "top_niches" in for_discovery()


def test_experiment_kinds_cover_mission():
    for kind in ("hook", "thumbnail", "camera_movement", "visual_pacing", "intro_duration"):
        assert kind in EXPERIMENT_KINDS


def test_learning_dashboard_shape():
    dash = build_learning_dashboard()
    for key in (
        "top_performing_topics",
        "highest_ctr",
        "best_hooks",
        "suggested_improvements",
        "viral_opportunity_queue",
        "knowledge_graph",
    ):
        assert key in dash


def test_continuous_learning_engine():
    engine = registry.get_engine("continuous_learning")
    assert engine is not None
    out = engine.run({"subject": "coral reefs", "target_platform": "tiktok", "target_runtime_sec": 45})
    assert out.get("learning_consulted") is True
    assert out.get("learning_brief")


def test_workflow_has_continuous_learning_before_script():
    steps = WORKFLOWS["intelligence"]
    assert steps.index("research") < steps.index("continuous_learning") < steps.index("psychology")
    assert steps.index("continuous_learning") < steps.index("script_generation")


def test_learning_engine_records_productions(tmp_path, monkeypatch):
    import services.analytics.store as analytics_store
    import services.learning.productions as productions
    import services.learning.graph as graph_mod

    monkeypatch.setattr(analytics_store, "_DEFAULT_DIR", str(tmp_path / "a"))
    monkeypatch.setattr(productions, "_DEFAULT_DIR", str(tmp_path / "p"))
    monkeypatch.setattr(graph_mod, "_DEFAULT_DIR", str(tmp_path / "g"))

    engine = registry.get_engine("learning")
    ctx = {
        "selected_ideas": [
            {"id": "x1", "title": "Tides", "hook": "Why do tides rise?", "psychology_score": 80, "pqa_score": 88}
        ],
        "analytics_summary": {"records": 0},
    }
    out = engine.run(ctx)
    assert "learning_report" in out
    assert out["learning_report"].get("productions_recorded", 0) >= 1
