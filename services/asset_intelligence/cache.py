"""Cache façade — reuse local_cache + asset_generation fingerprint cache.

Does not regenerate media; only resolves existing hits.
"""

from __future__ import annotations

from typing import Any


def resolve_cached_uri(kind: str, identifier: str) -> dict[str, Any]:
    """Look up an existing local_cache entry without downloading."""
    try:
        from services.media_production.local_cache import get_cached

        path = get_cached(kind, identifier)
        if path is not None:
            return {"ok": True, "source": "local_cache", "path": str(path), "cached": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "source": "local_cache", "cached": False, "error": str(exc)[:160]}
    return {"ok": False, "source": "local_cache", "cached": False, "error": "miss"}


def resolve_fingerprint_cache(fingerprint: str) -> dict[str, Any]:
    """Look up asset_generation registry by content fingerprint."""
    if not fingerprint:
        return {"ok": False, "cached": False, "error": "empty_fingerprint"}
    try:
        from services.asset_generation.cache import lookup_cached_asset
        from services.asset_generation.registry import get_asset_registry

        asset = lookup_cached_asset(get_asset_registry(), fingerprint)
        if asset:
            return {
                "ok": True,
                "source": "asset_generation",
                "cached": True,
                "asset_id": asset.get("asset_id"),
                "uri": asset.get("uri"),
                "fingerprint": fingerprint,
            }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "source": "asset_generation", "cached": False, "error": str(exc)[:160]}
    return {"ok": False, "source": "asset_generation", "cached": False, "error": "miss"}


def prefer_cached_media(
    *,
    kind: str = "",
    identifier: str = "",
    fingerprint: str = "",
) -> dict[str, Any]:
    """Prefer any existing cache over generating/downloading again."""
    if fingerprint:
        hit = resolve_fingerprint_cache(fingerprint)
        if hit.get("ok"):
            return hit
    if kind and identifier:
        hit = resolve_cached_uri(kind, identifier)
        if hit.get("ok"):
            return hit
    return {"ok": False, "cached": False, "error": "no_cache_hit"}
