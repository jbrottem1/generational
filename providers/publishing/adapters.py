"""Mock publishing adapters — deterministic, no API keys, no network.

Each adapter declares the platform's metadata constraints and simulates a
successful publish. Real integrations subclass the same adapter, override
`publish()` (and `is_available()` to check credentials), and register via
`providers.publishing.registry.register_publishing_provider()`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from providers.publishing_provider import PublishingProvider


class MockPublishingProvider(PublishingProvider):
    """Shared mock behavior — subclasses only declare identity + constraints."""

    key = "mock"
    label = "Mock Publisher"
    post_url_template = "mock://posts/{platform}/{post_id}"

    def is_available(self) -> bool:
        return True

    def publish(self, package: dict) -> dict:
        post_id = f"post_{uuid.uuid4().hex[:10]}"
        return {
            "status": "published",
            "provider": self.key,
            "platform": self.key,
            "post_id": post_id,
            "post_url": self.post_url_template.format(platform=self.key, post_id=post_id),
            "published_at": datetime.now(timezone.utc).isoformat(),
            "error": "",
            "mock": True,
        }


class YouTubeShortsProvider(MockPublishingProvider):
    key = "youtube_shorts"
    label = "YouTube Shorts"
    aliases = ("youtube", "youtube_long")

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 100,
            "max_description_chars": 5000,
            "max_hashtags": 15,
            "max_duration_sec": 60,
            "supports_playlists": True,
            "supports_categories": True,
        }

    def retry_policy(self) -> dict:
        return {"max_retries": 3, "base_delay_sec": 60}


class InstagramReelsProvider(MockPublishingProvider):
    key = "instagram_reels"
    label = "Instagram Reels"
    aliases = ("instagram",)

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 125,
            "max_description_chars": 2200,
            "max_hashtags": 30,
            "max_duration_sec": 90,
        }


class FacebookReelsProvider(MockPublishingProvider):
    key = "facebook_reels"
    label = "Facebook Reels"
    aliases = ("facebook",)

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 255,
            "max_description_chars": 5000,
            "max_hashtags": 30,
            "max_duration_sec": 90,
        }


class TikTokProvider(MockPublishingProvider):
    key = "tiktok"
    label = "TikTok"

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 100,
            "max_description_chars": 2200,
            "max_hashtags": 20,
            "max_duration_sec": 180,
        }

    def retry_policy(self) -> dict:
        # TikTok upload endpoints are rate-limit heavy — back off harder.
        return {"max_retries": 4, "base_delay_sec": 120}


class XProvider(MockPublishingProvider):
    key = "x"
    label = "X"
    aliases = ("twitter",)

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 280,
            "max_description_chars": 280,
            "max_hashtags": 5,
            "max_duration_sec": 140,
        }


class LinkedInProvider(MockPublishingProvider):
    key = "linkedin"
    label = "LinkedIn"

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 200,
            "max_description_chars": 3000,
            "max_hashtags": 5,
            "max_duration_sec": 600,
        }


class PinterestProvider(MockPublishingProvider):
    key = "pinterest"
    label = "Pinterest"

    def constraints(self) -> dict:
        return {
            **super().constraints(),
            "max_title_chars": 100,
            "max_description_chars": 500,
            "max_hashtags": 10,
            "max_duration_sec": 300,
        }
