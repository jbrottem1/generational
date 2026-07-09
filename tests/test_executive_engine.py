"""Tests for the Executive Intelligence Engine (Agent 24, key: autonomous_executive)."""

from __future__ import annotations

import ast
from pathlib import Path

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from services.executive import EXECUTIVE_PACKAGE_FIELDS, EXECUTIVE_SUMMARY_FIELDS
from services.executive.memory import ExecutiveMemory
from services.executive.models import EXECUTIVE_DECISION_FIELDS
from services.executive.resources import ExecutiveResourceAllocator
from services.orchestrator import ContentPackage, Orchestrator, StageStatus
from services.orchestrator.models import PipelineResult


def make_opportunity(title="Deep Ocean Mystery", platform="youtube_shorts", priority=85):
    return {
        "title": title,
        "topic": "deep ocean",
        "platform": platform,
        "priority": priority,
        "roi_score": 78,
        "expected_views": 120_000,
        "retention_estimate": 62,
        "competition_score": 40,
        "opportunity_score": 82,
        "rationale": "High ROI with moderate competition",
    }


def make_item(project_id="proj1"):
    return {
        "project_id": project_id,
        "topic": "deep ocean",
        "title": "Ocean Mystery",
        "target_platforms": ["youtube_shorts"],
        "opportunity_score": 70,
        "quality_score": 75,
        "script_package": {"script": "test"},
        "director_package": {"format": "short_form"},
        "creative_package": {"storyboard": []},
    }


# ----------------------------------------------------------------- contract


def test_executive_is_a_live_contract_engine():
    engine = registry.get_engine("autonomous_executive")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "autonomous_executive"
    assert diag["version"] == "1.0.0"
    assert diag["input_contract"] == []
    assert "executive_summary" in diag["output_contract"]
    assert "executive_plan" in diag["output_contract"]
    assert "executive-intelligence" in diag["capabilities"]
    assert "company-os" in diag["capabilities"]
    assert engine.health_check()["healthy"] is True


# ----------------------------------------------------------- empty context


def test_run_with_empty_context_never_fails():
    updates = registry.get_engine("autonomous_executive").run({"command": "probe"})
    summary = updates["executive_summary"]
    for field in EXECUTIVE_SUMMARY_FIELDS:
        assert field in summary, field
    assert summary["status"] in ("no_context", "planned", "active")
    assert updates["executive_packages"] == [] or isinstance(updates["executive_packages"], list)


# ------------------------------------------------------ market opportunities


def test_market_opportunities_produce_scored_decisions():
    context = {"market_opportunities": [make_opportunity(), make_opportunity("Volcano Lightning", "tiktok", 70)]}
    updates = registry.get_engine("autonomous_executive").run(context)
    decisions = updates["executive_plan"]["decisions"]
    assert len(decisions) >= 2
    for decision in decisions:
        for field in EXECUTIVE_DECISION_FIELDS:
            assert field in decision, field
        assert decision["roi_score"] > 0
        assert decision["views_estimate"] > 0
        assert decision["retention_estimate"] > 0
        assert decision["cost_estimate"] > 0
        assert decision["revenue_estimate"] >= 0
        assert 0 <= decision["risk_score"] <= 100
        assert 0 <= decision["confidence"] <= 100
        assert 0 <= decision["priority"] <= 100


# -------------------------------------------------------- slot ownership


def test_executive_package_slot_on_unified_packages_other_slots_untouched():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in ("script_package", "director_package", "creative_package")
    }
    registry.get_engine("autonomous_executive").run({
        "unified_packages": [item],
        "market_opportunities": [make_opportunity()],
    })
    assert item["executive_package"]
    for field in EXECUTIVE_PACKAGE_FIELDS:
        assert field in item["executive_package"], field
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated"


def test_content_package_carries_executive_slot():
    package = ContentPackage(executive_package={"executive_package_version": "1.0"})
    data = package.to_dict()
    assert data["executive_package"] == {"executive_package_version": "1.0"}
    restored = ContentPackage.from_dict(data)
    assert restored.executive_package == {"executive_package_version": "1.0"}


# -------------------------------------------------------- engine discovery


def test_allocator_discovers_engines_via_describe_all():
    allocator = ExecutiveResourceAllocator()
    discovered = allocator.discover()
    assert len(discovered) == len(registry.engine_keys())
    assert any(info["engine_id"] == "autonomous_executive" for info in discovered)
    allocation = allocator.allocate({"executive_budget": 100}, [{"decision_id": "d1", "delegated_stage": "research"}])
    assert allocation["engines_discovered"] == len(discovered)
    assert allocation["engines_ready"] >= 1


# ------------------------------------------------------------- orchestrator


def test_orchestrator_run_executive_stage():
    context = {
        "command": "probe",
        "market_opportunities": [make_opportunity()],
    }
    report = Orchestrator().run_executive_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["executive_summary"]["decisions"] >= 1


# ------------------------------------------------------------------- hook


def test_executive_hook_attaches_and_on_pipeline_complete_does_not_crash():
    from services.executive.hook import attach_executive_hook, detach_executive_hook

    attached = attach_executive_hook()
    assert "agent24-executive" in attached["hooks"]
    try:
        result = PipelineResult(
            status=StageStatus.SUCCESS,
            context={"market_opportunities": [make_opportunity()]},
            packages=[],
            stage_reports=[],
            production_report={},
        )
        from services.orchestrator.hooks import notify_hooks

        notify_hooks(result)
        assert result.context.get("executive_summary")
    finally:
        detach_executive_hook()


# -------------------------------------------------------------- memory


def test_executive_memory_persists_in_temp_dir(tmp_path):
    memory = ExecutiveMemory(directory=str(tmp_path))
    entry = memory.remember("test", {"key": "value"})
    assert entry["entry_id"]
    assert memory.count() == 1
    memory.snapshot("plan", {"decisions": 3})
    assert memory.load_snapshot("plan")["decisions"] == 3

    memory2 = ExecutiveMemory(directory=str(tmp_path))
    assert memory2.count() == 1
    assert memory2.load_snapshot("plan")["decisions"] == 3


# ---------------------------------------------------------- architecture


def test_executive_module_does_not_import_peer_engines():
    """services/executive must not import engines.* except lazy registry in resources."""
    exec_dir = Path(__file__).resolve().parent.parent / "services" / "executive"
    violations = []
    allowed_patterns = {"engines.registry"}

    for file in sorted(exec_dir.glob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for mod in modules:
                if mod.startswith("engines.") and mod not in allowed_patterns:
                    if file.name == "resources.py" and mod == "engines.registry":
                        continue
                    violations.append(f"{file.name} imports {mod}")
                if mod == "engines" and file.name != "resources.py":
                    violations.append(f"{file.name} imports engines")

    assert not violations, "Executive module must not import peer engines:\n  " + "\n  ".join(violations)
