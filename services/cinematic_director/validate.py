"""Validate cinematic direction — reject flat / static / repetitive plans."""

from __future__ import annotations

from typing import Any

from services.cinematic_director.vocabulary import CAMERA_MOVES


def validate_cinematic_direction(package: dict[str, Any]) -> dict[str, Any]:
    """Return ok + hard fails for directing quality before render."""
    shots = package.get("shot_list") or []
    fails: list[str] = []
    warnings: list[str] = []

    if len(shots) < 1:
        fails.append("empty_shot_list")
        return {"ok": False, "hard_fails": fails, "warnings": warnings, "passed": False}

    # Static too long
    static_run = 0.0
    prev_move = ""
    identical_streak = 0
    motion_scores = []

    for shot in shots:
        move = str(shot.get("camera") or "")
        dur = float(shot.get("duration_sec") or shot.get("timing", {}).get("duration_sec") or 3)
        meta = CAMERA_MOVES.get(move) or {}
        score = int(shot.get("movement_score") or 0)
        motion_scores.append(score)

        if meta.get("static") or move == "static" or score < 25:
            static_run += dur
            if static_run > 4.5:
                fails.append(f"static_too_long:{shot.get('scene_id')}")
        else:
            static_run = 0.0

        if move == prev_move:
            identical_streak += 1
            if identical_streak >= 2:
                fails.append(f"repetitive_motion:{move}")
        else:
            identical_streak = 0
        prev_move = move

        if not shot.get("emphasis") and score < 40:
            warnings.append(f"weak_emphasis:{shot.get('scene_id')}")

        if int(shot.get("emotional_pacing", {}).get("intensity_pct") or score) < 20:
            fails.append(f"emotional_pacing_flat:{shot.get('scene_id')}")

        if score < 22 and not meta.get("static"):
            warnings.append(f"visually_flat:{shot.get('scene_id')}")

    avg_motion = sum(motion_scores) / max(1, len(motion_scores))
    if avg_motion < 35:
        fails.append("overall_visually_flat")

    # First scene must be high energy
    first = shots[0]
    if int(first.get("movement_score") or 0) < 50:
        fails.append("weak_opening_three_seconds")

    # Dedupe fails
    hard = sorted(set(fails))
    return {
        "ok": not hard,
        "passed": not hard,
        "hard_fails": hard,
        "warnings": sorted(set(warnings)),
        "average_movement_score": round(avg_motion, 1),
        "shot_count": len(shots),
    }
