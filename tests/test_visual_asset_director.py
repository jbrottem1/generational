"""Tests for Visual Asset Director — QC gate, not a renderer."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from services.visual_asset_director import (
    STYLE_LIBRARY,
    attach_visual_package_to_candidate,
    build_visual_package,
    evaluate_candidate,
    list_styles,
    resolve_style_profile,
    validate_visual_package,
)


def _make_plate(path: Path, *, vivid: bool = True) -> Path:
    img = Image.new("RGB", (1080, 1920), (20, 40, 70) if vivid else (90, 95, 100))
    draw = ImageDraw.Draw(img)
    if vivid:
        draw.rectangle((200, 400, 880, 1400), fill=(30, 160, 200))
        draw.ellipse((400, 700, 700, 1100), fill=(220, 180, 60))
        draw.line((100, 200, 900, 1600), fill=(255, 255, 255), width=8)
    else:
        draw.rectangle((300, 800, 780, 1100), fill=(95, 100, 105))
    img.save(path)
    return path


def test_style_library_and_resolve():
    styles = list_styles()
    assert len(styles) >= 10
    assert "documentary" in STYLE_LIBRARY
    profile = resolve_style_profile(None, niche="biology", topic="octopus hearts", world_type="ocean_research_observatory")
    assert profile["style_key"] == "documentary"
    medical = resolve_style_profile(None, topic="heart anatomy medical", niche="science")
    assert medical["style_key"] == "medical_visualization"


def test_evaluate_rejects_tiny_blurry(tmp_path):
    bad = tmp_path / "bad.png"
    Image.new("RGB", (64, 64), (128, 128, 128)).save(bad)
    ev = evaluate_candidate(str(bad), scene={"purpose": "hook"}, style_profile={"style_key": "documentary"})
    assert ev["approved"] is False
    assert "low_resolution" in ev["reject_reasons"]


def test_direct_selects_strongest(tmp_path):
    scenes = tmp_path / "scenes"
    scenes.mkdir()
    strong = _make_plate(scenes / "00_hook.png", vivid=True)
    weak = _make_plate(scenes / "01_body.png", vivid=False)
    # Extra pool plate that is strong for scene 1
    _make_plate(scenes / "01b_alt.png", vivid=True)

    pkg = build_visual_package(
        {"topic": "Test Marine Facts"},
        topic="Test Marine Facts",
        niche="biology",
        style="documentary",
        fallback_scene_dirs=[scenes],
        character_refs=[{"name": "Professor", "continuity_lock": True}],
        world_package={"world_id": "WORLD-TEST", "world_type": "ocean_research_observatory"},
        write=True,
    )
    assert pkg["package_type"] == "VISUAL_PACKAGE"
    assert Path(pkg["path"]).exists()
    assert pkg["style_profile"]["style_key"] == "documentary"
    assert pkg["continuity_report"]["world_id"] == "WORLD-TEST"
    assert "asset_manifest" in pkg
    # At least the vivid plates should be approvable
    assert len(pkg["approved_assets"]) >= 1
    assert strong.exists() and weak.exists()

    cand = attach_visual_package_to_candidate(
        {"topic": "Test Marine Facts", "visual_package": {"scenes": [{"scene_id": "scene_00", "purpose": "hook"}]}},
        pkg,
    )
    assert cand.get("visual_asset_direction")
    assert cand.get("prefer_approved_visual_assets") is True


def test_validate_empty_fails():
    result = validate_visual_package({"style_profile": {}, "approved_assets": [], "asset_manifest": []})
    assert result["ok"] is False
    assert "no_approved_assets" in result["hard_fails"]
