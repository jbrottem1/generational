"""Upload helpers — chunked / resumable uploads for publishing connectors."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from services.provider_runtime.http_client import HttpResponse, request_json


@dataclass
class UploadSession:
    upload_id: str
    uri: str
    bytes_uploaded: int = 0
    total_bytes: int = 0
    chunk_size: int = 256 * 1024
    status: str = "active"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "upload_id": self.upload_id,
            "uri": self.uri,
            "bytes_uploaded": self.bytes_uploaded,
            "total_bytes": self.total_bytes,
            "chunk_size": self.chunk_size,
            "status": self.status,
            "metadata": dict(self.metadata),
            "progress_pct": round(100.0 * self.bytes_uploaded / self.total_bytes, 2) if self.total_bytes else 0.0,
        }


class ChunkedUploader:
    """Generic chunked uploader with resume support."""

    def __init__(
        self,
        chunk_size: int = 256 * 1024,
        transport_put: "Callable[[str, bytes, dict], HttpResponse] | None" = None,
    ) -> None:
        self.chunk_size = chunk_size
        self._put = transport_put or self._default_put
        self._sessions: dict[str, UploadSession] = {}

    @staticmethod
    def _default_put(url: str, data: bytes, headers: dict) -> HttpResponse:
        return request_json("PUT", url, data=data, headers=headers, timeout_sec=120.0, retries=1)

    def start(self, uri: str, total_bytes: int = 0, upload_id: str = "", metadata: "dict | None" = None) -> UploadSession:
        uid = upload_id or hashlib.sha1(f"{uri}:{total_bytes}".encode()).hexdigest()[:16]
        session = UploadSession(
            upload_id=uid,
            uri=uri,
            total_bytes=total_bytes,
            chunk_size=self.chunk_size,
            metadata=dict(metadata or {}),
        )
        self._sessions[uid] = session
        return session

    def resume(self, upload_id: str) -> "UploadSession | None":
        return self._sessions.get(upload_id)

    def upload_file(
        self,
        path: "str | Path",
        destination_url: str,
        *,
        headers: "dict | None" = None,
        upload_id: str = "",
        start_at: int = 0,
    ) -> UploadSession:
        path = Path(path)
        total = path.stat().st_size
        session = self.start(destination_url, total_bytes=total, upload_id=upload_id)
        session.bytes_uploaded = max(0, start_at)
        with path.open("rb") as handle:
            handle.seek(session.bytes_uploaded)
            while session.bytes_uploaded < total:
                chunk = handle.read(self.chunk_size)
                if not chunk:
                    break
                end = session.bytes_uploaded + len(chunk) - 1
                chunk_headers = {
                    **(headers or {}),
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {session.bytes_uploaded}-{end}/{total}",
                }
                resp = self._put(destination_url, chunk, chunk_headers)
                if not resp.ok and resp.status not in (200, 201, 308):
                    session.status = "failed"
                    session.metadata["error"] = f"upload chunk failed: {resp.status}"
                    return session
                session.bytes_uploaded += len(chunk)
        session.status = "completed"
        return session

    def upload_bytes(
        self,
        data: bytes,
        destination_url: str,
        *,
        headers: "dict | None" = None,
        upload_id: str = "",
        start_at: int = 0,
    ) -> UploadSession:
        total = len(data)
        session = self.start(destination_url, total_bytes=total, upload_id=upload_id)
        session.bytes_uploaded = max(0, min(start_at, total))
        while session.bytes_uploaded < total:
            end = min(session.bytes_uploaded + self.chunk_size, total)
            chunk = data[session.bytes_uploaded:end]
            chunk_headers = {
                **(headers or {}),
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {session.bytes_uploaded}-{end - 1}/{total}",
            }
            resp = self._put(destination_url, chunk, chunk_headers)
            if not resp.ok and resp.status not in (200, 201, 308):
                session.status = "failed"
                session.metadata["error"] = f"upload chunk failed: {resp.status}"
                return session
            session.bytes_uploaded = end
        session.status = "completed"
        return session


class OAuthTokenManager:
    """Refresh OAuth access tokens for publishing platforms."""

    def __init__(self, overrides: "dict[str, str] | None" = None) -> None:
        self._overrides = dict(overrides or {})
        self._cache: dict[str, dict] = {}

    def get_access_token(self, platform: str) -> str:
        from services.provider_runtime.config import get_credential

        env_map = {
            "youtube": ("YOUTUBE_ACCESS_TOKEN", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"),
            "tiktok": ("TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN", "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"),
            "instagram": ("INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_REFRESH_TOKEN", "INSTAGRAM_CLIENT_ID", "INSTAGRAM_CLIENT_SECRET"),
            "facebook": ("FACEBOOK_ACCESS_TOKEN", "FACEBOOK_REFRESH_TOKEN", "FACEBOOK_CLIENT_ID", "FACEBOOK_CLIENT_SECRET"),
            "x": ("X_ACCESS_TOKEN", "X_REFRESH_TOKEN", "X_CLIENT_ID", "X_CLIENT_SECRET"),
            "linkedin": ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_REFRESH_TOKEN", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"),
        }
        access_env, refresh_env, client_id_env, client_secret_env = env_map.get(
            platform, ("", "", "", "")
        )
        access = get_credential(access_env, self._overrides)
        if access:
            return access
        refresh = get_credential(refresh_env, self._overrides)
        client_id = get_credential(client_id_env, self._overrides)
        client_secret = get_credential(client_secret_env, self._overrides)
        if not (refresh and client_id and client_secret):
            return ""
        return self.refresh(platform, refresh, client_id, client_secret)

    def refresh(self, platform: str, refresh_token: str, client_id: str, client_secret: str) -> str:
        endpoints = {
            "youtube": "https://oauth2.googleapis.com/token",
            "tiktok": "https://open.tiktokapis.com/v2/oauth/token/",
            "instagram": "https://graph.facebook.com/v21.0/oauth/access_token",
            "facebook": "https://graph.facebook.com/v21.0/oauth/access_token",
            "x": "https://api.x.com/2/oauth2/token",
            "linkedin": "https://www.linkedin.com/oauth/v2/accessToken",
        }
        url = endpoints.get(platform)
        if not url:
            return ""
        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        resp = request_json("POST", url, json_body=body, timeout_sec=30.0, retries=1)
        if not resp.ok or not isinstance(resp.body, dict):
            return ""
        token = str(resp.body.get("access_token") or "")
        if token:
            self._cache[platform] = resp.body
            self._overrides[f"{platform.upper()}_ACCESS_TOKEN" if platform != "x" else "X_ACCESS_TOKEN"] = token
        return token

    def cached(self, platform: str) -> dict:
        return dict(self._cache.get(platform) or {})
