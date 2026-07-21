"""Tests for Continuous Learning & Publishing Intelligence V2.0."""

from __future__ import annotations

from services.publishing_intelligence import (
    build_complete_publish_packages,
    build_calibration_report,
    build_studio_intelligence_dashboard,
    estimate_business_metrics,
    recommend_highest_impact_improvement,
    run_intelligence_cycle,
)
from services.publishing_intelligence.pipeline import SUPPORTED_PLATFORMS
from services.launch_readiness import run_launch_readiness_audit


def test_publish_packages_cover_all_platforms():
    pkg = build_complete_publish_packages(
        {
            "topic": "Why turtles live so long",
            "title": "Why turtles live so long",
            "video_path": "/tmp/demo.mp4",
            "render_package": {"mp4_path": "/tmp/demo.mp4", "file_uri": "/tmp/demo.mp4"},
        }
    )
    assert pkg["seo_title"]
    assert pkg["suggested_publish_time"]
    assert pkg["suggested_audience"]
    assert set(pkg["platforms"].keys()) == set(SUPPORTED_PLATFORMS)
    for platform, body in pkg["platforms"].items():
        assert body.get("upload_checklist"), platform
        assert "seo_title" in pkg or body.get("title") or (body.get("metadata") or {}).get("title")


def test_intelligence_cycle_with_demo_actuals(tmp_path, monkeypatch):
    import services.publishing_intelligence.analytics_layer as al
    import services.publishing_intelligence.calibration as cal
    import services.publishing_intelligence.creative_library as cl
    import services.publishing_intelligence.dashboard as dash
    import services.publishing_intelligence.system as sysmod

    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    monkeypatch.setattr(cal, "CALIBRATION_PATH", analytics_dir / "prediction_calibration.json")
    monkeypatch.setattr(cal, "PRIORS_PATH", analytics_dir / "prediction_priors.json")
    monkeypatch.setattr(cl, "LIBRARY_PATH", analytics_dir / "creative_knowledge_library.json")
    monkeypatch.setattr(dash, "DASH_PATH", analytics_dir / "STUDIO_INTELLIGENCE_DASHBOARD.json")
    monkeypatch.setattr(sysmod, "CYCLE_DIR", analytics_dir / "cycles")

    intel_path = analytics_dir / "intelligence_records.json"

    def _persist(record, *, also_legacy_store: bool = False):
        rows = []
        if intel_path.exists():
            import json

            rows = json.loads(intel_path.read_text())
        rows.append(record)
        intel_path.write_text(__import__("json").dumps(rows))
        return {"ok": True, "record_id": record.get("record_id")}

    def _list(limit: int = 200):
        if not intel_path.exists():
            return []
        import json

        return json.loads(intel_path.read_text())[-limit:]

    monkeypatch.setattr(al, "persist_intelligence_record", _persist)
    monkeypatch.setattr(sysmod, "persist_intelligence_record", _persist)
    monkeypatch.setattr(al, "list_intelligence_records", _list)
    monkeypatch.setattr(cal, "list_intelligence_records", _list)
    monkeypatch.setattr(cl, "list_intelligence_records", _list)
    monkeypatch.setattr(dash, "list_intelligence_records", _list)
    import services.publishing_intelligence.business_intel as biz

    monkeypatch.setattr(biz, "list_intelligence_records", _list)

    result = run_intelligence_cycle(
        {"topic": "Coral reefs", "platform": "youtube_shorts", "hook": "This reef is disappearing."},
        quality_scores={"hook_strength": 80, "shareability": 70, "retention_prediction": 75},
        seed_demo_actuals=True,
    )
    assert result["analytics_record_id"]
    assert result["publish_packages"]["platforms"]
    assert result["highest_impact_improvement"]["recommendation"]
    assert result["business_intelligence"]["estimated_monthly_earnings_usd"] is not None

    cal_report = build_calibration_report()
    assert cal_report["videos_calibrated"] >= 1


def test_improvement_picks_one_element():
    rec = recommend_highest_impact_improvement(
        quality_scores={"hook_strength": 60, "retention_prediction": 92, "shareability": 90},
        calibration={"divergence_highlights": []},
        topic="science",
    )
    assert rec["recommendation"]["element"]
    assert "do_not_optimize_now" in rec


def test_business_intel_projection_shape():
    biz = estimate_business_metrics()
    for key in (
        "production_cost_usd_per_video",
        "time_per_video_minutes",
        "automation_rate",
        "estimated_monthly_output",
        "estimated_monthly_earnings_usd",
        "estimated_annual_earnings_usd",
    ):
        assert key in biz


def test_dashboard_builds():
    board = build_studio_intelligence_dashboard()
    assert "confidence_score" in board
    assert "productions_today" in board
    assert "business_intelligence" in board


def test_launch_readiness_audit_emits_score():
    audit = run_launch_readiness_audit()
    assert 0 <= float(audit["launch_readiness_score"]) <= 100
    assert audit["recommendation"] in (
        "BEGIN_CONTROLLED_PUBLIC_LAUNCH",
        "RESOLVE_BLOCKERS_BEFORE_LAUNCH",
    )
    assert audit.get("checks")
