"""Asset Manager engine — register all production assets for reuse."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import Asset
from engines.base import Engine
from services.assets import get_asset_manager

logger = get_logger(__name__)


class AssetManagerEngine(Engine):
    key = "asset_manager"
    label = "Asset Management"
    icon = "📦"
    description = "Track narration, visuals, subtitles, thumbnails, and stock assets."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        manager = get_asset_manager()
        niche = context.get("niche", "")

        for pkg in packages:
            assets = []
            for track in pkg.get("narration_tracks", []):
                asset = Asset(
                    asset_id=track["asset_id"],
                    asset_type="narration",
                    label=f"Narration — {track['scene_id']}",
                    path=track.get("path", ""),
                    metadata={"mode": track.get("mode"), "duration": track.get("duration_sec")},
                )
                manager.register(asset.to_dict(), niche=niche)
                assets.append(asset.to_dict())

            for vp in pkg.get("visual_prompts", []):
                asset = Asset(
                    asset_id=f"vis_{vp['scene_id']}",
                    asset_type="generated_image",
                    label=f"Visual prompt — {vp['scene_id']}",
                    metadata={"prompt": vp.get("prompt_text", "")[:200]},
                )
                manager.register(asset.to_dict(), niche=niche)
                assets.append(asset.to_dict())

            if pkg.get("thumbnail_concept") or pkg.get("title"):
                thumb = Asset(
                    asset_id=f"thumb_{pkg['content_id']}",
                    asset_type="thumbnail",
                    label=f"Thumbnail — {pkg['title'][:40]}",
                    metadata={"concept": pkg.get("thumbnail_concept", "")},
                )
                manager.register(thumb.to_dict(), niche=niche)
                assets.append(thumb.to_dict())

            music = Asset(
                asset_id=f"mus_{pkg['content_id']}",
                asset_type="music",
                label=f"Background bed — {niche}",
                metadata={"mood": "upbeat documentary", "placeholder": True},
            )
            manager.register(music.to_dict(), niche=niche)
            assets.append(music.to_dict())

            pkg["assets"] = assets

        log_event(logger, "asset_manager.completed", packages=len(packages))
        return {"production_packages": packages}
