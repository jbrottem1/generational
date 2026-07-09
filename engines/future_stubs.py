"""Contract-first stubs for the Agents 6-10 stages that have no engine yet.

Registering these now means the orchestrator, dashboards, and tests already
know every future stage — implementing one later is overriding `run()` and
`is_ready()` in the owning agent's landing zone, with zero orchestration
changes. See engines/render/README.md etc. for ownership.

Stages whose engine keys already exist as planned stubs (image, video,
publishing, analytics, learning) are NOT duplicated here.
"""

from __future__ import annotations

from engines.contracts import FutureEngine


class SeoOptimizationEngine(FutureEngine):
    """Agent 8 — global SEO & trend optimization (post-quality, pre-publish).

    Distinct from the live `seo` metadata-packaging engine in the refinement
    stage: this one optimizes across platforms, countries, and languages.
    """

    key = "seo_optimization"
    label = "SEO Optimization"
    icon = "🌍"
    description = "Global SEO & trend optimization across platforms, countries, languages."
    input_contract = ["ideas", "seo_keywords"]
    output_contract = ["seo_optimization_report"]
    dependencies = ["seo", "quality"]
    capabilities = ["seo", "multi-language", "multi-platform"]


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
