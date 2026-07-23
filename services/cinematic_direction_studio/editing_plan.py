"""Editing plan — cuts, transitions, reaction timing, music, ending beat."""

from __future__ import annotations

from typing import Any

from services.cinematic_direction_studio.models import TRANSITION_STYLES


def plan_editing(
    *,
    scene_index: int,
    total: int,
    emotion: str,
    duration_sec: float,
    purpose: str = "story_beat",
) -> dict[str, Any]:
    dur = max(float(duration_sec or 3.0), 1.0)
    emotion = str(emotion or "curiosity").lower()
    purpose = str(purpose or "story_beat").lower()

    # Internal cut points (for multi-beat scenes) — motivated, not random
    cuts = [
        {"t": round(dur * 0.35, 2), "reason": "after_pause_or_look", "type": "motivated"},
        {"t": round(dur * 0.65, 2), "reason": "into_explanation_or_gesture", "type": "motivated"},
    ]
    if dur < 2.5:
        cuts = [{"t": round(dur * 0.5, 2), "reason": "mid_beat_emphasis", "type": "motivated"}]

    if scene_index == 0:
        transition_in = "establish"
        transition_out = "hold_then_cut"
    elif purpose == "payoff" or scene_index >= max(0, total - 1):
        transition_in = "J_cut"
        transition_out = "dissolve"
    elif emotion in {"wonder", "inspiration"}:
        transition_in = "dissolve"
        transition_out = "match_cut"
    else:
        transition_in = "cut"
        transition_out = "cut"

    if transition_out not in TRANSITION_STYLES and transition_out not in {"establish", "dissolve"}:
        transition_out = "cut"

    return {
        "cut_points": cuts,
        "transition_in": transition_in,
        "transition_style": transition_out if transition_out in TRANSITION_STYLES else "cut",
        "transition_out": transition_out,
        "reaction_timing_sec": 0.45 if emotion in {"wonder", "discovery"} else 0.3,
        "music_timing": {
            "enter": "under_narration" if scene_index > 0 else "after_hook_line",
            "swell_at": round(dur * 0.7, 2) if emotion in {"inspiration", "resolution"} else None,
            "exit": "tail_into_next" if scene_index < total - 1 else "resolve_hold",
        },
        "ending_beat": (
            "hold_on_face"
            if emotion in {"inspiration", "resolution", "hope"}
            else "exit_on_action"
            if emotion in {"teaching", "urgency"}
            else "settle_then_cut"
        ),
        "forbid_random_cuts": True,
        "motivated_only": True,
    }
