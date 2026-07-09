"""Provider runtime request/response models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderRequest:
    """Unified request envelope for any provider operation."""

    operation: str
    payload: dict = field(default_factory=dict)
    capability: str = ""
    preferred_provider: str = ""
    optimize_for: str = "quality"  # quality | speed | cost
    timeout_sec: float = 120.0
    max_retries: int = 2
    allow_fallback: bool = True
    parallel_candidates: int = 0  # 0 = single provider; >1 = race/vote


@dataclass
class ProviderResponse:
    """Unified response from a provider operation."""

    success: bool
    data: dict = field(default_factory=dict)
    provider: str = ""
    operation: str = ""
    error: str = ""
    demo_mode: bool = False
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    attempts: int = 1
    fallbacks_used: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "provider": self.provider,
            "operation": self.operation,
            "error": self.error,
            "demo_mode": self.demo_mode,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "attempts": self.attempts,
            "fallbacks_used": list(self.fallbacks_used),
            "metadata": dict(self.metadata),
        }


@dataclass
class ProviderProfile:
    """Selection signals for one provider backend."""

    quality: float = 50.0
    cost_per_unit: float = 0.0
    speed: float = 50.0
    consistency: float = 50.0
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "quality": self.quality,
            "cost_per_unit": self.cost_per_unit,
            "speed": self.speed,
            "consistency": self.consistency,
            "latency_ms": self.latency_ms,
        }


@dataclass
class UsageRecord:
    """One logged provider invocation."""

    provider: str
    operation: str
    success: bool
    cost_usd: float = 0.0
    latency_ms: int = 0
    error: str = ""
    timestamp: str = ""
