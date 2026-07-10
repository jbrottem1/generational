"""Tests for master production pipeline registry, contracts, and readiness."""

from __future__ import annotations

from services.master_pipeline import (
    contract_audit,
    live_agent_registry,
    master_pipeline_map,
    normalize_content_package,
    production_readiness_report,
    registry_summary,
    resolve_production_type,
    run_production_qc,
)


def test_live_agent_registry_covers_agents_1_to_23():
    agents = live_agent_registry()
    numbers = {a["agent"] for a in agents}
    assert numbers >= set(range(1, 24)) - {0}
    assert 1 in numbers and 21 in numbers and 23 in numbers


def test_master_pipeline_map_non_empty():
    stages = master_pipeline_map()
    assert len(stages) >= 20
    assert stages[0]["orch_stage"] == "trend"
    assert any(s["orch_stage"] == "publish" for s in stages)


def test_resolve_production_type_short_and_long():
    assert resolve_production_type(platform="youtube_shorts", duration_sec=60) == "youtube_short"
    assert resolve_production_type(platform="tiktok", duration_sec=30) == "youtube_short"
    assert resolve_production_type(platform="youtube_long", duration_sec=600) == "longform"
    assert resolve_production_type(platform="documentary", duration_sec=1800) == "documentary"
    assert resolve_production_type(duration_sec=3600) == "longform"


def test_normalize_and_audit_packages():
    pkg = normalize_content_package({"hook": "H", "script_package": {"full_script": "S"}})
    assert "visual_package" in pkg
    assert pkg["script"] == "S"
    audit = contract_audit(pkg)
    assert "script_package" in audit["slots_present"]
    assert audit["completeness"] >= 0


def test_qc_passes_dry_run_shape():
    result = {
        "ideas": [{"title": "T", "script": "Hello world script", "visual_prompts": ["v"]}],
        "stage_reports": [{"stage": "research", "status": "SUCCESS"}],
        "unified_packages": [{"render_package": {"status": "mock", "uri": "mock://x"}}],
        "workflow_run_id": "run_test",
    }
    qc = run_production_qc(result, {"unified_packages": result["unified_packages"]})
    assert qc["passed"] is True
    assert qc["mock_render"] is True


def test_readiness_report_structure():
    report = production_readiness_report()
    assert "score" in report
    assert "band" in report
    assert "providers" in report
    assert "blockers" in report
    assert "next_priorities" in report
    summary = registry_summary()
    assert summary["engine_count"] >= 30
