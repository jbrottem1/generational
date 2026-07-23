"""Publishing Queue engine — queues render packages for future auto-posting.

Autonomous public publishing remains DISABLED until the kill-switch is on and
every intelligence + production quality gate passes. Packages are still
recorded so humans can review them — status is `held` by default.
"""

from __future__ import annotations

from core.constants import AUTONOMOUS_PUBLISHING_ENABLED
from core.log import get_logger, log_event
from engines.base import Engine
from engines.production_quality import score_production_package
from services.assets import get_publishing_queue

logger = get_logger(__name__)


class PublishingQueueEngine(Engine):
    key = "publishing_queue"
    label = "Publishing Queue"
    icon = "📤"
    description = "Queue completed render packages for platform publishing (held until gates pass)."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        queue = get_publishing_queue()
        niche = context.get("niche", "")
        autonomous = bool(
            context.get("autonomous_publishing_enabled", AUTONOMOUS_PUBLISHING_ENABLED)
        )

        queued = 0
        held = 0
        for pkg in packages:
            rp = pkg.get("render_package")
            if not rp:
                continue

            # Carry story beats onto the package for production scoring.
            if not pkg.get("story_beats"):
                pkg["story_beats"] = (pkg.get("idea") or {}).get("story_beats") or {}

            production_quality = score_production_package(pkg, niche=niche)
            pkg["production_quality"] = production_quality

            intelligence_ok = bool(pkg.get("publishable", True))
            # Fail closed: never mark ready-to-post unless kill-switch is on.
            if not autonomous:
                status = "held"
                hold_reason = "autonomous_publishing_disabled"
            elif not intelligence_ok:
                status = "held"
                hold_reason = "intelligence_gate_failed"
            elif not production_quality["passed"]:
                status = "held"
                hold_reason = ",".join(production_quality["gate_failures"]) or "production_quality"
            else:
                status = "queued"
                hold_reason = ""

            entry = queue.enqueue(
                content_id=pkg["content_id"],
                title=pkg.get("title", ""),
                render_package=rp,
                niche=niche,
                publish_score=pkg.get("publish_score", 0),
                status=status,
                hold_reason=hold_reason,
                autonomous_publishing_enabled=autonomous,
            )
            pkg["queue_status"] = entry.get("status", status)
            pkg["queue_id"] = entry.get("queue_id", "")
            pkg["hold_reason"] = hold_reason
            if status == "held":
                held += 1
            else:
                queued += 1

        log_event(
            logger,
            "publishing_queue.completed",
            queued=queued,
            held=held,
            autonomous_publishing_enabled=autonomous,
        )
        return {
            "production_packages": packages,
            "queued_count": queued,
            "held_count": held,
            "autonomous_publishing_enabled": autonomous,
        }
