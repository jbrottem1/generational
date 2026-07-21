"""Character Rig Studio — permanent digital actors."""

from __future__ import annotations

from services.character_rig_studio import (
    attach_character_rigs,
    build_character_rig,
    ensure_library,
    resolve_character_rig,
    validate_character_rig,
)
from services.character_rig_studio.models import PERFORMANCE_CLIPS, SKELETON_HIERARCHY


def test_doctor_rig_passes_and_composes_existing():
    pkg = build_character_rig("DOCTOR_001")
    assert pkg["package_type"] == "CHARACTER_RIG_PACKAGE"
    assert pkg["identity"]["forbid_regenerate_per_scene"] is True
    assert pkg["identity"]["composed_from_existing"] is True
    assert pkg["philosophy"]["not_a_renderer"] is True
    assert len(pkg["body_rig"]["hierarchy"]) >= len(SKELETON_HIERARCHY)
    assert "index_01_right" in pkg["body_rig"]["hierarchy"]
    assert set(PERFORMANCE_CLIPS).issubset(set(pkg["performance_system"]["clips"]))
    assert pkg["wardrobe"]["architecture"] == "clothing_separated_from_body"
    assert "lab_coat" in pkg["wardrobe"]["outfit_ids"]
    assert pkg["validation"]["ok"] is True


def test_founder_and_library():
    founder = build_character_rig("FOUNDER_001")
    assert founder["identity"]["canonical_name"] == "The Founder"
    assert founder["validation"]["ok"] is True
    lib = ensure_library(write_packages=True)
    ids = {a["character_id"] for a in lib["actors"]}
    assert {"DOCTOR_001", "FOUNDER_001", "TEACHER_001", "PATIENT_CHILD_001"}.issubset(ids)
    resolved = resolve_character_rig("DOCTOR_001")
    assert resolved["character_id"] == "DOCTOR_001"


def test_incomplete_rig_rejected():
    review = validate_character_rig({"identity": {"character_id": "X"}})
    assert review["ok"] is False
    assert "appearance_changes_between_scenes" in review["rejects_hit"] or review["failures"]


def test_attach_scene_refs_actor():
    scenes = attach_character_rigs(
        [{"scene_number": 1, "studio_character_id": "DOCTOR_001", "narration": "Teach."}]
    )
    row = scenes[0]
    assert row["character_rig_ref"]
    assert row["character_rig_package"]["do_not_regenerate"] is True
    assert row["character_continuity_version"]
