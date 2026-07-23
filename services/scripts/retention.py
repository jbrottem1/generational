"""Retention model — predicted audience behavior for one script variant.

Every finalized variant gets a deterministic retention estimate built from
its section-level attention/intensity curves, its text, and the idea's
psychology dimensions:

- drop_off_risk       0-100, risk of losing the viewer in the opening beats
- engagement_score    0-100, likelihood of comments / shares / saves
- retention_score     0-100, predicted average watch-through
- rewatch_probability 0.0-1.0, chance of an immediate replay
- curiosity_strength  0-100, how hard the open loops pull
- emotional_pacing    label + variance describing the intensity curve

Heuristic and reproducible in every mode — the future Learning Engine can
replace any formula with a learned model without changing the dict shape.
"""

from __future__ import annotations

from core.heuristics import CURIOSITY_WORDS, SURPRISE_WORDS, clamp, count_hits, sentences

# Sections inside the critical opening window where drop-off is decided.
OPENING_SECTIONS = ("primary_hook", "pattern_interrupt", "curiosity_hook")

ENGAGEMENT_VERBS = ["follow", "subscribe", "share", "comment", "save", "repost", "tag"]


def _sections_by_key(variant) -> dict:
    return {section.get("key"): section for section in (variant.sections or [])}


def _emotional_pacing(intensities: list) -> dict:
    if not intensities:
        return {"label": "flat", "range": 0, "curve": []}
    spread = max(intensities) - min(intensities)
    peak_index = intensities.index(max(intensities))
    late_peak = peak_index >= len(intensities) // 2
    if spread < 15:
        label = "flat"
    elif spread < 30:
        label = "steady build" if late_peak else "front-loaded"
    else:
        label = "cinematic arc" if late_peak else "rollercoaster"
    return {"label": label, "range": spread, "curve": list(intensities)}


def build_retention_model(variant, psychology: "dict | None" = None) -> dict:
    """Deterministic retention estimate for one finalized variant."""
    psychology = psychology or {}
    by_key = _sections_by_key(variant)
    all_attention = [s["attention_score"] for s in variant.sections] or [50]
    all_intensity = [s["emotional_intensity"] for s in variant.sections] or [50]
    opening_attention = [by_key[k]["attention_score"] for k in OPENING_SECTIONS if k in by_key]
    opening_avg = sum(opening_attention) / len(opening_attention) if opening_attention else 50

    text = variant.full_script
    long_sentences = [s for s in sentences(text) if len(s.split()) > 28]

    # Baseline ~40% risk for an average opening; every attention point in
    # the opening window buys risk down, long sentences and a weak
    # first-3-second psychology profile push it back up.
    drop_off_risk = clamp(
        70
        - 0.6 * opening_avg
        + 6 * min(len(long_sentences), 3)
        - round((psychology.get("first_3_second_hook", 50) - 50) * 0.2),
        3,
        97,
    )

    curiosity_strength = clamp(
        40
        + 9 * min(count_hits(text, CURIOSITY_WORDS), 4)
        + (10 if variant.curiosity_loop.strip() else 0)
        + round((psychology.get("curiosity_gap", 50) - 50) * 0.3),
        0,
        100,
    )

    engagement_score = clamp(
        38
        + 10 * min(count_hits(variant.call_to_action, ENGAGEMENT_VERBS), 2)
        + (8 if "you" in text.lower() else 0)
        + ("?" in text) * 6
        + round(
            (
                psychology.get("comment_likelihood", 50)
                + psychology.get("share_likelihood", 50)
                - 100
            )
            * 0.15
        ),
        0,
        100,
    )

    retention_score = clamp(
        0.55 * (sum(all_attention) / len(all_attention))
        + 0.20 * curiosity_strength
        + 0.15 * (100 - drop_off_risk)
        + 0.10 * min(len(variant.retention_checkpoints or []), 3) * 33,
        0,
        100,
    )

    # Short, surprising, dense scripts get replayed; long ones rarely do.
    runtime = max(variant.estimated_runtime_sec, 1)
    brevity = 1.0 if runtime <= 35 else max(0.0, 1.0 - (runtime - 35) / 120)
    surprise = min(count_hits(text, SURPRISE_WORDS), 3) / 3
    rewatch_probability = round(
        min(0.95, 0.12 + 0.35 * brevity + 0.20 * surprise + 0.30 * curiosity_strength / 100), 2
    )

    return {
        "drop_off_risk": drop_off_risk,
        "engagement_score": engagement_score,
        "retention_score": round(retention_score),
        "rewatch_probability": rewatch_probability,
        "curiosity_strength": curiosity_strength,
        "emotional_pacing": _emotional_pacing(all_intensity),
    }
