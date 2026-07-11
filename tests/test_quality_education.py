"""Tests for quality scoring and educational director."""

from services.education.director_review import review_lesson
from services.quality.content_score import score_production


def test_educational_review_passes_solid_lesson():
    review = review_lesson(
        hook="Why doesn't your stomach digest itself?",
        script="Stomach acid breaks down food. A mucus layer protects the stomach wall.",
        takeaway="Mucus shields living tissue from acid.",
        main_concept="Stomach self-protection",
        has_visual_demo=True,
        sources=["https://example.org/stomach"],
    )
    assert review.passed
    assert review.accuracy_score >= 60


def test_educational_review_fails_empty():
    review = review_lesson(script="Hi.")
    assert not review.passed
    assert review.hard_fails


def test_quality_score_hard_fail_missing_export():
    report = score_production({"qc": {"passed": True}})
    assert not report.passed
    assert "missing_export_path" in report.hard_fails


def test_quality_score_from_qc():
    report = score_production(
        {
            "export_path": "/tmp/out.mp4",
            "export_bytes": 120_000,
            "qc": {
                "passed": True,
                "purposeful_gestures": True,
                "idle_ratio": 0.4,
                "walk_ratio": 0.08,
                "mouth_varies": True,
                "speaking_ratio": 0.4,
                "grounded": True,
            },
            "hook": "Cells are life's building blocks.",
            "script": {"hook": "Cells are life's building blocks.", "takeaway": "Life is cellular."},
        }
    )
    assert report.scores["animation_quality"] >= 70
    assert report.hard_fails == []
