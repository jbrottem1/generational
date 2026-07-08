"""Render Package engine — bundles every asset for future renderers."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import RenderPackage
from engines.base import Engine

logger = get_logger(__name__)


class RenderPackageEngine(Engine):
    key = "render_package"
    label = "Render Package"
    icon = "📋"
    description = "Bundle scenes, narration, visuals, assets, subtitles, and timeline."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []

        for pkg in packages:
            timeline = pkg.get("timeline", {})
            rp = RenderPackage(
                package_id=f"rp_{pkg['content_id']}",
                title=pkg.get("title", ""),
                duration_sec=timeline.get("duration_sec", 0),
                scenes=pkg.get("scenes", []),
                narration_tracks=pkg.get("narration_tracks", []),
                visual_prompts=pkg.get("visual_prompts", []),
                assets=pkg.get("assets", []),
                subtitles=pkg.get("subtitles", {}),
                timeline=timeline,
                thumbnail_concept=pkg.get("thumbnail_concept", ""),
                metadata={
                    "niche": context.get("niche", ""),
                    "publish_score": pkg.get("publish_score", 0),
                    "content_id": pkg["content_id"],
                    "ready_for_render": True,
                },
            )
            pkg["render_package"] = rp.to_dict()

        log_event(logger, "render_package.completed", packages=len(packages))
        return {"production_packages": packages}
