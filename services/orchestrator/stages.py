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
    "trend": ["trend_discovery", "opportunity_ranking", "trend_forecasting"],
    "research": ["research", "ideation"],
    "psychology": ["psychology"],
    "script": ["script_generation"],
    "attention": ["attention_graph"],
    "visual": ["visual_intelligence"],
    "audio": ["voice_audio"],
    "quality": ["quality"],
    # Engines are planned/contract stubs today; these stages light up when
    # their engines report ready — nothing else changes. Ownership:
    # render → Agent 6 · publish → Agent 7 · seo → Agent 8 ·
    # analytics/learning → Agent 9 · brand_management → Agent 10.
    "render": ["image", "video"],
    "seo": ["seo_optimization"],
    "publish": ["scheduler", "publishing"],
    "analytics": ["analytics"],
    "learning": ["learning"],
    "brand_management": ["brand_management"],
    # Agent 13 — Experimentation & Optimization Laboratory. Runnable on
    # demand here; scheduled inside the full pipeline (after quality) via
    # services/optimization/integration.enable_optimization_stage().
    "optimization": ["optimization_lab"],
}

# Post-packaging distribution stages executed by the full production
# pipeline, in contract order (PIPELINE_SPEC.md): Render Engine → Global
# Content Optimization → Publishing. Each runs against the packaged
# context; unavailable engines skip with warnings — never a crash.
DISTRIBUTION_STAGES: "tuple[str, ...]" = ("render", "seo", "publish")


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
