"""Module 1 — Multi-Version Generation (A–E variants)."""

from __future__ import annotations

import copy
import hashlib

from services.optimization_lab.models import DEFAULT_VARIANT_COUNT, VARIANT_AXES, VARIANT_LABELS
from services.viewer_retention.hooks import generate_hook_candidates_v2

_NARRATION_STYLES = (
    "authoritative_educator",
    "curious_storyteller",
    "high_energy_host",
    "calm_documentary",
    "myth_buster",
)
_VISUAL_STYLES = (
    "science_documentary",
    "tech_neon",
    "nature_clean",
    "historical_warm",
    "kinetic_infographic",
)
_MUSIC_MOODS = ("soft_pulse", "cinematic_rise", "curious_pluck", "urgent_beat", "ambient_space")
_CAMERA_SETS = (
    ("slow_push", "orbit"),
    ("macro_push", "parallax"),
    ("reveal", "dolly"),
    ("whip_pan", "crash_zoom"),
    ("ken_burns", "tracking"),
)
_CAPTION_STYLES = ("kinetic_bold", "minimal_clean", "highlight_pop", "typewriter", "center_punch")
_THUMB_LAYOUTS = (
    "face_left_text_right",
    "centered_subject_bold_title",
    "before_after_split",
    "question_overlay",
    "stat_callout",
)


def _seed(candidate: dict) -> str:
    raw = f"{candidate.get('title')}|{candidate.get('topic')}|{candidate.get('hook')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _title_variants(base: str, subject: str) -> list[str]:
    base = (base or subject or "Untitled").strip()
    subject = subject or base
    return [
        base,
        f"The Hidden Truth About {subject}",
        f"{subject} Explained in 60 Seconds",
        f"Why Everyone Gets {subject} Wrong",
        f"The One Detail About {subject} That Changes Everything",
    ]


def generate_variants(candidate: dict, *, count: int = DEFAULT_VARIANT_COUNT) -> list[dict]:
    """Generate A–E production variants with intentional axis differences."""
    count = max(2, min(count, len(VARIANT_LABELS)))
    subject = str(candidate.get("topic") or candidate.get("title") or "this topic")
    hooks = generate_hook_candidates_v2(candidate, topic=subject)
    hook_texts = [h.text for h in hooks] or [str(candidate.get("hook") or subject)]
    titles = _title_variants(str(candidate.get("title") or ""), subject)
    seed = _seed(candidate)

    # Scene order permutations (stable)
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    scene_ids = [str(s.get("scene_id") or f"s{i+1}") for i, s in enumerate(scenes)]

    variants: list[dict] = []
    for i in range(count):
        label = VARIANT_LABELS[i]
        hook = hook_texts[i % len(hook_texts)]
        title = titles[i % len(titles)]
        # Rotate mid scenes for order diversity without breaking hook/payoff
        order = list(scene_ids)
        if len(order) > 3:
            mid = order[1:-1]
            mid = mid[i % len(mid) :] + mid[: i % len(mid)] if mid else mid
            order = [order[0]] + mid + [order[-1]]

        variant = {
            "variant_id": f"{seed}_{label}",
            "label": label,
            "axes": {
                "hook": hook,
                "narration": _NARRATION_STYLES[i % len(_NARRATION_STYLES)],
                "scene_order": order,
                "visual_style": _VISUAL_STYLES[i % len(_VISUAL_STYLES)],
                "music": _MUSIC_MOODS[i % len(_MUSIC_MOODS)],
                "camera_movement": list(_CAMERA_SETS[i % len(_CAMERA_SETS)]),
                "caption_style": _CAPTION_STYLES[i % len(_CAPTION_STYLES)],
                "thumbnail": _THUMB_LAYOUTS[i % len(_THUMB_LAYOUTS)],
                "title": title,
                "description": (
                    f"{hook} Learn {subject} with clear visuals and a memorable payoff."
                ),
                "seo": {
                    "title": title,
                    "tags": [subject.lower(), "shorts", "explained", f"v{label.lower()}"],
                    "hashtags": [f"#{subject.replace(' ', '')}", "#shorts", "#education"],
                },
            },
            "source_candidate_id": candidate.get("id") or candidate.get("title"),
            "baseline": False,
        }
        # Ensure every axis is represented
        assert set(variant["axes"].keys()) >= set(VARIANT_AXES)
        variants.append(variant)

    if variants:
        variants[0]["baseline"] = True
        # Keep original hook/title on A when present
        if candidate.get("hook"):
            variants[0]["axes"]["hook"] = str(candidate["hook"])
        if candidate.get("title"):
            variants[0]["axes"]["title"] = str(candidate["title"])
            variants[0]["axes"]["seo"]["title"] = str(candidate["title"])

    return variants


def apply_winner_to_candidate(candidate: dict, winner: dict) -> dict:
    """Promote winning variant axes onto the candidate (additive)."""
    axes = (winner.get("axes") if winner else None) or {}
    updated = copy.deepcopy(candidate)
    if axes.get("hook"):
        updated["hook"] = axes["hook"]
        updated["optimized_hook"] = axes["hook"]
    if axes.get("title"):
        updated["title"] = axes["title"]
        updated["optimized_title"] = axes["title"]
    if axes.get("description"):
        updated["description"] = axes["description"]
    if axes.get("seo"):
        updated["seo"] = {**(updated.get("seo") or {}), **axes["seo"]}
        updated["seo_package"] = {
            **(updated.get("seo_package") or {}),
            "title": axes["seo"].get("title"),
            "description": axes.get("description") or axes["seo"].get("title"),
            "tags": axes["seo"].get("tags") or [],
            "hashtags": axes["seo"].get("hashtags") or [],
        }
    if axes.get("narration"):
        updated["narration_style"] = axes["narration"]
    if axes.get("visual_style"):
        updated["visual_style"] = axes["visual_style"]
    if axes.get("caption_style"):
        updated["caption_style"] = axes["caption_style"]
    if axes.get("thumbnail"):
        updated["thumbnail_layout"] = axes["thumbnail"]
    if axes.get("camera_movement"):
        updated["preferred_camera_moves"] = axes["camera_movement"]
    if axes.get("music"):
        updated["music_mood"] = axes["music"]
    if axes.get("scene_order"):
        updated["optimized_scene_order"] = axes["scene_order"]
    updated["winning_variant_id"] = winner.get("variant_id")
    updated["winning_variant_label"] = winner.get("label")
    return updated
