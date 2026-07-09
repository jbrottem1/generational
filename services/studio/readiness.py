"""Production readiness for Studio UI."""

from __future__ import annotations


def get_production_readiness() -> dict:
    """Studio-facing wrapper around the readiness aggregator."""
    from services.readiness import build_readiness_report

    return build_readiness_report()
