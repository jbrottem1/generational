"""Character, Universe & IP department — service-level tests (Agent 15).

Covers: character/universe creation, relationship tracking, memory,
continuity validation, timeline management, brand/lore consistency,
franchise management, versioning/archiving, and failure handling.
"""

from __future__ import annotations

import pytest

from services.character_universe.bible import build_bible
from services.character_universe.config import (
    CharacterUniverseConfig,
    set_character_universe_config,
)
from services.character_universe.continuity import ContinuityEngine
from services.character_universe.franchise import FranchiseManager
from services.character_universe.memory import CharacterMemorySystem
from services.character_universe.models import (
    CHARACTER_FIELDS,
    RELATIONSHIP_FIELDS,
    VISUAL_PROFILE_FIELDS,
    VOICE_PROFILE_FIELDS,
    RelationType,
    build_character,
)
from services.character_universe.registry import CharacterUniverseRegistry
from services.character_universe.relationships import RelationshipEngine
from services.character_universe.store import CharacterUniverseStore
from services.character_universe.world_models import (
    STORY_BIBLE_FIELDS,
    UNIVERSE_FIELDS,
    build_universe,
)


@pytest.fixture(autouse=True)
def default_config():
    yield set_character_universe_config(CharacterUniverseConfig())


@pytest.fixture
def registry(tmp_path):
    return CharacterUniverseRegistry(CharacterUniverseStore(str(tmp_path / "cu")))


def make_character(registry, name="Captain Lyra", **extra):
    return registry.create_character(
        {
            "name": name,
            "biography": "A starship captain who teaches astronomy.",
            "personality_traits": ["brave", "curious"],
            "speech_style": "confident, warm",
            "catchphrases": ["To the stars!"],
            "visual_profile": {"hair": "silver hair", "art_style": "cel-shaded"},
            "voice_profile": {"voice_id": "voice_lyra_v1", "tone": "warm"},
            **extra,
        }
    )


# -------------------------------------------------------- character system


def test_character_creation_fills_full_contract(registry):
    character = make_character(registry)
    for field in CHARACTER_FIELDS:
        assert field in character, field
    for field in VISUAL_PROFILE_FIELDS:
        assert field in character["visual_profile"], field
    for field in VOICE_PROFILE_FIELDS:
        assert field in character["voice_profile"], field
    assert character["character_id"].startswith("char_")
    assert character["status"] == "active"
    assert character["memory"]["events"] == []
    # visual signature derived from parts when not given
    assert "silver hair" in character["visual_profile"]["visual_signature"]


def test_character_persists_and_reloads(registry):
    character = make_character(registry)
    loaded = registry.get("characters", character["character_id"])
    assert loaded["name"] == "Captain Lyra"
    assert loaded["catchphrases"] == ["To the stars!"]


def test_unknown_extra_fields_survive(registry):
    character = make_character(registry, future_field={"provider": "x"})
    loaded = registry.get("characters", character["character_id"])
    assert loaded["future_field"] == {"provider": "x"}


def test_character_limit_enforced(registry):
    set_character_universe_config(CharacterUniverseConfig(max_characters=1))
    make_character(registry)
    with pytest.raises(ValueError):
        make_character(registry, name="One Too Many")


# --------------------------------------------------------- universe system


def test_universe_creation_fills_full_contract(registry):
    universe = registry.create_universe(
        {"name": "Aster Belt", "lore": ["mining guilds rule"], "cultures": ["Belters"]}
    )
    for field in UNIVERSE_FIELDS:
        assert field in universe, field
    assert universe["timeline"]["universe_id"] == universe["universe_id"]


