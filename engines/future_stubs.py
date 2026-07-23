"""Contract-first stubs for stages whose engines are not yet merged.

Registering these now means the orchestrator, dashboards, and tests already
know every future stage — implementing one later is overriding `run()` and
`is_ready()` in the owning agent's landing zone (or merging their feature
branch), with zero orchestration changes.

Live engines that graduated out of this file:
- `seo_optimization` → `engines/seo_optimization.py` (Agent 8)
- `scheduler` → `engines/publishing/scheduler_engine.py` (Agent 7)

Agents 12, 14, 17 are live on this branch (`creative_studio`,
`asset_generation`, `post_production`). Agent 13 (`optimization_lab`)
graduated to live V4.0 in `engines/optimization_lab.py`. Agents 15–16
remain stubs until their feature branches merge.
"""

from __future__ import annotations

from engines.contracts import FutureEngine


class BrandManagementEngine(FutureEngine):
    """Multi-brand operating system (brand strategy updates)."""

    key = "brand_management"
    label = "Brand Management"
    icon = "🏢"
    description = "Per-brand strategy, identity, cadence, and portfolio decisions."
    input_contract = ["ideas"]
    output_contract = ["brand_strategy_update"]
    dependencies = ["learning"]
    capabilities = ["multi-brand", "strategy"]


class OptimizationLabEngine(FutureEngine):
    """DEPRECATED STUB — live engine is engines/optimization_lab.py (V4.0).

    Kept only so older imports of future_stubs.OptimizationLabEngine do not
    break; engines/__init__.py registers the live class instead.
    """

    key = "optimization_lab_stub_unused"
    label = "Optimization Lab (stub)"
    icon = "🧪"
    description = "Replaced by live OptimizationLabEngine V4.0"
    input_contract = ["ideas"]
    output_contract = ["optimization_report"]
    dependencies = ["quality"]
    capabilities = ["experimentation"]


class CharacterUniverseEngine(FutureEngine):
    """Agent 15 — Character, Universe & Intellectual Property.

    Persistent creative memory: characters, universes, continuity, canon.
    Built on a feature worktree; reserved so the stage is wired now.
    """

    key = "character_universe"
    label = "Character & Universe"
    icon = "🎭"
    description = (
        "Persistent characters, universes, relationships, canon, and brand "
        "IP — the company's permanent creative memory."
    )
    input_contract: "list[str]" = []
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


class AnimationEngineStub(FutureEngine):
    """Deprecated stub — live engine is engines.animation.AnimationEngine.

    Kept only so older imports of future_stubs.AnimationEngine do not crash.
    """

    key = "animation_stub_deprecated"
    label = "Animation Stub (deprecated)"
    icon = "🎥"
    description = "Deprecated — use engines.animation.AnimationEngine"
    input_contract = ["unified_packages"]
    output_contract = ["animation_summary"]
    capabilities = ["deprecated"]


# Back-compat alias (not registered)
AnimationEngine = AnimationEngineStub
