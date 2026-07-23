"""Module 4 — Narration Engine: educator cadence, emphasis, natural pauses."""

from __future__ import annotations

import re

from core.heuristics import clamp, sentences


def _psych(candidate: dict) -> dict:
    p = candidate.get("psychology") or {}
    if isinstance(p, dict) and isinstance(p.get("dimensions"), dict):
        return p["dimensions"]
    return p if isinstance(p, dict) else {}


def _script_text(candidate: dict) -> str:
    ss = candidate.get("structured_script") or {}
    if isinstance(ss, dict) and ss.get("full_script"):
        return str(ss["full_script"])
    for key in ("script", "narration", "voiceover"):
        if candidate.get(key):
            return str(candidate[key])
    return str(candidate.get("hook") or candidate.get("title") or "")


def optimize_sentence_rhythm(text: str) -> dict:
    """Split long sentences, insert pause markers, mark emphasis words."""
    raw = sentences(text) or [text]
    optimized: list[dict] = []
    for sent in raw:
        words = sent.split()
        # Break very long sentences into two beats
        if len(words) > 26:
            mid = len(words) // 2
            # Prefer split after comma-ish boundary
            for i in range(mid - 3, mid + 4):
                if 0 < i < len(words) and words[i - 1].endswith((",", ";", "—")):
                    mid = i
                    break
            chunks = [" ".join(words[:mid]).strip(), " ".join(words[mid:]).strip()]
        else:
            chunks = [sent.strip()]

        for chunk in chunks:
            if not chunk:
                continue
            w = chunk.split()
            emphasis = []
            for i, word in enumerate(w):
                bare = re.sub(r"[^\w]", "", word)
                if bare.lower() in {
                    "never", "always", "secret", "surprising", "impossible",
                    "actually", "because", "critical", "key", "only",
                } or (bare[:1].isupper() and i > 0 and len(bare) > 4):
                    emphasis.append(i)
            pause_after = len(w) >= 12 or chunk.endswith((".", "!", "?"))
            optimized.append(
                {
                    "text": chunk,
                    "word_count": len(w),
                    "emphasis_indices": emphasis[:4],
                    "pause_after_ms": 280 if pause_after else 120,
                    "speaking_rate": "energetic" if len(w) < 14 else "measured",
                }
            )
    return {
        "beats": optimized,
        "beat_count": len(optimized),
        "avg_words": round(
            sum(b["word_count"] for b in optimized) / max(1, len(optimized)), 1
        ),
    }


def build_narration_plan(candidate: dict, *, selected_hook: dict | None = None) -> dict:
    psych = _psych(candidate)
    text = _script_text(candidate)
    hook_text = ""
    if selected_hook:
        hook_text = str((selected_hook.get("selected") or selected_hook).get("text") or "")
    if hook_text and text and hook_text not in text:
        text = f"{hook_text} {text}".strip()

    rhythm = optimize_sentence_rhythm(text)
    authority = clamp(55 + round((float(psych.get("information_density") or 50) - 50) * 0.4), 0, 100)
    curiosity = clamp(55 + round((float(psych.get("curiosity_gap") or 50) - 50) * 0.5), 0, 100)
    excitement = clamp(50 + round((float(psych.get("emotional_intensity") or 50) - 50) * 0.45), 0, 100)

    # Avoid robotic cadence: vary rate across beats
    for i, beat in enumerate(rhythm["beats"]):
        if i % 3 == 0:
            beat["speaking_rate"] = "energetic"
        elif i % 3 == 1:
            beat["speaking_rate"] = "authoritative"
        else:
            beat["speaking_rate"] = "curious"

    score = clamp(
        48
        + min(20, rhythm["beat_count"] * 2)
        + (8 if 8 <= rhythm["avg_words"] <= 18 else 0)
        + int(authority * 0.1)
        + int(curiosity * 0.08),
        0,
        100,
    )

    return {
        "style": "experienced_science_educator",
        "traits": {
            "authority": authority,
            "curiosity": curiosity,
            "excitement": excitement,
            "clarity": 90,
        },
        "rhythm": rhythm,
        "selected_hook": hook_text,
        "score": score,
        "guidance": [
            "Human-sounding pauses after key claims",
            "Emphasize surprise words without shouting",
            "Never flat robotic cadence — vary energy every 2–3 beats",
        ],
    }
