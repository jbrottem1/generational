"""Creative Studio Engine — Agent 12's visual production design stage
(key: creative_studio).

The creative department of the OS: consumes finished ContentPackages
(script + visual + audio intelligence already attached), and designs each
one into a complete CreativeProductionPackage — Director blueprint,
professional storyboard, shot list, animation/character/environment/
motion/camera plans, asset requirements, thumbnail concepts, continuity
report, and a production readiness score the Render Engine can gate on.

Pipeline position (PIPELINE_SPEC.md):

    Packaging → Creative Studio → Render Engine

Failure policy: the studio NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item design failures degrade to diagnostics.
Ownership rules honored: only the `creative_package` slot and the
`creative_summary` / `creative_packages` context keys are written —
script, visual, audio, render, seo, publishing, and analytics slots are
read, never mutated. Asset sourcing is provider-driven
(`providers/creative/`) — no vendor is ever hardcoded.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine
from services.creative_studio.memory import record_production
from services.creative_studio.models import CREATIVE_ENGINE_VERSION, ReadinessStatus
from services.creative_studio.package import build_creative_package

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_creative_items(context: dict) -> "tuple[list, str]":
    """Items this run should design, preferring canonical ContentPackage
    dicts (same collection order as SEO, Publishing, and Analytics)."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


class CreativeStudioEngine(ContractEngine):
    """Agent 12 — Creative Studio & Visual Production (provider-driven)."""

    key = "creative_studio"
    label = "Creative Studio"
    icon = "🎬"
    description = (
        "Transform scripts into complete visual production blueprints — "
        "storyboards, shot lists, characters, environments, styles, motion, "
        "camera plans, and asset requirements — for any visual medium, "
        "before rendering."
    )
    version = CREATIVE_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["creative_summary", "creative_packages"]
    dependencies = ["quality"]
    capabilities = [
        "creative-direction", "storyboarding", "shot-listing",
        "character-consistency", "style-library", "environments",
        "continuity", "multi-format", "provider-driven",
        # v1.1 Creative Intelligence.
        "world-engine", "camera-direction", "color-lighting",
        "animation-planning", "asset-planning", "platform-adaptation",
        "creative-memory", "learning-loop",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        items, source_key = collect_creative_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to design."
            return {"creative_summary": summary, "creative_packages": []}

        packages = []
        for item in items:
            try:
                package = build_creative_package(item, context)
                entries = record_production(package, item)
                package["creative_memory"] = {
                    "entries": [
                        {"entry_id": entry["entry_id"], "kind": entry["kind"], "key": entry["key"]}
                        for entry in entries
                    ],
                    "recorded": bool(entries),
                }
                item["creative_package"] = package
            except Exception as exc:  # noqa: BLE001 - one bad item never stops the studio
                package = {
                    "engine_version": CREATIVE_ENGINE_VERSION,
                    "project_id": str(item.get("project_id", "")),
                    "production_readiness": {
                        "score": 0,
                        "status": ReadinessStatus.INCOMPLETE,
                        "blockers": [f"creative design failed: {exc}"],
                    },
                }
                log_event(
                    logger, "creative_studio.item_failed", level=30,
                    project_id=str(item.get("project_id", "")), error=str(exc)[:120],
                )
            packages.append(package)

        summary = self._summary(packages, items=len(items))
        log_event(
            logger, "creative_studio.completed",
            items=len(items), packages=len(packages),
            ready=summary["ready"], average_readiness=summary["average_readiness"],
            source=source_key or "none",
        )

        updates = {
            "creative_summary": summary,
            "creative_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    # ------------------------------------------------------------- helpers

    def _summary(self, packages: list, items: int) -> dict:
        readiness = [pkg.get("production_readiness", {}) for pkg in packages]
        scores = [int(r.get("score", 0)) for r in readiness]
        statuses = [r.get("status", "") for r in readiness]
        return {
            "engine_version": CREATIVE_ENGINE_VERSION,
            "status": "designed" if packages else "no_items",
            "items": items,
            "packages": len(packages),
            "ready": statuses.count(ReadinessStatus.READY),
            "needs_review": statuses.count(ReadinessStatus.NEEDS_REVIEW),
            "incomplete": statuses.count(ReadinessStatus.INCOMPLETE),
            "production_types": sorted(
                {
                    pkg.get("creative_blueprint", {}).get("production_type", "")
                    for pkg in packages
                    if pkg.get("creative_blueprint")
                }
            ),
            "styles": sorted(
                {
                    pkg.get("creative_blueprint", {}).get("visual_style", "")
                    for pkg in packages
                    if pkg.get("creative_blueprint")
                }
            ),
            "average_readiness": int(round(sum(scores) / len(scores))) if scores else 0,
            "generated_at": _now_iso(),
        }
