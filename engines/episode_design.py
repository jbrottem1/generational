"""Retention & Episode Design Engine — Agent 25 (key: episode_design).

NOTE: Mission brief named this Agent 24; registry assigns Agent 25 because
Agent 24 is already Executive Intelligence (key: autonomous_executive).

Reviews completed scripts before production and improves how educational
episodes engage, retain, and teach viewers. Emits per-item EpisodeDesignPackages
— never generating media or duplicating the work of downstream agents.

Pipeline position (PIPELINE_SPEC.md):

    Quality → Episode Design → AI Director → Creative Studio → …

Failure policy: NEVER crashes the pipeline. Empty context → "no_items"
summary; per-item failures degrade to diagnostics, siblings continue.
Ownership rules honored: only `item["episode_design_package"]` and the
`episode_design_summary` / `episode_design_packages` context keys are
written — all other slots are read, never mutated.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.episode_design.models import EPISODE_DESIGN_ENGINE_VERSION
from services.episode_design.package import (
    collect_episode_design_items,
    run_episode_design_engine,
)

logger = get_logger(__name__)


class EpisodeDesignEngine(ContractEngine):
    """Agent 25 — Director of Retention & Episode Design.

    NOTE: Mission brief said Agent 24; registry assigns Agent 25 because 24
    is Executive Intelligence.
    """

    key = "episode_design"
    label = "Retention & Episode Design"
    icon = "🎓"
    description = (
        "Reviews completed scripts and designs how educational episodes engage viewers. "
        "Produces lesson blueprints (7 timing beats), retention scores (7 dimensions), "
        "series planning, and feeds the Generational Episode Playbook — "
        "before AI Director and Creative Studio generate assets."
    )
    version = EPISODE_DESIGN_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["episode_design_summary", "episode_design_packages"]
    dependencies = ["quality"]
    capabilities = [
        "retention",
        "episode-design",
        "lesson-blueprint",
        "series-planning",
        "educational-pacing",
        "curiosity-design",
        "playbook",
        "graceful-degradation",
        "script-review",
        "emotional-pacing",
        "reveal-timing",
        "transition-design",
        "hook-optimization",
        "ending-design",
        "viewer-questions",
        "information-flow",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        try:
            return run_episode_design_engine(context)
        except Exception as exc:  # noqa: BLE001 - never crash the pipeline
            log_event(logger, "episode_design.engine_failed", level=30, error=str(exc)[:120])
            return run_episode_design_engine({})
