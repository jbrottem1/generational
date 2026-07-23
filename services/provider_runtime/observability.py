"""Observability bridge — emit ProviderRuntime metrics into Analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.provider_runtime.models import ProviderResponse


def build_provider_metric(response: ProviderResponse, **extra: Any) -> dict:
    """One analytics-ready metric record for a provider invocation."""
    return {
        "metric_type": "provider_runtime",
        "provider": response.provider,
        "operation": response.operation,
        "success": response.success,
        "demo_mode": response.demo_mode,
        "tokens_used": int(response.tokens_used or 0),
        "cost_usd": float(response.cost_usd or 0.0),
        "latency_ms": int(response.latency_ms or 0),
        "attempts": int(response.attempts or 1),
        "fallbacks_used": list(response.fallbacks_used or []),
        "error": response.error or "",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def emit_provider_metrics(response: ProviderResponse, **extra: Any) -> dict:
    """Best-effort write into AnalyticsStore; never raises into the runtime."""
    record = build_provider_metric(response, **extra)
    try:
        from services.analytics.store import get_analytics_store

        store = get_analytics_store()
        # Analytics records expect a broader schema; nest provider metrics.
        analytics_record = {
            "analytics_ref": f"provider:{response.provider}:{response.operation}:{record['recorded_at']}",
            "source": "provider_runtime",
            "platform": response.provider,
            "provider_metrics": record,
            "tokens_used": record["tokens_used"],
            "cost_usd": record["cost_usd"],
            "latency_ms": record["latency_ms"],
            "success": record["success"],
            "created_at": record["recorded_at"],
        }
        if hasattr(store, "add_record"):
            store.add_record(analytics_record)
        elif hasattr(store, "append"):
            store.append(analytics_record)
    except Exception:  # noqa: BLE001 — observability must not break generation
        pass
    return record


def summarize_provider_metrics(records: list[dict]) -> dict:
    """Aggregate provider metric records into a dashboard summary."""
    by_provider: dict[str, dict] = {}
    for rec in records:
        metrics = rec.get("provider_metrics") or rec
        name = str(metrics.get("provider") or "unknown")
        entry = by_provider.setdefault(
            name,
            {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "tokens": 0,
                "cost_usd": 0.0,
                "latency_total_ms": 0,
                "retries": 0,
            },
        )
        entry["calls"] += 1
        if metrics.get("success"):
            entry["successes"] += 1
        else:
            entry["failures"] += 1
        entry["tokens"] += int(metrics.get("tokens_used") or 0)
        entry["cost_usd"] += float(metrics.get("cost_usd") or 0)
        entry["latency_total_ms"] += int(metrics.get("latency_ms") or 0)
        entry["retries"] += max(0, int(metrics.get("attempts") or 1) - 1)
    for entry in by_provider.values():
        calls = entry["calls"] or 1
        entry["success_rate"] = round(entry["successes"] / calls, 4)
        entry["avg_latency_ms"] = round(entry["latency_total_ms"] / calls, 2)
    return by_provider
