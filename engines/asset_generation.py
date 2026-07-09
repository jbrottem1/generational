"""Universal Asset Generation Engine — Agent 14 (key: asset_generation).

The generation department of the OS: consumes structured creative requests
(Creative Studio asset requirements, thumbnail concepts, scene plans) and
transforms them into production-ready visual assets through swappable AI
provider adapters. Every image, illustration, thumbnail, texture, video
clip, and future media asset the platform uses originates here.

Pipeline position (PIPELINE_SPEC.md):

    Packaging → Asset Generation → Render Engine

Failure policy: the engine NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item generation failures degrade to diagnostics.
Ownership rules honored: only the `asset_package` slot and the
`asset_generation_summary` / `asset_packages` context keys are written —
script, visual, audio, creative, render, seo, publishing, and analytics
slots are read, never mutated. Provider selection and generation are
adapter-driven (`providers/asset_generation/`) — no vendor is ever
hardcoded.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.asset_generation.models import (
    ASSET_GENERATION_ENGINE_VERSION,
    PackageReadiness,
)
from services.asset_generation.package import collect_generation_items, generate_items

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AssetGenerationEngine(ContractEngine):
    """Agent 14 — Universal Asset Generation (provider-driven)."""

    key = "asset_generation"
    label = "Universal Asset Generation"
    icon = "🎨"
    description = (
        "Transform structured creative requests into production-ready visual "
        "assets — images, illustrations, thumbnails, textures, video clips, "
        "and future media — through swappable AI provider adapters."
    )
    version = ASSET_GENERATION_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["asset_generation_summary", "asset_packages"]
    dependencies = ["quality"]
    capabilities = [
        "asset-generation", "image-gen", "video-gen", "prompt-compilation",
        "provider-selection", "character-consistency", "style-packs",
        "asset-registry", "asset-caching", "quality-validation",
        "provider-driven",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_generation_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to generate."
            return {"asset_generation_summary": summary, "asset_packages": []}

        packages = generate_items(items, context)

        summary = self._summary(packages, items=len(items))
        log_event(
            logger, "asset_generation.completed",
            items=len(items), packages=len(packages),
            assets=summary["assets_generated"], cache_hits=summary["cache_hits"],
            source=source_key or "none",
        )

        updates = {
            "asset_generation_summary": summary,
            "asset_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    def _summary(self, packages: list, items: int) -> dict:
        assets = [asset for package in packages for asset in package.get("assets", [])]
        readiness = [package.get("readiness", {}) for package in packages]
        scores = [int(r.get("score", 0)) for r in readiness]
        statuses = [r.get("status", "") for r in readiness]
        providers = sorted(
            {
                asset.get("provider", "")
                for asset in assets
                if asset.get("provider")
            }
        )
        return {
            "engine_version": ASSET_GENERATION_ENGINE_VERSION,
            "status": "generated" if packages else "no_items",
            "items": items,
            "packages": len(packages),
            "assets_generated": sum(
                1 for asset in assets if asset.get("status") not in ("failed", "blocked")
            ),
            "cache_hits": sum(
                1 for package in packages
                for job in package.get("generation_jobs", [])
                if job.get("status") == "cache_hit"
            ),
            "placeholders": sum(1 for asset in assets if asset.get("placeholder")),
            "failures": sum(1 for asset in assets if asset.get("status") == "failed"),
            "providers_used": providers,
            "ready": statuses.count(PackageReadiness.READY),
            "needs_review": statuses.count(PackageReadiness.NEEDS_REVIEW),
            "incomplete": statuses.count(PackageReadiness.INCOMPLETE),
            "average_readiness": int(round(sum(scores) / len(scores))) if scores else 0,
            "generated_at": _now_iso(),
        }
