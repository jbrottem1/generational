"""Tests for the Agents 6-10 shared integration foundation.

Proves: future engines can register through the contract interface, missing
engines never crash the pipeline, the canonical ContentPackage carries the
render/seo/publishing/analytics/brand fields, and the orchestrator skips
unimplemented future stages cleanly.
"""

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine, FutureEngine
from services.orchestrator import (
    CONTENT_PACKAGE_FIELDS,
    ContentPackage,
    Orchestrator,
    ProductionPackage,
    StageStatus,
)
from services.orchestrator.stages import STAGE_GROUPS


# ---------------------------------------------------------------- contracts


def test_future_stage_stubs_registered_with_contracts():
    # seo_optimization graduated to a live engine (Agent 8) — covered in
    # tests/test_seo_optimization.py.
    for key in ("scheduler", "brand_management"):
        engine = registry.get_engine(key)
        assert isinstance(engine, ContractEngine), key
        assert engine.is_ready() is False, key
        diag = engine.diagnostics()
        assert diag["engine_id"] == key
        assert diag["version"]
        assert isinstance(diag["input_contract"], list)
        assert isinstance(diag["output_contract"], list)
        assert isinstance(diag["dependencies"], list)
        assert isinstance(diag["capabilities"], list)
        assert engine.health_check() == {"engine_id": key, "healthy": True, "ready": False}


def test_future_engine_stub_returns_not_implemented():
    result = registry.get_engine("brand_management").run({})
    assert result == {"brand_management_status": "NOT_IMPLEMENTED"}


def test_contract_engine_validation_reports_problems_without_crashing():
    class DemoContract(ContractEngine):
        key = "demo_contract"
        label = "Demo Contract"
        input_contract = ["ideas"]
        output_contract = ["demo_output"]

        def run(self, context):
            return {"demo_output": True}

    engine = DemoContract()
    assert engine.validate_input({}) == ["missing required context key: ideas"]
    assert engine.validate_input({"ideas": []}) == []
    assert engine.validate_output({}) == ["missing promised output key: demo_output"]
    assert engine.validate_output(engine.run({"ideas": []})) == []


def test_new_contract_engine_can_register_and_replace_stub():
    class LiveBrandEngine(FutureEngine):
        key = "brand_management"
        label = "Live Brand Management"

        def is_ready(self):
            return True

        def run(self, context):
            return {"brand_strategy_update": {"cadence": "daily"}}

    original = registry.get_engine("brand_management")
    try:
        registry.register(LiveBrandEngine())
        assert registry.get_engine("brand_management").is_ready() is True
        assert registry.get_engine("brand_management").run({}) == {
            "brand_strategy_update": {"cadence": "daily"}
        }
    finally:
        registry.register(original)


# ---------------------------------------------------------- content package


def test_content_package_is_the_production_package():
    assert ContentPackage is ProductionPackage


def test_content_package_accepts_agents_6_to_10_fields():
    package = ContentPackage(
        brand_id="brand-1",
        channel_id="chan-1",
        target_platforms=["youtube_shorts", "tiktok"],
        target_language="es",
        topic="octopus intelligence",
        keywords=["octopus", "intelligence"],
        opportunity_score=88,
        virality_score=74,
        script_package={"script": "..."},
        visual_package={"scenes": []},
        audio_package={"voice": "demo"},
        render_package={"file": "out.mp4"},
        publishing_package={"platform_post_id": "abc"},
        analytics_package={"views": 0},
        learning_metadata={"signals": []},
        status="rendered",
        diagnostics={"gate_failures": []},
    )
    data = package.to_dict()
    for field_name in CONTENT_PACKAGE_FIELDS:
        assert field_name in data, field_name
    assert ContentPackage.from_dict(data).render_package == {"file": "out.mp4"}


def test_content_package_roundtrip_preserves_unknown_fields_in_extras():
    data = ContentPackage().to_dict()
    data["future_field_from_agent_11"] = {"x": 1}
    restored = ContentPackage.from_dict(data)
    assert restored.extras["future_field_from_agent_11"] == {"x": 1}


# ------------------------------------------------------------- orchestrator


def test_orchestrator_knows_all_future_stages():
    for stage in ("render", "seo", "publish", "analytics", "learning", "brand_management"):
        assert stage in STAGE_GROUPS, stage


def test_unimplemented_future_stages_skip_cleanly():
    orch = Orchestrator()
    context = {"command": "test", "provider": "demo"}
    for runner in (
        orch.run_publish_stage,
        orch.run_analytics_stage,
        orch.run_learning_stage,
        orch.run_brand_stage,
    ):
        report = runner(dict(context))
        assert report.status in (StageStatus.WARNING, StageStatus.SKIPPED), report.stage
        assert report.status != StageStatus.FAILED
        assert not report.errors
        assert report.diagnostics  # explains why the stage did no work


def test_render_stage_is_implemented_and_safe_without_input():
    # Agent 6 landed: the render stage runs (SUCCESS) and degrades to a
    # SKIPPED summary instead of a warning when there is nothing to render.
    report = Orchestrator().run_render_stage({"command": "test", "provider": "demo"})
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert report.diagnostics


def test_seo_stage_is_implemented_and_safe_without_input():
    # Agent 8 landed: the seo stage runs (SUCCESS) and reports zero items
    # instead of warning when there is nothing to optimize.
    context = {"command": "test", "provider": "demo"}
    report = Orchestrator().run_seo_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["seo_optimization_report"]["items"] == 0
    assert context["publishing_packages"] == []


def test_missing_engine_key_does_not_crash_stage():
    orch = Orchestrator()
    report = orch.run_stage("brand_management", {"command": "test", "provider": "demo"})
    assert report.status != StageStatus.FAILED
    assert not report.errors
