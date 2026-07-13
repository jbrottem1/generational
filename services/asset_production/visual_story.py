"""Visual Story Plan — cinematic per-scene direction for asset production.

Upgrades scene planning without redesigning the orchestrator. Kept outside
``services.visual`` package init to avoid circular imports with engines.
"""

from __future__ import annotations

from typing import Any

# Media hierarchy (best → fallback). Asset production walks this list.
MEDIA_HIERARCHY = (
    "ai_animation",
    "ai_cinematic_artwork",
    "scientific_illustration",
    "motion_graphics",
    "real_world_photograph",
    "archival_reference",
    "map",
    "chart",
    "infographic",
    "animated_text",
    "cinematic_fallback_still",
)

PURPOSE_GRAMMAR = {
    "hook": {
        "shot_composition": "center-punched single subject, negative space above for text",
        "subject_placement": "dead center, filling 60% of frame",
        "transition_out": "hard cut",
        "zoom": "fast punch-in from 120% to 100% in the first 0.5s",
        "overlay": "bold 3-4 word headline, top third, high-contrast stroke",
        "caption_placement": "upper third — clear of the punch-in subject",
    },
    "pattern_interrupt": {
        "shot_composition": "off-center rule-of-thirds, tilted horizon",
        "subject_placement": "left third, facing into empty space",
        "transition_out": "whip cut",
        "zoom": "none — the whip carries the energy",
        "overlay": "single contradicting word stamped over the frame",
        "caption_placement": "center — stamped with the interrupt word",
    },
    "curiosity_loop": {
        "shot_composition": "layered foreground obscuring a partially visible subject",
        "subject_placement": "background center, half-hidden by foreground element",
        "transition_out": "match cut",
        "zoom": "creeping 100% to 108% push across the scene",
        "overlay": "teaser text lower third",
        "caption_placement": "lower third — under the concealed reveal",
    },
    "story_beat": {
        "shot_composition": "rule of thirds, subject leading the eye toward the next cut",
        "subject_placement": "alternating thirds each beat to reset attention",
        "transition_out": "hard cut",
        "zoom": "subtle 3% push on the key sentence",
        "overlay": "keyword text synced to every number or stat",
        "caption_placement": "bottom third, safe zone",
    },
    "payoff": {
        "shot_composition": "hero framing, shallow depth of field, clean background",
        "subject_placement": "center, isolated against defocused backdrop",
        "transition_out": "dissolve",
        "zoom": "slow-motion settle from 105% to 100%",
        "overlay": "the single takeaway line, large, centered",
        "caption_placement": "center — the takeaway IS the frame",
    },
    "cta": {
        "shot_composition": "centered, eye-level, symmetrical, direct eye contact with lens",
        "subject_placement": "center, direct eye contact with lens",
        "transition_out": "fade out",
        "zoom": "none — stability signals sincerity",
        "overlay": "animated follow/save button mimic, lower third",
        "caption_placement": "lower third — beside the follow button mimic",
    },
}

_MOTION_CYCLE = (
    "slow cinematic push-in",
    "ken burns drift right",
    "slow zoom out reveal",
    "pan left across subject",
    "documentary slow zoom",
    "subtle parallax push",
    "quick punch-in on key detail",
)

_SCIENCE_VISUAL_HINTS = (
    "scientific visualization, volumetric lighting, educational documentary style",
    "macro detail, crisp laboratory aesthetic, shallow depth of field",
    "clean diagrammatic clarity blended with cinematic atmosphere",
    "NASA-grade photorealism, deep contrast, premium educational channel look",
)

_NICHE_STYLES = {
    "science": "photorealistic scientific visualization, volumetric detail",
    "space": "NASA-grade astrophotography realism",
    "psychology": "moody editorial photography, intimate realism",
    "health": "bright lifestyle photography, natural realism",
    "ai": "sleek concept art, holographic sci-fi realism",
}


def _niche_style(niche: str) -> str:
    key = (niche or "science").strip().lower()
    for name, style in _NICHE_STYLES.items():
        if name in key:
            return style
    return _NICHE_STYLES["science"]


