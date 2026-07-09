"""Integration tests for the complete Generational production pipeline.

Agent 9's contract: ONE public entry point (`run_full_pipeline`) executes
every completed engine — Trend Discovery → Psychology → Script → Visual →
Voice & Audio → Render → Global Content Optimization → Publishing — and
returns one Production Report. Every stage is validated, diagnostics are
produced, unavailable engines degrade to warnings, and nothing ever crashes.

All tests run in Demo Mode (deterministic heuristics, no API key needed).
"""

import pytest

from engines import registry
from services.orchestrator import (
    PRODUCTION_REPORT_VERSION,
    Orchestrator,
    ProductionPackage,
    StageStatus,
    build_production_report,
    distribution_stage_names,
    get_orchestrator,
    pipeline_stage_names,
    run_full_pipeline,
)
from services.orchestrator.report import PRODUCTION_WORKFLOW

COMMAND = "Create 3 science shorts about deep sea creatures"

# The eight production areas the integrated workflow must cover, in order.
MISSION_AREAS = [
    "trend_discovery",
    "psychology",
    "script_generation",
    "visual_intelligence",
    "voice_audio",
    "render",
    "seo_optimization",
    "publishing",
]


@pytest.fixture(scope="module")
def pipeline_result():
    """One full end-to-end run shared by the read-only assertions below."""
    return get_orchestrator().run_full_pipeline(COMMAND, threshold=0)


# --------------------------------------------------------- one entry point

def test_single_entry_point_runs_every_stage_in_order(pipeline_result):
    assert pipeline_result.succeeded, pipeline_result.error
    reported = [report.stage for report in pipeline_result.stage_reports]
    expected = pipeline_stage_names() + ["production", "packaging"] + distribution_stage_names()
    assert reported == expected
    # Render → Post-Production → SEO → Publishing run last, in contract order.
    assert reported[-4:] == ["render", "post_production", "seo", "publish"]


def test_module_level_entry_point_matches_orchestrator():
    result = run_full_pipeline(COMMAND, threshold=0)
    assert result.succeeded
    assert result.production_report["report_version"] == PRODUCTION_REPORT_VERSION


# ------------------------------------------------- distribution stage output

def test_render_stage_produces_render_packages(pipeline_result):
    summary = pipeline_result.context["render_summary"]
    assert summary["rendered"] == len(pipeline_result.context["ideas"])
    assert summary["status"] in ("SUCCESS", "WARNING")
    for idea in pipeline_result.context["ideas"]:
        assert idea["render_package"]["render_package_version"]
        assert idea["render_package"]["timeline"]["segments"]


def test_seo_stage_produces_optimization_and_publishing_packages(pipeline_result):
    report = pipeline_result.context["seo_optimization_report"]
    assert report["status"] == "optimized"
    assert report["items"] > 0
    packages = pipeline_result.context["publishing_packages"]
    assert len(packages) == report["items"]
    for package in packages:
        assert package["title"]
        assert package["keywords"]
        assert package["publish_windows"]


def test_publish_stage_schedules_jobs(pipeline_result):
    result = pipeline_result.context["publishing_result"]
    assert result["status"] in ("SUCCESS", "WARNING")
    assert result["publish_mode"] == "scheduled"       # safe default: nothing posts immediately
    assert result["jobs_created"] > 0
    assert result["scheduled"] == result["jobs_created"]
    assert pipeline_result.context["publish_schedule"]


def test_final_packages_carry_distribution_output(pipeline_result):
    ready = [pkg for pkg in pipeline_result.packages if pkg.publish_ready]
    assert ready
    for pkg in ready:
        assert isinstance(pkg, ProductionPackage)
        assert pkg.render_package.get("render_package_version")
        assert pkg.seo_package.get("optimized_titles")
        assert pkg.publishing_package.get("status") in ("scheduled", "published")
        assert pkg.status in ("rendered", "scheduled", "published")


# --------------------------------------------------------- production report

def test_production_report_is_returned(pipeline_result):
    report = pipeline_result.production_report
    assert report["report_version"] == PRODUCTION_REPORT_VERSION
    assert report["command"] == COMMAND
    assert report["status"] == pipeline_result.status
    assert report["generated_at"]
    assert report["duration_ms"] >= 0
    assert report == pipeline_result.context["production_report"]
    assert pipeline_result.to_dict()["production_report"] == report


def test_production_report_covers_all_eight_areas(pipeline_result):
    workflow = pipeline_result.production_report["workflow"]
    assert [entry["area"] for entry in workflow] == MISSION_AREAS
    assert [area for area, _stages in PRODUCTION_WORKFLOW] == MISSION_AREAS
    for entry in workflow:
        assert entry["status"] in (StageStatus.SUCCESS, StageStatus.WARNING), entry


