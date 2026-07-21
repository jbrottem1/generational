"""Scene planner — the Cinematic AI Director's storyboard department.

Converts a scripted candidate into a fully directed storyboard. The planner
prefers the Script Engine's canonical `structured_script` handoff (scene
breakdown with timestamps and emotional beats) and falls back to the winning
variant / raw script, so it also works standalone on any idea dict.

Every scene is directed end to end: purpose, emotion, attention level,
professional shot type (lens, depth of field, motion), composition, subject
placement, lighting + environment (per-emotion looks), style-preset palette,
transitions, motion recommendation, asset sourcing, base AI image/video
prompts, stock footage query, overlays, caption placement + timing, SFX
timing, B-roll, thumbnail-candidate flag, 12-trigger visual psychology
scores, and predicted viewer retention.

Everything here is deterministic (same input → same storyboard), so the
Director works in Demo Mode, is unit-testable without an API key, and gives
future AI renderers a guaranteed-complete plan to execute.
"""

from __future__ import annotations

from core.heuristics import content_words, sentences
from services.visual.models import ScenePlan
from services.visual.psychology import (
    attention_level_for,
    predict_scene_retention,
    scene_visual_score,
    score_scene_visuals,
)
from services.visual.shots import SHOT_TYPES, shot_for
from services.visual.styles import resolve_style

# Seconds of story time per core-story beat — the pacing backbone. Short-form
# retention data favors a visual change roughly every 5-8 seconds.
SECONDS_PER_STORY_BEAT = 7.0
MAX_STORY_BEATS = 6

# Visual grammar per scene purpose (composition, placement, overlays,
# transitions). Camera/lens/DOF now come from the professional shot table
# (services/visual/shots.py). Data, not code.
PURPOSE_GRAMMAR = {
    "hook": {
        "shot_composition": "center-punched single subject, negative space above for text",
        "subject_placement": "dead center, filling 60% of frame",
        "transition_out": "hard cut",
        "zoom": "fast punch-in from 120% to 100% in the first 0.5s",
        "overlay": "bold 3-4 word headline, top third, high-contrast stroke",
        "caption_placement": "upper third — clear of the punch-in subject",
        "sound_effect": "deep sub-bass hit on frame one",
        "sfx_offset_sec": 0.0,
    },
    "pattern_interrupt": {
        "shot_composition": "off-center rule-of-thirds, tilted horizon",
        "subject_placement": "left third, facing into empty space",
        "transition_out": "whip cut",
        "zoom": "none — the whip carries the energy",
        "overlay": "single contradicting word stamped over the frame",
        "caption_placement": "center — stamped with the interrupt word",
        "sound_effect": "vinyl stop / record scratch",
        "sfx_offset_sec": 0.2,
    },
    "curiosity_loop": {
        "shot_composition": "layered foreground obscuring a partially visible subject",
        "subject_placement": "background center, half-hidden by foreground element",
        "transition_out": "match cut",
        "zoom": "creeping 100% to 108% push across the scene",
        "overlay": "teaser text: 'wait for it…' style, lower third",
        "caption_placement": "lower third — under the concealed reveal",
        "sound_effect": "soft riser building underneath",
        "sfx_offset_sec": 0.5,
    },
    "story_beat": {
        "shot_composition": "rule of thirds, subject leading the eye toward the next cut",
        "subject_placement": "alternating thirds each beat to reset attention",
        "transition_out": "hard cut",
        "zoom": "subtle 3% push on the key sentence",
        "overlay": "keyword text synced to every number or stat",
        "caption_placement": "bottom third, safe zone",
        "sound_effect": "whoosh on each cut",
        "sfx_offset_sec": 0.0,
    },
    "payoff": {
        "shot_composition": "hero framing, shallow depth of field, clean background",
        "subject_placement": "center, isolated against defocused backdrop",
        "transition_out": "dissolve",
        "zoom": "slow-motion settle from 105% to 100%",
        "overlay": "the single takeaway line, large, centered",
        "caption_placement": "center — the takeaway IS the frame",
        "sound_effect": "impact hit resolving into silence",
        "sfx_offset_sec": 0.3,
    },
    "cta": {
        "shot_composition": "centered, eye-level, symmetrical, direct eye contact with lens",
        "subject_placement": "center, direct eye contact with lens",
        "transition_out": "fade out",
        "zoom": "none — stability signals sincerity",
        "overlay": "animated follow/save button mimic, lower third",
        "caption_placement": "lower third — beside the follow button mimic",
        "sound_effect": "gentle chime on the closing line",
        "sfx_offset_sec": 0.5,
    },
}

