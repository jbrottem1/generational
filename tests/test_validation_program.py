"""Tests for V1 Validation Program — no new engines."""

from __future__ import annotations

from services.validation_program.bottlenecks import build_recommendations, detect_bottlenecks
from services.validation_program.catalog import MEASUREMENT_DIMENSIONS, build_validation_catalog, filter_catalog
from services.validation_program.library import ensure_library, list_validations, store_validation
from services.validation_program.scoring import score_validation_run


def test_catalog_is_100_across_ten_categories():
    cat = build_validation_catalog()
    assert len(cat) == 100
    cats = {r["category"] for r in cat}
    assert len(cats) == 10
    assert len(filter_catalog(categories=["biology"], limit=3)) == 3


def test_overall_professionalism_falls_back_when_ce_missing():
    ops = {
        "production_id": "ops_sparse",
        "success": True,
        "brief": {"topic": "Bridge Loads", "domain": "engineering"},
        "report": {
            "topic": "Bridge Loads",
            "hook_score": 80,
            "visual_score": 82,
            "narration_score": 78,
            "caption_score": 80,
            "educational_accuracy": 85,
            "retention_prediction": 70,
            "audio_score": 76,
            "animation_score": 74,
            "shareability": 68,
        },
        "status": {"success": True, "elapsed_ms": 1000, "stages": []},
        "context": {},
        "elapsed_ms": 1000,
    }
    card = score_validation_run(ops, category="engineering")
    assert card["measurements"]["overall_professionalism"] > 0
    assert card["measurements"]["overall_professionalism"] == card["legacy_scores"]["overall_production_score"]


def test_score_validation_run_maps_dimensions():
    ops = {
        "production_id": "ops_test",
        "success": True,
        "brief": {"topic": "Why Ice Floats", "domain": "physics"},
        "report": {
            "topic": "Why Ice Floats",
            "hook_score": 72,
            "visual_score": 80,
            "narration_score": 78,
            "caption_score": 85,
            "educational_accuracy": 88,
            "retention_prediction": 70,
            "audio_score": 76,
            "animation_score": 74,
            "shareability": 68,
            "creative_excellence_score": 71,
            "creative_recommendation": "Strengthen curiosity open",
            "audience_intelligence_lesson": "Confront wrong belief first",
        },
        "status": {
            "success": True,
            "elapsed_ms": 120000,
            "pipeline_health": "healthy",
            "stages": [
                {"key": "research", "duration_ms": 10000, "errors": [], "warnings": []},
                {"key": "rendering", "duration_ms": 5000, "errors": [], "warnings": ["mp4_not_yet_materialized"]},
            ],
        },
        "context": {
            "candidates": [{}],
            "creative_excellence": {
                "creative_excellence_score": 71,
                "single_recommendation": {"recommendation": "Strengthen curiosity open"},
                "scorecard": {
                    "v2_quality": {
                        "scores": {
                            "visual_quality": 80,
                            "motion_quality": 74,
                            "storytelling": 77,
                            "educational_clarity": 88,
                            "hook": 72,
                            "audio_quality": 76,
                            "overall_professionalism": 82,
                        }
                    }
                },
            },
        },
        "elapsed_ms": 120000,
    }
    card = score_validation_run(ops, category="physics")
    for dim in MEASUREMENT_DIMENSIONS:
        assert dim in card["measurements"]
        assert 0 <= card["measurements"][dim] <= 100
    assert card["overall_program_score"] > 0
    assert card["timing"]["elapsed_ms"] == 120000


def test_library_store_and_bottlenecks(tmp_path, monkeypatch):
    from services.validation_program import library as lib

    monkeypatch.setattr(lib, "LIB_ROOT", tmp_path)
    monkeypatch.setattr(lib, "DB_PATH", tmp_path / "VALIDATION_LIBRARY.db")
    monkeypatch.setattr(lib, "INDEX_JSON", tmp_path / "VALIDATION_LIBRARY.json")
    ensure_library()

    card = {
        "production_id": "ops_x",
        "topic": "Why Ice Floats",
        "category": "physics",
        "success": True,
        "measurements": {d: 70.0 for d in MEASUREMENT_DIMENSIONS},
        "overall_program_score": 70.0,
        "creative_excellence_score": 71.0,
        "opportunity_score": 66.0,
        "hook_score": 72.0,
        "viewer_prediction": 70.0,
        "timing": {
            "elapsed_ms": 90000,
            "render_ms": 8000,
            "stage_ms": {"research": 12000, "voice_generation": 40000},
        },
        "failures": [{"stage": "export", "warning": "mp4_not_yet_materialized"}],
        "weaknesses": [],
        "creative_recommendation": "Fix curiosity",
        "audience_lesson": "Wrong belief open",
    }
    card["measurements"]["hook_strength"] = 55
    card["measurements"]["visual_quality"] = 60
    stored = store_validation(card, validation_id="vp_test_001", optimization=[])
    assert (tmp_path / "runs" / "vp_test_001" / "Production_Report.json").exists()
    assert stored["validation_id"] == "vp_test_001"
    rows = list_validations(query="Ice")
    assert rows and rows[0]["validation_id"] == "vp_test_001"

    bottlenecks = detect_bottlenecks(rows)
    assert bottlenecks["sample_size"] == 1
    recs = build_recommendations(bottlenecks)
    assert recs
    assert all(r.get("architecture_change_allowed") is False for r in recs)
    assert "problem" in recs[0] and "evidence" in recs[0] and "priority" in recs[0]
