"""Publishing Queue engine — queues render packages for future auto-posting."""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.assets import get_publishing_queue

logger = get_logger(__name__)


class PublishingQueueEngine(Engine):
    key = "publishing_queue"
    label = "Publishing Queue"
    icon = "📤"
    description = "Queue completed render packages for platform publishing."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        queue = get_publishing_queue()
        niche = context.get("niche", "")

        queued = 0
        for pkg in packages:
            rp = pkg.get("render_package")
            if not rp:
                continue
            entry = queue.enqueue(
                content_id=pkg["content_id"],
                title=pkg.get("title", ""),
                render_package=rp,
                niche=niche,
                publish_score=pkg.get("publish_score", 0),
            )
            pkg["queue_status"] = entry.get("status", "queued")
            pkg["queue_id"] = entry.get("queue_id", "")
            queued += 1

        log_event(logger, "publishing_queue.completed", queued=queued)
        return {"production_packages": packages, "queued_count": queued}
