"""Module 10 — Continuous Improvement: each project teaches the next."""

from __future__ import annotations

from services.optimization_lab.knowledge import load_patterns, record_winning_patterns
from services.optimization_lab.history import search_experiments


def extract_lessons(winner: dict, critique: dict, revisions: list) -> list[str]:
    lessons: list[str] = []
    axes = winner.get("axes") or {}
    if axes.get("hook"):
        lessons.append(f"Winning hook style leaned on: {str(axes['hook'])[:80]}")
    if axes.get("narration"):
        lessons.append(f"Narration style '{axes['narration']}' contributed to win")
    if axes.get("thumbnail"):
        lessons.append(f"Thumbnail layout '{axes['thumbnail']}' selected")
    for rev in revisions[:3]:
        for fix in rev.get("fixes") or []:
            lessons.append(f"Revision learned: {fix}")
    for issue in (critique.get("issues") or [])[:3]:
        lessons.append(f"Avoid: {issue.get('kind')} — {issue.get('suggestion')}")
    return lessons[:12]


def improve_future_priors(winner: dict) -> dict:
    """Persist winning patterns so future productions start smarter."""
    patterns = record_winning_patterns(winner)
    history = search_experiments(limit=50)
    avg = (
        int(round(sum(int(e.get("production_score") or 0) for e in history) / len(history)))
        if history
        else int((winner.get("overall_score") or 0))
    )
    return {
        "patterns_updated": True,
        "pattern_keys": list(patterns.keys()),
        "rolling_avg_production_score": avg,
        "message": "Future productions will bias toward recorded winning patterns",
    }


def measurable_improvement_signal() -> dict:
    """Compare early vs recent experiment scores to prove learning over time."""
    rows = list(reversed(search_experiments(limit=40)))
    if len(rows) < 4:
        return {
            "enough_data": False,
            "early_avg": 0,
            "recent_avg": 0,
            "delta": 0,
            "improving": False,
        }
    mid = len(rows) // 2
    early = rows[:mid]
    recent = rows[mid:]
    early_avg = sum(int(r.get("production_score") or 0) for r in early) / max(1, len(early))
    recent_avg = sum(int(r.get("production_score") or 0) for r in recent) / max(1, len(recent))
    delta = recent_avg - early_avg
    return {
        "enough_data": True,
        "early_avg": round(early_avg, 1),
        "recent_avg": round(recent_avg, 1),
        "delta": round(delta, 1),
        "improving": delta >= 0,
    }
