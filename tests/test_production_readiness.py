"""Production readiness aggregator, API, dry-run publish, closed-loop pipeline."""

from __future__ import annotations

import json
from http.server import HTTPServer
from threading import Thread

import engines  # noqa: F401 — register engines
import pytest

from api.server import create_handler
from providers.analytics import YouTubeAnalyticsProvider, get_analytics_provider
from providers.publishing import get_publishing_provider
from services.analytics.integration import (
    disable_continuous_learning,
    enable_continuous_learning,
)
from services.orchestrator import StageStatus, get_orchestrator
from services.publishing import PUBLISH_MODES
from services.readiness import build_readiness_report


def test_publish_modes_include_dry_run():
    assert "dry_run" in PUBLISH_MODES


def test_publishing_provider_dry_run_validates_without_upload():
    provider = get_publishing_provider("youtube_shorts")
    assert provider is not None
    result = provider.dry_run({"title": "Test dry run", "diagnostics": {"format_warnings": []}})
    assert result["dry_run"] is True
    assert result["status"] == "published"
    assert result["post_id"].startswith("dryrun_")


def test_youtube_analytics_provider_registered():
    # Without credentials → mock fallback; with credentials → YouTube adapter.
    provider = get_analytics_provider("youtube_shorts")
    assert provider is not None
    yt = YouTubeAnalyticsProvider()
    assert yt.name == "youtube_analytics"
    assert not yt.is_available() or isinstance(provider, YouTubeAnalyticsProvider)


def test_pipeline_result_includes_context_summary():
    result = get_orchestrator().run_full_pipeline(
        "Create 1 short about coral reefs",
        count=1,
        model="demo",
        threshold=0,
        publish_mode="dry_run",
    )
    payload = result.to_dict()
    assert "context_summary" in payload
    assert payload["context_summary"].get("publish_mode") == "dry_run"
    assert "publish" in [r.stage for r in result.stage_reports]
    assert "analytics" in [r.stage for r in result.stage_reports]
    assert "learning" in [r.stage for r in result.stage_reports]


def test_e2e_closed_production_pipeline_dry_run(isolated_analytics_data):
    """Idea → … → publish (dry_run) → analytics → learning succeeds."""
    enabled = enable_continuous_learning()
    assert "agent9-analytics" in enabled["hooks"]
    try:
        result = get_orchestrator().run_full_pipeline(
            "Create 1 science short about deep ocean vents",
            count=1,
            model="demo",
            threshold=0,
            publish_mode="dry_run",
        )
        assert result.status in (StageStatus.SUCCESS, StageStatus.WARNING)
        stages = [r.stage for r in result.stage_reports]
        for required in (
            "ai_director",
            "creative",
            "asset_generation",
            "animation",
            "publish",
            "analytics",
            "learning",
        ):
            assert required in stages, f"missing stage {required}"
        assert result.context.get("publishing_result")
        assert result.context.get("analytics_summary") is not None or result.context.get("learning_report") is not None
        pub = result.context.get("publishing_result") or {}
        assert pub.get("publish_mode") == "dry_run"
    finally:
        disable_continuous_learning()


def test_readiness_report_scorecard_floors():
    enable_continuous_learning()
    try:
        report = build_readiness_report()
        assert report["overall"] >= 95
        scores = report["scorecard"]
        assert scores["api"] >= 95
        assert scores["analytics"] >= 90
        assert scores["learning"] >= 90
        assert scores["publishing"] >= 90
        assert scores["security"] >= 90
        assert report["publishing"]["dry_run_supported"] is True
        assert report["analytics"]["youtube_provider_registered"] is True
        assert report["learning"]["continuous_learning_armed"] is True
    finally:
        disable_continuous_learning()


def test_internal_api_health_and_readiness():
    enable_continuous_learning()
    handler = create_handler()
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
        assert health["status"] == "ok"

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/readiness", timeout=10) as resp:
            readiness = json.loads(resp.read().decode("utf-8"))
        assert readiness["overall"] >= 90
        assert "scorecard" in readiness
    finally:
        server.shutdown()
        disable_continuous_learning()
