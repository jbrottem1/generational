"""Stage & World Simulation Engine — persistent explorable stages."""

from __future__ import annotations

from services.stage_world_simulation import (
    attach_world_simulation,
    build_world_package,
    ensure_world_library,
    resolve_world_package,
    validate_world_package,
)
from services.stage_world_simulation.models import NAV_CAPABILITIES


def test_gmri_lab_world_passes():
    pkg = build_world_package("WORLD-GMRI-MEDICAL-LAB")
    assert pkg["package_type"] == "WORLD_PACKAGE"
    assert pkg["persistent"] is True
    assert pkg["flat_image_background"] is False
    assert pkg["geometry"]["not_a_flat_image"] is True
    assert pkg["geometry"]["floor"]
    assert set(NAV_CAPABILITIES).issubset(set(pkg["navigation"]["capabilities"]))
    assert pkg["interaction_points"]["count"] >= 3
    assert pkg["living_world"]["living"] is True
    assert pkg["camera"]["follows_performance"] is True
    assert pkg["camera"]["camera_replaces_actor_motion"] is False
    assert pkg["validation"]["ok"] is True


def test_recurring_locations_and_aliases():
    lib = ensure_world_library(write_packages=True)
    assert int(lib["count"]) >= 10
    museum = resolve_world_package("LOC-SCIENCE-MUSEUM")
    assert museum["world_id"] == "WORLD-SCIENCE-MUSEUM"
    forest = resolve_world_package("Forest")
    assert forest["world_id"] == "WORLD-FOREST"
    assert forest["validation"]["ok"] is True


def test_flat_photo_rejected():
    review = validate_world_package(
        {
            "flat_image_background": True,
            "geometry": {"not_a_flat_image": False, "explorable_volume": False},
            "navigation": {"capabilities": [], "nav_mesh": {}},
            "interaction_points": {"count": 0, "points": []},
            "living_world": {"living": False, "forbid_static_environment": False, "channels": []},
            "camera": {"follows_performance": False, "camera_replaces_actor_motion": True},
            "persistent": False,
        }
    )
    assert review["ok"] is False
    assert "flat_image_background" in review["rejects_hit"]


def test_attach_stamps_scene_refs():
    scenes = attach_world_simulation(
        [{"scene_number": 1, "narration": "Walk to the microscope."}],
        location="LOC-GMRI",
    )
    row = scenes[0]
    assert row["world_id"] == "WORLD-GMRI-MEDICAL-LAB"
    assert row["world_package_ref"]
    assert row["stage_world_package"]["flat_image_background"] is False
    assert row["true_motion"]["stage_world"] is True
