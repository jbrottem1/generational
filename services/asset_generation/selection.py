"""Provider Selection Engine — the best backend for every request.

Deterministic scoring over each candidate's declared profile
(quality / cost / speed / consistency), shaped by the configured
strategy, cost limits, explicit priority overrides, and offline
requirements. Output is a full selection plan: one primary provider plus
an ordered fallback chain that always ends in the offline deterministic
mock — generation can never dead-end.

No provider is ever named in this module: candidates come from the
`providers/asset_generation/` registry, and every signal scored here is
declared by the adapter itself.
"""

from __future__ import annotations

from providers.asset_generation import all_generation_providers
from services.asset_generation.config import AssetGenerationConfig, get_asset_generation_config

# strategy → profile weights (quality, cost, speed, consistency).
STRATEGY_WEIGHTS = {
    "balanced": {"quality": 0.35, "cost": 0.25, "speed": 0.15, "consistency": 0.25},
    "quality": {"quality": 0.70, "cost": 0.05, "speed": 0.05, "consistency": 0.20},
    "cost": {"quality": 0.15, "cost": 0.65, "speed": 0.10, "consistency": 0.10},
    "speed": {"quality": 0.15, "cost": 0.10, "speed": 0.65, "consistency": 0.10},
    "consistency": {"quality": 0.20, "cost": 0.05, "speed": 0.05, "consistency": 0.70},
}

# Cost above this is scored 0 on the cost axis (linear falloff below it).
_COST_CEILING_USD = 2.0


def score_provider(provider, strategy: str) -> float:
    """0-100 fitness of one provider under one strategy (deterministic)."""
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS["balanced"])
    profile = getattr(provider, "profile", {}) or {}
    cost = float(profile.get("cost_per_asset", 0.0))
    cost_score = max(0.0, 100.0 * (1.0 - min(cost, _COST_CEILING_USD) / _COST_CEILING_USD))
    total = (
        weights["quality"] * float(profile.get("quality", 0))
        + weights["cost"] * cost_score
        + weights["speed"] * float(profile.get("speed", 0))
        + weights["consistency"] * float(profile.get("consistency", 0))
    )
    return round(total, 2)


def candidate_providers(request: dict, config: "AssetGenerationConfig | None" = None) -> list:
    """Available providers that can serve this request, unranked."""
    config = config or get_asset_generation_config()
    asset_class = str(request.get("asset_class", "image"))
    asset_type = str(request.get("asset_type", ""))
    candidates = []
    for provider in all_generation_providers():
        if not provider.is_available():
            continue
        if not provider.supports(asset_class, asset_type):
            continue
        if config.offline_only and not getattr(provider, "offline", False):
            continue
        if provider.estimate_cost(request) > config.max_cost_per_asset:
            continue
        candidates.append(provider)
    return candidates


def select_providers(request: dict, config: "AssetGenerationConfig | None" = None) -> dict:
    """The full selection plan for one request.

    Returns {primary, fallbacks, strategy, candidates} where `candidates`
    is the scored ranking [{provider, score, cost_estimate, offline,
    local}, ...]. Explicit `provider_priority` entries for the request's
    asset class outrank scoring; the deterministic offline mock is always
    the final fallback.
    """
    config = config or get_asset_generation_config()
    strategy = config.selection_strategy if config.selection_strategy in STRATEGY_WEIGHTS else "balanced"
    candidates = candidate_providers(request, config)

    scored = sorted(
        (
            {
                "provider": provider.name,
                "score": score_provider(provider, strategy),
                "cost_estimate": provider.estimate_cost(request),
                "offline": bool(getattr(provider, "offline", False)),
                "local": bool(getattr(provider, "local", False)),
            }
            for provider in candidates
        ),
        key=lambda entry: (-entry["score"], entry["cost_estimate"], entry["provider"]),
    )

    ordered = [entry["provider"] for entry in scored]

    # Explicit priority override: configured names (that are candidates)
    # lead the chain in their configured order.
    priority = list(config.provider_priority.get(str(request.get("asset_class", "image")), []))
    if priority:
        prioritized = [name for name in priority if name in ordered]
        ordered = prioritized + [name for name in ordered if name not in prioritized]

    # The offline mock is always last — the fallback of last resort.
    mock_names = [entry["provider"] for entry in scored if entry["offline"] and entry["local"]]
    for name in mock_names:
        if name in ordered and name != ordered[-1] and len(ordered) > 1 and name not in priority:
            ordered.remove(name)
            ordered.append(name)

    primary = ordered[0] if ordered else ""
    return {
        "primary": primary,
        "fallbacks": ordered[1:],
        "strategy": strategy,
        "candidates": scored,
    }


def selection_overview(asset_classes: "list[str]", config: "AssetGenerationConfig | None" = None) -> dict:
    """asset class → primary provider name (the package's routing plan)."""
    return {
        asset_class: select_providers({"asset_class": asset_class}, config)["primary"]
        for asset_class in asset_classes
    }
