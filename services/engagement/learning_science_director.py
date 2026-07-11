"""Agent 24 — Audience Engagement & Learning Science Director (AELS).

Evidence-informed recommendations for attention, retention, and clarity.
Does not override Educational Director accuracy gates.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AELSReview:
    passed: bool = False
    engagement_score: float = 0.0
    retention_score: float = 0.0
    cognitive_load_score: float = 0.0  # higher = lower load (better)
    hook_score: float = 0.0
    pacing_score: float = 0.0
    demonstration_score: float = 0.0
    ending_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    self_review: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningScienceDirector:
    """Agent 24 — engagement + learning science review."""

    agent_id = "24"

    def review(
        self,
        *,
        hook: str = "",
        beats: list[dict[str, Any]] | None = None,
        takeaway: str = "",
        duration_sec: float = 0.0,
        qc: dict[str, Any] | None = None,
        has_visual_demo: bool = False,
    ) -> AELSReview:
        return review_engagement(
            hook=hook,
            beats=beats,
            takeaway=takeaway,
            duration_sec=duration_sec,
            qc=qc,
            has_visual_demo=has_visual_demo,
        )


_WEAK_HOOK = re.compile(r"^(today|in this video|hello|hey guys|welcome back)", re.I)
_QUESTION_HOOK = re.compile(r"\?|what if|did you know|here's something|watch", re.I)
_PATTERN_INTERRUPT = re.compile(
    r"doesn't|not one|strange|but why|—|surprising|secret|wrong",
    re.I,
)


def review_engagement(
    *,
    hook: str = "",
    beats: list[dict[str, Any]] | None = None,
    takeaway: str = "",
    duration_sec: float = 0.0,
    qc: dict[str, Any] | None = None,
    has_visual_demo: bool = False,
) -> AELSReview:
    """Heuristic AELS review — expand with analytics feedback loop later."""
    beats = beats or []
    qc = qc or {}
    recs: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []

    # Hook (curiosity gap / pattern interrupt)
    hook_score = 50.0
    if hook and len(hook) < 100:
        hook_score += 15.0
    if _QUESTION_HOOK.search(hook):
        hook_score += 20.0
    if _PATTERN_INTERRUPT.search(hook):
        hook_score += 12.0
    if _WEAK_HOOK.search(hook):
        hook_score -= 25.0
        weaknesses.append("generic_opening")
        recs.append("Replace generic intro with a curiosity gap or visual promise.")
    if hook_score < 72 and "generic_opening" not in weaknesses:
        weaknesses.append("hook_curiosity_gap")
        recs.append("Open with a question or pattern interrupt in the first 8 words.")
    if hook_score >= 70:
        strengths.append("strong_hook_pattern")

    # Cognitive load — beat count vs duration
    n_beats = len(beats)
    load_score = 70.0
    if duration_sec > 0:
        words_est = sum(len(str(b.get("text") or "").split()) for b in beats)
        wpm = words_est / max(duration_sec / 60.0, 0.1)
        if wpm > 180:
            load_score -= 20.0
            weaknesses.append("high_cognitive_load")
            recs.append("Shorten sentences; add 0.5s pause after dense beats.")
        elif wpm < 100:
            load_score += 10.0
            strengths.append("breathing_room")
    if n_beats > 10:
        load_score -= 10.0
        recs.append("Combine beats — one idea per pause, not one idea per second.")

    # Pacing — pauses
    pauses = [float(b.get("pause_after_sec") or 0) for b in beats]
    avg_pause = sum(pauses) / max(len(pauses), 1)
    pacing_score = 60.0 + min(25.0, avg_pause * 30)
    if avg_pause >= 0.5:
        strengths.append("intentional_silence")
    else:
        recs.append("Add intentional silence before key reveals (communicator_delivery).")

    # Demonstration
    demo_score = 55.0
    if has_visual_demo:
        demo_score += 25.0
    show_early = any("watch" in str(b.get("text") or "").lower() for b in beats[:3])
    if show_early:
        demo_score += 15.0
        strengths.append("show_before_tell")
    else:
        recs.append("Place 'Watch.' or visual cue within first 3 beats.")

    # Ending
    ending_score = 55.0
    if takeaway and len(takeaway) < 90:
        ending_score += 25.0
        strengths.append("clear_takeaway")
    else:
        recs.append("End with one memorable sentence under 12 words.")

    # Animation / performance from QC
    idle = float(qc.get("idle_ratio") or 0)
    if qc.get("purposeful_gestures"):
        strengths.append("purposeful_motion")
    if idle >= 0.4:
        strengths.append("calm_teaching_presence")
    elif idle < 0.2:
        recs.append("Increase stillness between gestures — calm idle aids comprehension.")

    engagement = round((hook_score + demo_score + pacing_score) / 3, 1)
    retention = round((ending_score + load_score + demo_score) / 3, 1)
    overall = (engagement + retention) / 2
    passed = overall >= 65.0 and hook_score >= 55.0

    self_review = {
        "hook_captured_attention": hook_score >= 65.0,
        "lesson_clear": load_score >= 60.0,
        "visuals_synchronized": bool(qc.get("passed")),
        "animation_natural": bool(qc.get("purposeful_gestures")),
        "ending_satisfying": ending_score >= 65.0,
        "could_be_shorter": duration_sec > 35.0,
        "could_be_more_memorable": ending_score < 70.0,
        "would_watch_next": overall >= 70.0,
    }

    return AELSReview(
        passed=passed,
        engagement_score=engagement,
        retention_score=retention,
        cognitive_load_score=round(load_score, 1),
        hook_score=round(hook_score, 1),
        pacing_score=round(pacing_score, 1),
        demonstration_score=round(demo_score, 1),
        ending_score=round(ending_score, 1),
        recommendations=recs[:5],
        strengths=strengths[:6],
        weaknesses=weaknesses[:5],
        self_review=self_review,
    )


def apply_recommendations_to_beats(
    beats: list[dict[str, Any]],
    recommendations: list[str],
    *,
    pause_boost: float = 0.0,
) -> list[dict[str, Any]]:
    """Apply validated pacing tweaks for next cycle (reversible)."""
    out = [dict(b) for b in beats]
    boost = pause_boost
    for rec in recommendations:
        if "pause" in rec.lower() or "silence" in rec.lower():
            boost = max(boost, 0.12)
        if "Watch" in rec and out:
            for i, b in enumerate(out):
                if i == 2 and "watch" not in str(b.get("text") or "").lower():
                    out.insert(2, {"text": "Watch.", "pause_after_sec": 0.45})
                    break
    if boost > 0:
        for b in out:
            b["pause_after_sec"] = round(float(b.get("pause_after_sec") or 0) + boost, 2)
    return out
