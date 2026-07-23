"""Production Pipeline Integration Layer.

Connects completed production agents into one executable workflow:

    Research → Psychology → Studio Director → Script Generator → Scene Builder
    → Media Generation → Voice Generation → Video Assembly → Quality Control → Export

Public surface:
    from services.production_pipeline import run_production_pipeline, verify_agents
"""

from __future__ import annotations

from services.production_pipeline.bridges import bridge_before_stage, sync_candidate_aliases, verify_stage_io
from services.production_pipeline.orchestrator import run_production_pipeline, verify_agents
from services.production_pipeline.stages import (
    PRODUCTION_STAGES,
    STAGE_KEYS,
    flat_engine_order,
    stage_contract_table,
)
from services.production_pipeline.status import load_status, status_path, write_status

__all__ = [
    "PRODUCTION_STAGES",
    "STAGE_KEYS",
    "bridge_before_stage",
    "flat_engine_order",
    "load_status",
    "run_production_pipeline",
    "stage_contract_table",
    "status_path",
    "sync_candidate_aliases",
    "verify_agents",
    "verify_stage_io",
    "write_status",
]
