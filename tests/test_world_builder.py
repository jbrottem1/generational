"""Persistent World & Environment System tests."""

from __future__ import annotations

from services.world_builder import (
    WORLD_TYPES,
    apply_state_event,
    apply_world_to_candidate,
    build_world_package,
    fulfill_world_request,
    get_catalog,
    get_library_world,
    load_state,
    place_candidate_in_world,
    reset_world_state,
    search_worlds,
    seed_library_from_catalog,
    select_best_world,
    select_world_type,
    validate_environment_package,
    validate_world_package,
)
from services.world_builder.models import empty_world_request


def test_catalog_covers_mission_templates():
    cat = get_catalog()
    assert "Ocean Research Observatory" in WORLD_TYPES
    assert "AI Laboratory" in WORLD_TYPES
    assert len(WORLD_TYPES) >= 23
    for wt in WORLD_TYPES:
        assert any(w["world_type"] == wt for w in cat.values()), wt


def test_seed_and_retrieve_library():
    seed = seed_library_from_catalog()
    assert seed["ok"]
    assert seed["total"] >= 20
    wid = "WORLD-OCEAN_RESEARCH_OBSERVATORY"
    w = get_library_world(wid)
    assert w
    assert len(w.get("zones") or []) == 3


def test_semantic_selection_octopus_and_ai():
    assert select_world_type(topic="Why Octopuses Have Three Hearts", niche="biology") == "Ocean Research Observatory"
    sel = select_best_world(topic="Why Octopuses Have Three Hearts", audience="general_public")
    assert "OCEAN" in str(sel["best"]["world_id"]).upper() or sel["best"]["world_type"] == "Ocean Research Observatory"
    assert select_world_type(topic="How Artificial Intelligence Learns Patterns", niche="technology") == "AI Laboratory"


def test_environment_packages_and_zone_continuity():
    reset_world_state("WORLD-OCEAN_RESEARCH_OBSERVATORY", "octopus_test")
    pkg = build_world_package(
        {
            "title": "Why Octopuses Have Three Hearts",
            "topic": "Why Octopuses Have Three Hearts",
            "niche": "biology",
            "platform": "youtube_shorts",
            "audience": "general_public",
            "script": (
                "Octopuses have three hearts. "
                "Two push blood through the gills. "
                "The third powers the body. "
                "When they swim, that heart nearly pauses."
            ),
            "visual_package": {
                "scenes": [
                    {"scene_id": "s1", "narration": "Hook at the observatory"},
                    {"scene_id": "s2", "narration": "View the octopus through glass"},
                    {"scene_id": "s3", "narration": "Heart diagram at the display"},
                ]
            },
        },
        scene_count=3,
        production_id="octopus_test",
        world_type="Ocean Research Observatory",
        platform="youtube_shorts",
        audience="general_public",
    )
    assert pkg["world_type"] == "Ocean Research Observatory"
    assert len(pkg["environment_packages"]) == 3
    zones = [e["selected_zone"] for e in pkg["environment_packages"]]
    assert zones[0] != zones[1] or zones[1] != zones[2] or len(set(zones)) >= 2
    assert pkg["validation"]["ok"] is True
    assert pkg["continuity_validation"]["ok"] is True
    # No cinematic prescriptions
    assert all(e.get("cinematic_prescriptions") is None for e in pkg["environment_packages"])
    # Persistent aquarium referenced
    all_obj_names = []
    for e in pkg["environment_packages"]:
        all_obj_names.extend([o.get("name") for o in e.get("required_persistent_objects") or []])
    assert any("aquarium" in str(n).lower() or "viewport" in str(n).lower() for n in all_obj_names)


def test_state_updates_and_reset():
    wid = "WORLD-AI_LABORATORY"
    reset_world_state(wid, "ai_state_test")
    state = load_state(wid, "ai_state_test")
    state = apply_state_event(state, "display_activated", {"display_id": "obj_neural_holo", "content": "patterns"})
    state = apply_state_event(
        state,
        "object_moved",
        {"object_id": "obj_ops_console", "position": {"x": 0.2, "y": 0.0, "z": 0.5}, "reason": "professor moves"},
    )
    assert state["displays"]["obj_neural_holo"]["active"] is True
    assert state["object_positions"]["obj_ops_console"]["position"]["x"] == 0.2
    reset = reset_world_state(wid, "ai_state_test")
    assert reset["displays"] == {}


