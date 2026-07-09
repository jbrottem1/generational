"""Character & Universe engine — pipeline/integration tests (Agent 15).

Covers: registration + contracts, orchestrator stage execution, Script
Generation integration payloads, Creative Studio context, Asset
Generation (Agent 14) request handover, Optimization Laboratory payload,
appearance/continuity flow through context, and Directive #1 safety.
"""

from __future__ import annotations

import pytest

import engines  # noqa: F401 - importing registers all engines
from engines import registry as engine_registry
from services.character_universe.config import (
    CharacterUniverseConfig,
    set_character_universe_config,
)
from services.character_universe.integrations import (
    asset_requests_for,
    character_prompt_fragment,
    creative_context_for,
    optimization_payload,
    script_context_for,
)
from services.character_universe.registry import CharacterUniverseRegistry
from services.character_universe.relationships import RelationshipEngine
from services.character_universe.seed import HOUSE_UNIVERSE_ID, ensure_house_cast
from services.character_universe.store import CharacterUniverseStore
from services.orchestrator import StageStatus, get_orchestrator
from services.orchestrator.stages import STAGE_GROUPS


@pytest.fixture(autouse=True)
def default_config():
    yield set_character_universe_config(CharacterUniverseConfig())


@pytest.fixture
def registry(tmp_path):
    return CharacterUniverseRegistry(CharacterUniverseStore(str(tmp_path / "cu")))


# -------------------------------------------------- registration & contract


def test_engine_registered_and_ready():
    engine = engine_registry.get_engine("character_universe")
    assert engine is not None
    assert engine.is_ready() is True
    assert engine.version.startswith("1.")


def test_engine_contract_diagnostics():
    engine = engine_registry.get_engine("character_universe")
    diagnostics = engine.diagnostics()
    assert diagnostics["engine_id"] == "character_universe"
    assert "character_script_contexts" in diagnostics["output_contract"]
    assert "story_bible" in diagnostics["output_contract"]
    assert diagnostics["dependencies"] == []          # no engine coupling
    assert engine.health_check()["healthy"] is True


def test_engine_output_satisfies_its_own_contract():
    engine = engine_registry.get_engine("character_universe")
    updates = engine.run({})
    assert engine.validate_output(updates) == []


# ------------------------------------------------------- orchestrator stage


def test_stage_registered_and_runs_through_orchestrator():
    assert "character_universe" in STAGE_GROUPS
    report = get_orchestrator().run_stage("character_universe", {"command": "probe"})
    assert report.status in (StageStatus.SUCCESS, StageStatus.WARNING)


def test_engine_run_seeds_house_cast_and_publishes_all_keys():
    engine = engine_registry.get_engine("character_universe")
    updates = engine.run({})

    summary = updates["character_universe_summary"]
    assert summary["characters_total"] >= 4            # house cast seeded
    assert summary["universe_id"] == HOUSE_UNIVERSE_ID
    assert summary["cast_size"] >= 1

    assert updates["story_bible"]["universe"]["name"] == "The Generational Universe"
    assert updates["character_continuity_report"]["errors"] == 0
    assert updates["character_asset_requests"]
    assert updates["character_performance_payload"]["character_popularity"]

    # idempotent — a second run never duplicates the cast
    again = engine.run({})
    assert again["character_universe_summary"]["seeded"] == {"universes": 0, "characters": 0}
    assert again["character_universe_summary"]["characters_total"] == summary["characters_total"]


def test_engine_respects_explicit_cast_and_records_appearances():
    engine = engine_registry.get_engine("character_universe")
    engine.run({})  # ensure seed
    updates = engine.run(
        {
            "character_ids": ["char_presenter_nova"],
            "character_appearances": [
                {
                    "character_id": "char_presenter_nova",
                    "content_id": "vid_777",
                    "voice_id": "voice_wrong",
                }
            ],
        }
    )
    contexts = updates["character_script_contexts"]
    assert len(contexts) == 1 and contexts[0]["name"] == "Nova"
    # the mismatched voice on the logged appearance surfaced as an issue
    assert any(
        issue["category"] == "voice_drift"
        for issue in updates["character_continuity_report"]["issues"]
    )


