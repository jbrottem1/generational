"""Tests for Version 1 launch checklist (no new engines)."""

from __future__ import annotations

from services.launch_plan import run_launch_checklist


def test_launch_checklist_runs_and_covers_required_areas():
    report = run_launch_checklist()
    assert report["version"] == "1.0.0"
    ids = {i["id"] for i in report["items"]}
    for required in (
        "production_pipeline",
        "export_pipeline",
        "publishing_packages",
        "thumbnail_generation",
        "seo_generation",
        "analytics_recording",
        "error_recovery",
        "logging",
        "configuration",
        "required_api_keys",
        "required_credentials",
    ):
        assert required in ids
    assert "documentation" in report
    assert report["documentation"]["launch_plan"] == "VERSION_1_LAUNCH_PLAN.md"