def test_ai_lab_validation_production():
    reset_world_state("WORLD-AI_LABORATORY", "ai_patterns")
    pkg = build_world_package(
        topic="How Artificial Intelligence Learns Patterns",
        niche="technology",
        world_type="AI Laboratory",
        scene_count=3,
        production_id="ai_patterns",
        platform="youtube_shorts",
        audience="general_public",
    )
    assert pkg["world_type"] == "AI Laboratory"
    assert len(pkg["environment_packages"]) == 3
    assert pkg["validation"]["ok"]
    # Holo remains at stage across packages unless moved
    positions = []
    for e in pkg["environment_packages"]:
        for o in e.get("required_persistent_objects") or []:
            if o.get("object_id") == "obj_neural_holo":
                positions.append(o.get("position"))
    assert positions
    assert all(p == positions[0] for p in positions)


def test_cinematic_director_separation():
    directed = place_candidate_in_world(
        {
            "title": "AI patterns",
            "topic": "How Artificial Intelligence Learns Patterns",
            "niche": "technology",
            "cinematic_direction_package": {"shot_list": [{"camera": "push_in"}], "keep": True},
            "visual_package": {
                "scenes": [
                    {"scene_id": "s1", "lighting": "dramatic", "camera": "push_in"},
                    {"scene_id": "s2", "lighting": "soft", "camera": "orbit"},
                ]
            },
        },
        world_type="AI Laboratory",
        production_id="sep_test",
    )
    assert directed["cinematic_direction_package"]["keep"] is True
    assert directed["visual_package"]["scenes"][0]["camera"] == "push_in"
    assert directed["visual_package"]["scenes"][0]["lighting"] == "dramatic"
    assert "environment_package" in directed["visual_package"]["scenes"][0]
    assert directed["world_package"]["contracts"]["cinematic_direction_package"] == "services.cinematic_director"


def test_request_contract_and_asset_requirements():
    req = empty_world_request(
        topic="Octopus hearts",
        location_type="Ocean Research Observatory",
        required_objects=["specimen label"],
        platform="youtube_shorts",
        audience="general_public",
    )
    pkg = fulfill_world_request(req, scene_count=2, production_id="req_test")
    assert pkg["environment_packages"]
    assert "asset_requirements" in pkg["environment_packages"][0]
    temps = pkg["environment_packages"][0].get("required_temporary_objects") or []
    assert any("specimen" in str(t.get("name")).lower() for t in temps)


def test_invalid_floating_and_missing_identity():
    bad = {
        "world_id": "",
        "world": {"objects": [{"name": "orb", "anchored": False, "surface": ""}]},
        "environment_packages": [],
        "continuity": {"scene_bindings": []},
    }
    v = validate_world_package(bad)
    assert v["ok"] is False
    assert v["hard_failures"]


def test_search_worlds():
    hits = search_worlds("ocean octopus", limit=5)
    assert hits
    assert any("OCEAN" in str(h.get("world_id") or "").upper() for h in hits)


def test_env_package_validator_rejects_cinematic_prescriptions():
    env = {
        "world_id": "W",
        "selected_zone": "z",
        "environment_name": "Lab",
        "spatial_layout": {"zone_id": "z"},
        "required_persistent_objects": [{"name": "desk", "surface": "floor", "anchored": True}],
        "cinematic_prescriptions": {"camera": "push_in"},
        "scale": "room",
    }
    v = validate_environment_package(env, world={"world_id": "W", "scale": "room", "zones": [{"id": "z"}]})
    assert "world_instructions_conflict_with_boundaries" in v["hard_fails"]


def test_apply_enriches_without_replacing_scene_builder_purpose():
    out = apply_world_to_candidate(
        {
            "visual_package": {
                "scenes": [{"scene_id": "s1", "purpose": "hook", "narration": "Stop"}]
            }
        },
        build_world_package(topic="DNA helix", niche="biology", world_type="DNA Interior", scene_count=1, production_id="dna_t"),
    )
    assert out["visual_package"]["scenes"][0]["purpose"] == "hook"
    assert out["visual_package"]["scenes"][0]["world_id"]
