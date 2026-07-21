"""AI Director Engine — Agent 18 (key: ai_director) — Studio Director V5.0.

The creative brain of the Generational AI Media OS. Before any video is
produced, the Director builds a Production Blueprint from topic, audience,
platform, goals, and historical performance — then applies that unified
vision onto candidates so every downstream engine follows the same direction.

Pipeline position (V5):

    Psychology → Audience Intelligence → AI Director (blueprint) →
    Script → Visuals → … → Studio Render → Optimization Lab → QA

Failure policy: the Director NEVER crashes the pipeline. Empty context →
"no_items" summary; per-item direction failures degrade to diagnostics.

Ownership: writes `director_package` (incl. production_blueprint) and
additive direction fields on items; does not overwrite script/visual/audio
package bodies.

Import policy: services.ai_director is imported lazily inside run() so that
`import engines` / `engines.heuristics` cannot circularly load this module
while services.ai_director.blueprint is still initializing.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.log import get_logger, log_event
from engines.contracts import ContractEngine

logger = get_logger(__name__)

# Keep version string local — avoid importing services.ai_director at module load
AI_DIRECTOR_ENGINE_VERSION = "5.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AiDirectorEngine(ContractEngine):
    """Agent 18 — AI Studio Director V5 (Executive Producer + Creative Director)."""

    key = "ai_director"
    label = "AI Studio Director"
    icon = "🎭"
    description = (
        "Studio Director V5 — Production Blueprint before any engine produces: "
        "style library, visual/narration/music/editing direction, platform "
        "strategy, competitor analysis, and a unified production plan for "
        "all downstream engines."
    )
    version = AI_DIRECTOR_ENGINE_VERSION
    input_contract = ["unified_packages"]
    output_contract = ["ai_director_summary", "ai_director_packages"]
    dependencies = ["audience_intelligence"]
    capabilities = [
        "executive-direction", "production-blueprint", "style-library",
        "production-strategy", "platform-selection", "format-selection",
        "creative-style", "visual-direction", "pacing", "camera-planning",
        "character-direction", "music-direction", "narration-direction",
        "editing-direction", "competitor-analysis", "optimization-hints",
        "conflict-detection", "graceful-degradation", "configurable-policies",
        "learning-feedback", "orchestration", "provider-agnostic",
        "retention-targets", "emotion-curves", "seo-strategy",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        from services.ai_director.consumers import apply_blueprint_to_candidate
        from services.ai_director.models import DirectorStatus
        from services.ai_director.package import build_director_package, collect_director_items

        items, source_key = collect_director_items(context)

        if not items:
            summary = self._summary([], items=0)
            summary["reason"] = "No content in context — nothing to direct."
            return {"ai_director_summary": summary, "ai_director_packages": []}

        packages = []
        for item in items:
            try:
                package = build_director_package(item, context)
                blueprint = package.get("production_blueprint") or {}
                # Apply additive direction so script/visual/render engines follow the plan.
                directed = apply_blueprint_to_candidate(item, blueprint, package)
                item.update(directed)
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
                item["director_package"] = package
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
            blueprints=summary.get("blueprints", 0),
        )

        updates = {
            "ai_director_summary": summary,
            "ai_director_packages": packages,
        }
        if source_key:
            updates[source_key] = context.get(source_key, [])
        return updates

    def _summary(self, packages: list, items: int) -> dict:
        from services.ai_director.models import DirectorStatus

        validations = [pkg.get("validation", {}) for pkg in packages]
        statuses = [v.get("status", DirectorStatus.INCOMPLETE) for v in validations]
        confidences = [int(v.get("confidence", 0)) for v in validations]
        degraded = sum(1 for v in validations if v.get("degraded"))
        blueprints = sum(1 for pkg in packages if pkg.get("production_blueprint"))
        styles = sorted(
            {
                (pkg.get("production_blueprint") or {}).get("production_style_id", "")
                for pkg in packages
                if (pkg.get("production_blueprint") or {}).get("production_style_id")
            }
        )

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
            "blueprints": blueprints,
            "production_styles": styles,
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
