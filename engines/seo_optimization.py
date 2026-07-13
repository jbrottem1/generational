"""Global Content Optimization Engine — Agent 8 (key: seo_optimization).

The post-render, pre-publish optimization stage: consumes finished content
(ideas or canonical ContentPackage dicts), and produces per-item enriched
`seo_package` data plus a standardized PublishingPackage for the Publishing
Engine. Pipeline position (PIPELINE_SPEC.md):

    Render Engine → Global Content Optimization Engine → Publishing Engine

Ownership rules honored here:
- The refinement-stage `seo` engine's base metadata (title, description,
  hashtags, keywords, seo_score) is never overwritten — only extended.
- The ContentPackage `publishing_package` slot belongs to Agent 7; this
  engine hands over standardized packages via the `publishing_packages`
  context key instead of writing into Agent 7's slot.

This module graduates the former contract stub from engines/future_stubs.py
(same key, same input contract, additive output contract).
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.seo.models import OPTIMIZATION_REPORT_FIELDS
from services.seo.package import optimize_content

logger = get_logger(__name__)


class SeoOptimizationEngine(ContractEngine):
    key = "seo_optimization"
    label = "Global Content Optimization"
    icon = "🌍"
    description = "Global SEO, CTR, localization, and posting-strategy optimization across platforms, countries, languages."
    version = "1.0.0"
    input_contract = ["ideas", "seo_keywords"]
    output_contract = ["seo_optimization_report", "publishing_packages"]
    dependencies = ["seo", "quality"]
    capabilities = [
        "seo", "multi-language", "multi-platform",
        "localization", "posting-strategy", "ctr-optimization",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = self._collect_items(context)

        publishing_packages = []
        reports = []
        for item in items:
            result = optimize_content(item, context)
            item["seo_package"] = result["seo_package"]
            item["optimization_report"] = result["report"]
            publishing_packages.append(result["publishing_package"])
            reports.append(result["report"])

        report = self._aggregate(reports, source_key)
        log_event(
            logger, "seo_optimization.completed",
            items=len(items), source=source_key or "none",
            overall=report.get("overall_optimization_score", 0),
        )

        updates = {
            "seo_optimization_report": report,
            "publishing_packages": publishing_packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    # ------------------------------------------------------------- helpers

    def _collect_items(self, context: dict) -> "tuple[list, str]":
        """Publish-eligible items, preferring canonical ContentPackage dicts."""
        packages = context.get("unified_packages") or []
        eligible = [pkg for pkg in packages if pkg.get("publish_ready", True)]
        if eligible:
            return eligible, "unified_packages"
        for key, flag in (("ideas", "publishable"), ("selected_ideas", "publishable")):
            items = [item for item in context.get(key, []) if item.get(flag, True)]
            if items:
                return items, key
        return [], ""

    def _aggregate(self, reports: "list[dict]", source_key: str) -> dict:
        if not reports:
            return {
                "status": "no_items",
                "items": 0,
                "source": source_key,
                **{metric: 0 for metric in OPTIMIZATION_REPORT_FIELDS},
            }
        averaged = {
            metric: int(round(sum(r.get(metric, 0) for r in reports) / len(reports)))
            for metric in OPTIMIZATION_REPORT_FIELDS
        }
        return {
            "status": "optimized",
            "items": len(reports),
            "source": source_key,
            **averaged,
            "item_reports": reports,
        }
