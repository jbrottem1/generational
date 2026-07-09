"""Executive Intelligence Engine — Agent 24 (key: autonomous_executive).

The company operating system layer: observes shared context, prioritizes
production decisions, plans strategy, allocates resources, and delegates
execution to the orchestrator — never calling peer engines directly.

Pipeline position (PIPELINE_SPEC.md):

    Manual stage / OrchestratorHook — NOT in DISTRIBUTION_STAGES

Failure policy: NEVER crashes the pipeline. Empty context → "no_context"
summary; failures degrade to diagnostics.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.executive.models import EXECUTIVE_ENGINE_VERSION
from services.executive.package import run_executive_engine

logger = get_logger(__name__)


class ExecutiveEngine(ContractEngine):
    """Agent 24 — Executive Intelligence & Company OS."""

    key = "autonomous_executive"
    label = "Executive Intelligence"
    icon = "🏛️"
    description = (
        "Company OS layer — strategic planning, decision prioritization, "
        "resource allocation, health monitoring, and orchestrator delegation."
    )
    version = EXECUTIVE_ENGINE_VERSION
    input_contract = []
    output_contract = [
        "executive_summary",
        "executive_plan",
        "executive_dashboard",
        "executive_reports",
        "executive_loop",
        "executive_packages",
    ]
    dependencies = []
    capabilities = [
        "executive-intelligence",
        "company-os",
        "engine-discovery",
        "strategic-planning",
        "decision-prioritization",
        "resource-allocation",
        "health-monitoring",
        "reporting",
        "orchestrator-delegation",
        "graceful-degradation",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        try:
            return run_executive_engine(context)
        except Exception as exc:  # noqa: BLE001 - never crash
            log_event(logger, "executive.engine_failed", level=30, error=str(exc)[:120])
            return run_executive_engine({})
