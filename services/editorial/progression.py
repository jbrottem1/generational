"""Viewer psychology progression for motivational productions.

Curiosity → Recognition → Reflection → Hope → Determination → Immediate Action
"""

from __future__ import annotations

from engines.heuristics import clamp, count_hits

MOTIVATIONAL_PROGRESSION = (
    "curiosity",
    "recognition",
    "reflection",
    "hope",
    "determination",
    "immediate_action",
)

PROGRESSION_LABELS = {
    "curiosity": "Curiosity",
    "recognition": "Recognition",
    "reflection": "Reflection",
    "hope": "Hope",
    "determination": "Determination",
    "immediate_action": "Immediate Action",
}

# Text cues used when scoring title/hook before a full script exists.
STAGE_SIGNAL_WORDS = {
    "curiosity": ("why", "what if", "secret", "nobody", "truth", "?"),
    "recognition": ("you", "you've", "your", "stuck", "tired", "familiar"),
    "reflection": ("think", "realize", "ask yourself", "notice", "consider"),
    "hope": ("can", "possible", "become", "change", "grow", "rebuild"),
    "determination": ("will", "decide", "commit", "discipline", "refuse", "stand"),
    "immediate_action": ("today", "now", "start", "do this", "first step", "begin"),
}


def score_viewer_progression(
    emotional_progression: "list | None" = None,
    text: str = "",
) -> dict:
    """Score how well a script/arc matches the six-stage motivational progression."""
    arc = [str(stage).strip().lower().replace(" ", "_") for stage in (emotional_progression or []) if stage]
    text_lower = (text or "").lower()

    # Order score: reward arcs that follow the canonical sequence (subsequence match).
    order_hits = 0
    expected_index = 0
    for stage in arc:
        while expected_index < len(MOTIVATIONAL_PROGRESSION):
            if stage == MOTIVATIONAL_PROGRESSION[expected_index] or stage in MOTIVATIONAL_PROGRESSION[expected_index]:
                order_hits += 1
                expected_index += 1
                break
            # Allow near-synonyms already normalized into the arc.
            if MOTIVATIONAL_PROGRESSION[expected_index] in stage or stage in MOTIVATIONAL_PROGRESSION[expected_index]:
                order_hits += 1
                expected_index += 1
                break
            expected_index += 1

    coverage = len(set(arc) & set(MOTIVATIONAL_PROGRESSION))
    signal_hits = sum(
        1
        for stage, words in STAGE_SIGNAL_WORDS.items()
        if count_hits(text_lower, words) or any(w in text_lower for w in words if len(w) > 1)
    )

    score = 28
    score += min(coverage, 6) * 8
    score += min(order_hits, 6) * 4
    score += min(signal_hits, 4) * 3
    if arc and arc[-1] in {"immediate_action", "action", "resolve"}:
        score += 6
    score = clamp(score)

    missing = [stage for stage in MOTIVATIONAL_PROGRESSION if stage not in set(arc)]
    note = (
        "Viewer feels understood first, then leaves determined to act."
        if coverage >= 5
        else f"Strengthen progression stages: {', '.join(PROGRESSION_LABELS[s] for s in missing[:3])}."
    )
    return {
        "score": score,
        "stages": list(MOTIVATIONAL_PROGRESSION),
        "present": [s for s in MOTIVATIONAL_PROGRESSION if s in set(arc)],
        "missing": missing,
        "order_hits": order_hits,
        "note": note,
    }
