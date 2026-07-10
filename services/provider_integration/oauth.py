"""OAuth connection management for publishing platforms.

Stores client id/secret and tokens via SecretManager (encrypted at rest when
PROVIDER_SECRETS_PASSPHRASE is set). Never returns raw secrets to callers —
only masked status fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.provider_integration.catalog import OAUTH_PLATFORMS
from services.provider_runtime.config import has_credential, load_runtime_config, save_runtime_config
from services.provider_runtime.secrets import SecretManager, mask_secret
from services.provider_runtime.security import get_audit_log

_ENV_MAP = {
    "youtube": {
        "client_id": "YOUTUBE_CLIENT_ID",
        "client_secret": "YOUTUBE_CLIENT_SECRET",
        "access_token": "YOUTUBE_ACCESS_TOKEN",
        "refresh_token": "YOUTUBE_REFRESH_TOKEN",
    },
    "tiktok": {
        "client_id": "TIKTOK_CLIENT_ID",
        "client_secret": "TIKTOK_CLIENT_SECRET",
        "access_token": "TIKTOK_ACCESS_TOKEN",
        "refresh_token": "TIKTOK_REFRESH_TOKEN",
    },
    "instagram": {
        "client_id": "INSTAGRAM_CLIENT_ID",
        "client_secret": "INSTAGRAM_CLIENT_SECRET",
        "access_token": "INSTAGRAM_ACCESS_TOKEN",
        "refresh_token": "INSTAGRAM_REFRESH_TOKEN",
    },
    "facebook": {
        "client_id": "FACEBOOK_CLIENT_ID",
        "client_secret": "FACEBOOK_CLIENT_SECRET",
        "access_token": "FACEBOOK_ACCESS_TOKEN",
        "refresh_token": "FACEBOOK_REFRESH_TOKEN",
    },
    "linkedin": {
        "client_id": "LINKEDIN_CLIENT_ID",
        "client_secret": "LINKEDIN_CLIENT_SECRET",
        "access_token": "LINKEDIN_ACCESS_TOKEN",
        "refresh_token": "LINKEDIN_REFRESH_TOKEN",
    },
    "x": {
        "client_id": "X_CLIENT_ID",
        "client_secret": "X_CLIENT_SECRET",
        "access_token": "X_ACCESS_TOKEN",
        "refresh_token": "X_REFRESH_TOKEN",
    },
}


def _mgr() -> SecretManager:
    return SecretManager()


def list_oauth_connections() -> list[dict[str, Any]]:
    cfg = load_runtime_config()
    oauth_meta = dict(cfg.get("oauth") or {})
    rows = []
    for platform in OAUTH_PLATFORMS:
        envs = _ENV_MAP.get(platform, {})
        access_env = envs.get("access_token", "")
        refresh_env = envs.get("refresh_token", "")
        client_id_env = envs.get("client_id", "")
        access_present = bool(access_env and has_credential(access_env))
        refresh_present = bool(refresh_env and has_credential(refresh_env))
        client_present = bool(client_id_env and has_credential(client_id_env))
        meta = dict(oauth_meta.get(platform) or {})
        status = "connected" if access_present else ("configured" if client_present else "disconnected")
        rows.append(
            {
                "platform": platform,
                "status": status,
                "client_id_present": client_present,
                "access_token_present": access_present,
                "refresh_token_present": refresh_present,
                "access_token_masked": "••••" if access_present else "",
                "expires_at": meta.get("expires_at", ""),
                "connected_at": meta.get("connected_at", ""),
                "last_tested_at": meta.get("last_tested_at", ""),
                "last_test_ok": meta.get("last_test_ok"),
                "env_map": {k: v for k, v in envs.items()},
            }
        )
    return rows


def save_oauth_tokens(
    platform: str,
    *,
    client_id: str = "",
    client_secret: str = "",
    access_token: str = "",
    refresh_token: str = "",
    expires_at: str = "",
) -> dict:
    platform = str(platform or "").lower().strip()
    if platform not in _ENV_MAP:
        return {"ok": False, "error": f"unsupported platform: {platform}"}
    envs = _ENV_MAP[platform]
    mgr = _mgr()
    saved = []
    mapping = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    for field, value in mapping.items():
        value = str(value or "").strip()
        if not value:
            continue
        env_var = envs[field]
        mgr.rotate(env_var, value)
        mgr.set_override(env_var, value)
        saved.append(field)

    cfg = load_runtime_config()
    oauth = dict(cfg.get("oauth") or {})
    meta = dict(oauth.get(platform) or {})
    if expires_at:
        meta["expires_at"] = expires_at
    meta["connected_at"] = datetime.now(timezone.utc).isoformat()
    oauth[platform] = meta
    cfg["oauth"] = oauth
    save_runtime_config(cfg)
    get_audit_log().record("oauth_tokens_saved", platform=platform, fields=saved)
    return {"ok": True, "platform": platform, "saved_fields": saved}


def disconnect_oauth(platform: str) -> dict:
    platform = str(platform or "").lower().strip()
    envs = _ENV_MAP.get(platform)
    if not envs:
        return {"ok": False, "error": f"unsupported platform: {platform}"}
    mgr = _mgr()
    for env_var in envs.values():
        mgr.delete(env_var)
    cfg = load_runtime_config()
    oauth = dict(cfg.get("oauth") or {})
    oauth[platform] = {"status": "disconnected", "disconnected_at": datetime.now(timezone.utc).isoformat()}
    cfg["oauth"] = oauth
    save_runtime_config(cfg)
    get_audit_log().record("oauth_disconnected", platform=platform)
    return {"ok": True, "platform": platform}


def run_oauth_connection_test(platform: str) -> dict:
    """Non-network structural test: credentials present + optional refresh attempt."""
    platform = str(platform or "").lower().strip()
    envs = _ENV_MAP.get(platform)
    if not envs:
        return {"ok": False, "error": f"unsupported platform: {platform}"}
    access_ok = has_credential(envs["access_token"])
    refresh_ok = has_credential(envs["refresh_token"])
    client_ok = has_credential(envs["client_id"]) and has_credential(envs["client_secret"])
    ok = access_ok or (refresh_ok and client_ok)
    refreshed = False
    if not access_ok and refresh_ok and client_ok:
        try:
            from services.provider_runtime.uploads import OAuthTokenManager

            mgr = OAuthTokenManager()
            # Best-effort; platforms without refresh endpoint stay structural-only.
            if hasattr(mgr, "refresh"):
                mgr.refresh(platform)
                refreshed = True
        except Exception as exc:  # noqa: BLE001
            cfg_err = str(exc)
            _record_test(platform, False)
            return {
                "ok": False,
                "platform": platform,
                "access_token_present": access_ok,
                "refresh_token_present": refresh_ok,
                "client_configured": client_ok,
                "error": cfg_err,
            }

    _record_test(platform, ok)
    return {
        "ok": ok,
        "platform": platform,
        "access_token_present": access_ok,
        "refresh_token_present": refresh_ok,
        "client_configured": client_ok,
        "refreshed": refreshed,
        "access_masked": "••••" if access_ok else "",
    }


def _record_test(platform: str, ok: bool) -> None:
    cfg = load_runtime_config()
    oauth = dict(cfg.get("oauth") or {})
    meta = dict(oauth.get(platform) or {})
    meta["last_tested_at"] = datetime.now(timezone.utc).isoformat()
    meta["last_test_ok"] = ok
    oauth[platform] = meta
    cfg["oauth"] = oauth
    save_runtime_config(cfg)
