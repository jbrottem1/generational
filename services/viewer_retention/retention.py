"""Module 8 — Retention Analyzer: simulate drop-off and flag weak sections."""

from __future__ import annotations

from core.heuristics import clamp
from services.viewer_retention.models import RetentionCheckpoint, ScenePacing


def _hook_strength(hook: dict) -> float:
    selected = hook.get("selected") or hook
    return float(selected.get("score") or 50) / 100.0


def simulate_retention(
    *,
    duration_sec: float,
    hook: dict,
    pacing: list[ScenePacing],
    narration_score: int,
    visual_score: int,
    psychology: dict | None = None,
) -> dict:
    """Predict retention at 3 / 10 / 20 / 40 / ending seconds."""
    psychology = psychology or {}
    h = _hook_strength(hook)
    psych_ret = float(psychology.get("retention_potential") or 55) / 100.0
    narr = narration_score / 100.0
    visu = visual_score / 100.0
    variety = len({p.pacing_label for p in pacing}) if pacing else 1

    # Survival curve — stronger hooks + pacing variety lift early and mid retention
    p3 = clamp(100 * (0.62 + 0.32 * h + 0.1 * psych_ret), 45, 99)
    p10 = clamp(p3 * (0.86 + 0.1 * narr + 0.06 * min(variety, 5) / 5), 35, 98)
    p20 = clamp(p10 * (0.82 + 0.12 * visu + 0.08 * psych_ret), 28, 97)
    p40 = clamp(p20 * (0.8 + 0.1 * narr + 0.1 * h), 22, 96)
    ending = clamp(
        p40 * (0.78 + 0.14 * psych_ret + 0.1 * (1 if duration_sec <= 65 else 0.88)),
        18,
        94,
    )

    # Scale checkpoints to actual duration
    checkpoints = [
        RetentionCheckpoint(3, "3s", p3 / 100.0, "high" if p3 < 70 else "low", "Hook window"),
        RetentionCheckpoint(10, "10s", p10 / 100.0, "high" if p10 < 60 else "medium" if p10 < 75 else "low", "Early education"),
        RetentionCheckpoint(20, "20s", p20 / 100.0, "high" if p20 < 50 else "medium" if p20 < 70 else "low", "Mid-body"),
        RetentionCheckpoint(min(40, duration_sec), "40s", p40 / 100.0, "high" if p40 < 45 else "low", "Late body"),
        RetentionCheckpoint(duration_sec, "ending", ending / 100.0, "medium" if ending < 55 else "low", "Completion"),
    ]

    weak = [c for c in checkpoints if c.risk == "high"]
    avg_ret = (p3 + p10 + p20 + p40 + ending) / 5.0

    return {
        "duration_sec": round(duration_sec, 2),
        "checkpoints": [c.to_dict() for c in checkpoints],
        "average_retention_pct": round(avg_ret, 1),
        "completion_rate": round(ending, 1),
        "weak_sections": [c.to_dict() for c in weak],
        "score": int(round(avg_ret)),
        "revision_needed": bool(weak) or avg_ret < 70,
    }


def estimate_duration(pacing: list[ScenePacing], narration_plan: dict | None = None) -> float:
    if pacing:
        return float(sum(p.duration_sec for p in pacing))
    beats = (narration_plan or {}).get("rhythm", {}).get("beats") or []
    if beats:
        return float(sum(max(1.1, b.get("word_count", 10) / 2.6) for b in beats))
    return 60.0
