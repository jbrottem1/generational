"""Provider status dashboard — wraps ProviderRuntime health and usage."""

from __future__ import annotations


def get_provider_dashboard() -> dict:
    """Aggregate provider health, cost, availability, and usage."""
    from services.provider_runtime import get_provider_runtime

    runtime = get_provider_runtime()
    catalog = runtime.catalog()
    health = runtime.health_report()
    usage = runtime.usage_summary()

    providers = []
    total_cost = 0.0
    total_calls = 0

    for entry in catalog:
        name = entry.get("name", entry.get("provider", "unknown"))
        health_info = health.get(name, {})
        usage_info = usage.get(name, {})
        cost = usage_info.get("total_cost_usd", 0.0)
        calls = usage_info.get("calls", 0)
        total_cost += cost
        total_calls += calls

        circuit_open = health_info.get("circuit_open", False)
        failures = health_info.get("failures", 0)
        available = entry.get("available", True) and not circuit_open

        providers.append({
            "name": name,
            "label": entry.get("label", name),
            "capabilities": entry.get("capabilities", []),
            "available": available,
            "health": "healthy" if available and failures == 0 else (
                "degraded" if available else "unavailable"
            ),
            "failures": failures,
            "circuit_open": circuit_open,
            "calls": calls,
            "successes": usage_info.get("successes", 0),
            "cost_usd": round(cost, 4),
            "estimated_runtime_sec": _estimate_runtime(entry),
        })

    providers.sort(key=lambda p: (-p["calls"], p["name"]))

    return {
        "providers": providers,
        "total_cost_usd": round(total_cost, 4),
        "total_calls": total_calls,
        "healthy_count": sum(1 for p in providers if p["health"] == "healthy"),
        "degraded_count": sum(1 for p in providers if p["health"] == "degraded"),
        "unavailable_count": sum(1 for p in providers if p["health"] == "unavailable"),
    }


def _estimate_runtime(provider_entry: dict) -> int:
    """Rough per-call runtime estimate based on capabilities."""
    caps = provider_entry.get("capabilities", [])
    if "video_generation" in caps:
        return 120
    if "image_generation" in caps:
        return 15
    if "speech" in caps:
        return 10
    if "music" in caps:
        return 30
    return 5
