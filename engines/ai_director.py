"""AI Director Engine — Agent 18 (key: ai_director).

The executive creative decision engine of the OS: consumes intelligence from
Psychology, Script, Visual Intelligence, Voice, Trend, Market, Analytics,
and Creative Studio packages, and determines the optimal production strategy
before assets are generated.

Pipeline position (PIPELINE_SPEC.md):

    Packaging → AI Director → Creative Studio → Asset Generation → …

Failure policy: the Director NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item direction failures degrade to diagnostics.
Ownership rules honored: only the `director_package` slot and the
`ai_director_summary` / `ai_director_packages` context keys are written —
script, visual, audio, creative, asset, render, and all other slots are
read, never mutated.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.ai_director.models import (
    AI_DIRECTOR_ENGINE_VERSION,
    DirectorStatus,
)
from services.ai_director.package import build_director_package, collect_director_items

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AiDirectorEngine(ContractEngine):
    """Agent 18 — AI Director & Executive Creative Decision Engine."""

    key = "ai_director"
    label = "AI Director"
    icon = "🎭"
    description = (
        "Executive creative direction for every production — format, platform, "
        "style, pacing, camera, characters, music, narration, editing, and "
        "orchestration notes for Agents 12–17 before assets are generated."
    )
    version = AI_DIRECTOR_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["ai_director_summary", "ai_director_packages"]
    dependencies = ["quality"]
    capabilities = [
        "executive-direction", "production-strategy", "platform-selection",
        "format-selection", "creative-style", "pacing", "camera-planning",
        "character-direction", "music-direction", "narration-direction",
        "editing-direction", "optimization-hints", "conflict-detection",
        "graceful-degradation", "configurable-policies", "learning-feedback",
        "orchestration", "provider-agnostic",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_director_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to direct."
            return {"ai_director_summary": summary, "ai_director_packages": []}

        packages = []
        for item in items:
            try:
                package = build_director_package(item, context)
                item["director_package"] = package
            except Exception as exc:  # noqa: BLE001 - one bad item never stops the director
                package = {
                    "engine_version": AI_DIRECTOR_ENGINE_VERSION,
                    "project_id": str(item.get("project_id", "")),
                    "validation": {
                        "status": DirectorStatus.INCOMPLETE,
                        "confidence": 0,
                        "blockers": [f"direction failed: {exc}"],
                    },
                }
                log_event(
                    logger, "ai_director.item_failed", level=30,
                    project_id=str(item.get("project_id", "")), error=str(exc)[:120],
                )
            packages.append(package)

        summary = self._summary(packages, items=len(items))
        log_event(
            logger, "ai_director.completed",
            items=len(items), packages=len(packages),
            ready=summary["ready"], source=source_key or "none",
        )

        updates = {
            "ai_director_summary": summary,
            "ai_director_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    def _summary(self, packages: list, items: int) -> dict:
        validations = [pkg.get("validation", {}) for pkg in packages]
        statuses = [v.get("status", DirectorStatus.INCOMPLETE) for v in validations]
        confidences = [int(v.get("confidence", 0)) for v in validations]
        degraded = sum(1 for v in validations if v.get("degraded"))

        overall = "directed"
        if not packages:
            overall = "no_items"
        elif degraded == len(packages) and packages:
            overall = "degraded"

        return {
            "engine_version": AI_DIRECTOR_ENGINE_VERSION,
            "status": overall,
            "items": items,
            "packages": len(packages),
            "ready": statuses.count(DirectorStatus.READY),
            "needs_review": statuses.count(DirectorStatus.NEEDS_REVIEW),
            "degraded": statuses.count(DirectorStatus.DEGRADED) + degraded,
            "incomplete": statuses.count(DirectorStatus.INCOMPLETE),
            "formats": sorted(
                {
                    pkg.get("production_strategy", {}).get("format", "")
                    for pkg in packages
                    if pkg.get("production_strategy")
                }
            ),
            "platforms": sorted(
                {
                    p.get("platform", "")
                    for pkg in packages
                    for p in (pkg.get("target_platforms") or [])
                    if p.get("platform")
                }
            ),
            "average_confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
            "generated_at": _now_iso(),
        }
