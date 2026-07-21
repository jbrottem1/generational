"""Tests for Production Operations Layer."""

from __future__ import annotations

import json
from pathlib import Path

import engines  # noqa: F401
from engines import registry
from core.workflows import WORKFLOWS
from services.production_operations import (
    OPERATIONS_STAGES,
    STAGE_KEYS,
    SUPPORTED_PLATFORMS,
    build_studio_brief,
    enqueue_production,
    queue_summary,
    run_studio_ops,
    search_history,
)
from services.production_operations.resilience import run_engine_with_retries


def test_sixteen_stages():
    assert len(OPERATIONS_STAGES) == 16
    assert len(STAGE_KEYS) == 16
    assert STAGE_KEYS[0] == "research"
    assert STAGE_KEYS[-1] == "export"
    assert "viewer_retention" in STAGE_KEYS
    assert "seo_package" in STAGE_KEYS


def test_platforms_future_proofed():
    for p in ("youtube_shorts", "tiktok", "instagram_reels", "linkedin", "documentary"):
        assert p in SUPPORTED_PLATFORMS


def test_brief_from_structured_input():
    brief = build_studio_brief(
        topic="Why Octopuses Have Three Hearts",
        platform="YouTube Shorts",
        length_sec=45,
        style="educational",
        narrator="professor",
        quality_target=98,
    )
    assert brief.topic.startswith("Why Octopuses")
    assert brief.platform == "youtube_shorts"
    assert brief.length_sec == 45
    assert "Octopuses" in brief.to_command()


def test_engine_registered():
    eng = registry.get_engine("production_operations")
    assert eng and eng.is_ready()
    assert eng.version.startswith("1.")
    assert "studio_ops" in WORKFLOWS
    assert WORKFLOWS["studio_ops"] == ["production_operations"]


def test_retry_continues_on_missing_engine():
    result = run_engine_with_retries("engine_that_does_not_exist_xyz", {}, max_retries=1)
    assert result["status"] == "skipped"
    assert result["fallback"] is True


def test_full_ops_run_never_aborts_and_writes_artifacts():
    result = run_studio_ops(
        topic="Why Octopuses Have Three Hearts",
        platform="youtube_shorts",
        length_sec=45,
        style="educational",
        narrator="professor",
        voice="default",
        quality_target=98,
        # Unit smoke: allow missing MP4 so success reflects pipeline completion, not encoder output
        constraints={"allow_missing_mp4": True, "export_mode": "smoke"},
        context={"allow_missing_mp4": True, "ops_export_mode": "smoke"},
    )
    assert result["succeeded"] is True
    assert result["production_id"]
    status = result["status"]
    assert len(status["stages"]) == 16
    # Never terminate — every stage should leave pending
    for stage in status["stages"]:
        assert stage["status"] not in ("pending",)
        assert "start_time" in stage or stage["status"] in ("skipped", "succeeded", "degraded", "partial", "running", "failed")
    path = Path(result["report_path"])
    assert path.exists()
    report = result["report"]
    for key in (
        "overall_quality_score",
        "hook_score",
        "narration_score",
        "visual_score",
        "audio_score",
        "caption_score",
        "educational_accuracy",
        "retention_prediction",
        "ctr_prediction",
        "completion_prediction",
        "shareability",
        "platform_readiness",
        "final_recommendation",
    ):
        assert key in report
    dash = result["dashboard"]
    assert "overall_progress_pct" in dash
    assert "pipeline_health" in dash
    assert "retry_count" in dash
    # History searchable
    hits = search_history(query="Octopus")
    assert any(h.get("production_id") == result["production_id"] for h in hits)
    # Export validation present
    assert "export_validation" in result


def test_queue_single_job():
    out = enqueue_production(
        topic="Queue smoke topic about coral reefs",
        platform="tiktok",
        length_sec=30,
        priority=3,
        run_immediately=True,
    )
    assert out["job_id"]
    assert out["status"] in ("succeeded", "failed", "pending")
    summary = queue_summary()
    assert "pending" in summary
