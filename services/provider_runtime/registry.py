"""ProviderRegistry — central catalog with discovery, health scoring, plugins."""

from __future__ import annotations

from typing import Callable

from services.provider_runtime.adapter import ProviderAdapter

_registry: "dict[str, ProviderAdapter]" = {}
_bootstrapped = False
_priority_overrides: "dict[str, float]" = {}
_plugin_hooks: "list[Callable[[], int]]" = []
_health_scores: "dict[str, float]" = {}


def register_provider(adapter: ProviderAdapter) -> ProviderAdapter:
    """Register (or replace) one provider adapter by name."""
    _registry[adapter.name] = adapter
    return adapter


def unregister_provider(name: str) -> None:
    _registry.pop(name, None)
    _priority_overrides.pop(name, None)
    _health_scores.pop(name, None)


def get_provider(name: str) -> "ProviderAdapter | None":
    return _registry.get(name)


def all_providers() -> list[ProviderAdapter]:
    return list(_registry.values())


def providers_for_capability(capability: str) -> list[ProviderAdapter]:
    return [p for p in _registry.values() if p.supports(capability)]


def available_providers(capability: str = "") -> list[ProviderAdapter]:
    candidates = providers_for_capability(capability) if capability else all_providers()
    return [p for p in candidates if p.is_available()]


def provider_catalog() -> list[dict]:
    catalog = []
    for provider in all_providers():
        entry = provider.describe()
        entry["priority"] = get_priority(provider.name)
        entry["health_score"] = health_score(provider.name)
        catalog.append(entry)
    return catalog


def set_priority(name: str, priority: float) -> None:
    """Higher priority wins ties during selection (default 0)."""
    _priority_overrides[name] = float(priority)


def get_priority(name: str) -> float:
    return float(_priority_overrides.get(name, 0.0))


def record_health_score(name: str, score: float) -> None:
    """Update rolling health score 0–100 for a provider."""
    _health_scores[name] = max(0.0, min(100.0, float(score)))


def health_score(name: str) -> float:
    if name in _health_scores:
        return _health_scores[name]
    provider = _registry.get(name)
    if provider is None:
        return 0.0
    return 100.0 if provider.is_available() else 0.0


def providers_by_priority(capability: str = "") -> list[ProviderAdapter]:
    candidates = available_providers(capability) if capability else available_providers()
    return sorted(
        candidates,
        key=lambda p: (get_priority(p.name), health_score(p.name), p.profile.quality),
        reverse=True,
    )


def register_plugin(hook: Callable[[], int]) -> None:
    """Register a plugin discovery hook invoked during bootstrap / refresh."""
    if hook not in _plugin_hooks:
        _plugin_hooks.append(hook)


def run_plugins() -> int:
    total = 0
    for hook in list(_plugin_hooks):
        try:
            total += int(hook() or 0)
        except Exception:  # noqa: BLE001 — plugins must not break bootstrap
            continue
    return total


def capability_lookup(capability: str) -> list[dict]:
    """Capability → ranked provider descriptions."""
    ranked = providers_by_priority(capability)
    if not ranked:
        ranked = providers_for_capability(capability)
    return [
        {
            **p.describe(),
            "priority": get_priority(p.name),
            "health_score": health_score(p.name),
        }
        for p in ranked
    ]


def ensure_registered() -> int:
    """Idempotent bootstrap — auto-discover and register all adapters."""
    global _bootstrapped
    if _bootstrapped:
        return len(_registry)
    from services.provider_runtime.adapters import discover_and_register

    discover_and_register()
    from services.provider_runtime.bridge import register_legacy_providers

    register_legacy_providers()
    run_plugins()
    _bootstrapped = True
    return len(_registry)


def refresh_registry() -> int:
    """Re-run discovery + plugins without clearing existing adapters."""
    from services.provider_runtime.adapters import discover_and_register

    discover_and_register()
    run_plugins()
    return len(_registry)


def reset_registry() -> None:
    """Clear registry (tests only)."""
    global _bootstrapped
    _registry.clear()
    _priority_overrides.clear()
    _health_scores.clear()
    _plugin_hooks.clear()
    _bootstrapped = False
    # Also clear factory class registry so re-bootstrap is clean.
    from services.provider_runtime.factory import ProviderFactory

    ProviderFactory._adapter_classes.clear()
