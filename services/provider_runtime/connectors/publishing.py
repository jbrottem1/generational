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

    def api_key(self) -> str:
        from services.provider_runtime.uploads import OAuthTokenManager

        token = OAuthTokenManager(self._credential_overrides()).get_access_token("youtube")
        return token or super().api_key()

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
        video_path = (package.get("video") or {}).get("path") or package.get("video_path") or ""
        schedule_at = package.get("scheduled_at") or request.payload.get("scheduled_at")
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
        if schedule_at:
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = schedule_at
        if not video_uri and not video_path:
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
        upload_url = resp.headers.get("Location") or resp.headers.get("location") or ""
        upload_meta = {}
        if video_path and upload_url:
            from pathlib import Path

            from services.provider_runtime.uploads import ChunkedUploader

            if Path(video_path).exists():
                session = ChunkedUploader().upload_file(
                    video_path,
                    upload_url,
                    headers={"Authorization": f"Bearer {self.api_key()}"},
                    upload_id=str(request.payload.get("upload_id") or ""),
                    start_at=int(request.payload.get("resume_bytes") or 0),
                )
                upload_meta = session.to_dict()
                if session.status == "failed":
                    return self.fail(request, upload_meta.get("error") or "chunked upload failed", upload=upload_meta)
        # Thumbnail upload
        thumb = package.get("thumbnail_uri") or package.get("thumbnail_path") or ""
        video_id = data.get("id") or ""
        if thumb and video_id:
            self.http(
                "POST",
                f"/thumbnails/set?videoId={video_id}",
                json_body={"uri": thumb},
                timeout_sec=30.0,
            )
        data.setdefault("url", f"https://youtube.com/watch?v={video_id}")
        result = self._success_payload(request, data)
        if upload_meta:
            result.data["upload"] = upload_meta
        if schedule_at:
            result.data["scheduled_at"] = schedule_at
            result.data["status"] = "scheduled"
        return result


class TikTokPublishingConnector(PublishingConnector):
    name = "tiktok"
    label = "TikTok"
    platform = "tiktok"
    api_key_env = "TIKTOK_ACCESS_TOKEN"
    base_url = "https://open.tiktokapis.com/v2"
    profile = ProviderProfile(quality=85, cost_per_unit=0.0, speed=60, consistency=88, latency_ms=12000)

    def api_key(self) -> str:
        from services.provider_runtime.uploads import OAuthTokenManager

        return OAuthTokenManager(self._credential_overrides()).get_access_token("tiktok") or super().api_key()

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
        if package.get("scheduled_at"):
            body["post_info"]["schedule_time"] = package["scheduled_at"]
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
        # Status polling hook
        publish_id = data.get("publish_id") or data.get("id") or ""
        if publish_id and request.payload.get("poll_status"):
            status = self.http(
                "POST",
                "/post/publish/status/fetch/",
                json_body={"publish_id": publish_id},
                timeout_sec=30.0,
            )
            if status.ok and isinstance(status.body, dict):
                data["poll"] = status.body
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


class LinkedInPublishingConnector(PublishingConnector):
    name = "linkedin"
    label = "LinkedIn"
    platform = "linkedin"
    api_key_env = "LINKEDIN_ACCESS_TOKEN"
    base_url = "https://api.linkedin.com/v2"
    profile = ProviderProfile(quality=83, cost_per_unit=0.0, speed=62, consistency=88, latency_ms=10000)

    def api_key(self) -> str:
        from services.provider_runtime.uploads import OAuthTokenManager

        return OAuthTokenManager(self._credential_overrides()).get_access_token("linkedin") or super().api_key()

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        package = self._package(request)
        from services.provider_runtime.config import get_credential

        author = get_credential("LINKEDIN_AUTHOR_URN", self._credential_overrides())
        if not author:
            return self.fail(request, "LINKEDIN_AUTHOR_URN required")
        text = str(package.get("description") or package.get("title") or "")
        body = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        video_urn = package.get("media_urn") or package.get("media_id")
        if video_urn:
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "VIDEO"
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "media": video_urn, "title": {"text": package.get("title") or ""}}
            ]
        resp = self.http("POST", "/ugcPosts", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"LinkedIn error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        data.setdefault("id", data.get("id") or "")
        return self._success_payload(request, data)
