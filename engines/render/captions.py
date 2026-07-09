"""CaptionRenderer — burn-in caption planning for vertical short-form video.

Produces the timing map and layout instructions a renderer needs to draw
captions: word-by-word or sentence mode, per-word timing distributed
across the scene's narration window, bold emphasis words, safe-area
positioning that clears every platform's UI chrome, and named style
presets. Nothing is drawn here — this is the caption side of the render
plan.
"""

from __future__ import annotations

import re

# Caption display modes this renderer supports.
CAPTION_MODES = ("word_by_word", "sentence")

DEFAULT_CAPTION_MODE = "word_by_word"

# Named style presets — a renderer maps these to fonts/strokes/animations.
CAPTION_STYLE_PRESETS = {
    "bold_pop": {
        "font": "Montserrat ExtraBold",
        "size_pct": 4.8,
        "fill": "#FFFFFF",
        "stroke": "#000000",
        "stroke_width_px": 6,
        "emphasis_fill": "#FFD400",
        "animation": "word pop 1.08x on entry",
        "case": "upper",
    },
    "clean_minimal": {
        "font": "Inter SemiBold",
        "size_pct": 4.0,
        "fill": "#FFFFFF",
        "stroke": "#00000088",
        "stroke_width_px": 3,
        "emphasis_fill": "#FFFFFF",
        "animation": "fade per sentence",
        "case": "sentence",
    },
    "karaoke_highlight": {
        "font": "Poppins Bold",
        "size_pct": 4.4,
        "fill": "#FFFFFFB3",
        "stroke": "#000000",
        "stroke_width_px": 4,
        "emphasis_fill": "#4DE1FF",
        "animation": "active word highlighted karaoke-style",
        "case": "sentence",
    },
    "documentary_lower_third": {
        "font": "Source Serif Pro Semibold",
        "size_pct": 3.6,
        "fill": "#F5F1E8",
        "stroke": "#1A1A1A",
        "stroke_width_px": 3,
        "emphasis_fill": "#E8C468",
        "animation": "slide up per sentence",
        "case": "sentence",
    },
}

DEFAULT_STYLE_PRESET = "bold_pop"

# Vertical 9:16 safe area — fractions of frame height/width that captions
# must clear so no platform's UI chrome (progress bar, action rail,
# description block) covers them. The union of Shorts/TikTok/Reels chrome.
SAFE_AREA = {
    "top_pct": 12.0,
    "bottom_pct": 20.0,
    "left_pct": 6.0,
    "right_pct": 12.0,  # right rail: like/comment/share stack
}

# Per-platform vertical layout deltas from the shared safe area.
PLATFORM_LAYOUTS = {
    "youtube_shorts": {"anchor_y_pct": 68.0, "notes": "clear the title/channel block at the bottom"},
    "tiktok": {"anchor_y_pct": 64.0, "notes": "clear caption + music marquee, keep off the right rail"},
    "instagram_reels": {"anchor_y_pct": 66.0, "notes": "clear the audio attribution row"},
    "facebook_reels": {"anchor_y_pct": 66.0, "notes": "mirror the Reels layout"},
}

_WORD_RE = re.compile(r"[\w'%-]+")

# Words too small to deserve emphasis when we pick emphasis heuristically.
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on",
    "is", "are", "was", "were", "it", "its", "this", "that", "with", "as",
    "at", "by", "be", "not", "you", "your", "so",
}


def _words_of(text: str) -> list:
    return _WORD_RE.findall(text or "")


def _pick_emphasis(words: list, declared: list) -> set:
    """Emphasis words: the Director's picks, else numbers + longest words."""
    declared_lower = {str(word).lower() for word in declared or []}
    if declared_lower:
        return {word for word in words if word.lower() in declared_lower}
    picked = {word for word in words if any(ch.isdigit() for ch in word)}
    candidates = sorted(
        (word for word in words if word.lower() not in _STOP_WORDS),
        key=len,
        reverse=True,
    )
    picked.update(candidates[: max(1, len(words) // 6)])
    return picked


class CaptionRenderer:
    """Builds the caption render plan (timing map + layout instructions)."""

    def build_scene_captions(
        self,
        scene: dict,
        *,
        start_sec: float,
        end_sec: float,
        mode: str = DEFAULT_CAPTION_MODE,
    ) -> dict:
        """Timed caption block for one scene, with per-word timing."""
        text = scene.get("narration", "") or scene.get("caption_text", "")
        words = _words_of(text)
        duration = max(end_sec - start_sec, 0.1)
        emphasis = _pick_emphasis(words, scene.get("caption_emphasis", []))

        word_entries = []
        if words:
            # Distribute the window across words weighted by length, so long
            # words hold the screen longer — reads naturally word-by-word.
            weights = [len(word) + 2 for word in words]
            total_weight = sum(weights)
            cursor = start_sec
            for word, weight in zip(words, weights):
                slot = duration * (weight / total_weight)
                word_entries.append(
                    {
                        "word": word,
                        "start_sec": round(cursor, 2),
                        "end_sec": round(cursor + slot, 2),
                        "emphasis": word in emphasis,
                    }
                )
                cursor += slot

        return {
            "scene_id": scene.get("scene_number", 0),
            "mode": mode,
            "start_sec": round(start_sec, 2),
            "end_sec": round(end_sec, 2),
            "sentence": text,
            "words": word_entries,
            "emphasis_words": sorted(emphasis),
            "placement": scene.get("caption_placement", "bottom third, safe zone"),
        }

    def build(
        self,
        scenes: list,
        timeline: "dict | None" = None,
        *,
        mode: str = DEFAULT_CAPTION_MODE,
        style_preset: str = DEFAULT_STYLE_PRESET,
    ) -> dict:
        """The full caption render plan for one video."""
        if mode not in CAPTION_MODES:
            mode = DEFAULT_CAPTION_MODE
        preset_key = style_preset if style_preset in CAPTION_STYLE_PRESETS else DEFAULT_STYLE_PRESET

        windows = {}
        for segment in (timeline or {}).get("segments", []):
            windows[segment["scene_id"]] = (segment["start_time"], segment["end_time"])

        segments = []
        cursor = 0.0
        for scene in scenes:
            scene_id = scene.get("scene_number", 0)
            if scene_id in windows:
                start, end = windows[scene_id]
            else:
                timing = scene.get("caption_timing", {})
                start = timing.get("start_sec", cursor)
                end = timing.get("end_sec", start + float(scene.get("length_sec", 0.0)))
            segments.append(
                self.build_scene_captions(scene, start_sec=start, end_sec=end, mode=mode)
            )
            cursor = end

        return {
            "mode": mode,
            "style_preset": preset_key,
            "style": dict(CAPTION_STYLE_PRESETS[preset_key]),
            "available_presets": list(CAPTION_STYLE_PRESETS),
            "safe_area": dict(SAFE_AREA),
            "platform_layouts": {key: dict(value) for key, value in PLATFORM_LAYOUTS.items()},
            "segments": segments,
        }
