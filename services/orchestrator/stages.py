"""Stage registry — the plugin surface of the orchestration layer.

The orchestrator NEVER defines its own engine order. The canonical order
lives in `core/workflows.py` (`WORKFLOWS["intelligence"]`); this module
partitions that list into named stages, so reordering the workflow
automatically reorders the orchestrated pipeline — one source of truth.

A future engine plugs in by registering its engine (auto-registered via
`engines/registry.py`) and calling `register_stage()` — no orchestrator
code changes, no hardcoded dependencies.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from core.workflows import WORKFLOWS

logger = get_logger(__name__)

# Engine key → user-facing stage name. Engines not listed here fall into
# the "refinement" stage (critique, revision, citation, SEO, gates, ...).
STAGE_OF_ENGINE = {
    "trend_discovery": "trend",
    "opportunity_ranking": "trend",
    "trend_forecasting": "trend",
    "market_intelligence": "trend",
    "research": "research",
    "ideation": "research",
    "psychology": "psychology",
    "script_generation": "script",
    "attention_graph": "attention",
    "visual_intelligence": "visual",
    "voice_audio": "audio",
    "quality": "quality",
}

# Named groups runnable on their own (fixture input, manual runs, future
# stages). Future engines ADD entries — render, publish, learning, avatar,
# voice clone, brand manager, ...
STAGE_GROUPS: "dict[str, list[str]]" = {
    "trend": ["trend_discovery", "opportunity_ranking", "trend_forecasting", "market_intelligence"],
    "research": ["research", "ideation"],
    "psychology": ["psychology"],
    "script": ["script_generation"],
    "attention": ["attention_graph"],
    "visual": ["visual_intelligence"],
    "audio": ["voice_audio"],
    "quality": ["quality"],
    # Post-quality media generation & distribution (Agents 6-18).
    # Ownership: ai_director → Agent 18 · creative → Agent 12 ·
    # character_universe → Agent 15 · asset_generation → Agent 14 ·
    # animation → Agent 16 · render → Agent 6 · post_production → Agent 17 ·
    # seo → Agent 8 · optimization → Agent 13 · publish → Agent 7 ·
    # analytics/learning → Agent 10 · brand → Agent 10.
    "ai_director": ["ai_director"],
    "creative": ["creative_studio"],
    "character_universe": ["character_universe"],
    "asset_generation": ["asset_generation"],
    "animation": ["animation"],
    "render": ["image", "video"],
    "post_production": ["post_production"],
    "seo": ["seo_optimization"],
    "optimization": ["optimization_lab"],
    "publish": ["scheduler", "publishing"],
    "analytics": ["analytics"],
    "learning": ["learning"],
    "brand_management": ["brand_management"],
    # Agent 24 — Executive Intelligence (manual / hook; NOT distribution).
    "executive": ["autonomous_executive"],
}

# Post-packaging distribution stages executed by the full production
# pipeline. Preferred media-generation order (v9.9 architecture review):
# AI Director → Creative → Character/Universe → Asset Generation →
# Animation → Render → Post-Production → SEO → Optimization Lab → Publishing.
# Unavailable engines skip with warnings — never a crash. Agents 13/15/16
# are FutureEngine stubs until their feature branches merge.
DISTRIBUTION_STAGES: "tuple[str, ...]" = (
    "ai_director",
    "creative",
    "character_universe",
    "asset_generation",
    "animation",
    "render",
    "post_production",
    "seo",
    "optimization",
    "publish",
)


def distribution_stage_names() -> list:
    return list(DISTRIBUTION_STAGES)


# Stages registered by future plugins for the full pipeline: (name, keys, after).
_EXTRA_STAGES: "list[tuple[str, list[str], str]]" = []


def build_pipeline_plan() -> "list[tuple[str, list[str]]]":
    """Ordered (stage_name, engine_keys) pairs for the full pipeline.

    Derived from WORKFLOWS["intelligence"] at call time, so canonical
    workflow changes are picked up automatically. Contiguous engines with
    the same stage name are grouped; unnamed engines become "refinement".
    """
    plan: "list[tuple[str, list[str]]]" = []
    for key in WORKFLOWS["intelligence"]:
        name = STAGE_OF_ENGINE.get(key, "refinement")
        if plan and plan[-1][0] == name:
            plan[-1][1].append(key)
        else:
            plan.append((name, [key]))

    for name, keys, after in _EXTRA_STAGES:
        index = next((i for i, (n, _) in enumerate(plan) if n == after), len(plan) - 1)
        plan.insert(index + 1, (name, list(keys)))
    return plan


def pipeline_stage_names() -> list:
    return [name for name, _ in build_pipeline_plan()]


def register_stage(name: str, engine_keys: list, after: "str | None" = None) -> None:
    """Plug a new stage into the orchestrator.

    `after=None` registers the group for manual runs only; `after="quality"`
    also schedules it in the full pipeline following that stage.
    """
    STAGE_GROUPS[name] = list(engine_keys)
    if after is not None:
        _EXTRA_STAGES.append((name, list(engine_keys), after))
    log_event(
        logger, "orchestrator.stage_registered",
        stage=name, engines=len(engine_keys), scheduled=after is not None,
    )


def unregister_stage(name: str) -> None:
    """Remove a plugged-in stage (used by tests and hot-swaps)."""
    STAGE_GROUPS.pop(name, None)
    _EXTRA_STAGES[:] = [entry for entry in _EXTRA_STAGES if entry[0] != name]


def get_stage(name: str) -> list:
    return list(STAGE_GROUPS.get(name, []))
