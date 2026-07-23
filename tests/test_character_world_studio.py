"""Tests — Character & World Studio."""

from __future__ import annotations

from pathlib import Path

from services.animation_engine import build_animation_package
from services.character_world_studio import (
    list_hosts,
    list_locations,
    studio_place_candidate,
)
from services.character_world_studio.gate import review_studio_package
from services.virtual_film_director import direct_candidate


def _candidate() -> dict:
    return {
        "topic": "Why Fire Hydrants Are Different Colors",
        "world_package": {"world_type": "Suburban Neighborhood"},
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "length_sec": 3.0,
                    "narration": "These colors could determine whether firefighters save your house.",
                    "subject": "fire hydrants",
                },
                {
                    "scene_number": 2,
                    "purpose": "story_beat",
                    "length_sec": 3.5,
                    "narration": "Engineers designed hydrant flow ratings you can read at a glance.",
                },
                {
                    "scene_number": 3,
                    "purpose": "payoff",
                    "length_sec": 3.0,
                    "narration": "Flow rate matters when seconds decide if a house is saved.",
                },
            ]
        },
    }


def test_cast_and_locations_exist():
    assert len(list_hosts()) >= 6
    assert len(list_locations()) >= 9
    names = {h["name"] for h in list_hosts()}
    assert {"The Doctor", "Professor Atlas", "Nova", "Orion", "Piper", "Luna"} <= names


def test_studio_place_writes_package(tmp_path):
    out = studio_place_candidate(_candidate(), write=True, out_dir=tmp_path)
    pkg = out["CHARACTER_WORLD_STUDIO_PACKAGE"]
    assert pkg["package_type"] == "CHARACTER_WORLD_STUDIO_PACKAGE"
    assert (tmp_path / "CHARACTER_WORLD_STUDIO_PACKAGE.json").is_file()
    assert (tmp_path / "STUDIO_NOTES.md").is_file()
    assert pkg["quality_gate"]["approved"] is True
    assert out["generational_universe"] is True
    assert out["primary_host"]["id"]
    plates = pkg["character_plates"]
    assert plates
    for path in plates.values():
        assert Path(path).is_file()
    scene0 = out["visual_package"]["scenes"][0]
    assert scene0["studio_character_id"]
    assert scene0["character_plate_path"]
    assert scene0["studio_expression"]


def test_engineering_topic_casts_piper_or_atlas():
    out = studio_place_candidate(_candidate(), write=False)
    host_ids = {h["id"] for h in out["studio_cast"]}
    assert host_ids & {"CHAR-PIPER", "CHAR-ATLAS"}


def test_ocean_topic_picks_ocean_location():
    cand = _candidate()
    cand["topic"] = "Why Octopuses Have Three Hearts"
    cand["visual_package"]["scenes"][0]["narration"] = "Deep in the ocean an octopus swims with three hearts."
    out = studio_place_candidate(cand, write=False)
    assert "OCEAN" in str(out["studio_location"]["id"]) or "ocean" in str(out["studio_location"]["name"]).lower()


def test_animation_engine_uses_studio_host():
    directed = direct_candidate(_candidate(), write=False)
    placed = studio_place_candidate(directed, write=False)
    pkg = build_animation_package(placed, topic=placed["topic"], write=False)
    char_layers = [(d.get("layers") or {}).get("character") or {} for d in pkg["scene_decisions"]]
    assert any(c.get("source") == "character_world_studio" for c in char_layers)
    assert any(c.get("character_plate_path") for c in char_layers)
    tm = pkg["scenes"][0]["true_motion"]
    assert tm.get("studio_character_id")
    assert tm.get("forbid_placeholder_characters") is True


def test_gate_rejects_empty_cast():
    gate = review_studio_package({"cast": [], "location": {}, "character_plates": {}, "scene_bindings": []})
    assert gate["approved"] is False
    assert gate["decision"] == "REJECT"
