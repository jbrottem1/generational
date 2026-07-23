"""Master editing timeline builder — tracks, layers, clips, markers."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def _clip_id() -> str:
    return uuid.uuid4().hex[:10]


def build_edit_timeline(
    render_package: dict,
    scene_cuts: list,
    config: "PostProductionConfig | None" = None,
) -> dict:
    """Build the master editing timeline from render package + cut decisions."""
    timeline = render_package.get("timeline") or {}
    segments = timeline.get("segments") or []
    total_duration = float(timeline.get("total_duration_sec") or 0.0)
    fps = int(timeline.get("fps") or 30)

    video_clips = []
    audio_clips = []
    caption_clips = []
    effect_clips = []

    cut_map = {cut["scene_id"]: cut for cut in scene_cuts}

    for segment in segments:
        scene_id = segment.get("scene_id", 0)
        cut = cut_map.get(scene_id, {})
        start = float(cut.get("edited_start", segment.get("start_time", 0.0)))
        end = float(cut.get("edited_end", segment.get("end_time", 0.0)))
        duration = max(end - start, 0.0)

        video_clips.append({
            "clip_id": _clip_id(),
            "asset_ref": segment.get("visual_reference", ""),
            "start_time": start,
            "end_time": end,
            "duration": duration,
            "in_point": 0.0,
            "out_point": duration,
            "transition_in": segment.get("transition_in", "cut"),
            "transition_out": segment.get("transition_out", "cut"),
            "effects": [],
            "metadata": {"scene_id": scene_id},
        })

        if segment.get("audio_reference") or segment.get("narration_reference"):
            audio_clips.append({
                "clip_id": _clip_id(),
                "asset_ref": segment.get("audio_reference") or segment.get("narration_reference", ""),
                "start_time": start,
                "end_time": end,
                "duration": duration,
                "in_point": 0.0,
                "out_point": duration,
                "transition_in": "none",
                "transition_out": "none",
                "effects": [],
                "metadata": {"scene_id": scene_id, "track": "dialogue"},
            })

        if segment.get("caption_reference"):
            caption_clips.append({
                "clip_id": _clip_id(),
                "asset_ref": segment.get("caption_reference", ""),
                "start_time": start,
                "end_time": end,
                "duration": duration,
                "in_point": 0.0,
                "out_point": duration,
                "transition_in": "none",
                "transition_out": "none",
                "effects": [],
                "metadata": {"scene_id": scene_id},
            })

    tracks = [
        {"track_id": "video_main", "track_type": "video", "layer": 0, "clips": video_clips, "muted": False, "locked": False},
        {"track_id": "audio_dialogue", "track_type": "audio", "layer": 0, "clips": audio_clips, "muted": False, "locked": False},
        {"track_id": "audio_music", "track_type": "audio", "layer": 1, "clips": [], "muted": False, "locked": False},
        {"track_id": "audio_sfx", "track_type": "audio", "layer": 2, "clips": [], "muted": False, "locked": False},
        {"track_id": "captions", "track_type": "caption", "layer": 0, "clips": caption_clips, "muted": False, "locked": False},
        {"track_id": "effects", "track_type": "effect", "layer": 0, "clips": effect_clips, "muted": False, "locked": False},
        {"track_id": "graphics", "track_type": "graphics", "layer": 1, "clips": [], "muted": False, "locked": False},
    ]

    markers = _build_markers(segments, scene_cuts, total_duration)

    return {
        "timeline_id": uuid.uuid4().hex[:12],
        "total_duration_sec": total_duration,
        "fps": fps,
        "tracks": tracks,
        "markers": markers,
        "metadata": {"source": "render_package", "segment_count": len(segments)},
    }


def _build_markers(segments: list, scene_cuts: list, total_duration: float) -> list:
    markers = []
    for segment in segments:
        scene_id = segment.get("scene_id", 0)
        start = float(segment.get("start_time", 0.0))
        markers.append({
            "marker_id": _clip_id(),
            "time": start,
            "label": f"scene_{scene_id}_start",
            "marker_type": "cut",
            "metadata": {"scene_id": scene_id},
        })

    if total_duration > 0:
        markers.append({
            "marker_id": _clip_id(),
            "time": total_duration,
            "label": "end",
            "marker_type": "chapter",
            "metadata": {},
        })

    return markers
