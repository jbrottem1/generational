"""Tests for Creative Studio service layer and UI integration (Agent 20)."""

from __future__ import annotations

import pytest

from core.storage.json_store import JsonProjectStore
from services import studio
from services.studio import models, pipeline, previews, production, projects


@pytest.fixture
def studio_store(tmp_path, monkeypatch):
    store = JsonProjectStore(directory=str(tmp_path / "projects"))
    import core.storage as storage_mod
    monkeypatch.setattr(storage_mod, "_store", store)
    return store


def test_studio_platforms_cover_required_formats():
    labels = {p["label"] for p in studio.STUDIO_PLATFORMS}
    assert "YouTube Long Form" in labels
    assert "TikTok" in labels
    assert "Podcasts" in labels
    assert "Multi-Platform Campaign" in labels
    assert len(studio.STUDIO_PLATFORMS) >= 15


def test_pipeline_stages_count():
    assert len(studio.STUDIO_PIPELINE_STAGES) == 12
    keys = [s["key"] for s in studio.STUDIO_PIPELINE_STAGES]
    assert keys[0] == "research"
    assert keys[-1] == "learning"


def test_build_default_settings_varies_by_platform():
    short = studio.build_default_settings("youtube_shorts")
    long = studio.build_default_settings("youtube_long")
    assert short["video_length_sec"] < long["video_length_sec"]


def test_map_stage_status():
    assert studio.map_stage_status("SUCCESS") == "completed"
    assert studio.map_stage_status("FAILED") == "failed"
    assert studio.map_stage_status("RUNNING") == "running"


def test_build_pipeline_view_from_stage_reports():
    reports = [
        {"stage": "research", "status": "SUCCESS", "duration_ms": 1500, "errors": [], "warnings": []},
        {"stage": "script_generation", "status": "SUCCESS", "duration_ms": 3200, "errors": [], "warnings": []},
        {"stage": "render", "status": "FAILED", "duration_ms": 500, "errors": ["timeout"], "warnings": []},
    ]
    stages = studio.build_pipeline_view(stage_reports=reports)
    assert len(stages) == 12
    research = next(s for s in stages if s["key"] == "research")
    assert research["status"] == "completed"
    rendering = next(s for s in stages if s["key"] == "rendering")
    assert rendering["status"] == "failed"
    assert rendering["can_retry"] is True


def test_build_pipeline_view_from_production_dashboard():
    dashboard = [
        {"key": "asset_generation", "label": "Assets", "state": "completed", "duration_ms": 2000},
        {"key": "render", "label": "Render", "state": "running"},
    ]
    stages = studio.build_pipeline_view(production_dashboard=dashboard)
    assets = next(s for s in stages if s["key"] == "asset_generation")
    assert assets["status"] == "completed"
    assert assets["elapsed_sec"] == 2.0


def test_build_settings_preview():
    settings = studio.build_default_settings("documentary")
    preview = studio.build_settings_preview("Create a 12 minute documentary", settings)
    assert preview["platform"] == "Documentaries"
    assert preview["longform"] is True
    assert preview["video_count"] >= 1


def test_is_longform_command():
    assert studio.is_longform_command("Create a 2 hour documentary") is True
    assert studio.is_longform_command("Make 3 TikTok videos") is False


def test_create_and_list_studio_projects(studio_store):
    studio.create_studio_project(
        "Doc Project",
        command="Ocean documentary",
        platform="documentary",
        folder="Nature",
        tags=["ocean", "science"],
    )
    results = studio.list_studio_projects(search="ocean")
    assert len(results) == 1
    assert results[0]["folder"] == "Nature"
    assert "ocean" in results[0]["tags"]


def test_duplicate_project(studio_store):
    studio.create_studio_project("Original", platform="tiktok")
    clone = studio.duplicate_project("Original", "Original Copy")
    assert clone["name"] == "Original Copy"
    assert clone["platform"] == "tiktok"
    assert studio_store.project_count() == 2


