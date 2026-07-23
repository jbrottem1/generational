"""Word / sentence timing helpers and light SSML handling."""

from __future__ import annotations

import re
from typing import Any

_SSML_TAG = re.compile(r"<[^>]+>")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def strip_ssml(text: str) -> str:
    """Remove SSML tags for providers that only accept plain text."""
    return _SSML_TAG.sub("", text or "").strip()


def has_ssml(text: str) -> bool:
    return bool(_SSML_TAG.search(text or ""))


def estimate_word_timestamps(text: str, duration_sec: float) -> list[dict[str, Any]]:
    """Evenly distribute word timings across duration (fallback when provider omits them)."""
    words = [w for w in re.findall(r"\S+", strip_ssml(text)) if w]
    if not words:
        return []
    duration = max(float(duration_sec or 0), 0.01)
    step = duration / len(words)
    out = []
    for index, word in enumerate(words):
        start = round(index * step, 3)
        end = round(min(duration, (index + 1) * step), 3)
        out.append({"word": word, "start": start, "end": end, "index": index})
    return out


def estimate_sentence_timestamps(text: str, duration_sec: float) -> list[dict[str, Any]]:
    plain = strip_ssml(text)
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(plain) if s.strip()]
    if not sentences:
        if plain:
            return [{"text": plain, "start": 0.0, "end": float(duration_sec or 0), "index": 0}]
        return []
    weights = [max(1, len(s.split())) for s in sentences]
    total = sum(weights) or 1
    duration = max(float(duration_sec or 0), 0.01)
    cursor = 0.0
    out = []
    for index, (sentence, weight) in enumerate(zip(sentences, weights)):
        span = duration * (weight / total)
        start = round(cursor, 3)
        end = round(cursor + span, 3)
        out.append({"text": sentence, "start": start, "end": end, "index": index})
        cursor = end
    if out:
        out[-1]["end"] = round(duration, 3)
    return out


def attach_timing_metadata(
    text: str,
    duration_sec: float,
    *,
    word_timestamps: list | None = None,
    sentence_timestamps: list | None = None,
) -> dict[str, Any]:
    words = list(word_timestamps or []) or estimate_word_timestamps(text, duration_sec)
    sentences = list(sentence_timestamps or []) or estimate_sentence_timestamps(text, duration_sec)
    return {
        "duration_sec": float(duration_sec or 0),
        "word_timestamps": words,
        "sentence_timestamps": sentences,
        "word_count": len(words),
        "sentence_count": len(sentences),
        "ssml": has_ssml(text),
    }
