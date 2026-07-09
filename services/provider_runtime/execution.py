"""Execution helpers — retries, timeouts, rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest, ProviderResponse


class RateLimiter:
    """Simple per-provider rate limiter (requests per minute)."""

    def __init__(self, default_rpm: int = 60) -> None:
        self._default_rpm = default_rpm
        self._windows: dict[str, list[float]] = defaultdict(list)

    def allow(self, provider_name: str, rpm: "int | None" = None) -> bool:
        limit = rpm or self._default_rpm
        now = time.time()
        window = self._windows[provider_name]
        window[:] = [t for t in window if now - t < 60.0]
        if len(window) >= limit:
            return False
        window.append(now)
        return True

    def reset(self) -> None:
        self._windows.clear()


def execute_with_retry(
    provider: ProviderAdapter,
    request: ProviderRequest,
    executor: Callable[[ProviderAdapter, ProviderRequest], ProviderResponse],
    rate_limiter: "RateLimiter | None" = None,
) -> ProviderResponse:
    """Execute with automatic retries and timeout handling."""
    max_attempts = max(1, request.max_retries + 1)
    last_response = ProviderResponse(success=False, operation=request.operation, provider=provider.name)

    for attempt in range(1, max_attempts + 1):
        if rate_limiter and not rate_limiter.allow(provider.name):
            last_response = ProviderResponse(
                success=False,
                operation=request.operation,
                provider=provider.name,
                error="Rate limit exceeded",
                attempts=attempt,
            )
            time.sleep(0.05)
            continue

        started = time.time()
        try:
            response = executor(provider, request)
            response.latency_ms = int((time.time() - started) * 1000)
            response.attempts = attempt
            if response.success:
                return response
            last_response = response
        except Exception as exc:  # noqa: BLE001 — provider must not crash runtime
            last_response = ProviderResponse(
                success=False,
                operation=request.operation,
                provider=provider.name,
                error=str(exc),
                attempts=attempt,
                latency_ms=int((time.time() - started) * 1000),
            )

        if attempt < max_attempts:
            time.sleep(min(0.1 * attempt, 1.0))

    return last_response
