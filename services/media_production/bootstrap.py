"""Bootstrap media-production integrations (gates, etc.)."""

from __future__ import annotations

from services.media_production.publish_gate import ensure_production_gate_registered

_BOOTSTRAPPED = False


def bootstrap_media_production() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    ensure_production_gate_registered()
    _BOOTSTRAPPED = True
