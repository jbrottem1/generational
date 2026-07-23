"""Tests for Audience Intelligence Engine — structured JSON only."""

from __future__ import annotations

from pathlib import Path

import engines  # noqa: F401 — register engines
from core.workflows import WORKFLOWS
from engines import registry
from services.audience_intelligence import (
    PSYCH_FIELDS,
    AudienceIntelligenceReport,
    analyze_topic,
    apply_guidance_to_script_context,
    script_generation_guidance,
)
from services.audience_intelligence.scoring import human_attention_score, score_psychological_drivers
from services.discovery.script_handoff import brief_to_script_context


def test_psychological_drivers_cover_required_fields():
    drivers = score_psychological_drivers(
        "Why scientists discovered a shocking secret about black holes explained"
    )
    data = drivers.to_dict()
    assert set(PSYCH_FIELDS) == set(data.keys())
    for v in data.values():
        assert 0 <= v <= 100
    assert drivers.curiosity_potential >= 55
    assert drivers.educational_value >= 55


def test_analyze_topic_structured_report():
    report = analyze_topic(
        "How cameras are made",
        category="science",
        angle="Factory process explained with surprising precision",
        youtube_intelligence={
            "brief": {
                "expected_watch_time_sec": 45,
                "expected_click_through_potential": 68,
                "recommended_video_type": "short",
                "cross_reference": {
                    "agreeing_sources": 3,
                    "sources": ["google_news", "youtube_search_trends", "reddit_trends"],
                    "has_google_news": True,
                    "has_youtube": True,
                    "has_reddit": True,
                },
            },
            "videos": [
                {
                    "scores": {
                        "educational": 72,
                        "clickability": 70,
                        "thumbnail_quality": 85,
                        "trend_momentum": 60,
                        "evergreen": 55,
                    }
                }
            ],
            "market": {"average_view_count": 1_000_000, "average_channel_size": 500_000},
        },
        google_news={
            "sample": [
                {
                    "scores": {
                        "breaking_news": 40,
                        "educational_potential": 70,
                        "psychology": 55,
                        "evergreen": 60,
                    }
                }
            ]
        },
    )
    payload = report.to_dict()
    assert payload["human_attention_score"] >= 40
    assert "psychological_drivers" in payload
    assert "engagement" in payload
    assert "audience_profile" in payload
    assert "creative" in payload
    assert payload["creative"]["suggested_opening_hook"]
    assert payload["creative"]["recommended_video_format"] in (
        "short",
        "long_form",
        "series",
        "breaking_news",
        "documentary",
        "animation",
    )
    # No raw API leakage
    blob = str(payload)
    assert "etag" not in blob
    assert "youtube#" not in blob


def test_report_round_trip():
    report = analyze_topic("axial tilt seasons explained")
    restored = AudienceIntelligenceReport.from_dict(report.to_dict())
    assert restored.to_dict()["topic"] == report.topic
    assert restored.human_attention_score == report.human_attention_score


def test_script_guidance_and_handoff():
    report = analyze_topic("How black holes work", category="science")
    guidance = script_generation_guidance(report)
    assert "suggested_opening_hook" in guidance
    assert "recommended_video_format" in guidance
    assert "target_platform" in guidance

    ctx = brief_to_script_context(
        "How black holes work",
        {"overall_opportunity_score": 70, "reasoning": "edu", "recommended_video_type": "short"},
        audience_intelligence=report.to_dict(),
    )
    assert ctx["candidates"][0]["hook"] == report.creative.suggested_opening_hook
    assert ctx["audience_intelligence"]["human_attention_score"] == report.human_attention_score
    assert ctx["research"]["human_attention_score"] == report.human_attention_score

    merged = apply_guidance_to_script_context({"candidates": [{"title": "x", "hook": "old"}]}, report)
    assert merged["candidates"][0]["hook"] == report.creative.suggested_opening_hook


def test_engine_enriches_candidates():
    engine = registry.get_engine("audience_intelligence")
    assert engine is not None
    assert engine.is_ready()
    updates = engine.run(
        {
            "candidates": [
                {"title": "Why the ocean is salty", "hook": "old hook", "angle": "science explained"},
            ],
            "trend_category": "science",
        }
    )
    assert updates["candidates"][0]["audience_intelligence"]
    assert updates["human_attention_score"] > 0
    assert updates["audience_script_guidance"]["suggested_opening_hook"]


