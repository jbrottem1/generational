"""Optimization Lab Engine — Agent 13's experimentation stage (key: optimization_lab).

The Experimentation & Optimization Laboratory: for every content item it
generates competing variants across the active experiment types (hooks,
titles, thumbnails, captions, narration styles, CTAs, publishing times,
...), scores them with configurable weighted scoring (psychology,
virality, SEO, trend, historical performance, brand fit, audience match,
retention/CTR/engagement predictions, platform and localization
suitability), ranks them with historical winner priors from the learning
bridge, concludes statistical experiments, and returns structured
recommendations — the strongest version of every decision.

Pipeline position (PIPELINE_SPEC.md):

    Quality Gate → Optimization Laboratory → Media Production
    (scheduled via services/optimization/integration.enable_optimization_stage();
     also runnable on demand: get_orchestrator().run_stage("optimization", ctx))

The laboratory consumes other engines' outputs and returns
recommendations only — it never modifies the Psychology, Script, Visual,
Creative, Voice, Render, SEO, Publishing, or Analytics engines, and never
calls another engine (Architecture Directive #1). Ownership: only the
`optimization_package` slot and its own context keys are written.

Failure policy: optimization NEVER crashes the pipeline. Empty context →
"no_items" report; invalid experiments, duplicate variants, low
confidence, missing history, and provider failures all degrade to
warnings inside the Optimization Report.
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from services.optimization.models import OPTIMIZATION_ENGINE_VERSION


class OptimizationLabEngine(ContractEngine):
    """Agent 13 — variant experimentation, scoring, ranking, recommendation."""

    key = "optimization_lab"
    label = "Optimization Lab"
    icon = "🧪"
    description = (
        "Generate competing variants for every content decision, predict "
        "their performance, rank them against historical winners, and "
        "recommend the strongest version before anything is published."
    )
    version = OPTIMIZATION_ENGINE_VERSION
    input_contract = ["ideas"]
    output_contract = ["optimization_report", "optimization_recommendations"]
    dependencies = ["quality"]
    capabilities = [
        "experimentation", "variant-generation", "scoring", "ranking",
        "prediction", "recommendations", "ab-testing", "learning-loop",
        "reporting",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        # Deferred import: the laboratory's service layer shares foundation
        # modules (engines.heuristics) with the rest of the system, and this
        # engine is imported during `engines` package registration — a
        # module-level import would create a registration-time cycle.
        from services.optimization.lab import run_optimization

        return run_optimization(context)
