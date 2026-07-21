"""Module 6 — Smart Text / Kinetic Typography Engine."""

from __future__ import annotations

import re

KEYWORD_SET = {
    "never", "always", "secret", "surprising", "impossible", "critical",
    "key", "only", "because", "force", "energy", "ai", "brain", "data",
}


def build_typography_plan(candidate: dict) -> dict:
    vr = candidate.get("viewer_retention_package") or {}
    captions = vr.get("caption_plan") or {}
    cues = list((captions.get("cues") if isinstance(captions, dict) else []) or [])

    kinetic: list[dict] = []
    if not cues:
        # Seed from hook / title
        text = str(
            (vr.get("selected_hook") or {}).get("text")
            or candidate.get("hook")
            or candidate.get("title")
            or ""
        )
        if text:
            cues = [{"text": text, "start_sec": 0.0, "end_sec": 2.5, "highlight_indices": []}]

    for cue in cues:
        words = str(cue.get("text") or "").split()
        word_anims = []
        for i, w in enumerate(words):
            bare = re.sub(r"[^\w]", "", w).lower()
            emphasize = bare in KEYWORD_SET or i in (cue.get("highlight_indices") or [])
            word_anims.append(
                {
                    "index": i,
                    "word": w,
                    "scale": 1.18 if emphasize else 1.0,
                    "opacity_anim": "fade_in",
                    "tracking": 1.05 if emphasize else 1.0,
                    "blur_reveal": emphasize,
                    "rotation_deg": 0,
                    "color": "#FFE566" if emphasize else "#FFFFFF",
                    "motion_blur": emphasize,
                }
            )
        kinetic.append(
            {
                "start_sec": cue.get("start_sec"),
                "end_sec": cue.get("end_sec"),
                "mode": "kinetic_word_by_word",
                "words": word_anims,
                "safe_margin_pct": 12,
                "readability": {
                    "outline": True,
                    "contrast_ok": True,
                    "max_lines": 3,
                },
            }
        )

    return {
        "style": "cinematic_kinetic",
        "cues": kinetic,
        "keyword_highlighting": True,
        "auto_color_emphasis": True,
        "score_hint": 90 if kinetic else 70,
    }
