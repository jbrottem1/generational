"""Tests for Character Systems (Agent 26) — Professor Gen consistency."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.animation.fluid_motion import GESTURE_POSES
from services.animation.stick_figure import StickFigureSpec, draw_stick_figure
from services.character_systems import (
    FORBIDDEN_PROFESSOR_GESTURES,
    PROFESSOR_CHARACTER_ID,
    ConsistencyError,
    load_character,
    load_character_systems_registry,
    validate_attire,
    validate_gesture_for_character,
    validate_palette,
    validate_production_character,
    validate_proportions,
)
from services.character_systems.validation import professor_stick_figure_spec

REPO = Path(__file__).resolve().parents[1]
PROF_DIR = REPO / "data" / "universe" / "characters" / "CHAR-PROFESSOR-001"
CS_DIR = REPO / "data" / "character_systems"

# Coat fill / teal accents from gated lab-coat path in stick_figure.py
_COAT_FILL = (245, 248, 252)
_TEAL_ACCENT = (64, 196, 180)


def _count_near_rgb(img, target: tuple[int, int, int], *, tol: int = 8, min_alpha: int = 100) -> int:
    tr, tg, tb = target
    n = 0
    for px in img.getdata():
        if len(px) < 4 or px[3] < min_alpha:
            continue
        if abs(px[0] - tr) <= tol and abs(px[1] - tg) <= tol and abs(px[2] - tb) <= tol:
            n += 1
    return n


def test_professor_folder_and_docs_exist():
    assert (PROF_DIR / "CHARACTER.md").is_file()
    assert (PROF_DIR / "design_spec.json").is_file()
    assert (PROF_DIR / "expression_sheet.json").is_file()
    assert (PROF_DIR / "gesture_sheet.json").is_file()
    assert (PROF_DIR / "turnaround_notes.md").is_file()
    for name in (
        "CHARACTER_BIBLE.md",
        "PROFESSOR_PROFILE.md",
        "CHARACTER_LIBRARY.md",
        "ANIMATION_STYLE_GUIDE.md",
        "CHARACTER_QC_CHECKLIST.md",
        "registry.json",
    ):
        assert (CS_DIR / name).is_file(), name
    assert (REPO / "CHARACTER_BIBLE.md").is_file()


def test_load_character_professor():
    data = load_character(PROFESSOR_CHARACTER_ID)
    assert data["character_id"] == PROFESSOR_CHARACTER_ID
    assert data["design_spec"]["character_id"] == PROFESSOR_CHARACTER_ID
    assert data["design_spec"]["name"] == "Professor Gen"
    assert data["design_spec"]["attire"] == "none"
    assert data["design_spec"]["stick_figure"]["attire"] == "none"
    assert data["design_spec"]["voice_profile"]["voice"] == "nova"
    assert data["design_spec"]["voice_profile"]["model"] == "tts-1-hd"


def test_validate_production_character_ok():
    result = validate_production_character(PROFESSOR_CHARACTER_ID, gestures=["idle", "write", "point"])
    assert result["ok"] is True
    assert result["errors"] == []


def test_validate_rejects_wrong_palette():
    bad = StickFigureSpec(
        character_id=PROFESSOR_CHARACTER_ID,
        name="Professor Gen",
        outline=(255, 0, 0, 255),
        face_fill=(255, 255, 255, 255),
        stroke=7,
        head_ratio=0.34,
    )
    result = validate_production_character(bad)
    assert result["ok"] is False
    assert any("palette.outline" in e for e in result["errors"])


def test_validate_rejects_wrong_face_fill():
    bad = StickFigureSpec(
        character_id=PROFESSOR_CHARACTER_ID,
        name="Professor Gen",
        outline=(0, 0, 0, 255),
        face_fill=(200, 200, 255, 255),
        stroke=7,
        head_ratio=0.34,
    )
    errs = validate_palette(bad, character_id=PROFESSOR_CHARACTER_ID)
    assert errs
    assert any("face_fill" in e for e in errs)


def test_validate_rejects_wrong_id():
    wrong = StickFigureSpec(
        character_id="CHAR-WRONG",
        name="Professor Gen",
        outline=(0, 0, 0, 255),
        face_fill=(255, 255, 255, 255),
        stroke=7,
        head_ratio=0.34,
    )
    # Treating as professor production via professor_mode still checks id when validating Gen path
    result = validate_production_character(wrong, professor_mode=True)
    # Wrong id is not Gen — palette rules for Gen not applied; gesture rules still apply
    assert result["character_id"] == "CHAR-WRONG"
    # Explicit id check for Gen loader
    loaded = load_character(PROFESSOR_CHARACTER_ID)
    loaded["design_spec"] = {**loaded["design_spec"], "character_id": "CHAR-FAKE"}
    result2 = validate_production_character(loaded)
    assert result2["ok"] is False
    assert any("mismatch" in e for e in result2["errors"])


def test_validate_rejects_wrong_proportions():
    bad = StickFigureSpec(
        character_id=PROFESSOR_CHARACTER_ID,
        name="Professor Gen",
        outline=(0, 0, 0, 255),
        face_fill=(255, 255, 255, 255),
        stroke=12,
        head_ratio=0.5,
    )
    errs = validate_proportions(bad, character_id=PROFESSOR_CHARACTER_ID)
    assert any("stroke" in e for e in errs)
    assert any("head_ratio" in e for e in errs)


def test_validate_rejects_lab_coat_attire():
    bad = StickFigureSpec(
        character_id=PROFESSOR_CHARACTER_ID,
        name="Professor Gen",
        outline=(0, 0, 0, 255),
        face_fill=(255, 255, 255, 255),
        stroke=7,
        head_ratio=0.34,
        attire="lab_coat",
    )
    errs = validate_attire(bad, character_id=PROFESSOR_CHARACTER_ID)
    assert errs
    assert any("lab_coat" in e for e in errs)
    result = validate_production_character(bad)
    assert result["ok"] is False
    assert any("attire" in e for e in result["errors"])


def test_wave_forbidden_for_professor():
    assert "wave" in FORBIDDEN_PROFESSOR_GESTURES
    errs = validate_gesture_for_character("wave", character_id=PROFESSOR_CHARACTER_ID, professor_mode=True)
    assert errs
    result = validate_production_character(
        PROFESSOR_CHARACTER_ID,
        gestures=["idle", "wave", "wave"],
        professor_mode=True,
    )
    assert result["ok"] is False
    assert any("wave" in e for e in result["errors"])
    assert any("spam" in e for e in result["errors"])


def test_react_forbidden_for_professor():
    result = validate_production_character(PROFESSOR_CHARACTER_ID, gestures=["react"])
    assert result["ok"] is False


def test_registry_covers_gesture_poses_and_planned():
    reg = load_character_systems_registry()
    locked_keys = {
        g["gesture_key"] for g in reg["gestures"] if g.get("status") == "locked"
    }
    planned_keys = {
        g["gesture_key"] for g in reg["gestures"] if g.get("status") == "planned"
    }
    assert set(GESTURE_POSES.keys()) == locked_keys
    for key in ("greeting", "listening", "celebrating"):
        assert key in planned_keys
    # All gesture statuses are locked or planned
    for g in reg["gestures"]:
        assert g["status"] in ("locked", "planned")


def test_universe_registry_lists_professor_without_breaking_others():
    universe = json.loads((REPO / "data" / "universe" / "registry.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in universe["characters"]}
    assert "CHAR-PROFESSOR-001" in by_id
    assert by_id["CHAR-PROFESSOR-001"]["status"] == "locked"
    assert by_id["CHAR-DASH"]["status"] == "locked"
    assert by_id["CHAR-STICK-001"]["status"] == "locked"
    assert "relationship" in by_id["CHAR-PROFESSOR-001"] or "role" in by_id["CHAR-PROFESSOR-001"]


def test_canonical_spec_validates():
    spec = professor_stick_figure_spec()
    assert spec.attire == "none"
    result = validate_production_character(spec, gestures=["idle", "write", "think", "present"])
    assert result["ok"] is True


def test_professor_coat_false_renders_without_coat_fill():
    """professor=True + coat=False (Gen default) must not paint coat / teal accents."""
    spec = professor_stick_figure_spec()
    clean = draw_stick_figure(size=256, professor=True, coat=False, gesture="idle", spec=spec)
    assert _count_near_rgb(clean, _COAT_FILL, tol=6) == 0
    assert _count_near_rgb(clean, _TEAL_ACCENT, tol=6) == 0

    # Default attire path (no coat arg) also stays clean
    defaulted = draw_stick_figure(size=256, professor=True, gesture="idle", spec=spec)
    assert _count_near_rgb(defaulted, _COAT_FILL, tol=6) == 0
    assert _count_near_rgb(defaulted, _TEAL_ACCENT, tol=6) == 0


def test_professor_coat_opt_in_still_draws_coat():
    """MacroCenter may request coat later — gated path must still work."""
    coated = draw_stick_figure(size=256, professor=True, coat=True, gesture="idle")
    assert _count_near_rgb(coated, _COAT_FILL, tol=6) > 50
    assert _count_near_rgb(coated, _TEAL_ACCENT, tol=10) > 10

    via_attire = draw_stick_figure(size=256, professor=True, attire="lab_coat", gesture="idle")
    assert _count_near_rgb(via_attire, _COAT_FILL, tol=6) > 50


def test_consistency_error_is_value_error():
    assert issubclass(ConsistencyError, ValueError)
