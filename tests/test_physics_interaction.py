"""Physics & Interaction Engine — physical behavior contracts."""

from __future__ import annotations

from services.physics_interaction import (
    attach_physics_interactions,
    build_interaction_package,
    build_physics_profile,
    build_scene_physics,
    ensure_physics_library,
    validate_interaction_package,
    validate_physics_profile,
)
from services.physics_interaction.models import SUPPORTED_INTERACTIONS


def test_interaction_package_fields():
    ix = build_interaction_package(
        actor="DOCTOR_001",
        target="microscope",
        interaction_type="using_microscopes",
        physics_state="manipulating",
        world_id="WORLD-GMRI-MEDICAL-LAB",
    )
    assert ix["package_type"] == "INTERACTION_PACKAGE"
    assert ix["actor"] == "DOCTOR_001"
    assert ix["interaction_type"] == "using_microscopes"
    assert ix["contact_points"]
    assert ix["constraints"]["no_float"] is True
    assert ix["constraints"]["no_clip"] is True
    assert ix["constraints"]["no_teleport"] is True
    assert ix["animation_requirements"]
    assert ix["completion_state"]["required_final_state"] == "complete"
    assert validate_interaction_package(ix)["ok"] is True


def test_physics_profile_and_library():
    try:
        from services.stage_world_simulation import resolve_world_package

        stage = resolve_world_package("WORLD-GMRI-MEDICAL-LAB")
    except Exception:  # noqa: BLE001
        stage = None
    profile = build_physics_profile(
        "DOCTOR_001",
        world_id="WORLD-GMRI-MEDICAL-LAB",
        stage_world=stage,
        interactions=[
            build_interaction_package(
                actor="DOCTOR_001",
                target="door",
                interaction_type="opening_doors",
            )
        ],
    )
    assert profile["package_type"] == "PHYSICS_PROFILE"
    assert set(SUPPORTED_INTERACTIONS).issubset(set(profile["supported_interactions"]))
    assert profile["hand_physics"]["capabilities"]
    assert profile["foot_physics"]["planting"]["no_slide"] is True
    assert profile["collision"]["enabled"] is True
    assert profile["objects"]
    assert profile["validation"]["ok"] is True
    lib = ensure_physics_library(write_packages=True)
    assert int(lib["count"]) >= 4


def test_rejects_broken_physics():
    assert validate_interaction_package({})["ok"] is False
    bad = validate_physics_profile(
        {
            "hand_physics": {},
            "foot_physics": {"planting": {}},
            "body_physics": {"forbid": [], "balance": {}},
            "collision": {"enabled": False},
            "clothing_physics": {},
            "hair_physics": {},
            "objects": [],
        }
    )
    assert bad["ok"] is False
    assert "floating_actors" in bad["rejects_hit"] or bad["failures"]


def test_attach_and_scene_physics():
    scenes = attach_physics_interactions(
        [
            {
                "scene_number": 1,
                "studio_character_id": "DOCTOR_001",
                "narration": "Open the door and use the microscope.",
                "length_sec": 4.0,
                "actor_interactions": {
                    "events": [
                        {"t": 1.0, "verb": "open_door", "target": "door"},
                        {"t": 2.0, "verb": "look_through_microscope", "target": "microscope"},
                    ]
                },
            }
        ],
        location="LOC-GMRI",
    )
    row = scenes[0]
    assert row["physics_constraints"]["no_float"] is True
    assert row["interaction_packages"]
    assert row["true_motion"]["physics_constrained"] is True
    bundle = build_scene_physics(
        character_id="DOCTOR_001",
        scene=row,
        scene_index=0,
        location="LOC-GMRI",
    )
    assert bundle["interaction_count"] >= 2
    assert bundle["validation"]["ok"] is True
