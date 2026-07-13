"""Publishing provider registry — platform id in, adapter out.

The engine, queue, and scheduler resolve platforms exclusively through this
registry, so supporting a new platform is one `register_publishing_provider`
call — no engine changes, no hardcoded platform lists anywhere.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from providers.publishing.adapters import (
    FacebookReelsProvider,
    InstagramReelsProvider,
    LinkedInProvider,
    PinterestProvider,
    TikTokProvider,
    XProvider,
    YouTubeShortsProvider,
)
from providers.publishing_provider import PublishingProvider

logger = get_logger(__name__)

_providers: "dict[str, PublishingProvider]" = {}
_aliases: "dict[str, str]" = {}


def register_publishing_provider(provider: PublishingProvider) -> PublishingProvider:
    """Register (or replace) the adapter for a platform, including aliases."""
    _providers[provider.key] = provider
    for alias in provider.aliases:
        _aliases[alias] = provider.key
    log_event(logger, "publishing.provider_registered", platform=provider.key, label=provider.label)
    return provider


def resolve_platform_key(platform: str) -> str:
    """Canonical platform key for a pipeline platform id (aliases resolved)."""
    return _aliases.get(platform, platform)


def get_publishing_provider(platform: str) -> "PublishingProvider | None":
    """The registered adapter for a platform, or None if unsupported."""
    provider = _providers.get(resolve_platform_key(platform))
    if provider is not None and provider.is_available():
        return provider
    return None


def publishing_provider_keys() -> "list[str]":
    return list(_providers.keys())


# Default mock adapters — real integrations replace these one at a time.
for _adapter_class in (
    YouTubeShortsProvider,
    InstagramReelsProvider,
    FacebookReelsProvider,
    TikTokProvider,
    XProvider,
    LinkedInProvider,
    PinterestProvider,
):
    if _adapter_class.key not in _providers:
        register_publishing_provider(_adapter_class())
