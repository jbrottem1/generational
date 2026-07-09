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


def test_run_studio_production_demo_mode(monkeypatch):
    """Integration test — runs pipeline via orchestrator in demo mode."""
    result = studio.run_studio_production(
        "Create 2 psychology shorts",
        studio.build_default_settings("youtube_shorts"),
        model="gpt-4o-mini",
        threshold=0,
    )
    assert result.get("ideas")
    assert result.get("settings_preview")
    assert result.get("studio_settings")


def test_submit_longform_job(tmp_path):
    from services.provider_runtime.longform import RuntimeExecutionEngine

    engine = RuntimeExecutionEngine(checkpoint_dir=tmp_path / "checkpoints")
    settings = studio.build_default_settings("documentary")

    checkpoint = engine.start_production(
        "Create a 90 minute documentary",
        production_type="documentary",
        options={"model": "gpt-4o-mini", "context_extra": {"studio_settings": settings}},
    )
    assert checkpoint.job_id
    assert checkpoint.context_snapshot.get("longform") is True


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
