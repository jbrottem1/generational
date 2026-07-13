"""TimelineBuilder — the master timeline the renderer executes.

Converts the directed scene list into contiguous timeline segments with
authoritative timing. Scene lengths come from the planning layer; the
timeline recomputes start/end cumulatively so segments are guaranteed
gap-free and overlap-free regardless of how the plan's per-scene
caption_timing was rounded. Each segment carries references (not copies)
to its narration, visual, caption, and audio material — the render package
holds one source of truth per plan.
"""

from __future__ import annotations

from engines.render.models import OUTPUT_FORMAT, TimelineSegment
from engines.render.motion import MotionPlanner
from engines.render.transitions import TransitionPlanner

# Fallback scene length when the planning layer supplied none (seconds).
DEFAULT_SCENE_SEC = 4.0


def _reference(kind: str, scene_id: int) -> str:
    """Stable lookup key into the render package's per-scene material."""
    return f"{kind}/scene_{scene_id}"


class TimelineBuilder:
    """Builds the contiguous segment timeline for one video."""

    def __init__(
        self,
        transition_planner: "TransitionPlanner | None" = None,
        motion_planner: "MotionPlanner | None" = None,
    ) -> None:
        self._transitions = transition_planner or TransitionPlanner()
        self._motion = motion_planner or MotionPlanner()

    def build(self, scenes: list) -> dict:
        """Timeline dict: fps, duration, and one segment per scene."""
        transition_plan = self._transitions.plan(scenes)
        transitions = transition_plan["transitions"]
        motion_by_scene = {plan["scene_id"]: plan for plan in self._motion.plan(scenes)}

        segments = []
        warnings = list(transition_plan["warnings"])
        cursor = 0.0
        for index, scene in enumerate(scenes):
            scene_id = scene.get("scene_number", index + 1)
            duration = float(scene.get("length_sec") or 0.0)
            if duration <= 0:
                duration = DEFAULT_SCENE_SEC
                warnings.append(
                    f"Scene {scene_id} had no length — defaulted to {DEFAULT_SCENE_SEC}s."
                )
            transition_in = transitions[index - 1]["type"] if index > 0 else "cut"
            transition_out = transitions[index]["type"] if index < len(transitions) else "cut"
            segment = TimelineSegment(
                scene_id=scene_id,
                start_time=round(cursor, 2),
                end_time=round(cursor + duration, 2),
                duration=round(duration, 2),
                narration_reference=_reference("narration", scene_id),
                visual_reference=_reference("visual", scene_id),
                caption_reference=_reference("captions", scene_id),
                audio_reference=_reference("audio", scene_id),
                transition_in=transition_in,
                transition_out=transition_out,
                motion_effect=motion_by_scene.get(scene_id, {}).get("effect", "static"),
                overlay_text=scene.get("text_overlay", ""),
                render_status="planned",
            )
            segments.append(segment.to_dict())
            cursor += duration

        return {
            "fps": OUTPUT_FORMAT["fps"],
            "total_duration_sec": round(cursor, 2),
            "segment_count": len(segments),
            "segments": segments,
            "transitions": transitions,
            "warnings": warnings,
        }
