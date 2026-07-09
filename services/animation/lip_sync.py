"""Provider-independent lip sync planning.

Maps narration / voice timing into phoneme, word, sentence, pause, and
breath cues. Real TTS providers later fill exact timings; this module
produces a stable contract either way.
"""

from __future__ import annotations

import re

from services.animation.config import AnimationConfig

# Approximate English phoneme inventory used for planning (not IPA-perfect —
# enough for provider adapters to remap).
_VOWELS = set("aeiou")
_PUNCT_PAUSE = {".", "!", "?", ";"}
_COMMA_PAUSE = {",", "—", "-"}


def _words(text: str) -> "list[str]":
    return re.findall(r"[A-Za-z0-9']+|[.!?…,;]", text or "")


def _phonemes_for_word(word: str) -> "list[str]":
    cleaned = re.sub(r"[^A-Za-z]", "", word).lower()
    if not cleaned:
        return []
    phonemes: "list[str]" = []
    i = 0
    while i < len(cleaned):
        ch = cleaned[i]
        if ch in _VOWELS:
            # Collapse vowel runs into one phoneme family.
            run = ch
            while i + 1 < len(cleaned) and cleaned[i + 1] in _VOWELS:
                i += 1
                run += cleaned[i]
            phonemes.append(f"V_{run[0]}")
        else:
            phonemes.append(f"C_{ch}")
        i += 1
    return phonemes or ["C_sil"]


def _estimate_word_duration(word: str, base: float = 0.28) -> float:
    letters = len(re.sub(r"[^A-Za-z]", "", word))
    return round(max(0.12, base + letters * 0.035), 3)


def plan_lip_sync(
    scenes: "list[dict]",
    scene_timing: "list[dict]",
    item: dict,
    config: AnimationConfig,
) -> "list[dict]":
    """Build lip sync plans per speaking character / scene."""
    if not config.enable_lip_sync:
        return []

    audio = item.get("audio_package") or {}
    voice_assets = item.get("voice_assets") or audio.get("voice_assets") or {}
    timing_by_scene = {entry["scene_id"]: entry for entry in scene_timing}
    creative = item.get("creative_package") or {}
    cast = list((creative.get("character_plan") or {}).get("cast") or [])
    default_speaker = (
        cast[0].get("character_id") if cast else "char_narrator"
    )

    plans: "list[dict]" = []
    for scene in scenes:
        narration = str(scene.get("narration") or "").strip()
        if not narration:
            continue
        scene_id = scene.get("scene_id", "")
        timing = timing_by_scene.get(scene_id, {})
        start = float(timing.get("start_sec", 0.0))
        end = float(timing.get("end_sec", start + 3.0))
        window = max(0.5, end - start)

        tokens = _words(narration)
        word_entries: "list[dict]" = []
        phoneme_entries: "list[dict]" = []
        pauses: "list[dict]" = []
        breaths: "list[dict]" = []
        sentences: "list[dict]" = []

        # Allocate time proportionally across speakable tokens.
        speakable = [t for t in tokens if re.search(r"[A-Za-z0-9]", t)]
        raw_durations = [_estimate_word_duration(w) for w in speakable]
        total_raw = sum(raw_durations) or 1.0
        # Leave ~12% of the window for pauses/breaths.
        speak_budget = window * 0.88
        scale = speak_budget / total_raw

        cursor = start
        sentence_start = start
        sentence_words: "list[str]" = []
        speak_index = 0

        for token in tokens:
            if token in _PUNCT_PAUSE:
                pause_dur = min(0.35, window * 0.05)
                pauses.append({
                    "start_sec": round(cursor, 3),
                    "end_sec": round(cursor + pause_dur, 3),
                    "kind": "sentence",
                })
                if sentence_words:
                    sentences.append({
                        "text": " ".join(sentence_words),
                        "start_sec": round(sentence_start, 3),
                        "end_sec": round(cursor, 3),
                    })
                    sentence_words = []
                cursor += pause_dur
                sentence_start = cursor
                continue
            if token in _COMMA_PAUSE:
                pause_dur = min(0.18, window * 0.03)
                pauses.append({
                    "start_sec": round(cursor, 3),
                    "end_sec": round(cursor + pause_dur, 3),
                    "kind": "clause",
                })
                cursor += pause_dur
                continue

            duration = round(raw_durations[speak_index] * scale, 3)
            speak_index += 1
            word_start = cursor
            word_end = cursor + duration
            word_entries.append({
                "word": token,
                "start_sec": round(word_start, 3),
                "end_sec": round(word_end, 3),
            })
            sentence_words.append(token)

            phonemes = _phonemes_for_word(token)
            if phonemes:
                slot = duration / len(phonemes)
                p_cursor = word_start
                for phoneme in phonemes:
                    phoneme_entries.append({
                        "phoneme": phoneme,
                        "start_sec": round(p_cursor, 3),
                        "end_sec": round(p_cursor + slot, 3),
                    })
                    p_cursor += slot
            cursor = word_end

        if sentence_words:
            sentences.append({
                "text": " ".join(sentence_words),
                "start_sec": round(sentence_start, 3),
                "end_sec": round(cursor, 3),
            })

        # One breath near the midpoint of longer lines.
        if window >= 2.5:
            mid = start + window / 2
            breaths.append({
                "start_sec": round(mid - 0.08, 3),
                "end_sec": round(mid + 0.08, 3),
                "kind": "inhale",
            })

        speakers = scene.get("characters") or [default_speaker]
        speaker = speakers[0] if speakers else default_speaker
        audio_ref = (
            voice_assets.get("uri")
            or voice_assets.get("asset_id")
            or audio.get("voice_style", {}).get("name")
            or f"voice://{scene_id}"
        )
        plans.append({
            "lip_sync_id": f"lipsync_{scene_id}_{speaker}",
            "scene_id": scene_id,
            "character_id": speaker,
            "audio_ref": str(audio_ref),
            "phonemes": phoneme_entries,
            "words": word_entries,
            "sentences": sentences,
            "pauses": pauses,
            "breaths": breaths,
        })
    return plans
