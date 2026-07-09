"""Production readiness aggregation (Agent 1).

Single report used by Studio dashboard, internal API, and PRODUCTION_READINESS.md.
"""

from services.readiness.report import (
    build_readiness_report,
    readiness_scorecard,
)

__all__ = [
    "build_readiness_report",
    "readiness_scorecard",
]
