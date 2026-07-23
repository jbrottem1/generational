"""ProviderHealthMonitor — health tracking and circuit breakers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from services.provider_runtime.adapter import ProviderAdapter


@dataclass
class CircuitState:
    failures: int = 0
    successes: int = 0
    open_until: float = 0.0
    last_error: str = ""


class ProviderHealthMonitor:
    """Tracks provider health and implements circuit breaker pattern."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 60.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_sec
        self._circuits: dict[str, CircuitState] = field(default_factory=dict)  # type: ignore
        self._circuits = {}

    def record_success(self, provider_name: str) -> None:
        state = self._get(provider_name)
        state.successes += 1
        state.failures = 0
        state.open_until = 0.0
        state.last_error = ""

    def record_failure(self, provider_name: str, error: str = "") -> None:
        state = self._get(provider_name)
        state.failures += 1
        state.last_error = error
        if state.failures >= self._failure_threshold:
            state.open_until = time.time() + self._recovery_timeout

    def is_healthy(self, provider: ProviderAdapter) -> bool:
        state = self._get(provider.name)
        if state.open_until and time.time() < state.open_until:
            return False
        if state.open_until and time.time() >= state.open_until:
            state.failures = 0
            state.open_until = 0.0
        return provider.is_available()

    def health_report(self) -> dict:
        now = time.time()
        report = {}
        for name, state in self._circuits.items():
            report[name] = {
                "failures": state.failures,
                "successes": state.successes,
                "circuit_open": bool(state.open_until and now < state.open_until),
                "last_error": state.last_error,
            }
        return report

    def _get(self, name: str) -> CircuitState:
        if name not in self._circuits:
            self._circuits[name] = CircuitState()
        return self._circuits[name]

    def reset(self) -> None:
        self._circuits.clear()
