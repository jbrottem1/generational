"""Tests — permanent Studio Asset #0001 The Doctor."""

from __future__ import annotations

from pathlib import Path

from services.character_world_studio import list_hosts, list_locations, studio_place_candidate
from services.studio_assets import ensure_the_doctor_asset, get_asset, the_doctor_host_profile


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "data" / "studio_assets" / "CHAR-0001-THE-DOCTOR"


def test_ensure_writes_permanent_package():
    manifest = ensure_the_doctor_asset(force=False)
    assert manifest["id"] == "CHAR-0001"
    assert (ASSET / "CHARACTER_PROFILE.json").is_file()
    assert (ASSET / "CHARACTER_MODEL_GUIDE.pdf").is_file()
    assert (ASSET / "VOICE_PROFILE.json").is_file()
    assert (ASSET / "BIOGRAPHY.md").is_file()
    assert (ASSET / "CONTINUITY_RULES.md").is_file()
    assert (ASSET / "CHARACTER_IDENTITY.json").is_file()
    assert (ASSET / "HUMAN_REALISM" / "SKELETON_PROFILE.json").is_file()
    assert (ASSET / "COLOR_GUIDE.md").is_file()
    assert (ASSET / "WORLD_GUIDE.md").is_file()
    assert len(list((ASSET / "CHARACTER_EXPRESSIONS").glob("*.png"))) >= 14
    assert len(list((ASSET / "POSE_LIBRARY").glob("*.png"))) >= 15
    assert (ASSET / "ENVIRONMENT_PACKAGE" / "WORLD_PACKAGE.json").is_file()
    assert get_asset("CHAR-0001") is not None


def test_host_profile_is_permanent_flagship():
    host = the_doctor_host_profile()
    assert host["id"] == "CHAR-0001"
    assert host["permanent_ip"] is True
    assert host["flagship_science_educator"] is True
    assert "medicine" in host["domains"]


def test_cws_includes_doctor_and_gmri():
    ids = {h["id"] for h in list_hosts()}
    assert "DOCTOR_001" in ids
    assert "CHAR-0001" in ids  # legacy alias
    locs = {loc["id"] for loc in list_locations()}
    assert "LOC-GMRI" in locs


def test_science_topic_casts_the_doctor():
    cand = {
        "topic": "How Your Heart Pumps Blood",
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": "Anatomy and medicine begin with the beating heart.",
                    "length_sec": 3.0,
                }
            ]
        },
    }
    out = studio_place_candidate(cand, write=False)
    assert out["primary_host"]["id"] == "DOCTOR_001"
    assert out["primary_host"]["name"] == "The Doctor"
    assert out["primary_host"].get("legacy_alias") == "CHAR-0001"


def test_ensure_idempotent_does_not_require_force():
    a = ensure_the_doctor_asset(force=False)
    b = ensure_the_doctor_asset(force=False)
    assert a["id"] == b["id"] == "CHAR-0001"
