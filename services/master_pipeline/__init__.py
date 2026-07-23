"""Master Production Pipeline — Agent 1 integration façade.

Canonical entry:
    from services.master_pipeline import run_master_production, production_readiness_report
"""

from __future__ import annotations

from services.master_pipeline.contracts import contract_audit, normalize_content_package, normalize_pipeline_context
from services.master_pipeline.qc import run_production_qc
from services.master_pipeline.readiness import production_readiness_report, provider_integration_status
from services.master_pipeline.registry import (
    live_agent_registry,
    live_engine_registry,
    master_pipeline_map,
    registry_summary,
)
from services.master_pipeline.runner import (
    LONG_FORM_DURATIONS,
    SHORT_FORM_DURATIONS,
    resolve_production_type,
    run_master_production,
)

__all__ = [
    "contract_audit",
    "live_agent_registry",
    "live_engine_registry",
    "LONG_FORM_DURATIONS",
    "master_pipeline_map",
    "normalize_content_package",
    "normalize_pipeline_context",
    "production_readiness_report",
    "provider_integration_status",
    "registry_summary",
    "resolve_production_type",
    "run_master_production",
    "run_production_qc",
    "SHORT_FORM_DURATIONS",
]
