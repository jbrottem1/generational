"""Publishing platform connectors — YouTube, TikTok, Instagram, Facebook, X.

These adapters implement ProviderRuntime capabilities for publish operations
while remaining compatible with the legacy PublishingProvider interface used
by the Publishing Engine. Real OAuth tokens come from env vars; without them
adapters report unavailable and the mock publishing path remains the fallback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse

PUBLISH = cap.PUBLISH


class PublishingConnector(ProductionConnector):
    """Shared publish connector behavior."""

    platform: str = ""
    capabilities = (PUBLISH,)
    profile = ProviderProfile(quality=80, cost_per_unit=0.0, speed=70, consistency=90, latency_ms=5000)
    implementation_status = "production"
    default_timeout_sec = 60.0

    def _package(self, request: ProviderRequest) -> dict:
        return dict(request.payload.get("package") or request.payload)

    def _success_payload(self, request: ProviderRequest, remote: dict) -> ProviderResponse:
        package = self._package(request)
        post_id = str(remote.get("id") or remote.get("post_id") or f"post_{uuid.uuid4().hex[:10]}")
        return self.ok(
            request,
            {
                "status": "published",
                "provider": self.name,
                "platform": self.platform or self.name,
                "post_id": post_id,
                "post_url": remote.get("url") or remote.get("post_url") or "",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "title": package.get("title") or "",
                "mock": False,
            },
        )


class YouTubePublishingConnector(PublishingConnector):
    name = "youtube"
    label = "YouTube"
    platform = "youtube"
    api_key_env = "YOUTUBE_ACCESS_TOKEN"
    base_url = "https://www.googleapis.com/upload/youtube/v3"
    profile = ProviderProfile(quality=88, cost_per_unit=0.0, speed=55, consistency=92, latency_ms=15000)

    def auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key()}",
            "Content-Type": "application/json",
        }

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        if not package.get("title"):
            return self.fail(request, "YouTube publish requires title")
        video_uri = (package.get("video") or {}).get("uri") or package.get("video_uri") or ""
        body = {
            "snippet": {
                "title": package.get("title"),
                "description": package.get("description") or "",
                "tags": package.get("hashtags") or [],
                "categoryId": str(package.get("category_id") or "22"),
            },
            "status": {
                "privacyStatus": str(package.get("visibility") or "private"),
                "selfDeclaredMadeForKids": False,
            },
        }
        # Metadata-only init when binary upload is handled out-of-band.
        if not video_uri:
            body["status"]["privacyStatus"] = "private"
        resp = self.http(
            "POST",
            "/videos?part=snippet,status&uploadType=resumable",
            json_body=body,
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"YouTube error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        data.setdefault("url", f"https://youtube.com/watch?v={data.get('id', '')}")
        return self._success_payload(request, data)


class TikTokPublishingConnector(PublishingConnector):
    name = "tiktok"
    label = "TikTok"
    platform = "tiktok"
    api_key_env = "TIKTOK_ACCESS_TOKEN"
    base_url = "https://open.tiktokapis.com/v2"
    profile = ProviderProfile(quality=85, cost_per_unit=0.0, speed=60, consistency=88, latency_ms=12000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        body = {
            "post_info": {
                "title": package.get("title") or "",
                "privacy_level": str(package.get("visibility") or "SELF_ONLY"),
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_url": (package.get("video") or {}).get("uri") or package.get("video_uri") or "",
            },
        }
        resp = self.http(
            "POST",
            "/post/publish/video/init/",
            json_body=body,
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"TikTok error: {resp.status} {resp.body}")
        data = (resp.body or {}).get("data") if isinstance(resp.body, dict) else {}
        data = data or (resp.body if isinstance(resp.body, dict) else {})
        return self._success_payload(request, data)


class InstagramPublishingConnector(PublishingConnector):
    name = "instagram"
    label = "Instagram"
    platform = "instagram"
    api_key_env = "INSTAGRAM_ACCESS_TOKEN"
    base_url = "https://graph.facebook.com/v21.0"
    profile = ProviderProfile(quality=84, cost_per_unit=0.0, speed=58, consistency=86, latency_ms=14000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        from services.provider_runtime.config import get_credential

        ig_user = get_credential("INSTAGRAM_BUSINESS_ACCOUNT_ID", self._credential_overrides())
        if not ig_user:
            return self.fail(request, "INSTAGRAM_BUSINESS_ACCOUNT_ID required")
        video_url = (package.get("video") or {}).get("uri") or package.get("video_uri") or ""
        caption = " ".join(
            filter(
                None,
                [
                    package.get("title") or "",
                    package.get("description") or "",
                    " ".join(package.get("hashtags") or []),
                ],
            )
        )
        create_body = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": self.api_key(),
        }
        resp = self.http(
            "POST",
            f"/{ig_user}/media",
            json_body=create_body,
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"Instagram create error: {resp.status} {resp.body}")
        creation_id = (resp.body or {}).get("id") if isinstance(resp.body, dict) else ""
        publish = self.http(
            "POST",
            f"/{ig_user}/media_publish",
            json_body={"creation_id": creation_id, "access_token": self.api_key()},
            timeout_sec=request.timeout_sec,
        )
        if not publish.ok:
            return self.fail(request, f"Instagram publish error: {publish.status} {publish.body}")
        data = publish.body if isinstance(publish.body, dict) else {"id": creation_id}
        return self._success_payload(request, data)


class FacebookPublishingConnector(PublishingConnector):
    name = "facebook"
    label = "Facebook"
    platform = "facebook"
    api_key_env = "FACEBOOK_ACCESS_TOKEN"
    base_url = "https://graph.facebook.com/v21.0"
    profile = ProviderProfile(quality=82, cost_per_unit=0.0, speed=60, consistency=85, latency_ms=12000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        from services.provider_runtime.config import get_credential

        page_id = get_credential("FACEBOOK_PAGE_ID", self._credential_overrides())
        if not page_id:
            return self.fail(request, "FACEBOOK_PAGE_ID required")
        video_url = (package.get("video") or {}).get("uri") or package.get("video_uri") or ""
        body = {
            "file_url": video_url,
            "description": package.get("description") or package.get("title") or "",
            "access_token": self.api_key(),
        }
        resp = self.http(
            "POST",
            f"/{page_id}/videos",
            json_body=body,
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"Facebook error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self._success_payload(request, data)


class XPublishingConnector(PublishingConnector):
    name = "x"
    label = "X (Twitter)"
    platform = "x"
    api_key_env = "X_ACCESS_TOKEN"
    base_url = "https://api.x.com/2"
    profile = ProviderProfile(quality=80, cost_per_unit=0.0, speed=75, consistency=84, latency_ms=8000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        text = str(package.get("title") or package.get("description") or "")
        if not text:
            return self.fail(request, "X publish requires text")
        hashtags = package.get("hashtags") or []
        if hashtags:
            text = f"{text} {' '.join(hashtags)}".strip()
        body = {"text": text[:280]}
        media_id = package.get("media_id")
        if media_id:
            body["media"] = {"media_ids": [str(media_id)]}
        resp = self.http("POST", "/tweets", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"X error: {resp.status} {resp.body}")
        data = (resp.body or {}).get("data") if isinstance(resp.body, dict) else {}
        data = data or (resp.body if isinstance(resp.body, dict) else {})
        tweet_id = data.get("id") or ""
        data["url"] = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else ""
        return self._success_payload(request, data)
