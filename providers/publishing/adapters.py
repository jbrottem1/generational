"""Publishing adapters — mock by default, real via ProviderRuntime when keyed.

Each adapter declares the platform's metadata constraints. When the matching
ProviderRuntime publishing connector has credentials, `publish()` routes
through ProviderRuntime (never bypassing the orchestrator/runtime layer).
Otherwise the deterministic mock path is used.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from providers.publishing_provider import PublishingProvider

# Maps publishing registry keys → ProviderRuntime connector names.
_RUNTIME_PROVIDER_MAP = {
    "youtube_shorts": "youtube",
    "youtube": "youtube",
    "tiktok": "tiktok",
    "instagram_reels": "instagram",
    "instagram": "instagram",
    "facebook_reels": "facebook",
    "facebook": "facebook",
    "x": "x",
    "twitter": "x",
    "linkedin": "linkedin",
}


class MockPublishingProvider(PublishingProvider):
    """Shared mock behavior — subclasses only declare identity + constraints."""

    key = "mock"
    label = "Mock Publisher"
    post_url_template = "mock://posts/{platform}/{post_id}"
    runtime_provider: str = ""
    credential_env: str = ""

    def is_available(self) -> bool:
        return True

    def _runtime_publish(self, package: dict) -> "dict | None":
        """Attempt a real publish via ProviderRuntime when credentials exist."""
        runtime_name = self.runtime_provider or _RUNTIME_PROVIDER_MAP.get(self.key, "")
        if not runtime_name:
            return None
        try:
            from services.provider_runtime import get_provider, get_provider_runtime
            from services.provider_runtime.config import has_credential

            adapter = get_provider(runtime_name)
            env = self.credential_env or (adapter.api_key_env if adapter else "")
            if not env or not has_credential(env):
                return None
            runtime = get_provider_runtime()
            response = runtime.publish(
                {"package": package, "platform": self.key},
                preferred_provider=runtime_name,
                allow_fallback=False,
            )
            if not response.success:
                return {
                    "status": "failed",
                    "provider": runtime_name,
                    "platform": self.key,
                    "post_id": "",
                    "post_url": "",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "error": response.error,
                    "mock": False,
                }
            data = dict(response.data)
            data.setdefault("provider", runtime_name)
            data.setdefault("platform", self.key)
            data.setdefault("mock", False)
            data.setdefault("error", "")
            return data
        except Exception as exc:  # noqa: BLE001 — never break the publish queue
            return {
                "status": "failed",
                "provider": runtime_name,
                "platform": self.key,
                "post_id": "",
                "post_url": "",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "mock": False,
            }

    def dry_run(self, package: dict) -> dict:
        """Validate credentials/constraints without uploading (production smoke)."""
        problems = []
        try:
            constraints = self.constraints() if hasattr(self, "constraints") else {}
            title = str((package.get("title") or package.get("metadata", {}).get("title") or ""))
            max_title = int(constraints.get("max_title_chars") or 0)
            if max_title and len(title) > max_title:
                problems.append(f"title exceeds {max_title} chars")
        except Exception as exc:  # noqa: BLE001
            problems.append(str(exc))

        runtime_name = self.runtime_provider or _RUNTIME_PROVIDER_MAP.get(self.key, "")
        credentials_present = False
        if runtime_name or self.credential_env:
            try:
                from services.provider_runtime import get_provider
                from services.provider_runtime.config import has_credential

                adapter = get_provider(runtime_name) if runtime_name else None
                env = self.credential_env or (adapter.api_key_env if adapter else "")
                credentials_present = bool(env and has_credential(env))
            except Exception:  # noqa: BLE001
                credentials_present = False

        post_id = f"dryrun_{uuid.uuid4().hex[:10]}"
        return {
            "status": "failed" if problems else "published",
            "provider": self.key,
            "platform": self.key,
            "post_id": post_id,
            "post_url": "",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "error": "; ".join(problems),
            "mock": True,
            "dry_run": True,
            "credentials_present": credentials_present,
            "validated": not problems,
        }

    def publish(self, package: dict) -> dict:
        if package.get("dry_run") or package.get("publish_mode") == "dry_run":
            return self.dry_run(package)
        real = self._runtime_publish(package)
        if real is not None:
            return real
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
    runtime_provider = "youtube"
    credential_env = "YOUTUBE_ACCESS_TOKEN"

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
    runtime_provider = "instagram"
    credential_env = "INSTAGRAM_ACCESS_TOKEN"

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
    runtime_provider = "facebook"
    credential_env = "FACEBOOK_ACCESS_TOKEN"

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
    runtime_provider = "tiktok"
    credential_env = "TIKTOK_ACCESS_TOKEN"

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
    runtime_provider = "x"
    credential_env = "X_ACCESS_TOKEN"

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
    runtime_provider = "linkedin"
    credential_env = "LINKEDIN_ACCESS_TOKEN"

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
