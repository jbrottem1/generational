"""Phase 5 — Continuous improvement: one highest-impact recommendation per cycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.publishing_intelligence.calibration import build_calibration_report
from services.publishing_intelligence.creative_library import recommend_creative_patterns

# Impact ordering — never optimize everything at once.
IMPACT_PRIORITY = (
    ("hook", 95, "Tighten first 3 seconds using Creative Library hook winners."),
    ("retention", 90, "Raise mid-video visual change rate and payoff timing."),
    ("ctr", 88, "Improve thumbnail contrast + title curiosity from calibration CTR gap."),
    ("shareability", 82, "Add explicit share/tag CTA near emotional peak."),
    ("completion", 80, "Shorten static holds; strengthen mid-body pattern interrupt."),
    ("narration", 75, "Adjust pacing/emphasis toward educator delivery winners."),
    ("visuals", 72, "Increase cinematic camera compounds over static frames."),
    ("publishing_time", 65, "Shift schedule toward historically stronger windows."),
    ("speed", 55, "Reduce candidate breadth for faster export loops."),
)


def recommend_highest_impact_improvement(
    *,
    quality_scores: dict | None = None,
    calibration: dict | None = None,
    topic: str = "",
    platform: str = "youtube_shorts",
) -> dict[str, Any]:
    """Identify ONE highest-impact improvement from scores + calibration + library."""
    quality_scores = quality_scores or {}
    calibration = calibration or build_calibration_report()
    creative = recommend_creative_patterns(topic=topic, platform=platform, limit=8)

    weak_internal = []
    floors = {
        "hook": ("hook_strength", 85),
        "retention": ("retention_prediction", 85),
        "shareability": ("shareability", 85),
        "completion": ("completion_prediction", 85),
        "narration": ("narration_quality", 85),
        "visuals": ("visual_quality", 85),
        "ctr": ("ctr_score", 80),
    }
    for key, (score_key, floor) in floors.items():
        val = float(quality_scores.get(score_key) or 100)
        if val < floor:
            weak_internal.append((key, floor - val, val))

    # Calibration divergences
    divergences = []
    for row in calibration.get("divergence_highlights") or []:
        metric = str(row.get("metric") or "")
        mapped = {
            "ctr": "ctr",
            "completion": "completion",
            "shareability": "shareability",
            "hook_vs_retention": "retention",
        }.get(metric, metric)
        divergences.append((mapped, float(row.get("mean_abs_error") or 0)))

    candidates = []
    for key, impact, action in IMPACT_PRIORITY:
        severity = 0.0
        for wkey, gap, _ in weak_internal:
            if wkey == key:
                severity = max(severity, gap)
        for dkey, mae in divergences:
            if dkey == key:
                severity = max(severity, mae)
        if severity <= 0 and key not in {w[0] for w in weak_internal} and key not in {d[0] for d in divergences}:
            continue
        pattern = next((r for r in creative.get("recommendations") or [] if r.get("dimension") in (key, "hook", "thumbnail_style") and key in ("hook", "ctr", "opening")), None)
        if key == "hook":
            pattern = next((r for r in creative.get("recommendations") or [] if r.get("dimension") == "hook"), pattern)
        if key == "ctr":
            pattern = next((r for r in creative.get("recommendations") or [] if r.get("dimension") == "thumbnail_style"), pattern)
        priority = impact * (1 + severity / 50.0)
        candidates.append(
            {
                "element": key,
                "impact": impact,
                "severity": round(severity, 2),
                "priority_score": round(priority, 2),
                "action": action,
                "creative_pattern": (pattern or {}).get("pattern"),
                "improves": _improves_for(key),
            }
        )

    candidates.sort(key=lambda c: -c["priority_score"])
    top = candidates[0] if candidates else {
        "element": "retention",
        "impact": 90,
        "severity": 0,
        "priority_score": 90,
        "action": "Maintain quality bars; monitor next publish for calibration data.",
        "creative_pattern": None,
        "improves": ["Viewer Retention", "Prediction Accuracy"],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "recommendation": top,
        "do_not_optimize_now": [c["element"] for c in candidates[1:6]],
        "principle": "Never optimize everything simultaneously — ship one highest-impact fix.",
        "runner_ups": candidates[1:4],
    }


def _improves_for(element: str) -> list[str]:
    mapping = {
        "hook": ["Production Quality", "Viewer Retention"],
        "retention": ["Viewer Retention", "Prediction Accuracy"],
        "ctr": ["Publishing Efficiency", "Prediction Accuracy"],
        "shareability": ["Viewer Retention", "Production Quality"],
        "completion": ["Viewer Retention"],
        "narration": ["Production Quality"],
        "visuals": ["Production Quality", "Viewer Retention"],
        "publishing_time": ["Publishing Efficiency"],
        "speed": ["Production Speed"],
    }
    return mapping.get(element, ["Production Quality"])
