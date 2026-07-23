"""Exactly ONE highest-impact creative recommendation — ranked by retention gain."""

from __future__ import annotations

from typing import Any

from services.creative_excellence.models import RETENTION_IMPACT_RANK

# Concrete creative prescriptions (attention craft, not software)
PRESCRIPTIONS = {
    "first_3_seconds": (
        "Rebuild second 0–3 as a concrete myth visual with a hard negation "
        "(X-out / smash-cut), spoken in ≤12 words. No definitions."
    ),
    "first_6_seconds": (
        "Add a second visual beat by 3.5s that proves the reframe before any explanation continues."
    ),
    "first_15_seconds": (
        "Plant one unpaid curiosity loop by second 12 that can only resolve at the ending payoff."
    ),
    "middle_pacing": (
        "Insert one pattern interrupt at ~40–50% runtime (fact card + micro-pause), then accelerate cuts."
    ),
    "ending": (
        "Land the payoff in one sentence, then one share/tag CTA tied to the emotional peak — nothing else."
    ),
    "visual_movement": (
        "Raise early cut rate to ≤2.5s average shot length for the first 15 seconds; kill single-still opens."
    ),
    "narration_energy": (
        "Stress only the hook and punchline lines; keep body copy calmer to create human contour."
    ),
    "curiosity": (
        "Replace explanatory open with a wrong-belief confrontation the viewer feels compelled to resolve."
    ),
    "payoff": (
        "State the demystifying claim once, clearly, after the open loop — then stop talking."
    ),
    "viewer_emotion": (
        "Attach the idea to a personal stake (embarrassment, amazement, relief) before the first fact."
    ),
}


def pick_single_recommendation(
    *,
    segments: dict[str, float],
    craft: dict[str, float],
    floor: float = 92.0,
) -> dict[str, Any]:
    """Return exactly one recommendation ranked by expected retention gain."""
    scored: dict[str, float] = {**segments, **craft}
    candidates = []
    for key, impact, why in RETENTION_IMPACT_RANK:
        val = float(scored.get(key) or 100)
        if val >= floor:
            continue
        gap = floor - val
        # Expected retention gain proxy: impact weight × how far below excellence floor
        expected_gain = round(impact * (gap / 100.0), 2)
        candidates.append(
            {
                "element": key,
                "current_score": round(val, 1),
                "excellence_floor": floor,
                "gap": round(gap, 1),
                "impact_weight": impact,
                "expected_retention_gain": expected_gain,
                "why_this_ranks_first": why,
                "recommendation": PRESCRIPTIONS.get(key, "Strengthen this craft signal only."),
            }
        )
    candidates.sort(key=lambda c: (-c["expected_retention_gain"], -c["impact_weight"]))
    if not candidates:
        # Even strong pieces get a maintenance recommendation at the next cliff
        weakest = min(scored.items(), key=lambda kv: kv[1])
        key = weakest[0]
        return {
            "element": key,
            "current_score": round(float(weakest[1]), 1),
            "excellence_floor": floor,
            "gap": round(max(0.0, floor - float(weakest[1])), 1),
            "impact_weight": next((i for k, i, _ in RETENTION_IMPACT_RANK if k == key), 50),
            "expected_retention_gain": 1.0,
            "why_this_ranks_first": "Maintain excellence — reinforce the softest high-performer before shipping scale.",
            "recommendation": PRESCRIPTIONS.get(key, "Hold craft; do not open new creative fronts."),
            "mode": "maintain",
        }
    top = candidates[0]
    top["mode"] = "improve"
    top["do_not_touch"] = [c["element"] for c in candidates[1:6]]
    top["principle"] = "Never suggest 20 improvements. Ship one highest-impact creative change."
    top["runner_ups"] = [
        {"element": c["element"], "expected_retention_gain": c["expected_retention_gain"]}
        for c in candidates[1:4]
    ]
    return top
