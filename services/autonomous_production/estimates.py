"""Cost / runtime estimation for Autonomous Production Executor (Agent 23)."""

from __future__ import annotations

from services.autonomous_production.modes import (
    detect_content_duration_sec,
    mode_defaults,
    resolve_production_mode,
)

# Rough wall-clock seconds per stage (demo / mock pipeline).
_STAGE_RUNTIME_SEC = {
    "trend": 2.0,
    "research": 3.0,
    "psychology": 2.0,
    "script": 4.0,
    "attention": 1.5,
    "visual": 3.0,
    "audio": 2.5,
    "refinement": 1.5,
    "quality": 1.0,
    "production": 5.0,
    "packaging": 1.0,
    "ai_director": 2.0,
    "creative": 2.5,
    "character_universe": 2.0,
    "asset_generation": 6.0,
    "animation": 8.0,
    "render": 10.0,
    "post_production": 4.0,
    "seo": 1.5,
    "optimization": 1.5,
    "publish": 2.0,
    "analytics": 1.0,
    "learning": 1.0,
}

# USD cost hints per stage at standard quality (ProviderRuntime demo ≈ 0).
_STAGE_COST_USD = {
    "script": 0.05,
    "visual": 0.08,
    "audio": 0.06,
    "asset_generation": 0.25,
    "animation": 0.40,
    "render": 0.30,
    "post_production": 0.10,
    "creative": 0.05,
    "ai_director": 0.03,
}


def estimate_runtime_sec(
    command: str,
    *,
    mode: str = "",
    stages: list[str] | None = None,
    unit_count: int = 1,
    longform: bool = False,
) -> float:
    mode = mode or resolve_production_mode(command)
    defaults = mode_defaults(mode)
    units = max(1, unit_count or int(defaults.get("unit_count", 1)))
    stage_list = stages or list(_STAGE_RUNTIME_SEC.keys())
    base = sum(_STAGE_RUNTIME_SEC.get(s, 2.0) for s in stage_list)
    content = detect_content_duration_sec(command)
    # Long-form content adds proportional planning/render overhead.
    content_factor = 1.0 + (content / 3600.0) * (1.5 if longform or defaults.get("longform") else 0.3)
    return round(base * content_factor * units, 1)


def estimate_cost_usd(
    command: str,
    *,
    mode: str = "",
    stages: list[str] | None = None,
    unit_count: int = 1,
    quality_level: str = "standard",
    budget_usd: float = 0.0,
) -> dict:
    mode = mode or resolve_production_mode(command)
    defaults = mode_defaults(mode)
    units = max(1, unit_count or int(defaults.get("unit_count", 1)))
    stage_list = stages or list(_STAGE_COST_USD.keys())
    base = sum(_STAGE_COST_USD.get(s, 0.02) for s in stage_list)
    quality_mult = {"draft": 0.5, "standard": 1.0, "high": 1.8, "premium": 2.5}.get(
        (quality_level or "standard").lower(), 1.0
    )
    content = detect_content_duration_sec(command)
    content_mult = 1.0 + (content / 1800.0) * 0.4
    total = round(base * quality_mult * content_mult * units, 4)
    over_budget = bool(budget_usd and total > budget_usd)
    return {
        "estimated_cost_usd": total,
        "per_unit_usd": round(total / units, 4),
        "unit_count": units,
        "quality_level": quality_level,
        "budget_usd": budget_usd,
        "over_budget": over_budget,
        "currency": "USD",
    }


def remaining_runtime_sec(estimated_sec: float, progress_pct: float) -> float:
    if estimated_sec <= 0:
        return 0.0
    pct = max(0.0, min(100.0, float(progress_pct or 0)))
    return round(estimated_sec * (100.0 - pct) / 100.0, 1)
