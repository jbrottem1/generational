"""Timeline review — judge the open, middle, and end like a retention team."""

from __future__ import annotations

import re
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def _text_blob(candidate: dict) -> str:
    parts = [
        candidate.get("hook"),
        candidate.get("v2_hook"),
        (candidate.get("structured_script") or {}).get("primary_hook"),
        (candidate.get("structured_script") or {}).get("full_script"),
        candidate.get("script"),
        (candidate.get("voice_package") or {}).get("plain_text"),
        (candidate.get("voice_package") or {}).get("text"),
    ]
    return " ".join(str(p) for p in parts if p)


def _psych(candidate: dict) -> dict:
    p = candidate.get("psychology") or {}
    if isinstance(p.get("dimensions"), dict):
        return p["dimensions"]
    return p if isinstance(p, dict) else {}


def _scene_count(candidate: dict) -> int:
    scenes = (
        (candidate.get("visual_package") or {}).get("scenes")
        or candidate.get("scenes")
        or (candidate.get("structured_script") or {}).get("scene_breakdown")
        or []
    )
    return len(scenes) if isinstance(scenes, list) else 0


def _has_meta_leak(text: str) -> bool:
    low = text.lower()
    leaks = (
        "narrator professor",
        "educational style",
        "youtube shorts",
        "length_sec",
        "production brief",
    )
    return any(x in low for x in leaks)


def _curiosity_verbs(text: str) -> int:
    return len(
        re.findall(
            r"\b(secret|hidden|actually|wait|stop|most people|wrong|never|before you|the truth|nobody)\b",
            text.lower(),
        )
    )


def review_timeline_segments(candidate: dict, *, report: dict | None = None) -> dict[str, Any]:
    """Score mandatory timeline windows + craft signals (0–100)."""
    report = report or {}
    text = _text_blob(candidate)
    psych = _psych(candidate)
    scenes = _scene_count(candidate)
    duration = float(
        candidate.get("duration_sec")
        or report.get("length_sec")
        or (candidate.get("render_package") or {}).get("duration_sec")
        or 45
    )
    hook = float(report.get("hook_score") or candidate.get("hook_score") or psych.get("first_3_second_hook") or 70)
    visual = float(report.get("visual_score") or candidate.get("visual_score") or 70)
    narration = float(report.get("narration_score") or 70)
    retention = float(report.get("retention_prediction") or 70)
    share = float(report.get("shareability") or psych.get("share_likelihood") or 70)
    edu = float(report.get("educational_accuracy") or 70)
    animation = float(report.get("animation_score") or visual)
    curio_hits = _curiosity_verbs(text)
    meta_leak = _has_meta_leak(text)

    # First 3s — scroll stop
    first_3 = _clamp(
        0.55 * hook
        + 0.20 * min(100, 50 + curio_hits * 12)
        + 0.15 * visual
        + 0.10 * (40 if meta_leak else 90),
        0,
        100,
    )
    # Penalty: single static open reads as skippable
    if scenes <= 1 and visual < 95:
        first_3 = _clamp(first_3 - 12, 0, 100)

    # First 6s — confirm promise with visual argument
    first_6 = _clamp(
        0.40 * first_3
        + 0.25 * visual
        + 0.20 * animation
        + 0.15 * (85 if scenes >= 2 else 55),
        0,
        100,
    )

    # First 15s — lock promise before mid drop
    first_15 = _clamp(
        0.35 * first_6
        + 0.25 * retention
        + 0.20 * narration
        + 0.20 * (90 if curio_hits >= 2 else 65),
        0,
        100,
    )

    # Middle pacing — cuts / interrupts
    change_proxy = _clamp(40 + scenes * 8 + (animation - 70) * 0.5, 0, 100)
    middle = _clamp(0.45 * change_proxy + 0.35 * retention + 0.20 * visual, 0, 100)
    if duration > 50:
        middle = _clamp(middle - 6, 0, 100)

    # Ending — payoff + share seed
    cta = str(
        (candidate.get("structured_script") or {}).get("call_to_action")
        or candidate.get("call_to_action")
        or text[-280:]
    ).lower()
    has_share = any(w in cta for w in ("share", "tag", "send", "save", "follow"))
    ending = _clamp(
        0.35 * share
        + 0.30 * edu
        + 0.20 * (90 if has_share else 55)
        + 0.15 * retention,
        0,
        100,
    )

    # Craft signals
    emotion = _clamp(
        float(psych.get("emotional_intensity") or 0) or (0.5 * hook + 0.5 * share),
        0,
        100,
    )
    curiosity = _clamp(
        float(psych.get("curiosity_gap") or 0) or (55 + curio_hits * 10),
        0,
        100,
    )
    if meta_leak:
        curiosity = _clamp(curiosity - 10, 0, 100)
    payoff = _clamp(0.5 * ending + 0.3 * edu + 0.2 * first_15, 0, 100)
    visual_movement = _clamp(
        0.5 * animation + 0.3 * change_proxy + 0.2 * visual,
        0,
        100,
    )
    narration_energy = _clamp(
        narration * (0.92 if meta_leak else 1.0) + (5 if "!" in text[:120] or "—" in text[:120] else 0),
        0,
        100,
    )

    segments = {
        "first_3_seconds": round(first_3, 1),
        "first_6_seconds": round(first_6, 1),
        "first_15_seconds": round(first_15, 1),
        "middle_pacing": round(middle, 1),
        "ending": round(ending, 1),
    }
    craft = {
        "viewer_emotion": round(emotion, 1),
        "curiosity": round(curiosity, 1),
        "payoff": round(payoff, 1),
        "visual_movement": round(visual_movement, 1),
        "narration_energy": round(narration_energy, 1),
    }
    notes = {
        "first_3_seconds": "Scroll-stop window — concrete contradiction beats definition.",
        "first_6_seconds": "Must prove the open with a visual argument.",
        "first_15_seconds": "Promise locked or viewer exits.",
        "middle_pacing": "Cut density / pattern interrupt against mid-drop.",
        "ending": "Payoff clarity + share seed.",
        "meta_leak_detected": meta_leak,
        "scene_count": scenes,
        "curiosity_hits": curio_hits,
        "share_cta_detected": has_share,
    }
    return {"segments": segments, "craft": craft, "notes": notes}
