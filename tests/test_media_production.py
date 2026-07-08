"""Tests for the v4.0 Media Production Pipeline."""

import engines  # noqa: F401
from core.workflows import WorkflowEngine
from services.production import run_media_production

COMMAND = "Create 5 science shorts about black holes"


def _intelligence_context(threshold=0):
    ctx = {"command": COMMAND, "count": 10, "model": "gpt-4o-mini", "threshold": threshold}
    run = WorkflowEngine().execute("intelligence", ctx)
    assert run.succeeded
    ctx["pipeline_steps"] = run.summary()["steps"]
    return ctx


def _approved_idea(script="Hook. Insight one. Insight two. Follow for more."):
    return {
        "title": "Test Video",
        "hook": "Hook.",
        "script": script,
        "publishable": True,
        "scores": {"publish": 80},
        "thumbnail_concept": "Bold text overlay",
    }


def test_media_production_workflow_succeeds():
    ctx = {"niche": "Science", "approved_content": [_approved_idea()]}
    run = WorkflowEngine().execute("media_production", ctx)
    assert run.succeeded, run.summary()
    assert len(ctx["production_packages"]) == 1


def test_scene_planning_creates_structured_scenes():
    ctx = {"niche": "Science", "approved_content": [_approved_idea()]}
    WorkflowEngine().execute(["scene_planning"], ctx)
    pkg = ctx["production_packages"][0]
    assert len(pkg["scenes"]) >= 1
    scene = pkg["scenes"][0]
    for field in (
        "scene_id", "title", "duration_sec", "narration", "visual_description",
        "emotion", "camera_movement", "transition", "on_screen_text", "keywords",
    ):
        assert field in scene


def test_full_production_builds_render_package():
    ctx = {"niche": "Science", "subject": "black holes", "approved_content": [_approved_idea()]}
    run = WorkflowEngine().execute("media_production", ctx)
    assert run.succeeded
    pkg = ctx["production_packages"][0]
    assert pkg.get("narration_tracks")
    assert pkg.get("visual_prompts")
    assert pkg.get("assets")
    assert pkg.get("subtitles", {}).get("srt_content")
    assert pkg.get("timeline", {}).get("duration_sec", 0) > 0
    rp = pkg.get("render_package", {})
    assert rp.get("package_id")
    assert rp.get("metadata", {}).get("ready_for_render")
    assert pkg.get("queue_status") == "queued"


def test_run_media_production_from_intelligence_context():
    ctx = _intelligence_context(threshold=0)
    production = run_media_production(ctx)
    assert not production.get("production_skipped")
    assert production["production_packages"]
    assert len(production["production_dashboard"]) == 17
    completed = [s for s in production["production_dashboard"] if s["state"] == "completed"]
    assert len(completed) >= 15


def test_unapproved_scripts_skipped():
    ctx = _intelligence_context(threshold=100)
    production = run_media_production(ctx)
    assert production.get("production_skipped") is True
    assert production["production_packages"] == []


def test_production_attaches_summary_to_ideas():
    ctx = _intelligence_context(threshold=0)
    run_media_production(ctx)
    produced = [i for i in ctx["ideas"] if i.get("production")]
    assert len(produced) >= 1
    assert produced[0]["production"]["scenes"] >= 1