def test_archive_and_filter(studio_store):
    studio.create_studio_project("Active", platform="tiktok")
    studio.create_studio_project("Old", platform="tiktok")
    studio.archive_project("Old")
    active = studio.list_studio_projects()
    assert len(active) == 1
    all_projects = studio.list_studio_projects(include_archived=True)
    assert len(all_projects) == 2


def test_update_project_metadata(studio_store):
    studio.create_studio_project("Meta Test", platform="podcast")
    updated = studio.update_project_metadata(
        "Meta Test",
        tags=["audio"],
        folder="Audio Projects",
        studio_settings=studio.build_default_settings("podcast"),
    )
    assert updated["tags"] == ["audio"]
    assert updated["folder"] == "Audio Projects"


def test_extract_previews_from_result():
    result = {
        "ideas": [{
            "title": "Test Video",
            "hook": "Did you know?",
            "script": "Full script here.",
            "thumbnail_concept": "Bold text on dark background",
            "description": "A test description",
            "hashtags": ["#test"],
            "visual_package": {
                "storyboard": [{"purpose": "hook", "description": "Opening shot"}],
                "thumbnails": [{"label": "A", "description": "Concept A", "overall": 85}],
            },
        }],
        "research": {"summary": "Research findings."},
    }
    previews_data = studio.extract_previews(result)
    assert len(previews_data["scripts"]) == 2
    assert len(previews_data["thumbnails"]) >= 1
    assert len(previews_data["images"]) >= 1


def test_get_provider_dashboard():
    dashboard = studio.get_provider_dashboard()
    assert "providers" in dashboard
    assert "total_cost_usd" in dashboard
    assert isinstance(dashboard["providers"], list)


def test_get_executive_dashboard(studio_store):
    studio.create_studio_project("Dash Test", platform="youtube_shorts")
    dashboard = studio.get_executive_dashboard()
    assert dashboard["projects_total"] >= 1
    assert "provider_usage" in dashboard
    assert "publishing_queue" in dashboard
    assert "analytics_summary" in dashboard


def test_collect_output_library(studio_store):
    studio.create_studio_project(
        "Lib Test",
        platform="tiktok",
        result={
            "command": "test",
            "niche": "Tech",
            "video_count": 1,
            "goal": "test",
            "ideas": [{"title": "T", "script": "script text", "hook": "hook"}],
            "demo_mode": True,
            "model": "gpt-4o-mini",
        },
    )
    library = studio.collect_output_library()
    assert len(library["projects"]) >= 1
    assert len(library["scripts"]) >= 1


def test_run_studio_production_demo_mode(monkeypatch, tmp_path):
    """Integration — Studio routes through Workflow Executor → Orchestrator."""
    from services.workflow_executor import reset_workflow_executor, reset_workflow_store
    from services.workflow_executor.store import WorkflowRunStore

    store = WorkflowRunStore(tmp_path / "workflow_runs")
    reset_workflow_store()
    reset_workflow_executor()
    monkeypatch.setattr(
        "services.workflow_executor.executor.get_workflow_store",
        lambda: store,
    )

    result = studio.run_studio_production(
        "Create 2 psychology shorts",
        studio.build_default_settings("youtube_shorts"),
        model="demo",
        threshold=0,
    )
    assert result.get("ideas")
    assert result.get("settings_preview")
    assert result.get("studio_settings")
    assert result.get("workflow_run_id")
    assert result.get("workflow_status") in ("completed", "failed")
    assert result.get("stage_reports")
    stages = [r["stage"] for r in result["stage_reports"]]
    assert "publish" in stages
    assert "analytics" in stages
    assert "learning" in stages


