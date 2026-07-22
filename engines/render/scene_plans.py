"""SceneRenderer — one complete render instruction sheet per scene.

For each scene this collapses the planning-layer material (Director scene,
resolved asset, motion instruction, audio cue) into the flat structure a
renderer executes: what footage fills the frame, which prompts/queries
produced it, which future footage slots apply (user / avatar / reaction),
how the camera moves, what text goes on screen, where captions sit, and
when sound cues fire. Fields are pinned by SCENE_RENDER_PLAN_FIELDS.
"""

from __future__ import annotations

from engines.render.motion import MotionPlanner

# Sources whose footage occupies a dedicated slot in the scene plan.
_SLOT_SOURCES = ("user_asset", "avatar", "reaction")


def _slot_for(scene: dict, asset: dict, slot_source: str) -> dict:
    """A footage slot: reserved when the scene calls for that source."""
    wanted = scene.get("asset_type", "") == slot_source or asset.get("fallback_for") == slot_source
    return {
        "reserved": wanted,
        "status": asset.get("status", "empty") if wanted else "empty",
        "notes": f"{slot_source} footage will replace the placeholder when its provider lands."
        if wanted
        else "",
    }


class SceneRenderer:
    """Builds the per-scene render plan (instructions, not pixels)."""

    def __init__(self, motion_planner: "MotionPlanner | None" = None) -> None:
        self._motion = motion_planner or MotionPlanner()

    def build_scene_plan(self, scene: dict, asset: "dict | None" = None, audio_cue: "dict | None" = None) -> dict:
        asset = asset or {}
        audio_cue = audio_cue or {}
        scene_id = scene.get("scene_number", 0)
        motion = self._motion.plan_scene(scene)
        timing = scene.get("caption_timing", {})

        sound_cues = []
        sfx_timing = scene.get("sfx_timing") or {}
        if scene.get("sound_effect") or sfx_timing:
            sound_cues.append(
                {
                    "cue": sfx_timing.get("cue", scene.get("sound_effect", "")),
                    "at_sec": sfx_timing.get("at_sec", timing.get("start_sec", 0.0)),
                    "track": "sfx",
                }
            )
        for sfx in audio_cue.get("sfx", []):
            if isinstance(sfx, dict) and sfx not in sound_cues:
                sound_cues.append({**sfx, "track": "sfx"})

        text_overlays = []
        if scene.get("text_overlay"):
            text_overlays.append(
                {
                    "text": scene.get("text_overlay", ""),
                    "treatment": scene.get("overlay", ""),
                    "start_sec": timing.get("start_sec", 0.0),
                    "end_sec": timing.get("end_sec", 0.0),
                }
            )

        return {
            "scene_id": scene_id,
            "visual_asset_type": scene.get("asset_type", "ai_image"),
            "image_prompt": scene.get("ai_image_prompt", ""),
            "video_prompt": scene.get("ai_video_prompt", ""),
            "stock_footage_query": scene.get("stock_footage_query", ""),
            "user_footage_slot": _slot_for(scene, asset, "user_asset"),
            "avatar_footage_slot": _slot_for(scene, asset, "avatar"),
            "reaction_footage_slot": _slot_for(scene, asset, "reaction"),
            "camera_movement": {
                "motion": scene.get("camera_motion", ""),
                "angle": scene.get("camera_angle", ""),
                "shot_type": scene.get("shot_type", "medium"),
            },
            "effect": {
                "name": motion["effect"],
                "zoom": motion["zoom"],
                "pan": motion["pan"],
                "ken_burns": motion["ken_burns"],
                "intensity": motion["intensity"],
            },
            "text_overlays": text_overlays,
            "caption_placement": scene.get("caption_placement", "bottom third, safe zone"),
            "sound_cues": sound_cues,
            "narration": scene.get("narration", ""),
            "duration_sec": float(scene.get("length_sec", 0.0)),
            "resolved_asset": asset,
        }

    def build(self, scenes: list, assets: "list | None" = None, audio_cues: "list | None" = None) -> list:
        """One render plan per scene; assets/cues matched by scene number."""
        assets_by_scene = {
            asset.get("scene_number", 0): asset for asset in (assets or [])
        }
        cues_by_scene = {
            cue.get("scene_number", 0): cue for cue in (audio_cues or [])
        }
        plans = []
        for scene in scenes:
            scene_no = scene.get("scene_number", 0)
            # Prefer an asset already attached on the scene (asset_production path).
            asset = scene.get("resolved_asset") or assets_by_scene.get(scene_no)
            plans.append(
                self.build_scene_plan(
                    scene,
                    asset=asset,
                    audio_cue=cues_by_scene.get(scene_no),
                )
            )
        return plans
