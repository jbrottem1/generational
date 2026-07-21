"""Permanent Studio Character DOCTOR_001 — complete reusable package."""

from __future__ import annotations

from pathlib import Path

from services.character_world_studio import list_hosts, studio_place_candidate
from services.studio_assets import ensure_doctor_001_asset, get_asset
from services.studio_assets.doctor_001.catalog import EXPRESSIONS


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "data" / "studio_assets" / "DOCTOR_001"


def test_ensure_builds_complete_studio_character():
    manifest = ensure_doctor_001_asset(force=False)
    assert manifest["character_id"] == "DOCTOR_001"
    assert manifest["status"] == "permanent"
    assert manifest["philosophy"]["not_episode_sheet"] is True
    assert (ASSET / "IDENTITY.json").is_file()
    assert (ASSET / "FACIAL_TOPOLOGY.json").is_file()
    assert (ASSET / "EYE_MOVEMENT_MODEL.json").is_file()
    assert (ASSET / "BLINKING_MODEL.json").is_file()
    assert (ASSET / "BREATHING_PROFILE.json").is_file()
    assert (ASSET / "RIG_SPECIFICATION.json").is_file()
    assert (ASSET / "ANIMATION_CONSTRAINTS.json").is_file()
    assert (ASSET / "VOICE_IDENTITY.json").is_file()
    assert (ASSET / "CATCH_PHRASES.json").is_file()
    assert (ASSET / "BIOGRAPHY.md").is_file()
    assert (ASSET / "CONTINUITY_RULES.md").is_file()
    assert (ASSET / "TEACHING_STYLE.md").is_file()
    assert (ASSET / "STRENGTHS_FLAWS.json").is_file()
    assert len(list((ASSET / "EXPRESSIONS").glob("*.png"))) >= 50
    assert len(EXPRESSIONS) >= 50
    assert len(list((ASSET / "ORTHOGRAPHIC").glob("*.png"))) >= 4
    assert len(list((ASSET / "HAND_POSES").glob("*.png"))) >= 10
    assert (ASSET / "ANIMATION" / "walking_cycle.json").is_file()
    assert (ASSET / "ANIMATION" / "running_cycle.json").is_file()
    assert (ASSET / "ANIMATION" / "idle.json").is_file()
    assert (ASSET / "ANIMATION" / "talking.json").is_file()
    assert (ASSET / "ANIMATION" / "teaching.json").is_file()
    assert (ASSET / "SCALE_REFERENCE" / "scale_185cm.png").is_file()
    assert (ASSET / "CAMERA_TESTS" / "index.json").is_file()
    assert (ASSET / "ENVIRONMENT_INTERACTIONS" / "index.json").is_file()
    assert get_asset("DOCTOR_001") is not None


def test_cws_casts_doctor_001_for_medical_topics():
    ids = {h["id"] for h in list_hosts()}
    assert "DOCTOR_001" in ids
    out = studio_place_candidate(
        {
            "topic": "Trichomonas and Clinical Clarity",
            "visual_package": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "Anatomy and medicine begin with careful observation.",
                        "length_sec": 3.0,
                    }
                ]
            },
        },
        write=False,
    )
    assert out["primary_host"]["id"] == "DOCTOR_001"
    assert out["visual_package"]["scenes"][0].get("performance_plan")
