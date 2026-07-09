"""Integration tests for the orchestration layer — command in, ProductionPackage out.

All tests run in Demo Mode (deterministic heuristics, no API key needed).
"""

import pytest

from engines import registry
from engines.base import Engine
from services.orchestrator import (
    PRODUCTION_PACKAGE_FIELDS,
    OrchestratorHook,
    Orchestrator,
    ProductionPackage,
    StageStatus,
    attach_hook,
    detach_hook,
    get_orchestrator,
    pipeline_stage_names,
    register_stage,
    unregister_stage,
)

COMMAND = "Create 3 science shorts about black holes"


@pytest.fixture(scope="module")
def pipeline_result():
    """One full end-to-end run shared by the read-only assertions below."""
    return get_orchestrator().run_full_pipeline(COMMAND, threshold=0)


# ------------------------------------------------------------ full pipeline

def test_full_pipeline_succeeds_end_to_end(pipeline_result):
    assert pipeline_result.succeeded, pipeline_result.error
    assert pipeline_result.status in (StageStatus.SUCCESS, StageStatus.WARNING)


def test_full_pipeline_produces_production_packages(pipeline_result):
    assert pipeline_result.packages
    for pkg in pipeline_result.packages:
        assert isinstance(pkg, ProductionPackage)
        data = pkg.to_dict()
        for field in PRODUCTION_PACKAGE_FIELDS:
            assert field in data, f"missing contract field: {field}"
        assert pkg.hook
        assert pkg.script
        assert pkg.scene_breakdown
        assert pkg.visual_assets["image_prompts"]
        assert pkg.voice_assets["narration_plan"]
        assert pkg.music_assets
        assert pkg.seo_package["title"]
        assert 0 <= pkg.quality_score <= 100
    assert any(pkg.publish_ready for pkg in pipeline_result.packages)


def test_every_stage_reports_diagnostics(pipeline_result):
    reported = [report.stage for report in pipeline_result.stage_reports]
    assert reported == pipeline_stage_names() + ["production", "packaging"]
    # The named stages the OS contract promises are all present.
    for stage in ("trend", "research", "psychology", "script", "visual", "audio", "quality"):
        assert stage in reported
    for report in pipeline_result.stage_reports:
        assert report.status in (StageStatus.SUCCESS, StageStatus.WARNING)
        assert report.started_at and report.finished_at
        assert report.duration_ms >= 0
        assert 0 <= report.confidence <= 100
        assert not report.errors


def test_pipeline_steps_exposed_for_dashboard(pipeline_result):
    steps = pipeline_result.context.get("pipeline_steps", [])
    engines_run = [step["engine"] for step in steps]
    assert engines_run[0] == "trend_discovery"
    assert "quality" in engines_run


# --------------------------------------------------------- package contract

def test_package_dict_round_trip():
    pkg = ProductionPackage(hook="h", script="s", trend_score=80, publish_ready=True)
    pkg.extras["title"] = "T"
    restored = ProductionPackage.from_dict(pkg.to_dict())
    assert restored.to_dict() == pkg.to_dict()


def test_future_fields_are_additive_and_survive():
    data = ProductionPackage(hook="h").to_dict()
    data["render_manifest"] = {"engine": "future"}  # field added by a future engine
    restored = ProductionPackage.from_dict(data)
    assert restored.to_dict()["render_manifest"] == {"engine": "future"}
    for field in PRODUCTION_PACKAGE_FIELDS:
        assert field in restored.to_dict()


# ------------------------------------------------------------ stage runners

def test_named_stage_runner_runs_trend_stage():
    orch = Orchestrator()
    context = {"command": COMMAND}
    report = orch.run_trend_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert context["trends"]
    assert context["trend_opportunities"]