def test_locations_and_organizations_attach_to_universe(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    location = registry.create_location(
        {"name": "Port Ceres", "location_type": "city", "universe_id": universe["universe_id"]}
    )
    organization = registry.create_organization(
        {"name": "Miners Guild", "universe_id": universe["universe_id"]}
    )
    reloaded = registry.get("universes", universe["universe_id"])
    assert location["location_id"] in reloaded["location_ids"]
    assert organization["organization_id"] in reloaded["organization_ids"]


# ---------------------------------------------------- relationship engine


def test_relationship_tracking_and_strength_changes(registry):
    lyra = make_character(registry)
    kade = make_character(registry, name="Engineer Kade")
    engine = RelationshipEngine(registry)

    relationship = engine.link(
        lyra["character_id"], kade["character_id"], RelationType.MENTOR, strength=60
    )
    for field in RELATIONSHIP_FIELDS:
        assert field in relationship, field

    # indexed on both characters
    assert relationship["relationship_id"] in registry.get("characters", lyra["character_id"])["relationship_ids"]
    assert relationship["relationship_id"] in registry.get("characters", kade["character_id"])["relationship_ids"]

    adjusted = engine.adjust_strength(relationship["relationship_id"], +25, "saved the ship")
    assert adjusted["strength"] == 85
    assert adjusted["history"][-1]["change"] == "saved the ship"

    # clamped to 0-100
    assert engine.adjust_strength(relationship["relationship_id"], +999)["strength"] == 100

    ended = engine.end(relationship["relationship_id"], "graduated")
    assert ended["status"] == "ended" and ended["ended_at"]
    assert engine.relationship_context(lyra["character_id"]) == []


def test_relationship_queries(registry):
    lyra = make_character(registry)
    kade = make_character(registry, name="Engineer Kade")
    engine = RelationshipEngine(registry)
    engine.link(lyra["character_id"], kade["character_id"], RelationType.FRIEND)

    assert len(engine.for_character(lyra["character_id"])) == 1
    assert len(engine.between(lyra["character_id"], kade["character_id"])) == 1
    context = engine.relationship_context(lyra["character_id"])
    assert context[0]["with_name"] == "Engineer Kade"
    assert context[0]["relation_type"] == RelationType.FRIEND


# ------------------------------------------------------------ memory system


def test_character_memory_remember_and_recall(registry):
    lyra = make_character(registry)
    memory = CharacterMemorySystem(registry)
    memory.remember(lyra["character_id"], "events", "Discovered the Aster Belt", content_id="vid_001")
    memory.remember(lyra["character_id"], "achievements", "First contact")
    memory.record_evolution(lyra["character_id"], "became more cautious", reason="lost a crewmate")

    events = memory.recall(lyra["character_id"], "events")
    assert events[0]["summary"] == "Discovered the Aster Belt"
    assert events[0]["content_id"] == "vid_001"
    assert memory.recall(lyra["character_id"], "achievements")[0]["summary"] == "First contact"
    assert memory.recall(lyra["character_id"], "personality_evolution")
    assert memory.recall(lyra["character_id"], "growth_log")


def test_memory_compaction_respects_configured_size(registry):
    set_character_universe_config(CharacterUniverseConfig(memory_size=5))
    lyra = make_character(registry)
    memory = CharacterMemorySystem(registry)
    for index in range(12):
        memory.remember(lyra["character_id"], "events", f"event {index}")
    entries = memory.recall(lyra["character_id"], "events")
    assert len(entries) <= 5
    assert entries[0].get("compacted_count")          # oldest were summarized
    assert entries[-1]["summary"] == "event 11"        # newest kept verbatim


def test_memory_failure_handling(registry):
    memory = CharacterMemorySystem(registry)
    assert memory.remember("char_missing", "events", "x") is None
    with pytest.raises(ValueError):
        memory.remember("char_missing", "not_a_category", "x")


# -------------------------------------------------------- continuity engine


def test_duplicate_characters_detected(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    make_character(registry, universe_id=universe["universe_id"])
    make_character(registry, name="captain lyra", universe_id=universe["universe_id"])
    issues = ContinuityEngine(registry).validate_all(universe["universe_id"])
    assert any(issue["category"] == "duplicate_character" for issue in issues)


def test_missing_references_detected(registry):
    make_character(registry, universe_id="uni_nowhere")
    issues = ContinuityEngine(registry).validate_all()
    assert any(issue["category"] == "missing_reference" for issue in issues)


def test_relationship_errors_detected(registry):
    lyra = make_character(registry)
    engine = RelationshipEngine(registry)
    engine.link(lyra["character_id"], "char_ghost")
    issues = ContinuityEngine(registry).validate_all()
    assert any(issue["category"] == "relationship_error" for issue in issues)


def test_timeline_errors_detected(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    registry.create_canon_event(
        {"universe_id": universe["universe_id"], "title": "First landing", "sequence": 1}
    )
    registry.create_canon_event(
        {"universe_id": universe["universe_id"], "title": "Second landing", "sequence": 1}
    )
    issues = ContinuityEngine(registry).validate_all(universe["universe_id"])
    assert any(issue["category"] == "timeline_error" for issue in issues)


def test_canon_events_ordered_and_attached(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    second = registry.create_canon_event(
        {"universe_id": universe["universe_id"], "title": "War ends", "sequence": 2}
    )
    first = registry.create_canon_event(
        {"universe_id": universe["universe_id"], "title": "War begins", "sequence": 1}
    )
    events = registry.canon_events_for(universe["universe_id"])
    assert [event["event_id"] for event in events] == [first["event_id"], second["event_id"]]
    assert first["event_id"] in registry.get("universes", universe["universe_id"])["canon_event_ids"]


def test_visual_and_voice_drift_detected_on_appearance(registry):
    lyra = make_character(registry)
    continuity = ContinuityEngine(registry)
    result = continuity.record_appearance(
        {
            "character_id": lyra["character_id"],
            "content_id": "vid_002",
            "outfit": "red jumpsuit",
            "visual_signature": "completely different green-haired person",
            "voice_id": "voice_other_v9",
        }
    )
    categories = {issue["category"] for issue in result["issues"]}
    assert "visual_drift" in categories
    assert "voice_drift" in categories
    # history is queryable afterwards
    assert continuity.history_for(lyra["character_id"])[0]["content_id"] == "vid_002"
    assert continuity.outfit_history(lyra["character_id"])[0]["outfit"] == "red jumpsuit"


def test_lore_violations_and_brand_drift(registry):
    set_character_universe_config(
        CharacterUniverseConfig(
            lore_rules=[{"forbid": "time travel", "scope": "biography", "reason": "no time travel"}],
            brand_rules=[{"forbid": "competitor logo", "reason": "brand safety"}],
        )
    )
    rogue = make_character(registry, biography="A rogue who uses time travel.")
    issues = ContinuityEngine(registry).validate_all()
    assert any(issue["category"] == "lore_violation" for issue in issues)

    result = ContinuityEngine(registry).record_appearance(
        {"character_id": rogue["character_id"], "outfit": "jacket with competitor logo"}
    )
    assert any(issue["category"] == "brand_drift" for issue in result["issues"])


def test_continuity_strictness_modes(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    make_character(registry, universe_id=universe["universe_id"])  # clean catalog otherwise
    registry.create_canon_event({"universe_id": universe["universe_id"], "sequence": 3})
    registry.create_canon_event({"universe_id": universe["universe_id"], "sequence": 3})

    set_character_universe_config(CharacterUniverseConfig(continuity_strictness="strict"))
    strict = ContinuityEngine(registry).validate_all(universe["universe_id"])
    assert strict and all(issue["severity"] == "error" for issue in strict)

    set_character_universe_config(CharacterUniverseConfig(continuity_strictness="relaxed"))
    relaxed = ContinuityEngine(registry).validate_all(universe["universe_id"])
    assert all(issue["severity"] == "error" for issue in relaxed)  # warnings suppressed


def test_deceased_character_appearance_warns(registry):
    hero = make_character(registry, status="deceased")
    result = ContinuityEngine(registry).record_appearance(
        {"character_id": hero["character_id"], "content_id": "vid_003"}
    )
    assert any(issue["category"] == "status_error" for issue in result["issues"])


# ------------------------------------------------------ franchise management


def test_franchise_seasons_episodes_and_spinoffs(registry):
    lyra = make_character(registry)
    manager = FranchiseManager(registry)
    franchise = manager.create_franchise({"name": "Star Lessons", "franchise_type": "educational_program"})
    season = manager.add_season(franchise["franchise_id"], {"name": "Season One"})
    episode = manager.add_episode(
        franchise["franchise_id"], season["season_id"],
        {"title": "Gravity", "character_ids": [lyra["character_id"]], "content_id": "vid_010"},
    )
    assert episode["number"] == 1
    assert manager.episodes(franchise["franchise_id"])[0]["title"] == "Gravity"
    # cast rolls up to the franchise
    assert lyra["character_id"] in registry.get("franchises", franchise["franchise_id"])["character_ids"]
    assert manager.franchises_for_character(lyra["character_id"])[0]["name"] == "Star Lessons"

    spinoff = manager.create_spinoff(franchise["franchise_id"], {"name": "Star Lessons Jr."})
    assert spinoff["spinoff_of"] == franchise["franchise_id"]

    manager.record_performance(franchise["franchise_id"], {"avg_retention": 0.61})
    assert registry.get("franchises", franchise["franchise_id"])["performance"]["avg_retention"] == 0.61


def test_franchise_failure_handling(registry):
    manager = FranchiseManager(registry)
    assert manager.add_season("fra_missing") is None
    assert manager.add_episode("fra_missing", "sea_missing") is None
    assert manager.record_performance("fra_missing", {}) is None


# ------------------------------------------------- versioning & archiving


def test_update_bumps_version_and_archive_preserves_record(registry):
    lyra = make_character(registry)
    assert lyra["version"] == 1
    updated = registry.update("characters", lyra["character_id"], {"occupation": "admiral"})
    assert updated["version"] == 2
    assert updated["occupation"] == "admiral"

    assert registry.archive("characters", lyra["character_id"]) is True
    archived = registry.get("characters", lyra["character_id"])
    assert archived["status"] == "archived"          # archived, never deleted

    set_character_universe_config(CharacterUniverseConfig(archive_instead_of_delete=False))
    assert registry.archive("characters", lyra["character_id"]) is True
    assert registry.get("characters", lyra["character_id"]) is None


def test_update_and_archive_failure_handling(registry):
    assert registry.update("characters", "char_missing", {"name": "x"}) is None
    assert registry.archive("characters", "char_missing") is False


# ----------------------------------------------------------- story bible


def test_story_bible_snapshot(registry):
    universe = registry.create_universe({"name": "Aster Belt"})
    lyra = make_character(registry, universe_id=universe["universe_id"])
    kade = make_character(registry, name="Engineer Kade", universe_id=universe["universe_id"])
    RelationshipEngine(registry).link(lyra["character_id"], kade["character_id"])
    registry.create_canon_event({"universe_id": universe["universe_id"], "title": "Launch", "sequence": 1})

    bible = build_bible(universe["universe_id"], registry)
    for field in STORY_BIBLE_FIELDS:
        assert field in bible, field
    assert bible["universe"]["name"] == "Aster Belt"
    assert len(bible["characters"]) == 2
    assert len(bible["relationships"]) == 1
    assert len(bible["canon_events"]) == 1
    assert isinstance(bible["continuity_issues"], list)


def test_builders_are_pure_dict_normalizers():
    character = build_character({"name": "Solo"})
    universe = build_universe({})
    assert character["name"] == "Solo"
    assert universe["universe_id"].startswith("uni_")
    # fresh mutable defaults — no shared state between records
    character["goals"].append("x")
    assert build_character({"name": "Duo"})["goals"] == []
