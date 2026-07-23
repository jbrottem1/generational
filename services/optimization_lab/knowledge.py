"""Module 6 — Knowledge Database of successful patterns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.env import project_root

_PATTERN_FILE = "data/analytics/optimization_patterns.json"

DEFAULT_PATTERNS = {
    "best_hook_structures": [
        "open_loop",
        "shock_statistic",
        "contradiction",
        "immediate_payoff",
    ],
    "highest_retention_pacing": ["cut_2s", "zoom_rhythm", "montage"],
    "most_effective_camera_movements": ["macro_push", "orbit", "reveal", "parallax"],
    "strong_narration_patterns": ["authoritative_educator", "high_energy_host"],
    "high_performing_thumbnail_layouts": [
        "question_overlay",
        "stat_callout",
        "before_after_split",
    ],
    "caption_styles": ["kinetic_bold", "highlight_pop"],
    "color_palettes": ["science_documentary", "technology"],
    "opening_techniques": ["visual_mystery_first_2s", "stat_popup_on_hook"],
    "closing_techniques": ["callback_to_hook", "one_line_takeaway"],
}


def _path() -> Path:
    return project_root() / _PATTERN_FILE


def load_patterns() -> dict[str, Any]:
    path = _path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = dict(DEFAULT_PATTERNS)
                merged.update(data)
                return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_PATTERNS)


def save_patterns(patterns: dict[str, Any]) -> Path:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(patterns, indent=2), encoding="utf-8")
    return path


def apply_patterns_to_axes(axes: dict, patterns: dict | None = None) -> tuple[dict, list[dict]]:
    """Bias variant axes toward historically successful patterns (non-destructive)."""
    patterns = patterns or load_patterns()
    applied: list[dict] = []
    out = dict(axes)

    hooks = patterns.get("best_hook_structures") or []
    if hooks and not out.get("hook"):
        applied.append({"dimension": "hook", "value": hooks[0]})

    cams = patterns.get("most_effective_camera_movements") or []
    if cams and len(out.get("camera_movement") or []) < 2:
        out["camera_movement"] = list(cams[:2])
        applied.append({"dimension": "camera_movement", "value": out["camera_movement"]})

    narr = patterns.get("strong_narration_patterns") or []
    if narr and out.get("narration") not in narr:
        # Don't override unless weak — leave as guidance only
        applied.append({"dimension": "narration_guidance", "value": narr[0]})

    thumbs = patterns.get("high_performing_thumbnail_layouts") or []
    if thumbs and out.get("thumbnail") not in thumbs:
        applied.append({"dimension": "thumbnail_guidance", "value": thumbs[0]})

    captions = patterns.get("caption_styles") or []
    if captions and out.get("caption_style") not in captions:
        applied.append({"dimension": "caption_guidance", "value": captions[0]})

    return out, applied


def record_winning_patterns(winner: dict) -> dict:
    """Update knowledge DB from a winning variant."""
    patterns = load_patterns()
    axes = winner.get("axes") or {}

    def _prepend(key: str, value: str | list, limit: int = 8) -> None:
        cur = list(patterns.get(key) or [])
        values = value if isinstance(value, list) else [value]
        for v in reversed(values):
            if not v:
                continue
            if v in cur:
                cur.remove(v)
            cur.insert(0, v)
        patterns[key] = cur[:limit]

    if axes.get("narration"):
        _prepend("strong_narration_patterns", axes["narration"])
    if axes.get("thumbnail"):
        _prepend("high_performing_thumbnail_layouts", axes["thumbnail"])
    if axes.get("caption_style"):
        _prepend("caption_styles", axes["caption_style"])
    if axes.get("visual_style"):
        _prepend("color_palettes", axes["visual_style"])
    if axes.get("camera_movement"):
        _prepend("most_effective_camera_movements", axes["camera_movement"])

    save_patterns(patterns)
    return patterns
