"""Publishing provider adapters — one per supported platform, all mock today.

Never hardcode platforms in engine logic: resolve adapters through
`get_publishing_provider(platform)` / `publishing_provider_keys()`. A real
API integration replaces one adapter via `register_publishing_provider()`
without touching the queue, retry, scheduler, or engine code.
"""

from providers.publishing.adapters import (
    MockPublishingProvider,
    FacebookReelsProvider,
    InstagramReelsProvider,
    LinkedInProvider,
    PinterestProvider,
    TikTokProvider,
    XProvider,
    YouTubeShortsProvider,
)
from providers.publishing.registry import (
    get_publishing_provider,
    publishing_provider_keys,
    register_publishing_provider,
    resolve_platform_key,
)

__all__ = [
    "FacebookReelsProvider",
    "InstagramReelsProvider",
    "LinkedInProvider",
    "MockPublishingProvider",
    "PinterestProvider",
    "TikTokProvider",
    "XProvider",
    "YouTubeShortsProvider",
    "get_publishing_provider",
    "publishing_provider_keys",
    "register_publishing_provider",
    "resolve_platform_key",
]
