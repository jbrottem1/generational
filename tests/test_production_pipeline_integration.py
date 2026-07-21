"""Tests for Production Pipeline Integration Layer."""

from __future__ import annotations

import json
from pathlib import Path

import engines  # noqa: F401
from engines import registry
from core.workflows import WORKFLOWS
from services.production_pipeline import (
    PRODUCTION_STAGES,
    STAGE_KEYS,
    flat_engine_order,
    run_production_pipeline,
    stage_contract_table,
    sync_candidate_aliases,
    verify_agents,
)
from services.production_pipeline.bridges import bridge_before_stage, prepare_approved_content


def test_ten_stages_in_order():
    assert STAGE_KEYS == (
        "research",
        "psychology",
        "studio_director",
        "script_generator",
        "scene_builder",
        "media_generation",
        "voice_generation",
        "video_assembly",
        "quality_control",
        "export",
    )
    assert len(PRODUCTION_STAGES) == 10


def test_contracts_declared_for_every_stage():
    table = stage_contract_table()
    assert len(table) == 10
    for row in table:
        assert row["engines"]
        assert row["inputs"]
        assert row["outputs"]


def test_agent_verification():
    report = verify_agents()
    assert "stages" in report
    assert report["engine_order"] == flat_engine_order()
    # Core engines used by the conceptual pipeline must be registered
    required = {"research", "psychology", "ai_director", "script_generation", "scene_planning"}
    registered = set()
    for stage in report["stages"]:
        for eng in stage["engines"]:
            if eng["registered"]:
                registered.add(eng["key"])
    assert required.issubset(registered)


def test_workflow_registered():
    assert "production_pipeline" in WORKFLOWS
    steps = WORKFLOWS["production_pipeline"]
    assert steps.index("research") < steps.index("psychology")
    assert steps.index("psychology") < steps.index("ai_director")
    assert steps.index("ai_director") < steps.index("script_generation")
    assert steps.index("script_generation") < steps.index("scene_planning")
    assert steps.index("quality") < steps.index("production_qa")


def test_engine_registered():
    engine = registry.get_engine("production_pipeline")
    assert engine is not None
    assert engine.is_ready()
    assert engine.version.startswith("1.")
    assert "pipeline-integration" in engine.capabilities


def test_bridges_sync_and_approved_content():
    ctx = {
        "candidates": [
            {
                "title": "AI Explained",
                "topic": "AI",
                "script": "AI is software that learns from data.",
                "psychology": {"viral_score": 80},
            }
        ]
    }
    synced = sync_candidate_aliases(ctx)
    assert synced["ideas"]
    assert synced["selected_ideas"]
    assert synced["unified_packages"]
    prepared = prepare_approved_content(synced)
    assert prepared["approved_content"]
    assert prepared["approved_content"][0]["script"]


def test_bridge_before_each_stage_is_safe():
    ctx = {"command": "deep ocean mysteries", "subject": "deep ocean"}
    for key in STAGE_KEYS:
        ctx = bridge_before_stage(key, ctx)
        assert isinstance(ctx, dict)


def test_end_to_end_writes_pipeline_status(tmp_path, monkeypatch):
    # Keep artifacts under validation folder for predictability when possible;
    # status writer uses data/productions/{id}/ which is fine.
    result = run_production_pipeline(
        "Artificial Intelligence explained in 60 seconds",
        production_id="pipeline_integration_test",
        platform="youtube_shorts",
        stop_on_failure=False,
    )
    assert result["production_id"] == "pipeline_integration_test"
    path = Path(result["status_path"])
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["current_stage"] or payload["overall_status"]
    assert "elapsed_ms" in payload
    assert "validation_score" in payload
    assert "output_location" in payload
    assert len(payload["stages"]) == 10
    for stage in payload["stages"]:
        assert "status" in stage
        assert "validation_score" in stage
        assert "output_location" in stage or stage["status"] in ("pending", "skipped")
    # Research + psychology + director should normally advance
    keys_done = {s["key"] for s in payload["stages"] if s["status"] in ("succeeded", "failed", "skipped")}
    assert "research" in keys_done
    assert result.get("agent_verification")
