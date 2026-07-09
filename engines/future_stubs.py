"""Contract-first stubs for the Agents 6-10 stages that have no engine yet.

Registering these now means the orchestrator, dashboards, and tests already
know every future stage — implementing one later is overriding `run()` and
`is_ready()` in the owning agent's landing zone, with zero orchestration
changes. See engines/render/README.md etc. for ownership.

Stages whose engine keys already exist as planned stubs (image, video,
publishing, analytics, learning) are NOT duplicated here. The
`seo_optimization` stub graduated to a live engine in
`engines/seo_optimization.py` (Agent 8).
"""

from __future__ import annotations

from engines.contracts import FutureEngine


class SchedulerEngine(FutureEngine):
    """Agent 7 — optimal-window publish scheduling for the publishing queue."""

    key = "scheduler"
    label = "Scheduler"
    icon = "🗓️"
    description = "Schedule queued content into optimal posting windows per platform."
    input_contract = ["production_packages"]
    output_contract = ["publish_schedule"]
    dependencies = ["publishing_queue"]
    capabilities = ["scheduling", "publishing"]


class BrandManagementEngine(FutureEngine):
    """Agent 10 — multi-brand operating system (brand strategy updates)."""

    key = "brand_management"
    label = "Brand Management"
    icon = "🏢"
    description = "Per-brand strategy, identity, cadence, and portfolio decisions."
    input_contract = ["ideas"]
    output_contract = ["brand_strategy_update"]
    dependencies = ["learning"]
    capabilities = ["multi-brand", "strategy"]
