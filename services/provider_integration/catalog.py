"""Provider catalog — categories, roles, and expandable registration metadata."""

from __future__ import annotations

from copy import deepcopy

PROVIDER_CATEGORIES = (
    "text",
    "image",
    "video",
    "voice",
    "music",
    "publishing",
    "analytics",
    "platform",
    "other",
)

MODEL_ROLES = (
    "default_text",
    "reasoning",
    "research",
    "image",
    "video",
    "voice",
    "music",
    "publishing",
    "analytics",
)

OAUTH_PLATFORMS = (
    "youtube",
    "tiktok",
    "instagram",
    "facebook",
    "linkedin",
    "x",
)

# Capability tags → operator-facing category.
_CAP_TO_CATEGORY = {
    "llm": "text",
    "reasoning": "text",
    "script": "text",
    "caption": "text",
    "metadata": "text",
    "image_generation": "image",
    "video_generation": "video",
    "animation": "video",
    "motion": "video",
    "speech": "voice",
    "voice_cloning": "voice",
    "music": "music",
    "sound_effects": "voice",
    "publish": "publishing",
    "analytics": "analytics",
}

# Declared future / planned providers (installable without code changes once adapter lands).
_EXTRA_CATALOG: dict[str, dict] = {
    "openrouter": {
        "name": "openrouter",
        "label": "OpenRouter",
        "category": "text",
        "api_key_env": "OPENROUTER_API_KEY",
        "capabilities": ["llm", "reasoning"],
        "status": "planned",
    },
    "cartesia": {
        "name": "cartesia",
        "label": "Cartesia",
        "category": "voice",
        "api_key_env": "CARTESIA_API_KEY",
        "capabilities": ["speech"],
        "status": "planned",
    },
    "playht": {
        "name": "playht",
        "label": "PlayHT",
        "category": "voice",
        "api_key_env": "PLAYHT_API_KEY",
        "capabilities": ["speech"],
        "status": "planned",
    },
    "suno": {
        "name": "suno",
        "label": "Suno",
        "category": "music",
        "api_key_env": "SUNO_API_KEY",
        "capabilities": ["music"],
        "status": "planned",
    },
    "udio": {
        "name": "udio",
        "label": "Udio",
        "category": "music",
        "api_key_env": "UDIO_API_KEY",
        "capabilities": ["music"],
        "status": "planned",
    },
    "pinterest": {
        "name": "pinterest",
        "label": "Pinterest",
        "category": "publishing",
        "api_key_env": "PINTEREST_ACCESS_TOKEN",
        "capabilities": ["publish"],
        "status": "planned",
    },
    "google_analytics": {
        "name": "google_analytics",
        "label": "Google Analytics",
        "category": "analytics",
        "api_key_env": "GA_ACCESS_TOKEN",
        "capabilities": ["analytics"],
        "status": "planned",
    },
    "youtube_analytics": {
        "name": "youtube_analytics",
        "label": "YouTube Analytics",
        "category": "analytics",
        "api_key_env": "YOUTUBE_ACCESS_TOKEN",
        "capabilities": ["analytics"],
        "status": "registered",
    },
    "tiktok_analytics": {
        "name": "tiktok_analytics",
        "label": "TikTok Analytics",
        "category": "analytics",
        "api_key_env": "TIKTOK_ACCESS_TOKEN",
        "capabilities": ["analytics"],
        "status": "planned",
    },
    "meta_insights": {
        "name": "meta_insights",
        "label": "Meta Insights",
        "category": "analytics",
        "api_key_env": "FACEBOOK_ACCESS_TOKEN",
        "capabilities": ["analytics"],
        "status": "planned",
    },
    "linkedin_analytics": {
        "name": "linkedin_analytics",
        "label": "LinkedIn Analytics",
        "category": "analytics",
        "api_key_env": "LINKEDIN_ACCESS_TOKEN",
        "capabilities": ["analytics"],
        "status": "planned",
    },
}


def _infer_category(entry: dict) -> str:
    caps = entry.get("capabilities") or []
    for cap in caps:
        if cap in _CAP_TO_CATEGORY:
            return _CAP_TO_CATEGORY[cap]
    name = str(entry.get("name") or "")
    if name in OAUTH_PLATFORMS or name in ("youtube", "tiktok", "instagram", "facebook", "linkedin", "x", "pinterest"):
        return "publishing"
    return "other"


def register_catalog_entry(entry: dict) -> dict:
    """Register a future provider metadata entry (plugin surface)."""
    name = str(entry.get("name") or "").strip()
    if not name:
        raise ValueError("catalog entry requires name")
    payload = deepcopy(entry)
    payload.setdefault("category", _infer_category(payload))
    payload.setdefault("status", "planned")
    _EXTRA_CATALOG[name] = payload
    return payload


def list_registered_providers() -> list[dict]:
    """Merged live ProviderRuntime catalog + planned catalog entries."""
    from services.provider_runtime import ensure_registered, get_provider_runtime
    from services.provider_runtime.config import has_credential, load_runtime_config

    ensure_registered()
    runtime = get_provider_runtime()
    cfg = load_runtime_config()
    disabled = set((cfg.get("disabled_providers") or []))
    enabled_overrides = set((cfg.get("enabled_providers") or []))
    health = runtime.health_report() if hasattr(runtime, "health_report") else {}

    by_name: dict[str, dict] = {}
    for entry in runtime.catalog():
        name = entry.get("name") or entry.get("provider") or ""
        if not name:
            continue
        env = entry.get("api_key_env") or ""
        item = {
            **entry,
            "name": name,
            "category": _infer_category(entry),
            "status": "live" if entry.get("available") else "registered",
            "credential_present": bool(env and has_credential(env)),
            "enabled": name not in disabled,
            "health": health.get(name, {}),
        }
        if enabled_overrides and name not in enabled_overrides and name in disabled:
            item["enabled"] = False
        by_name[name] = item

    for name, extra in _EXTRA_CATALOG.items():
        if name in by_name:
            by_name[name].setdefault("category", extra.get("category"))
            continue
        env = extra.get("api_key_env") or ""
        by_name[name] = {
            **extra,
            "available": False,
            "credential_present": bool(env and has_credential(env)),
            "enabled": name not in disabled,
            "health": {},
            "capabilities": list(extra.get("capabilities") or []),
        }

    return sorted(by_name.values(), key=lambda p: (p.get("category", ""), p.get("name", "")))


def catalog_by_category() -> dict[str, list[dict]]:
    grouped = {cat: [] for cat in PROVIDER_CATEGORIES}
    for item in list_registered_providers():
        cat = item.get("category") or "other"
        grouped.setdefault(cat, []).append(item)
    return grouped
