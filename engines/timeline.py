"""Timeline Builder engine — assembles the production blueprint."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import Timeline, TimelineClip
from engines.base import Engine

logger = get_logger(__name__)


class TimelineEngine(Engine):
    key = "timeline"
    label = "Timeline"
    icon = "⏱️"
    description = "Assemble narration, visual, subtitle, music, and effect timing."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []

        for pkg in packages:
            scenes = pkg.get("scenes", [])
            scene_order = [s["scene_id"] for s in scenes]
            duration = scenes[-1]["timing_end"] if scenes else 0.0

            narration_clips = [
                TimelineClip(
                    clip_id=f"nar_{t['scene_id']}",
                    track="narration",
                    start_sec=next((s["timing_start"] for s in scenes if s["scene_id"] == t["scene_id"]), 0),
                    end_sec=next((s["timing_end"] for s in scenes if s["scene_id"] == t["scene_id"]), t["duration_sec"]),
                    asset_id=t.get("asset_id", ""),
                    label=f"Narration {t['scene_id']}",
                ).to_dict()
                for t in pkg.get("narration_tracks", [])
            ]

            visual_clips = [
                TimelineClip(
                    clip_id=f"vis_{vp['scene_id']}",
                    track="visual",
                    start_sec=next((s["timing_start"] for s in scenes if s["scene_id"] == vp["scene_id"]), 0),
                    end_sec=next((s["timing_end"] for s in scenes if s["scene_id"] == vp["scene_id"]), 5),
                    asset_id=f"vis_{vp['scene_id']}",
                    label=vp.get("subject", "")[:40],
                ).to_dict()
                for vp in pkg.get("visual_prompts", [])
            ]

            subtitle_clips = [
                TimelineClip(
                    clip_id=f"sub_{i}",
                    track="subtitle",
                    start_sec=c["start_sec"],
                    end_sec=c["end_sec"],
                    label=c["text"][:30],
                ).to_dict()
                for i, c in enumerate(pkg.get("subtitles", {}).get("cues", []))
            ]

            music_clips = [
                TimelineClip(
                    clip_id=f"mus_{pkg['content_id']}",
                    track="music",
                    start_sec=0.0,
                    end_sec=duration,
                    asset_id=f"mus_{pkg['content_id']}",
                    label="Background music bed",
                ).to_dict()
            ]

            transitions = [
                {"from_scene": scenes[i]["scene_id"], "to_scene": scenes[i + 1]["scene_id"], "type": scenes[i].get("transition", "cut")}
                for i in range(len(scenes) - 1)
            ]

            timeline = Timeline(
                duration_sec=round(duration, 2),
                scene_order=scene_order,
                narration_clips=narration_clips,
                visual_clips=visual_clips,
                subtitle_clips=subtitle_clips,
                music_clips=music_clips,
                effect_clips=[],
                transitions=transitions,
            )
            pkg["timeline"] = timeline.to_dict()

        log_event(logger, "timeline.completed", packages=len(packages))
        return {"production_packages": packages}