def test_run_studio_production_uses_workflow_executor(monkeypatch):
    """Studio must not bypass Agent 21 — production goes through WorkflowExecutor."""
    calls = {}

    class FakeStep:
        stage = "research"
        status = "completed"
        duration_ms = 10
        errors = []
        warnings = []
        confidence = 80
        diagnostics = {}
        attempt = 1
        required = True
        optional = False

    class FakeRun:
        run_id = "run_test123"
        command = "Create a short about focus"
        status = "completed"
        production_type = "youtube_short"
        created_at = ""
        updated_at = ""
        started_at = ""
        finished_at = ""
        estimated_completion_at = ""
        provider_usage = {}
        estimated_cost_usd = 0.0
        context = {
            "command": "Create a short about focus",
            "niche": "Tech",
            "video_count": 1,
            "goal": "test",
            "ideas": [{"title": "T", "script": "s", "hook": "h"}],
            "demo_mode": True,
            "count": 1,
            "model": "demo",
        }
        config = type("C", (), {"model": "demo", "count": 1, "longform_mode": False, "budget_usd": 0.0, "template": "youtube_short"})()
        workflow = type("W", (), {"steps": [FakeStep()], "progress_pct": 100.0})()
        result = type("R", (), {"packages": [], "production_report": {}, "error": "", "partial": False, "provider_usage": {}, "estimated_cost_usd": 0.0, "failure_reports": [], "production_package": {}, "asset_package": {}, "animation_package": {}, "post_production_package": {}, "render_package": {}, "publishing_package": {}, "analytics_package": {}, "learning_context": {}})()
        log = type("L", (), {"entries": []})()

    class FakeExecutor:
        def execute(self, command, config=None, context_extra=None, **kwargs):
            calls["command"] = command
            calls["config"] = config
            calls["context_extra"] = context_extra
            return FakeRun()

    monkeypatch.setattr("services.workflow_executor.get_workflow_executor", lambda *a, **k: FakeExecutor())
    result = production.run_studio_production("Create a short about focus", studio.build_default_settings("youtube_shorts"), model="demo")
    assert calls["command"] == "Create a short about focus"
    assert calls["context_extra"]["studio_settings"]["platform"] == "youtube_shorts"
    assert result["workflow_run_id"] == "run_test123"
    assert result["ideas"]


def test_submit_longform_job(tmp_path, monkeypatch):
    """Long-form Studio jobs use Workflow Executor + workflow_run queue."""
    from core.jobs import JobQueue
    from services.workflow_executor import WORKFLOW_JOB_TYPE, reset_workflow_executor
    from services.workflow_executor.store import WorkflowRunStore

    store = WorkflowRunStore(tmp_path / "workflow_runs")
    reset_workflow_executor()
    monkeypatch.setattr("services.workflow_executor.executor.get_workflow_store", lambda: store)
    queue = JobQueue()
    monkeypatch.setattr("core.jobs.get_queue", lambda: queue)
    settings = studio.build_default_settings("documentary")
    job = studio.submit_longform_job("Create a 90 minute documentary", settings, model="demo", project_name="Doc")
    assert job["run_id"]
    assert job["job_id"]
    assert job["longform"] is True
    assert job["workflow_job_type"] == WORKFLOW_JOB_TYPE
    assert queue.has_handler(WORKFLOW_JOB_TYPE)


def test_studio_example_prompts():
    assert len(models.STUDIO_EXAMPLE_PROMPTS) >= 5


def test_list_folders_and_tags(studio_store):
    studio.create_studio_project("A", platform="tiktok", folder="Campaigns", tags=["launch"])
    studio.create_studio_project("B", platform="linkedin", folder="B2B", tags=["b2b"])
    assert "Campaigns" in projects.list_folders()
    assert "launch" in projects.list_tags()


def test_pipeline_estimate_remaining():
    reports = [
        {"stage": "research", "status": "SUCCESS", "duration_ms": 1000, "errors": [], "warnings": []},
    ]
    stages = pipeline.build_pipeline_view(stage_reports=reports)
    pending = [s for s in stages if s["status"] == "pending"]
    assert len(pending) > 0