# Recommended asset source per purpose (adapter keys from sources.py).
# Story beats rotate sources so the timeline never feels single-sourced.
PURPOSE_ASSET_TYPES = {
    "hook": ["ai_video"],
    "pattern_interrupt": ["ai_video"],
    "curiosity_loop": ["ai_image"],
    "story_beat": ["ai_image", "stock_footage", "ai_video", "stock_footage"],
    "payoff": ["ai_video"],
    "cta": ["ai_image"],
}

# Scene purposes whose frames are strong thumbnail-extraction candidates.
THUMBNAIL_CANDIDATE_PURPOSES = {"hook", "payoff"}

# Lighting + environment per emotion — modulates the purpose grammar so the
# same structural beat looks different in a fear arc vs. a wonder arc.
EMOTION_LOOKS = {
    "curiosity": ("single hard key light with deep falloff", "dim room with one illuminated focal object"),
    "intrigue": ("low-key split lighting, half the face in shadow", "moody interior, practical lights in background"),
    "anticipation": ("pulsing accent light, rising intensity", "dark stage with a spotlight warming up"),
    "skepticism": ("flat overhead fluorescent, clinical", "sterile desk with evidence laid out"),
    "tension": ("flickering low-key light, hard shadows", "tight corridor or cluttered space closing in"),
    "empathy": ("soft window light, warm bounce fill", "lived-in room with personal objects"),
    "shock": ("harsh strobe-adjacent key, blown highlights", "stark empty space, subject isolated"),
    "surprise": ("sudden high-key reveal light", "the same space suddenly fully lit"),
    "revelation": ("volumetric god rays through haze", "grand open space, dust motes in the light"),
    "recognition": ("mirror-lit dual key", "reflective surfaces doubling the subject"),
    "understanding": ("balanced three-point, gentle contrast", "organized space, diagram wall behind"),
    "vindication": ("golden backlight, triumphant rim", "elevated vantage over the disproven claim"),
    "reflection": ("dusk ambience, blue hour window light", "quiet room, long shadows"),
    "clarity": ("clean high-key, minimal shadows", "white studio sweep, single prop"),
    "resolve": ("steady warm key, confident contrast", "open doorway with light beyond"),
    "connection": ("warm tungsten practicals", "shared table, two mugs, close quarters"),
    "confidence": ("crisp editorial key with rim light", "minimal set, strong single-color backdrop"),
    "satisfaction": ("golden hour warmth, soft glow", "completed scene — everything in its place"),
}
DEFAULT_LOOK = ("soft natural key with rim accent", "clean cinematic backdrop supporting the subject")

# Retained for backward compatibility (pre-Cinematic-Director callers).
# Canonical palettes now live in the style presets (services/visual/styles.py).
NICHE_VISUAL_PALETTES = {
    "Science": "deep blue and cyan with white highlights, high contrast",
    "Psychology": "warm amber and charcoal, soft intimate shadows",
    "Finance": "navy and gold, clean corporate minimalism",
    "Space": "black starfield with nebula purple and teal",
    "Dark History": "desaturated sepia, film grain, candlelight orange",
    "Health": "fresh green and white, bright natural light",
    "AI & Future Tech": "neon cyan on dark grid, holographic accents",
}
DEFAULT_PALETTE = "cinematic teal and orange, balanced contrast"

# Structured-script section names → the Director's scene purposes. Covers
# both the 9-section cinematic skeleton (services/scripts/sections.py) and
# the older 5-section vocabulary, so any script era plans cleanly.
SECTION_PURPOSES = {
    "hook": "hook",
    "primary_hook": "hook",
    "pattern_interrupt": "pattern_interrupt",
    "curiosity_loop": "curiosity_loop",
    "curiosity_hook": "curiosity_loop",
    "context": "story_beat",
    "escalation": "story_beat",
    "evidence": "story_beat",
    "core_story": "story_beat",
    "emotional_peak": "payoff",
    "resolution": "story_beat",
    "cta": "cta",
    "call_to_action": "cta",
}


def palette_for(niche: str) -> str:
    return NICHE_VISUAL_PALETTES.get(niche, DEFAULT_PALETTE)


def _best_variant(idea: dict) -> dict:
    variants = idea.get("script_variants") or []
    return variants[0] if variants else {}