def _purpose_from_segment(segment_type: str) -> str:
    raw = str(segment_type or "story_beat").lower().strip()
    mapping = {
        "hook": "hook",
        "context": "story_beat",
        "escalation": "curiosity_loop",
        "evidence": "story_beat",
        "payoff": "payoff",
        "cta": "cta",
        "pattern_interrupt": "pattern_interrupt",
        "retention_hook": "curiosity_loop",
        "story_beat": "story_beat",
        "curiosity_loop": "curiosity_loop",
    }
    return mapping.get(raw, "story_beat")


def _media_choice(purpose: str, index: int, narration: str) -> str:
    text = f"{purpose} {narration}".lower()
    if any(w in text for w in ("dna", "cell", "microscope", "molecule", "gene", "crispr")):
        return "scientific_illustration"
    if any(w in text for w in ("planet", "galaxy", "star", "mars", "space", "orbit", "black hole")):
        return "ai_cinematic_artwork"
    if any(w in text for w in ("map", "continent", "ocean current", "migration")):
        return "map"
    if any(w in text for w in ("chart", "percent", "data", "statistic", "rate")):
        return "infographic"
    if purpose in {"hook", "payoff"}:
        return "ai_cinematic_artwork"
    if purpose == "pattern_interrupt":
        return "motion_graphics"
    cycle = (
        "ai_cinematic_artwork",
        "scientific_illustration",
        "ai_cinematic_artwork",
        "real_world_photograph",
        "infographic",
    )
    return cycle[index % len(cycle)]


def _cinematic_prompt(scene: dict, *, niche: str, title: str) -> str:
    art_style = _niche_style(niche)
    visual = str(scene.get("visual_description") or title or "scientific subject")
    lighting = str(scene.get("lighting") or "cinematic volumetric lighting")
    composition = str(scene.get("shot_composition") or "rule of thirds")
    mood = str(scene.get("emotion") or scene.get("purpose") or "wonder")
    media = scene.get("media_type") or "ai_cinematic_artwork"
    hint = _SCIENCE_VISUAL_HINTS[int(scene.get("scene_number") or 1) % len(_SCIENCE_VISUAL_HINTS)]
    overlay = str(scene.get("text_overlay") or "").strip()
    parts = [
        f"A 9:16 vertical cinematic frame: {visual}.",
        f"Mood: {mood}. Lighting: {lighting}. Composition: {composition}.",
        f"Style: {art_style}. {hint}.",
        "ultra-detailed, sharp focus, professional color grade, 8k",
        "cinematic educational short, no watermark, no UI chrome",
        "rich detail filling the entire frame — never blank or flat color",
        f"media intent: {str(media).replace('_', ' ')}",
    ]
    if overlay:
        parts.append(f"leave subtle title treatment space for: {overlay}")
    return " ".join(parts)


