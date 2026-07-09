"""Generation provider registry — the swappable backend surface of the
Universal Asset Generation Engine (Agent 14).

Real backends implement `GenerationProvider` (`providers/
generation_provider.py`) and register here by name; the engine's Provider
Selection Engine discovers candidates through this registry and never
talks to a vendor SDK directly. Until real backends are wired, every
request resolves to the deterministic `MockGenerationProvider`, so the
whole engine runs end-to-end (offline) today.

Phase 2 additions:
- `provider_catalog()` — uniform self-descriptions for every backend
- `providers_for_class()` / `providers_by_capability()` — discovery helpers
- `ensure_providers_registered()` — idempotent bootstrap for tests/reloads
"""

from __future__ import annotations

from providers.asset_generation.adapters import ADAPTER_CLASSES
from providers.asset_generation.mock import MockGenerationProvider
from providers.generation_provider import (
    GENERATION_ASSET_CLASSES,
    PROVIDER_PROFILE_FIELDS,
    GenerationProvider,
)

_mock = MockGenerationProvider()

# name → provider. Real backends replace/extend entries via
# register_generation_provider() — nothing in the engine changes.
_providers: "dict[str, GenerationProvider]" = {}
_bootstrapped = False


def register_generation_provider(provider: GenerationProvider) -> GenerationProvider:
    """Register (or replace) one generation backend by its `name`."""
    _providers[provider.name] = provider
    return provider


def unregister_generation_provider(name: str) -> None:
    """Remove a registered backend (used by tests and hot-swaps)."""
    _providers.pop(name, None)


def get_generation_provider(name: str) -> "GenerationProvider | None":
    if name == _mock.name:
        return _mock
    return _providers.get(name)


def all_generation_providers() -> "list[GenerationProvider]":
    """Every registered provider plus the always-available mock (last)."""
    others = [provider for provider in _providers.values() if provider.name != _mock.name]
    return others + [_mock]


def available_generation_providers(
    asset_class: str = "", asset_type: str = ""
) -> "list[GenerationProvider]":
    """Providers that are available now and cover the requested class/type."""
    candidates = []
    for provider in all_generation_providers():
        if not provider.is_available():
            continue
        if asset_class and not provider.supports(asset_class, asset_type):
            continue
        candidates.append(provider)
    return candidates


def providers_for_class(asset_class: str) -> "list[GenerationProvider]":
    """Every registered provider (available or not) that declares a class."""
    return [
        provider for provider in all_generation_providers()
        if asset_class in provider.asset_classes
    ]


def providers_by_capability(capability: str) -> "list[GenerationProvider]":
    """Providers advertising one capability tag."""
    return [
        provider for provider in all_generation_providers()
        if capability in getattr(provider, "capabilities", ())
    ]


def provider_catalog() -> "list[dict]":
    """Uniform self-descriptions of every registered provider (for UI/docs)."""
    return [provider.describe() for provider in all_generation_providers()]


def ensure_providers_registered() -> int:
    """Idempotent bootstrap — register every ADAPTER_CLASSES entry once.
    Returns the number of providers currently in the registry (excl. mock)."""
    global _bootstrapped
    for adapter_class in ADAPTER_CLASSES:
        instance = adapter_class()
        if instance.name not in _providers:
            register_generation_provider(instance)
    _bootstrapped = True
    return len([name for name in _providers if name != _mock.name])


# Bootstrap on import (same behaviour as Phase 1).
ensure_providers_registered()


__all__ = [
    "GENERATION_ASSET_CLASSES",
    "PROVIDER_PROFILE_FIELDS",
    "GenerationProvider",
    "MockGenerationProvider",
    "all_generation_providers",
    "available_generation_providers",
    "ensure_providers_registered",
    "get_generation_provider",
    "provider_catalog",
    "providers_by_capability",
    "providers_for_class",
    "register_generation_provider",
    "unregister_generation_provider",
]
