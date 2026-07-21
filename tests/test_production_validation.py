"""Smoke test for content validation evaluate/roadmap (no full domain matrix)."""

from __future__ import annotations

from services.production_validation.catalog import DOMAIN_PRODUCTIONS, SCORE_DIMENSIONS
from services.production_validation.evaluate import aggregate_weaknesses, evaluate_production
from services.production_validation.roadmap import write_improvement_roadmap


def test_domain_catalog_covers_mission_examples():
    domains = {d["domain"] for d in DOMAIN_PRODUCTIONS}
    for required in (
        "artificial_intelligence",
        "biology",
        "physics",
        "history",
        "astronomy",
        "medicine",
        "finance",
        "psychology",
        "engineering",
        "nature",
    ):
        assert required in domains
    for brief in DOMAIN_PRODUCTIONS:
        for key in ("topic", "platform", "length_sec", "style", "audience", "voice"):
            assert brief.get(key), key


def test_evaluate_production_scorecard():
    fake = {
        "production_id": "ops_test",
        "succeeded": True,
        "elapsed_ms": 5000,
        "brief": {
            "topic": "Test",
            "platform": "youtube_shorts",
            "length_sec": 45,
            "style": "educational",
            "narrator": "professor",
            "domain": "science",
            "constraints": {"audience": "adults"},
        },
        "report": {
            "hook_score": 72,
            "narration_score": 88,
            "visual_score": 70,
            "audio_score": 68,
            "caption_score": 75,
            "educational_accuracy": 91,
            "retention_prediction": 71,
            "ctr_prediction": 4.2,
            "completion_prediction": 69,
            "shareability": 70,
            "overall_quality_score": 86,
            "final_recommendation": "REVISE_THEN_PUBLISH",
        },
        "context": {"candidates": [{"title": "Test"}], "export_validation": {"ok": True, "video_exists": False}},
        "status": {"elapsed_ms": 5000},
        "export_validation": {"ok": True, "video_exists": False, "thumbnail_generated": False},
    }
    ev = evaluate_production(fake)
    for key in SCORE_DIMENSIONS:
        assert key in ev["scores"], key
    assert ev["scores"]["overall_production_score"] < 90  # honest composite, not inflated report
    assert ev["weaknesses"], "expected ranked weaknesses for below-floor scores"
    assert ev["weaknesses"][0]["rank"] == 1


def test_aggregate_and_roadmap(tmp_path):
    evaluations = [
        {
            "domain": "biology",
            "weaknesses": [
                {
                    "id": "weak_hook",
                    "label": "Weak hook",
                    "impact": 95,
                    "score": 70,
                    "fix_hint": "Tighten hook",
                }
            ],
        },
        {
            "domain": "physics",
            "weaknesses": [
                {
                    "id": "weak_hook",
                    "label": "Weak hook",
                    "impact": 95,
                    "score": 72,
                    "fix_hint": "Tighten hook",
                },
                {
                    "id": "static_visuals",
                    "label": "Static visuals",
                    "impact": 88,
                    "score": 68,
                    "fix_hint": "More motion",
                },
            ],
        },
    ]
    ranked = aggregate_weaknesses(evaluations)
    assert ranked[0]["id"] == "weak_hook"
    summary = {
        "publish_ready_pct": 40.0,
        "average_scores": {"overall_production_score": 86.0},
        "weakness_ranking": ranked,
    }
    path = write_improvement_roadmap(summary, tmp_path)
    assert path.exists()
    assert "Highest-impact" in path.read_text(encoding="utf-8")