def _story_beats(core_story: str, story_seconds: float) -> list:
    """Split the core story into evenly sized beats, one per ~7s of runtime."""
    lines = sentences(core_story)
    if not lines:
        return []
    beat_count = max(1, min(MAX_STORY_BEATS, round(story_seconds / SECONDS_PER_STORY_BEAT) or 1))
    beat_count = min(beat_count, len(lines))
    per_beat = max(1, len(lines) // beat_count)
    beats = [" ".join(lines[i : i + per_beat]) for i in range(0, len(lines), per_beat)]
    # Fold any remainder chunk into the last beat so beat_count holds.
    if len(beats) > beat_count:
        beats[beat_count - 1] = " ".join(beats[beat_count - 1 :])
        beats = beats[:beat_count]
    return beats


def _overlay_text(narration: str, max_words: int = 5) -> str:
    words = narration.split()
    text = " ".join(words[:max_words])
    return text.upper() if len(words) <= max_words else f"{text.upper()}…"


def _visual_description(purpose: str, narration: str, subject: str, environment: str, grammar: dict) -> str:
    lead = {
        "hook": f"Scroll-stopping opening frame of {subject}",
        "pattern_interrupt": f"Jarring visual reversal around {subject}",
        "curiosity_loop": f"Partially concealed reveal of {subject}",
        "story_beat": f"Narrative beat visualizing: {narration[:90]}",
        "payoff": f"The satisfying reveal moment for {subject}",
        "cta": "Direct-to-camera closing address",
    }.get(purpose, f"Scene about {subject}")
    return f"{lead}. {environment}. {grammar['shot_composition']}."


def _stock_footage_query(narration: str, subject: str, niche: str) -> str:
    """Short keyword query a licensed-stock adapter can search directly."""
    keywords = content_words(narration)[:3]
    terms = list(dict.fromkeys([w for w in subject.lower().split() if len(w) > 2] + keywords))
    if niche:
        terms.append(niche.lower())
    return " ".join(terms[:6])


def _segments_from_structured(structured: dict) -> "list[tuple[str, str, float]]":
    """(purpose, narration, seconds) segments from the Script Engine handoff.

    The core_story section is re-split into ~7s story beats; framing sections
    keep the Script Engine's word-proportional timings.
    """
    segments = []
    for scene in structured.get("scene_breakdown", []):
        purpose = SECTION_PURPOSES.get(scene.get("section", ""), "story_beat")
        narration = scene.get("narration", "")
        seconds = float(scene.get("duration_sec") or 0) or 2.0
        if purpose == "story_beat":
            beats = _story_beats(narration, seconds) or [narration]
            per_beat = round(seconds / len(beats), 1)
            segments.extend(("story_beat", beat, per_beat) for beat in beats)
        else:
            segments.append((purpose, narration, seconds))
    return segments


def _segments_from_variant(idea: dict) -> "list[tuple[str, str, float]]":
    """Fallback segmentation when no structured_script is present."""
    variant = _best_variant(idea)
    runtime = float(idea.get("estimated_runtime_sec") or variant.get("estimated_runtime_sec") or 30)

    hook_text = variant.get("hook") or idea.get("hook", "")
    interrupt_text = variant.get("pattern_interrupt", "")
    loop_text = variant.get("curiosity_loop", "")
    core_story = variant.get("core_story") or idea.get("script", "")
    cta_text = variant.get("call_to_action") or idea.get("cta", "")

    framing = [
        ("hook", hook_text, 3.0),
        ("pattern_interrupt", interrupt_text, 2.0),
        ("curiosity_loop", loop_text, 3.0),
    ]
    framing = [(purpose, text, seconds) for purpose, text, seconds in framing if text]
    cta_seconds = 3.0 if cta_text else 0.0
    framing_seconds = sum(seconds for _, _, seconds in framing) + cta_seconds
    story_seconds = max(4.0, runtime - framing_seconds)

    segments = list(framing)
    beats = _story_beats(core_story, story_seconds)
    if beats:
        per_beat = round(story_seconds / len(beats), 1)
        segments.extend(("story_beat", beat, per_beat) for beat in beats)
    if cta_text:
        segments.append(("cta", cta_text, cta_seconds))
    return segments


def plan_scenes(
    idea: dict,
    *,
    niche: str = "",
    subject: str = "",
    style_key: str = "",
    attention: "dict | None" = None,
) -> "list[ScenePlan]":
    """Deterministically direct the full storyboard for one scripted idea.

    Prefers the Script Engine's `structured_script` handoff; consumes the
    Attention Graph's concept scores (when available) for retention
    prediction; applies the resolved style preset to every frame.
    """
    variant = _best_variant(idea)
    subject = subject or (idea.get("title") or "the subject")
    style_name, style = resolve_style(style_key=style_key or str(idea.get("visual_style", "")), niche=niche)
    palette = style["palette"]
    attention = attention if attention is not None else idea.get("attention_graph")

    arc = list(variant.get("emotional_progression") or idea.get("emotional_progression") or [])
    broll = list(variant.get("broll_suggestions") or idea.get("broll_suggestions") or [])
    sfx_bank = list(variant.get("sound_effects") or idea.get("sound_effects") or [])
    music = variant.get("music_style") or idea.get("music_style") or "understated cinematic underscore"

    structured = idea.get("structured_script") or {}
    segments = _segments_from_structured(structured) if structured.get("scene_breakdown") else _segments_from_variant(idea)

    # Guarantee a payoff: unless the script already carries an emotional
    # peak, the last story beat is promoted and gets hero treatment.
    has_payoff = any(purpose == "payoff" for purpose, _, _ in segments)
    beat_positions = [i for i, (purpose, _, _) in enumerate(segments) if purpose == "story_beat"]
    if not has_payoff and beat_positions:
        last = beat_positions[-1]
        segments[last] = ("payoff", segments[last][1], segments[last][2])

    scenes = []
    cursor = 0.0
    purpose_counts: dict = {}
    total = len(segments)
    for number, (purpose, narration, seconds) in enumerate(segments, start=1):
        grammar = PURPOSE_GRAMMAR[purpose]
        occurrence = purpose_counts.get(purpose, 0)
        purpose_counts[purpose] = occurrence + 1

        shot_key, shot = shot_for(purpose, occurrence)
        emotion = arc[(number - 1) % len(arc)] if arc else "curiosity"
        lighting_base, environment = EMOTION_LOOKS.get(emotion, DEFAULT_LOOK)
        lighting = f"{lighting_base}; style bias: {style['lighting_bias']}"
        asset_rotation = PURPOSE_ASSET_TYPES.get(purpose, ["ai_image"])
        asset_type = asset_rotation[occurrence % len(asset_rotation)]
        description = _visual_description(purpose, narration, subject, environment, grammar)
        sfx = sfx_bank[(number - 1) % len(sfx_bank)] if sfx_bank else grammar["sound_effect"]

        scene = ScenePlan(
            scene_number=number,
            purpose=purpose,
            emotion=emotion,
            length_sec=round(seconds, 1),
            visual_style=style_name,
            narration=narration,
            visual_description=description,
            shot_type=shot_key,
            camera_angle=shot["label"].lower(),
            camera_motion=shot["camera_motion"],
            lens_recommendation=shot["lens"],
            depth_of_field=shot["depth_of_field"],
            shot_composition=grammar["shot_composition"],
            subject_placement=grammar["subject_placement"],
            lighting=lighting,
            environment=environment,
            color_palette=palette,
            transition_in=scenes[-1].transition_out if scenes else "none",
            transition_out=grammar["transition_out"],
            motion_intensity=shot["motion_intensity"],
            motion_recommendation=f"{shot['energy']} — {shot['camera_motion']} at intensity {shot['motion_intensity']}/100",
            zoom=grammar["zoom"],
            background=f"{environment}, rendered in {palette}",
            asset_type=asset_type,
            ai_image_prompt=(
                f"{description} Lighting: {lighting_base}. Style: {style['art_style']}. "
                f"Palette: {palette}. Grade: {style['grade']}."
            ),
            ai_video_prompt=(
                f"{description} Camera: {shot['camera_motion']}, {shot['lens']}. "
                f"Mood: {emotion}. Style: {style['art_style']}. Duration: {round(seconds, 1)}s."
            ),
            stock_footage_query=_stock_footage_query(narration, subject, niche),
            overlay=f"{grammar['overlay']} ({style['overlay_style']})",
            text_overlay=_overlay_text(narration),
            caption_placement=grammar["caption_placement"],
            caption_timing={"start_sec": round(cursor, 1), "end_sec": round(cursor + seconds, 1)},
            sound_effect=sfx,
            sfx_timing={"at_sec": round(cursor + grammar["sfx_offset_sec"], 1), "cue": sfx},
            music_style=music,
            broll=[broll[(number - 1) % len(broll)]] if broll else [],
            thumbnail_candidate=purpose in THUMBNAIL_CANDIDATE_PURPOSES,
        )
        scene.visual_scores = score_scene_visuals(scene.to_dict())
        scene.visual_score = scene_visual_score(scene.visual_scores)
        scene.predicted_retention = predict_scene_retention(
            scene.to_dict(), scene_index=number - 1, total_scenes=total, attention=attention
        )
        scene.attention_level = attention_level_for(scene.predicted_retention)
        scenes.append(scene)
        cursor += seconds

    return scenes
