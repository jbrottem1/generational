"""Tests for Trend & Opportunity Intelligence — executive layer only."""

from __future__ import annotations

from services.trend_opportunity import (
    build_production_brief,
    handoff_pipeline,
    list_provider_interfaces,
    run_trend_opportunity,
    validate_opportunity,
    verify_brief_ready,
)
from services.trend_opportunity.library import ensure_db
from services.trend_opportunity.scoring import score_opportunity_card


def test_provider_interfaces_cover_mission_sources():
    rows = list_provider_interfaces()
    keys = {r["mission_key"] for r in rows}
    assert "youtube_trending" in keys
    assert "google_trends" in keys
    assert "reddit" in keys
    assert "rss_feeds" in keys


def test_opportunity_scoring_and_validation():
    scored = score_opportunity_card(
        "Why octopuses have three hearts",
        category="science",
        source_signals={"search_volume": 120000, "growth_pct": 55, "competition": 0.3},
    )
    assert 0 <= scored["overall_opportunity_score"] <= 100
    assert "curiosity_score" in scored["scores"]
    assert "educational_score" in scored["scores"]
    card = {
        "topic": "Why octopuses have three hearts",
        "category": "science",
        "overall_opportunity_score": scored["overall_opportunity_score"],
        "scores": scored["scores"],
        "analysis": scored["analysis"],
        "confidence": 0.8,
        "previous_productions_count": 0,
    }
    gate = validate_opportunity(card)
    assert gate["accepted"] is True


def test_rejects_oversaturated_weak_edu():
    card = {
        "topic": "celebrity gossip",
        "category": "entertainment",
        "overall_opportunity_score": 30,
        "scores": {
            "educational_score": 20,
            "curiosity_score": 25,
            "visual_score": 20,
            "competition_score": 10,
        },
        "analysis": {"competition": 90, "educational_value": 20, "curiosity_gap": 25, "visual_potential": 20},
        "confidence": 0.2,
        "previous_productions_count": 5,
    }
    gate = validate_opportunity(card)
    assert gate["accepted"] is False
    assert gate["reject_reasons"]


def test_production_brief_ready_for_pipeline():
    scored = score_opportunity_card("How black holes bend time", category="science")
    brief = build_production_brief("How black holes bend time", scores=scored, category="science")
    assert brief["manual_editing_required"] is False
    assert brief["command"]
    assert brief["research_goals"]
    assert brief["world_selection"]
    check = verify_brief_ready(brief)
    assert check["ok"] is True


def test_run_science_and_handoff(tmp_path, monkeypatch):
    from services.trend_opportunity import library as lib
    from services.trend_opportunity import reports as rep

    monkeypatch.setattr(lib, "DB_PATH", tmp_path / "OPPORTUNITY_LIBRARY.db")
    monkeypatch.setattr(lib, "LIB_DIR", tmp_path)
    monkeypatch.setattr(rep, "OUT_DIR", tmp_path / "reports")
    ensure_db(tmp_path / "OPPORTUNITY_LIBRARY.db")

    result = run_trend_opportunity(
        "science education",
        category="science",
        top_n=25,
        brief_count=10,
        high_confidence_count=5,
        use_discovery_engine=False,  # faster / offline-friendly
        persist=True,
        write_reports=True,
    )
    assert result["ok"]
    assert len(result["top_opportunities"]) >= 25
    assert len(result["production_briefs"]) == 10
    assert len(result["highest_confidence"]) == 5
    assert (tmp_path / "reports" / "TOP_OPPORTUNITIES.json").exists()
    assert (tmp_path / "reports" / "PRODUCTION_BRIEF.md").exists()
    assert (tmp_path / "reports" / "CONTENT_CALENDAR.json").exists()
    assert (tmp_path / "OPPORTUNITY_LIBRARY.db").exists()

    brief = result["number_one"]["production_brief"]
    handoff = handoff_pipeline(brief, execute_ops=False, enqueue=False)
    assert handoff["ok"] is True
    assert handoff["manual_editing_required"] is False
    assert handoff["research"]["verification"]["ok"] is True
    assert handoff["studio_ops"]["studio_brief"]["topic"]
