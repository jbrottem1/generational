"""Contract-first stubs for stages whose engines are not yet merged.

Registering these now means the orchestrator, dashboards, and tests already
know every future stage — implementing one later is overriding `run()` and
`is_ready()` in the owning agent's landing zone (or merging their feature
branch), with zero orchestration changes.

Live engines that graduated out of this file:
- `seo_optimization` → `engines/seo_optimization.py` (Agent 8)
- `scheduler` → `engines/publishing/scheduler_engine.py` (Agent 7)

Agents 12, 14, 17 are live on this branch (`creative_studio`,
`asset_generation`, `post_production`). Agents 13, 15, 16 remain stubs
until their feature branches merge.
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
    """Agent 13 — Optimization Laboratory (variant experimentation).

    Built on a feature worktree; reserved here so the `optimization` stage
    is wired and skips cleanly until the live engine merges.
    """

    key = "optimization_lab"
    label = "Optimization Lab"
    icon = "🧪"
    description = (
        "Generate competing variants for every content decision, predict "
        "performance, rank against historical winners, and recommend the "
        "strongest version before publishing."
    )
    input_contract = ["ideas"]
    output_contract = ["optimization_report", "optimization_recommendations"]
    dependencies = ["quality"]
    capabilities = [
        "experimentation", "variant-generation", "scoring", "ranking",
        "prediction", "recommendations", "ab-testing", "learning-loop",
    ]


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


class AnimationEngine(FutureEngine):
    """Agent 16 — Animation & Cinematic Production.

    Plans motion (timeline, camera, lip sync, VFX) without rendering final
    video. Built on a feature worktree; reserved so the stage is wired now.
    """

    key = "animation"
    label = "Animation & Cinematics"
    icon = "🎥"
    description = (
        "Transform creative assets into cinematic production plans — "
        "timeline, camera, character motion, facial animation, lip sync, "
        "VFX, and provider instructions — without rendering final video."
    )
    input_contract = ["unified_packages"]
    output_contract = ["animation_summary", "animation_packages"]
    dependencies = ["quality"]
    capabilities = [
        "animation-planning", "cinematics", "camera-planning", "timeline",
        "character-motion", "facial-animation", "lip-sync", "visual-effects",
        "provider-driven",
    ]
