"""ProviderCostEstimator — cost prediction and usage logging."""

from __future__ import annotations

from datetime import datetime, timezone

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest, ProviderResponse, UsageRecord


class ProviderCostEstimator:
    """Estimates and tracks provider costs."""

    def __init__(self) -> None:
        self._usage_log: list[UsageRecord] = []

    def estimate(self, provider: ProviderAdapter, request: ProviderRequest) -> float:
        return provider.estimate_cost(request)

    def log_usage(self, response: ProviderResponse) -> UsageRecord:
        record = UsageRecord(
            provider=response.provider,
            operation=response.operation,
            success=response.success,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            error=response.error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._usage_log.append(record)
        return record

    def total_cost(self, provider: str = "") -> float:
        records = self._usage_log
        if provider:
            records = [r for r in records if r.provider == provider]
        return sum(r.cost_usd for r in records)

    def usage_summary(self) -> dict:
        by_provider: dict[str, dict] = {}
        for record in self._usage_log:
            entry = by_provider.setdefault(record.provider, {
                "calls": 0, "successes": 0, "failures": 0, "total_cost_usd": 0.0,
            })
            entry["calls"] += 1
            if record.success:
                entry["successes"] += 1
            else:
                entry["failures"] += 1
            entry["total_cost_usd"] += record.cost_usd
        return by_provider

    def clear(self) -> None:
        self._usage_log.clear()
