"""Character, Universe & IP engine — Agent 15 (key: character_universe).

The permanent creative memory of the company. This engine never generates
media, never writes scripts, never renders — it maintains every persistent
character, universe, relationship, canon event, franchise, and brand
identity, and publishes structured context for the rest of the pipeline
(Architecture Directive #1: outputs go onto shared context keys; the
orchestrator routes them; no engine-to-engine calls):

- character_universe_summary:   cast size, universes, continuity health
- character_script_contexts:    per-character speaking style, dialogue
                                rules, personality, motivation,
                                relationship + story context, canon
                                history — for Script Generation
- character_creative_context:   scene participants, world rules, visual
                                references, creative constraints — for
                                the Creative Studio
- character_asset_requests:     definitions, reference prompts, style
                                packs, environments, consistency rules —
                                REQUESTS for Universal Asset Generation
                                (Agent 14), never generated assets
- character_continuity_report:  contradictions, drift, and lore
                                violations detected across the catalog
- story_bible:                  the canonical Story Bible snapshot
- character_performance_payload: popularity/franchise signals for the
                                Optimization Laboratory

Optional context inputs (all additive): `character_ids` (explicit cast),
`universe_id` (scope), `character_appearances` (appearance records to
log), `franchise_metrics` (performance written back from analytics).

All logic lives in `services/character_universe/`; this module is the
thin pipeline adapter.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.character_universe.bible import build_bible
from services.character_universe.continuity import ContinuityEngine
from services.character_universe.franchise import FranchiseManager
from services.character_universe.integrations import (
    asset_requests_for,
    continuity_report,
    creative_context_for,
    optimization_payload,
    script_context_for,
)
from services.character_universe.models import CHARACTER_UNIVERSE_VERSION, CharacterStatus
from services.character_universe.registry import get_character_universe_registry
from services.character_universe.seed import HOUSE_UNIVERSE_ID, ensure_house_cast

logger = get_logger(__name__)


class CharacterUniverseEngine(ContractEngine):
    key = "character_universe"
    label = "Character & Universe"
    icon = "🎭"
    description = "Persistent characters, universes, relationships, canon, and brand IP — the company's permanent creative memory."
    version = CHARACTER_UNIVERSE_VERSION
    input_contract: "list[str]" = []  # runs from its own persistent registry
    output_contract = [
        "character_universe_summary",
        "character_script_contexts",
        "character_creative_context",
        "character_asset_requests",
        "character_continuity_report",
        "story_bible",
        "character_performance_payload",
    ]
    dependencies: "list[str]" = []
    capabilities = [
        "characters", "universes", "relationships", "continuity",
        "canon-management", "franchise-management", "brand-identity",
        "character-memory", "story-bible", "ip-protection",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        registry = get_character_universe_registry()
        seeded = ensure_house_cast(registry)
        continuity = ContinuityEngine(registry)

        universe_id = context.get("universe_id") or HOUSE_UNIVERSE_ID

        # Explicit cast wins; otherwise every active character in scope.
        cast_ids = list(context.get("character_ids") or [])
        if not cast_ids:
            cast_ids = [
                character["character_id"]
                for character in registry.characters_in_universe(universe_id)
                if character.get("status") == CharacterStatus.ACTIVE
            ]

        # Log appearances handed in by the orchestrator (published content).
        appearance_issues = []
        for spec in context.get("character_appearances", []) or []:
            appearance_issues += continuity.record_appearance(spec)["issues"]

        # Merge analytics-provided franchise metrics back onto franchises.
        franchises = FranchiseManager(registry)
        for franchise_id, metrics in (context.get("franchise_metrics") or {}).items():
            franchises.record_performance(franchise_id, metrics)

        script_contexts = [
            script_context_for(character_id, registry) for character_id in cast_ids
        ]
        script_contexts = [entry for entry in script_contexts if entry]

        report = continuity_report(universe_id, registry)
        report["issues"] = report["issues"] + appearance_issues
        report["errors"] = sum(1 for issue in report["issues"] if issue["severity"] == "error")
        report["warnings"] = sum(1 for issue in report["issues"] if issue["severity"] == "warning")
        report["clean"] = not report["issues"]

        summary = {
            "engine_version": self.version,
            "universe_id": universe_id,
            "characters_total": registry.store.count("characters"),
            "universes_total": registry.store.count("universes"),
            "franchises_total": registry.store.count("franchises"),
            "cast_size": len(cast_ids),
            "seeded": seeded,
            "continuity_errors": report["errors"],
            "continuity_warnings": report["warnings"],
        }

        log_event(
            logger, "character_universe.completed",
            cast=len(cast_ids), universe=universe_id,
            continuity_errors=report["errors"],
        )
        return {
            "character_universe_summary": summary,
            "character_script_contexts": script_contexts,
            "character_creative_context": creative_context_for(cast_ids, universe_id, registry),
            "character_asset_requests": asset_requests_for(cast_ids, universe_id, registry),
            "character_continuity_report": report,
            "story_bible": build_bible(universe_id, registry),
            "character_performance_payload": optimization_payload(registry),
        }