def enrich_scene_story_plan(scene: dict, *, niche: str = "science", title: str = "", index: int = 0) -> dict:
    """Attach Visual Story Plan fields onto one scene dict."""
    out = dict(scene)
    purpose = _purpose_from_segment(str(out.get("purpose") or "story_beat"))
    out["purpose"] = purpose
    grammar = PURPOSE_GRAMMAR.get(purpose) or PURPOSE_GRAMMAR["story_beat"]
    narration = str(out.get("narration") or "")
    media = _media_choice(purpose, index, narration)
    motion = _MOTION_CYCLE[index % len(_MOTION_CYCLE)]
    if purpose == "hook":
        motion = "quick punch-in on key detail"
    elif purpose == "cta":
        motion = "slow cinematic push-in"

    visual = str(out.get("visual_description") or "").strip()
    if (
        not visual
        or visual.lower().startswith(purpose.replace("_", " "))
        or "visual:" in visual.lower()
    ):
        subject = narration[:160] if narration else title or "scientific subject"
        visual = (
            f"{grammar.get('shot_composition', 'cinematic framing')}; "
            f"subject: {subject}; "
            f"emotion: {out.get('emotion') or purpose}; "
            f"educational documentary lighting"
        )

    out.setdefault("shot_composition", grammar.get("shot_composition", ""))
    out.setdefault("subject_placement", grammar.get("subject_placement", ""))
    out.setdefault("lighting", "cinematic volumetric lighting, educational documentary grade")
    out.setdefault("transition_out", grammar.get("transition_out", "hard cut"))
    out["visual_description"] = visual
    out["camera_motion"] = motion
    out["zoom"] = grammar.get("zoom") or out.get("zoom") or "subtle 3% push"
    out["motion_intensity"] = int(out.get("motion_intensity") or (75 if purpose == "hook" else 55))
    out["media_type"] = media
    out["media_hierarchy"] = list(MEDIA_HIERARCHY)
    out["asset_type"] = "ai_video" if media == "ai_animation" else "ai_image"
    if not out.get("text_overlay"):
        words = narration.split()[:5]
        out["text_overlay"] = " ".join(words) if words else ""
    out.setdefault("overlay", grammar.get("overlay", ""))
    out.setdefault("caption_placement", grammar.get("caption_placement", "bottom third, safe zone"))
    out["on_screen_text"] = out.get("text_overlay") or ""
    out["supporting_graphics"] = (
        media if media in {"map", "chart", "infographic", "scientific_illustration"} else ""
    )
    out["ai_image_prompt"] = _cinematic_prompt(out, niche=niche, title=title)
    out["ai_video_prompt"] = f"Cinematic motion, {motion}: {out['ai_image_prompt'][:400]}"
    out["visual_story_plan"] = {
        "see": visual,
        "media_type": media,
        "camera_movement": motion,
        "motion_effects": out.get("zoom"),
        "transition": out.get("transition_out"),
        "on_screen_text": out.get("on_screen_text"),
        "captions": out.get("caption_placement"),
        "supporting_graphics": out.get("supporting_graphics"),
        "density_target_sec": 3.5,
    }
    length = float(out.get("length_sec") or 0)
    if length <= 0:
        out["length_sec"] = 4.0
    elif length > 8:
        out["motion_intensity"] = max(int(out["motion_intensity"]), 60)
    return out


def _try_director_scenes(asset: dict, niche: str) -> list[dict]:
    """Optionally use Cinematic AI Director when import graph allows."""
    try:
        from services.visual.scenes import plan_scenes

        planned = plan_scenes(asset, niche=niche) or []
        scenes = []
        for item in planned:
            if hasattr(item, "to_dict"):
                scenes.append(item.to_dict())
            elif isinstance(item, dict):
                scenes.append(dict(item))
        return scenes
    except Exception:  # noqa: BLE001
        return []


def build_visual_story_plans(asset: dict, *, niche: str = "science") -> list[dict[str, Any]]:
    """Build enriched Visual Story Plans for an asset.

    Prefers ``video_script.segments`` (authoritative for asset production), then
    optionally falls back to the Cinematic AI Director storyboard.
    """
    title = str(asset.get("title") or "Untitled")
    scenes: list[dict] = []

    vs = asset.get("video_script") if isinstance(asset.get("video_script"), dict) else {}
    for index, seg in enumerate(vs.get("segments") or []):
        if not isinstance(seg, dict):
            continue
        start = float(seg.get("start_time") or 0)
        end = float(seg.get("end_time") or start)
        scenes.append(
            {
                "scene_number": index + 1,
                "purpose": seg.get("segment_type") or "story_beat",
                "emotion": seg.get("emotion") or "",
                "length_sec": max(0.5, end - start),
                "narration": str(seg.get("voiceover") or ""),
                "caption_timing": {"start_sec": start, "end_sec": end},
            }
        )

    if not scenes:
        scenes = _try_director_scenes(asset, niche)

    if not scenes:
        scenes = [
            {
                "scene_number": 1,
                "purpose": "hook",
                "length_sec": 5.0,
                "narration": str(asset.get("hook") or asset.get("title") or "Science short"),
                "visual_description": f"Cinematic opening for {title}",
            }
        ]

    enriched = [
        enrich_scene_story_plan(scene, niche=niche, title=title, index=i)
        for i, scene in enumerate(scenes)
    ]
    for i, scene in enumerate(enriched):
        scene["scene_number"] = i + 1
    return enriched
