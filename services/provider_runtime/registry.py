"""ProviderRegistry — central catalog of all registered adapters."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter

_registry: "dict[str, ProviderAdapter]" = {}
_bootstrapped = False


def register_provider(adapter: ProviderAdapter) -> ProviderAdapter:
    """Register (or replace) one provider adapter by name."""
    _registry[adapter.name] = adapter
    return adapter


def unregister_provider(name: str) -> None:
    _registry.pop(name, None)


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
    return [p.describe() for p in all_providers()]


def ensure_registered() -> int:
    """Idempotent bootstrap — auto-discover and register all adapters."""
    global _bootstrapped
    if _bootstrapped:
        return len(_registry)
    from services.provider_runtime.adapters import discover_and_register

    discover_and_register()
    from services.provider_runtime.bridge import register_legacy_providers

    register_legacy_providers()
    _bootstrapped = True
    return len(_registry)


def reset_registry() -> None:
    """Clear registry (tests only)."""
    global _bootstrapped
    _registry.clear()
    _bootstrapped = False
