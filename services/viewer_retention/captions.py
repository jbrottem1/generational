"""Module 6 — Caption Engine: dynamic emphasis, safe positioning, multi-format."""

from __future__ import annotations

import re

from core.heuristics import clamp

KEYWORD_EMPHASIS = {
    "never", "always", "secret", "surprising", "impossible", "actually",
    "critical", "key", "only", "because", "ai", "brain", "data", "learn",
}


def _aspect(candidate: dict) -> str:
    vp = candidate.get("visual_package") or {}
    return str(vp.get("aspect_ratio") or candidate.get("aspect_ratio") or "9:16")


def build_caption_plan_v2(candidate: dict, narration_plan: dict | None = None) -> dict:
    aspect = _aspect(candidate)
    vertical = aspect in ("9:16", "9/16", "vertical")
    beats = (narration_plan or {}).get("rhythm", {}).get("beats") or []

    cues: list[dict] = []
    t = 0.0
    for beat in beats:
        text = str(beat.get("text") or "")
        words = text.split()
        if not words:
            continue
        # ~2.6 words/sec energetic educator
        dur = max(1.1, len(words) / 2.6)
        highlighted = []
        for i, w in enumerate(words):
            bare = re.sub(r"[^\w]", "", w).lower()
            if bare in KEYWORD_EMPHASIS or i in (beat.get("emphasis_indices") or []):
                highlighted.append(i)
        cues.append(
            {
                "start_sec": round(t, 2),
                "end_sec": round(t + dur, 2),
                "text": text,
                "highlight_indices": highlighted[:5],
                "font_scale": 1.15 if highlighted else 1.0,
                "motion": "pop_emphasis" if highlighted else "fade_in",
            }
        )
        t += dur + (beat.get("pause_after_ms") or 120) / 1000.0

    # Safe area: never cover faces / focal lower-third research visuals
    layout = {
        "aspect_ratio": aspect,
        "position": "lower_third" if vertical else "bottom_center",
        "margin_v_pct": 12 if vertical else 8,
        "max_width_pct": 86 if vertical else 70,
        "avoid_zones": ["top_10_pct", "center_focal"] if vertical else ["lower_left_logo"],
        "typography": {
            "weight": "bold",
            "outline": True,
            "keyword_color": "#FFE566",
            "base_color": "#FFFFFF",
        },
    }

    existing = (candidate.get("visual_package") or {}).get("caption_plan") or {}
    score = clamp(
        50
        + min(30, len(cues) * 2)
        + (10 if layout["avoid_zones"] else 0)
        + (8 if any(c.get("highlight_indices") for c in cues) else 0),
        0,
        100,
    )

    return {
        "cues": cues,
        "layout": layout,
        "dynamic_sizing": True,
        "keyword_highlighting": True,
        "supports_formats": ["9:16", "16:9", "1:1"],
        "inherits_visual_caption_plan": bool(existing),
        "score": score,
    }
