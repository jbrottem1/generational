"""Health / diagnostics aggregation for the Settings Health tab."""

from __future__ import annotations


def get_health_dashboard() -> dict:
    from services.provider_runtime import get_provider_runtime
    from services.provider_runtime.security import get_audit_log
    from services.studio.providers import get_provider_dashboard

    runtime = get_provider_runtime()
    dash = get_provider_dashboard()
    health = runtime.health_report() if hasattr(runtime, "health_report") else {}
    reliability = runtime.reliability_report() if hasattr(runtime, "reliability_report") else {}

    providers = []
    for entry in dash.get("providers") or []:
        name = entry.get("name")
        h = health.get(name, {}) if isinstance(health, dict) else {}
        providers.append(
            {
                "name": name,
                "label": entry.get("label", name),
                "status": entry.get("health", "unknown"),
                "available": entry.get("available"),
                "latency_ms": h.get("latency_ms") or entry.get("estimated_runtime_sec", 0) * 1000,
                "failures": entry.get("failures", 0),
                "retries": h.get("retries", 0),
                "circuit_open": entry.get("circuit_open", False),
                "quota_remaining": h.get("quota_remaining", "unknown"),
                "api_errors": h.get("api_errors", entry.get("failures", 0)),
                "calls": entry.get("calls", 0),
                "cost_usd": entry.get("cost_usd", 0),
            }
        )

    return {
        "healthy_count": dash.get("healthy_count", 0),
        "degraded_count": dash.get("degraded_count", 0),
        "unavailable_count": dash.get("unavailable_count", 0),
        "providers": providers,
        "reliability": reliability if isinstance(reliability, dict) else {},
        "audit_events": get_audit_log().events()[-50:],
        "secrets": runtime.secrets_status() if hasattr(runtime, "secrets_status") else {},
    }
