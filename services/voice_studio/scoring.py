"""Heuristic voice scoring for educational narration fitness."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG, normalize_profile_key

# Keyword buckets — public marketing labels from ElevenLabs voice names only
_CLARITY = ("clear", "crisp", "articulate", "precise", "bright", "radio", "broadcaster")
_EDU = ("educator", "teacher", "professor", "informative", "knowledgable", "knowledgeable", "mature", "reassuring")
_ENERGY_HI = ("energetic", "enthusiast", "fiery", "fierce", "excited", "social", "creator", "quirky", "playful")
_ENERGY_LO = ("calm", "soft", "relaxed", "gentle", "soothing", "wise", "warm", "laid-back", "laid back")
_PRO = ("professional", "confident", "authoritative", "executive", "steady", "trustworthy", "resonant", "firm")
_LONG = ("documentary", "storyteller", "narrator", "warm", "comforting", "velvety", "balanced", "mature")


def _hay(voice: dict[str, Any]) -> str:
    return " ".join(
        str(voice.get(k) or "") for k in ("name", "category", "description", "labels", "accent")
    ).lower()


def _hit_score(hay: str, words: tuple[str, ...], base: float = 6.0, step: float = 1.2) -> float:
    score = base
    for w in words:
        if w in hay:
            score = min(10.0, score + step)
    return score


def score_voice_dimensions(voice: dict[str, Any], *, audio_path: str | Path | None = None) -> dict[str, Any]:
    """Score one voice 0–10 on clarity, educational tone, energy, professionalism, long-form comfort."""
    hay = _hay(voice)
    clarity = _hit_score(hay, _CLARITY, 6.5, 1.0)
    educational = _hit_score(hay, _EDU, 6.0, 1.3)
    energy = 5.5
    for w in _ENERGY_HI:
        if w in hay:
            energy = min(10.0, energy + 1.4)
    for w in _ENERGY_LO:
        if w in hay:
            energy = max(2.0, energy - 1.2)
    professionalism = _hit_score(hay, _PRO, 6.5, 1.1)
    long_form = _hit_score(hay, _LONG, 6.0, 1.1)
    if "social" in hay or "creator" in hay:
        long_form = max(3.0, long_form - 1.5)
        energy = min(10.0, energy + 0.8)

    acoustics: dict[str, Any] = {}
    if audio_path:
        acoustics = _acoustic_adjust(Path(audio_path))
        if acoustics.get("mean_volume") is not None:
            mean = float(acoustics["mean_volume"])
            # Prefer moderate loudness for educational (-18 to -28 dB)
            if -28 <= mean <= -18:
                clarity = min(10.0, clarity + 0.6)
                long_form = min(10.0, long_form + 0.4)
            elif mean > -12:
                clarity = max(3.0, clarity - 0.8)
                energy = min(10.0, energy + 0.5)
            elif mean < -40:
                clarity = max(3.0, clarity - 1.2)
                energy = max(2.0, energy - 1.0)

    dims = {
        "clarity": round(clarity, 2),
        "educational_tone": round(educational, 2),
        "energy": round(energy, 2),
        "professionalism": round(professionalism, 2),
        "long_form_comfort": round(long_form, 2),
    }
    overall = round(sum(dims.values()) / len(dims), 2)
    return {
        "voice_id": voice.get("voice_id") or "",
        "name": voice.get("name") or "",
        "category": voice.get("category") or "",
        "dimensions": dims,
        "overall": overall,
        "acoustics": acoustics,
    }


# Extra name/label affinity per profile (keyword → bonus) so recommendations diversify
_PROFILE_AFFINITY: dict[str, tuple[str, ...]] = {
    "professor": ("educator", "knowledgable", "knowledgeable", "professional", "mature", "reassuring"),
    "documentary": ("warm", "storyteller", "resonant", "comforting", "wise", "balanced"),
    "storyteller": ("storyteller", "captivating", "warm", "velvety", "actress"),
    "science_educator": ("educator", "clear", "informative", "knowledgable", "knowledgeable", "professional"),
    "technology_explainer": ("clear", "confident", "energetic", "creator", "engaging", "educator"),
    "history_narrator": ("wise", "mature", "balanced", "deep", "broadcaster", "storyteller"),
    "calm_instructor": ("calm", "soft", "relaxed", "reassuring", "gentle", "educator"),
    "energetic_presenter": ("energetic", "enthusiast", "social", "creator", "fiery", "playful"),
    "energetic_explainer": ("energetic", "enthusiast", "social", "creator", "fiery", "playful"),
    "calm_educator": ("calm", "soft", "relaxed", "reassuring", "gentle", "educator"),
}


def score_for_profile(voice_score: dict[str, Any], profile_key: str) -> float:
    key = normalize_profile_key(profile_key)
    weights = (NARRATOR_PROFILE_CATALOG.get(key) or {}).get("score_weights") or {}
    dims = voice_score.get("dimensions") or {}
    if not dims:
        return 0.0
    total = 0.0
    wsum = 0.0
    for dim, val in dims.items():
        w = float(weights.get(dim, 1.0))
        total += float(val) * w
        wsum += w
    base = total / max(wsum, 1e-6)
    hay = f"{voice_score.get('name') or ''} {voice_score.get('category') or ''}".lower()
    bonus = 0.0
    for token in _PROFILE_AFFINITY.get(key, ()):
        if token in hay:
            bonus += 0.35
    return round(min(10.0, base + bonus), 2)


def rank_voices_for_profile(scored: list[dict[str, Any]], profile_key: str) -> list[dict[str, Any]]:
    ranked = []
    for row in scored:
        fit = score_for_profile(row, profile_key)
        ranked.append({**row, "profile_fit": fit, "profile_key": normalize_profile_key(profile_key)})
    ranked.sort(key=lambda r: (-float(r.get("profile_fit") or 0), -float(r.get("overall") or 0)))
    return ranked


def educational_shorts_score(voice_score: dict[str, Any]) -> float:
    """Composite optimized for educational YouTube Shorts."""
    d = voice_score.get("dimensions") or {}
    return round(
        float(d.get("clarity") or 0) * 1.4
        + float(d.get("educational_tone") or 0) * 1.5
        + float(d.get("energy") or 0) * 1.1
        + float(d.get("professionalism") or 0) * 1.0
        + float(d.get("long_form_comfort") or 0) * 0.5,
        2,
    )


def _acoustic_adjust(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        from services.elevenlabs.validation import _probe_loudness

        loud = _probe_loudness(path)
        return {"mean_volume": loud.get("mean_volume"), "max_volume": loud.get("max_volume")}
    except Exception:  # noqa: BLE001
        return {}


def sanitize_voice_filename(name: str, voice_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (name or "voice").strip())[:40].strip("_").lower()
    vid = (voice_id or "unknown")[:12]
    return f"{slug}_{vid}"