def test_production_report_has_stage_diagnostics(pipeline_result):
    stages = pipeline_result.production_report["stages"]
    assert len(stages) == len(pipeline_result.stage_reports)
    for stage in stages:
        assert stage["status"] in (StageStatus.SUCCESS, StageStatus.WARNING)
        assert stage["started_at"] and stage["finished_at"]
        assert 0 <= stage["confidence"] <= 100


def test_production_report_inventories_engines(pipeline_result):
    engines = {entry["engine"]: entry for entry in pipeline_result.production_report["engines"]}
    for key in (
        "trend_discovery", "psychology", "script_generation", "visual_intelligence",
        "voice_audio", "video", "seo_optimization", "scheduler", "publishing",
    ):
        assert key in engines, f"missing engine in report: {key}"
        assert engines[key]["available"] and engines[key]["ready"]


def test_production_report_summarizes_content(pipeline_result):
    content = pipeline_result.production_report["content"]
    assert content["packages"] == len(pipeline_result.packages)
    assert content["publish_ready"] > 0
    assert content["render"]["rendered"] > 0
    assert content["optimization"]["items"] > 0
    assert content["publishing"]["jobs_created"] > 0


# ----------------------------------------------------- graceful degradation

def test_unavailable_engine_degrades_to_warning_never_crashes(monkeypatch):
    """Marking the SEO engine unavailable must not stop the pipeline: the
    seo stage skips with a warning, publishing still runs, and the report
    records the degradation."""
    engine = registry.get_engine("seo_optimization")
    monkeypatch.setattr(engine, "is_ready", lambda: False)

    result = Orchestrator().run_full_pipeline(COMMAND, threshold=0)

    assert result.succeeded                       # WARNING, not FAILED
    assert result.status == StageStatus.WARNING
    seo_report = next(r for r in result.stage_reports if r.stage == "seo")
    assert seo_report.status == StageStatus.WARNING
    assert any("seo_optimization" in warning for warning in seo_report.warnings)
    # Publishing still ran (without optimization packages) and reported.
    assert "publishing_result" in result.context
    # The degradation is visible in the one Production Report.
    workflow = {entry["area"]: entry for entry in result.production_report["workflow"]}
    assert workflow["seo_optimization"]["status"] == StageStatus.WARNING
    assert result.production_report["warnings"]


def test_failed_distribution_stage_degrades_run_not_crash(monkeypatch):
    """A crashing distribution engine degrades the run to WARNING with the
    error preserved — the finished content is never discarded."""
    engine = registry.get_engine("seo_optimization")
    monkeypatch.setattr(engine, "run", lambda context: (_ for _ in ()).throw(RuntimeError("seo exploded")))

    result = Orchestrator().run_full_pipeline(COMMAND, threshold=0)

    assert result.succeeded
    assert result.status == StageStatus.WARNING
    assert result.packages                          # content preserved
    seo_report = next(r for r in result.stage_reports if r.stage == "seo")
    assert seo_report.status == StageStatus.FAILED
    assert "seo exploded" in seo_report.errors[0]
    assert any("seo exploded" in error for error in result.production_report["errors"])


def test_failed_intelligence_stage_still_returns_production_report(monkeypatch):
    monkeypatch.setattr(
        "services.orchestrator.orchestrator.build_pipeline_plan",
        lambda: [("trend", ["trend_discovery", "opportunity_ranking"]),
                 ("research", ["engine_that_never_existed_xyz"])],
    )
    result = Orchestrator().run_full_pipeline(COMMAND)
    # Unregistered engine → skipped WARNING, run continues; report exists.
    assert result.production_report["report_version"] == PRODUCTION_REPORT_VERSION
    assert result.production_report["status"] == result.status


# ------------------------------------------------------- stage validation

def test_contract_validation_surfaces_missing_inputs_as_diagnostics():
    """Running a contract stage without its declared inputs produces
    validation diagnostics and warnings — never a failure."""
    report = Orchestrator().run_stage("seo", {"command": COMMAND})
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    validation = report.diagnostics.get("contract_validation", [])
    assert any("missing required context key" in problem for problem in validation)
    assert any(problem in report.warnings for problem in validation)


def test_report_builder_never_raises_on_malformed_result():
    class Broken:
        status = StageStatus.FAILED

        @property
        def stage_reports(self):
            raise RuntimeError("boom")

    report = build_production_report(Broken())
    assert report["report_version"] == PRODUCTION_REPORT_VERSION
    assert "failed safely" in report["error"]