def test_render_and_publish_stages_are_live_and_safe_without_input():
    orch = Orchestrator()
    context = {"command": COMMAND}
    render = orch.run_render_stage(context)
    publish_context = {"command": COMMAND}
    publish = orch.run_publish_stage(publish_context)
    # Render (Agent 6) is live: no ideas in context → safe SKIPPED summary.
    assert render.status == StageStatus.SUCCESS
    assert context["render_summary"]["status"] == "SKIPPED"
    # Publishing (Agent 7) is live: nothing to publish → safe SKIPPED result.
    assert publish.status == StageStatus.SUCCESS
    assert publish_context["publishing_result"]["status"] == "SKIPPED"
    assert not render.errors and not publish.errors


# ------------------------------------------------------------ error handling

class _ExplodingEngine(Engine):
    key = "exploding_test_engine"
    label = "Exploding"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        raise RuntimeError("engine exploded")


def test_failing_stage_reports_failed_with_diagnostics():
    registry.register(_ExplodingEngine())
    register_stage("exploding_stage", ["exploding_test_engine"])
    try:
        report = Orchestrator().run_stage("exploding_stage", {"command": COMMAND})
        assert report.status == StageStatus.FAILED
        assert "engine exploded" in report.errors[0]
    finally:
        unregister_stage("exploding_stage")


def test_pipeline_stops_gracefully_on_stage_failure(monkeypatch):
    registry.register(_ExplodingEngine())
    monkeypatch.setattr(
        "services.orchestrator.orchestrator.build_pipeline_plan",
        lambda: [("trend", ["trend_discovery", "opportunity_ranking"]),
                 ("exploding_stage", ["exploding_test_engine"])],
    )
    result = Orchestrator().run_full_pipeline(COMMAND)
    assert result.status == StageStatus.FAILED
    assert result.error
    assert not result.packages
    # The trend stage completed before the stop — partial results preserved.
    assert result.stage_reports[0].status == StageStatus.SUCCESS
    assert result.context.get("trends")


def test_unknown_stage_fails_without_crashing():
    report = Orchestrator().run_stage("no_such_stage", {})
    assert report.status == StageStatus.FAILED


# -------------------------------------------------------------- plugins/hooks

def test_register_stage_schedules_into_full_pipeline():
    register_stage("plugin_test_stage", ["quality"], after="quality")
    try:
        names = pipeline_stage_names()
        assert "plugin_test_stage" in names
        assert names.index("plugin_test_stage") == names.index("quality") + 1
    finally:
        unregister_stage("plugin_test_stage")
        assert "plugin_test_stage" not in pipeline_stage_names()


class _RecordingHook(OrchestratorHook):
    kind = "analytics"
    name = "recording"

    def __init__(self):
        self.results = []

    def on_pipeline_complete(self, result):
        self.results.append(result)


def test_hooks_notified_on_pipeline_completion(monkeypatch):
    # Short (failing) pipeline keeps this test fast; hooks fire either way.
    registry.register(_ExplodingEngine())
    monkeypatch.setattr(
        "services.orchestrator.orchestrator.build_pipeline_plan",
        lambda: [("exploding_stage", ["exploding_test_engine"])],
    )
    hook = _RecordingHook()
    attach_hook(hook)
    try:
        Orchestrator().run_full_pipeline(COMMAND)
        assert len(hook.results) == 1
        assert hook.results[0].status == StageStatus.FAILED
    finally:
        detach_hook(hook)


# ------------------------------------------------------------ UI service seam

def test_ideation_service_returns_orchestrated_result(monkeypatch, tmp_path):
    from services import ideation, knowledge

    monkeypatch.setattr(
        knowledge, "get_knowledge_base",
        lambda: knowledge.KnowledgeBase(directory=str(tmp_path / "kb")),
    )
    result = ideation.run_command(COMMAND, count=5, model="gpt-4o-mini", threshold=0)
    assert result["ideas"]
    assert result["pipeline_steps"]
    assert result["quality_summary"]
    assert result["unified_packages"]
    assert result["stage_reports"]
    for pkg in result["unified_packages"]:
        for field in PRODUCTION_PACKAGE_FIELDS:
            assert field in pkg
