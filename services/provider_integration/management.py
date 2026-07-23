"""Provider enable/disable, model defaults, connection tests, dashboard."""

from __future__ import annotations

import time
from typing import Any

from services.provider_integration.catalog import MODEL_ROLES, list_registered_providers
from services.provider_runtime.config import load_runtime_config, save_runtime_config
from services.provider_runtime.security import get_audit_log, validate_credential


def get_model_defaults() -> dict[str, str]:
    cfg = load_runtime_config()
    defaults = dict(cfg.get("model_defaults") or {})
    for role in MODEL_ROLES:
        defaults.setdefault(role, "")
    return defaults


def set_model_defaults(updates: dict[str, str]) -> dict:
    cfg = load_runtime_config()
    defaults = dict(cfg.get("model_defaults") or {})
    for role, value in (updates or {}).items():
        if role in MODEL_ROLES:
            defaults[role] = str(value or "")
    cfg["model_defaults"] = defaults
    # Fallback chains
    fallbacks = dict(cfg.get("fallback_providers") or {})
    if "fallbacks" in (updates or {}):
        fallbacks.update(updates.get("fallbacks") or {})
        cfg["fallback_providers"] = fallbacks
    save_runtime_config(cfg)
    get_audit_log().record("model_defaults_updated", roles=list(updates or {}))
    return defaults


def enable_provider(name: str) -> dict:
    name = str(name or "").strip()
    cfg = load_runtime_config()
    disabled = [p for p in (cfg.get("disabled_providers") or []) if p != name]
    cfg["disabled_providers"] = disabled
    save_runtime_config(cfg)
    get_audit_log().record("provider_enabled", provider=name)
    return {"ok": True, "provider": name, "enabled": True}


def disable_provider(name: str) -> dict:
    name = str(name or "").strip()
    cfg = load_runtime_config()
    disabled = list(cfg.get("disabled_providers") or [])
    if name and name not in disabled:
        disabled.append(name)
    cfg["disabled_providers"] = disabled
    save_runtime_config(cfg)
    get_audit_log().record("provider_disabled", provider=name)
    return {"ok": True, "provider": name, "enabled": False}


def run_provider_connection_test(name: str) -> dict[str, Any]:
    """Auth + optional health probe. Never returns secrets."""
    from services.provider_runtime import get_provider_runtime

    name = str(name or "").strip()
    runtime = get_provider_runtime()
    started = time.time()
    auth = validate_credential(name)
    latency_ms = 0
    health_score = 0.0
    version = ""
    probe_ok = False
    error = ""

    try:
        from services.provider_runtime.registry import get_provider

        adapter = get_provider(name)
    except Exception:  # noqa: BLE001
        adapter = None

    if adapter is not None:
        version = getattr(adapter, "api_version", "") or getattr(adapter, "model", "") or ""
        try:
            t0 = time.time()
            if hasattr(adapter, "health_check"):
                result = adapter.health_check()
                probe_ok = bool(result is True or (isinstance(result, dict) and result.get("ok", True)))
            elif hasattr(adapter, "is_available"):
                probe_ok = bool(adapter.is_available())
            else:
                probe_ok = bool(auth.get("valid"))
            latency_ms = int((time.time() - t0) * 1000)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            probe_ok = False
            latency_ms = int((time.time() - started) * 1000)

    health = {}
    try:
        health = (runtime.health_report() or {}).get(name, {})
        health_score = float(health.get("health_score") or health.get("score") or (100 if probe_ok else 0))
    except Exception:  # noqa: BLE001
        health_score = 100.0 if probe_ok and auth.get("valid") else 0.0

    usage = {}
    try:
        usage = (runtime.usage_summary() or {}).get(name, {})
    except Exception:  # noqa: BLE001
        usage = {}

    ok = bool(auth.get("valid")) and (probe_ok or adapter is None)
    report = {
        "provider": name,
        "ok": ok,
        "authentication": bool(auth.get("valid")),
        "auth_reason": auth.get("reason", ""),
        "connection": probe_ok,
        "latency_ms": latency_ms,
        "health_score": health_score,
        "version": version,
        "daily_usage": usage.get("calls", 0),
        "monthly_usage": usage.get("calls", 0),
        "estimated_cost_usd": round(float(usage.get("total_cost_usd") or 0), 4),
        "quota_status": "unknown",
        "error": error,
        "duration_ms": int((time.time() - started) * 1000),
    }
    get_audit_log().record("provider_connection_test", provider=name, ok=ok)
    return report


def get_integration_dashboard() -> dict:
    providers = list_registered_providers()
    by_cat: dict[str, int] = {}
    for p in providers:
        by_cat[p.get("category", "other")] = by_cat.get(p.get("category", "other"), 0) + 1
    return {
        "provider_count": len(providers),
        "enabled_count": sum(1 for p in providers if p.get("enabled")),
        "credentialed_count": sum(1 for p in providers if p.get("credential_present")),
        "live_count": sum(1 for p in providers if p.get("status") == "live"),
        "by_category": by_cat,
        "model_defaults": get_model_defaults(),
        "providers": providers,
    }
