"""Runtime reliability — weighting, blacklist, latency, automatic recovery."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class LatencyStats:
    samples: list[float] = field(default_factory=list)

    def record(self, latency_ms: float) -> None:
        self.samples.append(float(latency_ms))
        if len(self.samples) > 100:
            self.samples = self.samples[-100:]

    @property
    def avg_ms(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.samples:
            return 0.0
        ordered = sorted(self.samples)
        idx = min(len(ordered) - 1, int(len(ordered) * 0.95))
        return ordered[idx]


class ProviderReliabilityManager:
    """Tracks weights, blacklist, latency, and recovery for providers."""

    def __init__(self, blacklist_ttl_sec: float = 300.0) -> None:
        self._weights: dict[str, float] = {}
        self._blacklist: dict[str, float] = {}  # name -> unblock_at
        self._latency: dict[str, LatencyStats] = defaultdict(LatencyStats)
        self._blacklist_ttl = blacklist_ttl_sec
        self._retry_counts: dict[str, int] = defaultdict(int)
        self._failure_counts: dict[str, int] = defaultdict(int)
        self._success_counts: dict[str, int] = defaultdict(int)

    def set_weight(self, provider: str, weight: float) -> None:
        self._weights[provider] = max(0.0, float(weight))

    def get_weight(self, provider: str) -> float:
        return float(self._weights.get(provider, 1.0))

    def blacklist(self, provider: str, ttl_sec: "float | None" = None) -> None:
        self._blacklist[provider] = time.time() + float(ttl_sec if ttl_sec is not None else self._blacklist_ttl)

    def unblacklist(self, provider: str) -> None:
        self._blacklist.pop(provider, None)

    def is_blacklisted(self, provider: str) -> bool:
        until = self._blacklist.get(provider)
        if until is None:
            return False
        if time.time() >= until:
            self._blacklist.pop(provider, None)
            return False
        return True

    def record_latency(self, provider: str, latency_ms: float) -> None:
        self._latency[provider].record(latency_ms)

    def record_success(self, provider: str, latency_ms: float = 0.0) -> None:
        self._success_counts[provider] += 1
        if latency_ms:
            self.record_latency(provider, latency_ms)
        # Gradual weight recovery
        self._weights[provider] = min(2.0, self.get_weight(provider) + 0.05)
        self.unblacklist(provider)

    def record_failure(self, provider: str, error: str = "", latency_ms: float = 0.0) -> None:
        self._failure_counts[provider] += 1
        self._retry_counts[provider] += 1
        if latency_ms:
            self.record_latency(provider, latency_ms)
        self._weights[provider] = max(0.1, self.get_weight(provider) - 0.2)
        # Auto-blacklist after repeated failures
        if self._failure_counts[provider] >= 5 and self._failure_counts[provider] % 5 == 0:
            self.blacklist(provider)

    def success_rate(self, provider: str) -> float:
        ok = self._success_counts[provider]
        fail = self._failure_counts[provider]
        total = ok + fail
        return (ok / total) if total else 1.0

    def latency_report(self) -> dict:
        return {
            name: {"avg_ms": stats.avg_ms, "p95_ms": stats.p95_ms, "samples": len(stats.samples)}
            for name, stats in self._latency.items()
        }

    def report(self) -> dict:
        names = set(self._weights) | set(self._success_counts) | set(self._failure_counts) | set(self._blacklist)
        out = {}
        for name in names:
            out[name] = {
                "weight": self.get_weight(name),
                "blacklisted": self.is_blacklisted(name),
                "successes": self._success_counts[name],
                "failures": self._failure_counts[name],
                "retries": self._retry_counts[name],
                "success_rate": round(self.success_rate(name), 4),
                "latency": {
                    "avg_ms": self._latency[name].avg_ms,
                    "p95_ms": self._latency[name].p95_ms,
                },
            }
        return out

    def recover(self, provider: str = "") -> int:
        """Force recovery — clear blacklist and restore weights."""
        if provider:
            self.unblacklist(provider)
            self._weights[provider] = 1.0
            self._failure_counts[provider] = 0
            return 1
        count = len(self._blacklist)
        self._blacklist.clear()
        for name in list(self._weights):
            self._weights[name] = 1.0
        return count