def test_engine_never_mutates_other_agents_context_keys():
    engine = engine_registry.get_engine("character_universe")
    context = {"candidates": [{"id": 1}], "seo_package": {"title": "t"}, "render_package": {"x": 1}}
    snapshot = {key: repr(value) for key, value in context.items()}
    updates = engine.run(context)
    for key, value in snapshot.items():
        assert repr(context[key]) == value, f"engine mutated context key '{key}'"
    assert not set(updates) & set(snapshot), "engine must not overwrite other agents' keys"


# --------------------------------------------- script generation integration


def test_script_context_payload(registry):
    ensure_house_cast(registry)
    nova = registry.get("characters", "char_presenter_nova")
    RelationshipEngine(registry).link("char_presenter_nova", "char_mascot_gen", "teammate")

    context = script_context_for("char_presenter_nova", registry)
    assert context["name"] == "Nova"
    assert context["speaking_style"] == nova["speech_style"]
    assert context["personality"] == nova["personality_traits"]
    assert "never contradict canon history" in context["dialogue_rules"]
    assert context["relationship_context"][0]["with_name"] == "Gen"
    assert "canon_history" in context and "story_context" in context
    assert script_context_for("char_missing", registry) == {}  # failure handling


# ------------------------------------------------ creative studio integration


def test_creative_context_payload(registry):
    ensure_house_cast(registry)
    registry.create_location(
        {"name": "Studio One", "universe_id": HOUSE_UNIVERSE_ID, "lighting_profile": "soft key"}
    )
    context = creative_context_for(["char_presenter_nova", "char_missing"], HOUSE_UNIVERSE_ID, registry)
    assert len(context["scene_participants"]) == 1     # unknown ids skipped safely
    participant = context["scene_participants"][0]
    assert "Nova" in participant["prompt_fragment"]
    assert "navy" in participant["prompt_fragment"]
    assert context["world_rules"]                       # universe rules exposed
    assert context["creative_constraints"]              # consistency rules exposed
    assert context["locations"][0]["name"] == "Studio One"


def test_prompt_fragment_is_the_consistency_anchor(registry):
    ensure_house_cast(registry)
    gen = registry.get("characters", "char_mascot_gen")
    fragment = character_prompt_fragment(gen)
    assert gen["visual_profile"]["visual_signature"] in fragment
    assert "amber" in fragment


# ------------------------------------------- asset generation (Agent 14) hand-off


def test_asset_requests_are_requests_not_assets(registry):
    ensure_house_cast(registry)
    registry.create_location({"name": "Studio One", "universe_id": HOUSE_UNIVERSE_ID})
    registry.create("style_packs", {"name": "House Cel", "universe_id": HOUSE_UNIVERSE_ID})

    requests = asset_requests_for(["char_presenter_nova"], HOUSE_UNIVERSE_ID, registry)
    types = {request["request_type"] for request in requests}
    assert types == {"character_reference", "environment_reference"}

    character_request = next(r for r in requests if r["request_type"] == "character_reference")
    assert character_request["reference_prompt"]
    assert character_request["consistency_rules"]
    assert character_request["style_pack_ids"]
    assert character_request["character_definition"]["visual_profile"]["visual_signature"]
    # requests carry NO media — definitions and prompts only
    assert "path" not in character_request and "file_uri" not in character_request


# --------------------------------------------- optimization lab integration


def test_optimization_payload(registry):
    ensure_house_cast(registry)
    payload = optimization_payload(registry)
    assert len(payload["character_popularity"]) >= 4
    assert payload["audience_preferences"]["most_popular"]
    entry = payload["character_popularity"][0]
    assert {"character_id", "popularity_score", "brand_importance", "status"} <= set(entry)


def test_franchise_metrics_flow_in_through_context():
    engine = engine_registry.get_engine("character_universe")
    engine.run({})
    from services.character_universe.franchise import FranchiseManager
    from services.character_universe.registry import get_character_universe_registry

    live_registry = get_character_universe_registry()
    franchise = FranchiseManager(live_registry).create_franchise(
        {"name": "Nova Explains", "universe_id": HOUSE_UNIVERSE_ID}
    )
    updates = engine.run({"franchise_metrics": {franchise["franchise_id"]: {"avg_retention": 0.7}}})
    performances = updates["character_performance_payload"]["franchise_performance"]
    stored = next(p for p in performances if p["franchise_id"] == franchise["franchise_id"])
    assert stored["performance"]["avg_retention"] == 0.7
