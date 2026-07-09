"""Render preparation — the machine-consumable handoff to the Render Engine.

The Director does NOT render. This module compiles the directed storyboard
into a **Render Package**: a flat, JSON-safe timeline of instructions
(asset requests, transitions, overlays, captions, zoom moves, SFX cues)
that a future Render Engine can execute clip by clip without re-deriving
any creative decision. Contract version is pinned so renderers can detect
format changes.
"""

from __future__ import annotations

from services.visual.sources import build_asset_requests

RENDER_PACKAGE_VERSION = "1.0"


def _clip_for(scene: dict, asset_request: dict) -> dict:
    """One renderable clip — everything the renderer needs for this beat."""
    timing = scene.get("caption_timing", {})
    return {
        "clip_number": scene["scene_number"],
        "start_sec": timing.get("start_sec", 0.0),
        "end_sec": timing.get("end_sec", 0.0),
        "duration_sec": scene["length_sec"],
        "asset_request": asset_request,
        "shot_type": scene.get("shot_type", "medium"),
        "camera_motion": scene.get("camera_motion", ""),
        "zoom": scene.get("zoom", ""),
        "transition_in": scene.get("transition_in", "none"),
        "transition_out": scene.get("transition_out", "hard cut"),
        "overlay": {
            "text": scene.get("text_overlay", ""),
            "treatment": scene.get("overlay", ""),
        },
        "caption": {
            "text": scene.get("narration", ""),
            "placement": scene.get("caption_placement", "bottom third, safe zone"),
            "start_sec": timing.get("start_sec", 0.0),
            "end_sec": timing.get("end_sec", 0.0),
        },
        "sfx": scene.get("sfx_timing", {}),
        "predicted_retention": scene.get("predicted_retention", 0),
    }


def build_render_package(
    scenes: list,
    *,
    idea: dict,
    style_key: str,
    aspect_ratio: str,
    thumbnails: list,
) -> dict:
    """The complete Render Package for one idea (JSON-safe dict)."""
    asset_requests = build_asset_requests(scenes)
    clips = [_clip_for(scene, request) for scene, request in zip(scenes, asset_requests)]
    total = round(sum(scene["length_sec"] for scene in scenes), 1)
    return {
        "render_package_version": RENDER_PACKAGE_VERSION,
        "title": idea.get("title", ""),
        "style": style_key,
        "aspect_ratio": aspect_ratio,
        "total_duration_sec": total,
        "clip_count": len(clips),
        "clips": clips,
        "music_style": scenes[0].get("music_style", "") if scenes else "",
        "thumbnail_brief": thumbnails[0] if thumbnails else {},
        "retention_curve": [
            {"scene_number": scene["scene_number"], "predicted_retention": scene["predicted_retention"]}
            for scene in scenes
        ],
    }
