"""Tests — Generational Visual Foundation V1."""

from __future__ import annotations

from pathlib import Path

from services.visual_foundation import load_foundation, review_visual_foundation, visual_target

ROOT = Path(__file__).resolve().parents[1]


def test_foundation_files_exist():
    assert (ROOT / "GENERATIONAL_VISUAL_FOUNDATION_V1.md").is_file()
    assert (ROOT / "data/visual_foundation/VISUAL_FOUNDATION_V1.json").is_file()
    assert (ROOT / "data/visual_foundation/HUMAN_CHARACTER_REALISM_V1.md").is_file()


def test_target_is_cinematic_realism_not_photoreal_slogan():
    assert "cinematic" in visual_target().lower()
    data = load_foundation()
    assert "uncanny_photoreal_real_life" in (data.get("not_target") or [])


def test_gate_approves_living_studio_cast():
    report = review_visual_foundation(
        {
            "style_mode": "cinematic_realism",
            "studio_cast": [{"id": "CHAR-0001", "silhouette": "doctor", "permanent_ip": True}],
            "studio_location": {
                "id": "LOC-GMRI",
                "ambient_life": ["staff"],
                "detail_dressing": ["props"],
            },
            "visual_package": {
                "scenes": [{"studio_character_id": "CHAR-0001", "studio_expression": "teaching"}]
            },
        }
    )
    assert report["approved"] is True
    assert report["decision"] == "APPROVE"


def test_gate_rejects_empty_world():
    report = review_visual_foundation({"topic": "x", "visual_package": {"scenes": [{}]}})
    assert report["approved"] is False
    assert report["decision"] == "REJECT"
