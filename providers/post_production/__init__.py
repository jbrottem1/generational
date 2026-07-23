"""Post-production provider registry — swappable editing backends."""

from __future__ import annotations

from providers.post_production.mock import MockPostProductionProvider
from providers.post_production_provider import PostProductionProvider

_mock = MockPostProductionProvider()
_providers: dict[str, PostProductionProvider] = {}
_bootstrapped = False

# Future adapter classes — register when real backends are wired.
ADAPTER_CLASSES: tuple = ()


def register_post_production_provider(provider: PostProductionProvider) -> PostProductionProvider:
    _providers[provider.name] = provider
    return provider


def unregister_post_production_provider(name: str) -> None:
    _providers.pop(name, None)


def get_post_production_provider(name: str) -> PostProductionProvider | None:
    if name == _mock.name:
        return _mock
    return _providers.get(name)


def default_post_production_provider() -> PostProductionProvider:
    return _mock


def provider_catalog() -> list:
    ensure_providers_registered()
    seen = {_mock.name: _mock.profile()}
    for provider in _providers.values():
        seen[provider.name] = provider.profile()
    return list(seen.values())


def ensure_providers_registered() -> None:
    global _bootstrapped
    if _bootstrapped:
        return
    for cls in ADAPTER_CLASSES:
        register_post_production_provider(cls())
    _bootstrapped = True
