"""Post-Production & Intelligent Editing Engine — Agent 17 (key: post_production).

The editing department of the OS: consumes completed animation/render
packages and transforms them into polished, publication-ready productions
through intelligent editing, audio finalization, caption styling, color
grading, motion graphics, platform optimization, and export preparation.

Pipeline position (PIPELINE_SPEC.md):

    Render Engine → Post-Production → Global Content Optimization → Publishing

Failure policy: the engine NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item failures degrade to diagnostics.
Ownership rules honored: only the `post_production_package` slot and the
`post_production_summary` / `post_production_packages` context keys are
written — render, audio, creative, asset, seo, publishing, and analytics
slots are read, never mutated.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.post_production.models import (
    POST_PRODUCTION_ENGINE_VERSION,
    EditStatus,
    PackageReadiness,
)
from services.post_production.package import collect_post_production_items, post_produce_items

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PostProductionEngine(ContractEngine):
    """Agent 17 — Post-Production & Intelligent Editing."""

    key = "post_production"
    label = "Post-Production & Intelligent Editing"
    icon = "🎬"
    description = (
        "Intelligently edit, refine, enhance, synchronize, package, and "
        "prepare completed productions for final rendering and publishing."
    )
    version = POST_PRODUCTION_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["post_production_summary", "post_production_packages"]
    dependencies = ["render"]
    capabilities = [
        "intelligent-editing", "timeline", "scene-cuts", "audio-mix",
        "caption-engine", "color-grading", "visual-effects", "motion-graphics",
        "platform-optimization", "quality-control", "export-preparation",
        "provider-driven", "batch-editing", "pacing-optimization",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_post_production_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to post-produce."
            return {"post_production_summary": summary, "post_production_packages": []}

        packages = post_produce_items(items, context)

        summary = self._summary(packages, items=len(items))
        log_event(
            logger, "post_production.completed",
            items=len(items), packages=len(packages),
            ready=summary["ready"], source=source_key or "none",
        )

        updates = {
            "post_production_summary": summary,
            "post_production_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    def _summary(self, packages: list, items: int) -> dict:
        readiness = [p.get("production_readiness", {}) for p in packages]
        scores = [int(r.get("score", 0)) for r in readiness]
        statuses = [r.get("status", "") for r in readiness]
        issues = sum(
            len(p.get("quality_report", {}).get("issues", []))
            for p in packages
        )

        if not packages:
            status = EditStatus.SKIPPED
        elif statuses.count(PackageReadiness.INCOMPLETE) == len(statuses):
            status = EditStatus.FAILED
        elif statuses.count(PackageReadiness.READY) == len(statuses):
            status = EditStatus.SUCCESS
        else:
            status = EditStatus.WARNING

        return {
            "engine_version": POST_PRODUCTION_ENGINE_VERSION,
            "status": status,
            "items": items,
            "packages": len(packages),
            "ready": statuses.count(PackageReadiness.READY),
            "needs_review": statuses.count(PackageReadiness.NEEDS_REVIEW),
            "incomplete": statuses.count(PackageReadiness.INCOMPLETE),
            "average_readiness": int(round(sum(scores) / len(scores))) if scores else 0,
            "issues_found": issues,
            "generated_at": _now_iso(),
        }