def test_workflow_places_audience_before_script():
    steps = WORKFLOWS["intelligence"]
    assert "audience_intelligence" in steps
    assert steps.index("audience_intelligence") > steps.index("psychology")
    assert steps.index("script_generation") > steps.index("audience_intelligence")


def test_attention_score_blend():
    drivers = score_psychological_drivers("How to learn physics explained — surprising myth")
    from services.audience_intelligence.scoring import estimate_engagement

    eng = estimate_engagement(drivers)
    score = human_attention_score(drivers, eng)
    assert 0 <= score <= 100


def test_creative_brief_and_memory(tmp_path, monkeypatch):
    from services.audience_intelligence import brief as brief_mod
    from services.audience_intelligence import memory as mem

    monkeypatch.setattr(mem, "KB_ROOT", tmp_path)
    monkeypatch.setattr(mem, "KB_PATH", tmp_path / "CREATIVE_MEMORY.json")
    monkeypatch.setattr(mem, "LESSONS_PATH", tmp_path / "PRODUCTION_LESSONS.json")
    monkeypatch.setattr(mem, "BRIEF_DIR", tmp_path / "briefs")
    monkeypatch.setattr(mem, "REVIEW_DIR", tmp_path / "reviews")
    monkeypatch.setattr(brief_mod, "BRIEF_DIR", tmp_path / "briefs")

    seeded = mem.seed_bootstrap_lessons()
    assert seeded["total"] >= 1

    from services.audience_intelligence import attach_brief_to_candidate, build_creative_brief

    brief = build_creative_brief(
        topic="Why Octopuses Have Three Hearts",
        niche="biology",
        platform="youtube_shorts",
        narrator="professor",
    )
    assert brief["recommended_opening_hook"]
    assert brief["ideal_pacing"]
    assert brief["recommended_visual_density"]
    assert brief["suggested_camera_style"]
    assert brief["thumbnail_strategy"]
    assert brief["potential_weak_points"]
    assert Path(brief["path"]).exists()

    cand = attach_brief_to_candidate({"topic": "Why Octopuses Have Three Hearts"}, brief)
    assert cand["audience_intelligence_brief"]["topic"]
    assert cand.get("suggested_opening_hook") or cand.get("hook")

    hits = mem.search_lessons("ocean biology", platform="youtube_shorts", limit=5)
    assert hits
    assert "confidence" in hits[0]
    assert "evidence" in hits[0]


def test_post_review_records_one_lesson(tmp_path, monkeypatch):
    from services.audience_intelligence import memory as mem
    from services.audience_intelligence import post_review as pr

    monkeypatch.setattr(mem, "KB_ROOT", tmp_path)
    monkeypatch.setattr(mem, "KB_PATH", tmp_path / "CREATIVE_MEMORY.json")
    monkeypatch.setattr(mem, "LESSONS_PATH", tmp_path / "PRODUCTION_LESSONS.json")
    monkeypatch.setattr(mem, "BRIEF_DIR", tmp_path / "briefs")
    monkeypatch.setattr(mem, "REVIEW_DIR", tmp_path / "reviews")
    monkeypatch.setattr(pr, "REVIEW_DIR", tmp_path / "reviews")

    from services.audience_intelligence import list_analytics_interfaces, review_production_audience

    interfaces = list_analytics_interfaces()
    assert {i["name"] for i in interfaces} >= {
        "youtube_analytics",
        "tiktok_analytics",
        "instagram_insights",
        "ab_test_results",
    }

    review = review_production_audience(
        topic="Why Octopuses Have Three Hearts",
        niche="biology",
        platform="youtube_shorts",
        production_id="test_octopus_ai",
        creative_excellence={
            "creative_excellence_score": 88.5,
            "scorecard": {
                "creative_excellence_score": 88.5,
                "craft_scores": {
                    "hook": 72,
                    "visual": 90,
                    "storytelling": 86,
                    "educational_clarity": 91,
                    "audio": 88,
                    "retention": 80,
                    "overall_professionalism": 93.7,
                },
            },
            "single_recommendation": {
                "dimension": "curiosity",
                "recommendation": "Open by confronting the wrong belief that octopuses have one heart.",
            },
        },
    )
    assert review["lesson_recorded"]["lesson_id"]
    assert review["highest_impact_improvement"]["statement"]
    assert Path(review["path"]).exists()
    assert Path(review["markdown_path"]).exists()
    kb = mem.load_knowledge()
    assert any(l.get("production_id") == "test_octopus_ai" for l in kb.get("lessons") or [])
