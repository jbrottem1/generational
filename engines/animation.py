"""Animation & Cinematic Production Engine — Agent 16 (key: animation).

The motion department of the OS: consumes Creative Studio blueprints,
Asset Generation packages, Visual Intelligence scenes, Voice / Script /
Psychology / Optimization outputs, and transforms them into a complete
`animation_package` — timeline, camera, character motion, facial, lip sync,
VFX, transitions, audio sync, and provider instructions.

This engine does NOT create final videos. It plans HOW every scene moves
so Render / Post-Production can execute.

Pipeline position (PIPELINE_SPEC.md):

    Creative / Asset Generation → Animation → Render Engine

Failure policy: the engine NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item planning failures degrade to diagnostics.
Ownership rules honored: only the `animation_package` slot and the
`animation_summary` / `animation_packages` context keys are written —
script, visual, audio, creative, asset, render, seo, publishing, and
analytics slots are read, never mutated. Provider routing is adapter-
driven (`providers/animation/`) — no vendor is ever hardcoded.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.animation.models import ANIMATION_ENGINE_VERSION, ReadinessStatus
from services.animation.package import collect_animation_items, plan_items

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnimationEngine(ContractEngine):
    """Agent 16 — Animation & Cinematic Production (provider-driven)."""

    key = "animation"
    label = "Animation & Cinematics"
    icon = "🎥"
    description = (
        "Transform creative assets into complete cinematic production plans — "
        "timeline, camera, character motion, facial animation, lip sync, VFX, "
        "transitions, and provider instructions — without rendering final video."
    )
    version = ANIMATION_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["animation_summary", "animation_packages"]
    dependencies = ["quality"]
    capabilities = [
        "animation-planning", "cinematics", "camera-planning", "timeline",
        "character-motion", "facial-animation", "lip-sync", "choreography",
        "visual-effects", "transitions", "motion-graphics", "audio-sync",
        "provider-driven", "batch-planning", "series-production",
        "quality-validation",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_animation_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to animate."
            return {"animation_summary": summary, "animation_packages": []}

        packages = plan_items(items, context)

        summary = self._summary(packages, items=len(items))
        log_event(
            logger, "animation.completed",
            items=len(items), packages=len(packages),
            ready=summary["ready"], average_readiness=summary["average_readiness"],
            total_duration_sec=summary["total_duration_sec"],
            source=source_key or "none",
        )

        updates = {
            "animation_summary": summary,
            "animation_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    def _summary(self, packages: list, items: int) -> dict:
        readiness = [pkg.get("production_readiness", {}) for pkg in packages]
        scores = [int(r.get("score", 0)) for r in readiness]
        statuses = [r.get("status", "") for r in readiness]
        providers = sorted(
            {
                ins.get("provider_id", "")
                for pkg in packages
                for ins in pkg.get("provider_instructions", [])
                if ins.get("provider_id")
            }
        )
        total_duration = round(
            sum(
                float((pkg.get("timeline") or {}).get("total_duration_sec", 0) or 0)
                for pkg in packages
            ),
            3,
        )
        return {
            "engine_version": ANIMATION_ENGINE_VERSION,
            "status": "planned" if packages else "no_items",
            "items": items,
            "packages": len(packages),
            "ready": statuses.count(ReadinessStatus.READY),
            "needs_review": statuses.count(ReadinessStatus.NEEDS_REVIEW),
            "incomplete": statuses.count(ReadinessStatus.INCOMPLETE),
            "total_duration_sec": total_duration,
            "average_readiness": int(round(sum(scores) / len(scores))) if scores else 0,
            "providers_planned": providers,
            "generated_at": _now_iso(),
        }
