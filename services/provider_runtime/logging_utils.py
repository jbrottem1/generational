"""Structured provider logging helpers."""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event

logger = get_logger("provider_runtime")


def log_provider_event(event: str, **fields: Any) -> None:
    """Emit a structured provider runtime event."""
    log_event(logger, f"provider.{event}", **fields)


def log_request_start(provider: str, operation: str, **fields: Any) -> None:
    log_provider_event("request_start", provider=provider, operation=operation, **fields)


def log_request_end(
    provider: str,
    operation: str,
    *,
    success: bool,
    latency_ms: int = 0,
    cost_usd: float = 0.0,
    error: str = "",
    **fields: Any,
) -> None:
    log_provider_event(
        "request_end",
        provider=provider,
        operation=operation,
        success=success,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        error=error,
        **fields,
    )
