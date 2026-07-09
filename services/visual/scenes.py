"""Scene planner — breaks a generated script into an art-directed storyboard.

Every scripted idea becomes an ordered list of `ScenePlan` objects: hook,
pattern interrupt, curiosity loop, story beats sized to the runtime, payoff,
and CTA. Each scene carries the full visual grammar (camera angle + motion,
shot composition, subject placement, lighting, environment, palette,
transitions, motion intensity, zoom, background, overlays, caption timing,
sound effects, music style, B-roll) plus its 12-dimension visual psychology
scores.

Everything here is deterministic (same input → same storyboard), so Visual
Intelligence works in Demo Mode, is unit-testable without an API key, and
gives future AI renderers a guaranteed-complete plan to execute.
"""

from __future__ import annotations

from engines.heuristics import sentences
from services.visual.models import ScenePlan
from services.visual.psychology import scene_visual_score, score_scene_visuals

# Seconds of story time per core-story beat — the pacing backbone. Short-form
# retention data favors a visual change roughly every 5-8 seconds.
SECONDS_PER_STORY_BEAT = 7.0
MAX_STORY_BEATS = 6

# Visual grammar per scene purpose. Data, not code — an art-direction change
# is an edit to this table, never to the planner.
PURPOSE_GRAMMAR = {
    "hook": {
        "camera_angle": "extreme close-up",
        "camera_motion": "crash zoom",
        "shot_composition": "center-punched single subject, negative space above for text",
        "subject_placement": "dead center, filling 60% of frame",
        "transition_out": "hard cut",
        "motion_intensity": 85,
        "zoom": "fast punch-in from 120% to 100% in the first 0.5s",
        "overlay": "bold 3-4 word headline, top third, high-contrast stroke",
        "sound_effect": "deep sub-bass hit on frame one",
    },
    "pattern_interrupt": {
        "camera_angle": "dutch angle medium shot",
        "camera_motion": "whip pan",
        "shot_composition": "off-center rule-of-thirds, tilted horizon",
        "subject_placement": "left third, facing into empty space",
        "transition_out": "whip cut",
        "motion_intensity": 75,
        "zoom": "none — the whip pan carries the energy",
        "overlay": "single contradicting word stamped over the frame",
        "sound_effect": "vinyl stop / record scratch",
    },
    "curiosity_loop": {
        "camera_angle": "over-the-shoulder reveal",
        "camera_motion": "slow push-in",
        "shot_composition": "layered foreground obscuring a partially visible subject",
        "subject_placement": "background center, half-hidden by foreground element",
        "transition_out": "match cut",
        "motion_intensity": 45,
        "zoom": "creeping 100% to 108% push across the scene",
        "overlay": "teaser text: 'wait for it…' style, lower third",
        "sound_effect": "soft riser building underneath",
    },
    "story_beat": {
        "camera_angle": "medium shot",
        "camera_motion": "tracking",
        "shot_composition": "rule of thirds, subject leading the eye toward the next cut",
        "subject_placement": "alternating thirds each beat to reset attention",
        "transition_out": "hard cut",
        "motion_intensity": 55,
        "zoom": "subtle 3% push on the key sentence",
        "overlay": "keyword text synced to every number or stat",
        "sound_effect": "whoosh on each cut",
    },
    "payoff": {
        "camera_angle": "slow-motion close-up",
        "camera_motion": "orbit",
        "shot_composition": "hero framing, shallow depth of field, clean background",
        "subject_placement": "center, isolated against defocused backdrop",
        "transition_out": "dissolve",
        "motion_intensity": 60,
        "zoom": "slow-motion settle from 105% to 100%",
        "overlay": "the single takeaway line, large, centered",
        "sound_effect": "impact hit resolving into silence",
    },
    "cta": {
        "camera_angle": "direct-address medium close-up",
        "camera_motion": "locked-off",
        "shot_composition": "centered, eye-level, symmetrical",
        "subject_placement": "center, direct eye contact with lens",
        "transition_out": "fade out",
        "motion_intensity": 30,
        "zoom": "none — stability signals sincerity",
        "overlay": "animated follow/save button mimic, lower third",
        "sound_effect": "gentle chime on the closing line",
    },
}

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

# Color palettes per niche — shared visual identity across scenes, prompts,
# and thumbnails for the same idea.
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


def plan_scenes(
    idea: dict,
    *,
    niche: str = "",
    subject: str = "",
) -> "list[ScenePlan]":
    """Deterministically build the full storyboard for one scripted idea."""
    variant = _best_variant(idea)
    subject = subject or (idea.get("title") or "the subject")
    runtime = float(idea.get("estimated_runtime_sec") or variant.get("estimated_runtime_sec") or 30)
    palette = palette_for(niche)
    arc = list(variant.get("emotional_progression") or idea.get("emotional_progression") or [])
    broll = list(variant.get("broll_suggestions") or idea.get("broll_suggestions") or [])
    sfx_bank = list(variant.get("sound_effects") or idea.get("sound_effects") or [])
    music = variant.get("music_style") or idea.get("music_style") or "understated cinematic underscore"

    hook_text = variant.get("hook") or idea.get("hook", "")
    interrupt_text = variant.get("pattern_interrupt", "")
    loop_text = variant.get("curiosity_loop", "")
    core_story = variant.get("core_story") or idea.get("script", "")
    cta_text = variant.get("call_to_action") or idea.get("cta", "")

    # Fixed framing budget; the core story absorbs whatever runtime remains.
    framing = [
        ("hook", hook_text, 3.0),
        ("pattern_interrupt", interrupt_text, 2.0),
        ("curiosity_loop", loop_text, 3.0),
    ]
    framing = [(purpose, text, seconds) for purpose, text, seconds in framing if text]
    cta_seconds = 3.0 if cta_text else 0.0
    framing_seconds = sum(seconds for _, _, seconds in framing) + cta_seconds
    story_seconds = max(4.0, runtime - framing_seconds)

    beats = _story_beats(core_story, story_seconds)
    segments = list(framing)
    if beats:
        # The last beat is the payoff — it gets its own hero treatment.
        per_beat = round(story_seconds / len(beats), 1)
        for beat in beats[:-1]:
            segments.append(("story_beat", beat, per_beat))
        segments.append(("payoff", beats[-1], per_beat))
    if cta_text:
        segments.append(("cta", cta_text, cta_seconds))

    scenes = []
    cursor = 0.0
    for number, (purpose, narration, seconds) in enumerate(segments, start=1):
        grammar = PURPOSE_GRAMMAR[purpose]
        emotion = arc[(number - 1) % len(arc)] if arc else "curiosity"
        lighting, environment = EMOTION_LOOKS.get(emotion, DEFAULT_LOOK)
        scene = ScenePlan(
            scene_number=number,
            purpose=purpose,
            emotion=emotion,
            length_sec=round(seconds, 1),
            narration=narration,
            visual_description=_visual_description(purpose, narration, subject, environment, grammar),
            camera_angle=grammar["camera_angle"],
            camera_motion=grammar["camera_motion"],
            shot_composition=grammar["shot_composition"],
            subject_placement=grammar["subject_placement"],
            lighting=lighting,
            environment=environment,
            color_palette=palette,
            transition_in=scenes[-1].transition_out if scenes else "none",
            transition_out=grammar["transition_out"],
            motion_intensity=grammar["motion_intensity"],
            zoom=grammar["zoom"],
            background=f"{environment}, rendered in {palette}",
            overlay=grammar["overlay"],
            text_overlay=_overlay_text(narration),
            caption_timing={"start_sec": round(cursor, 1), "end_sec": round(cursor + seconds, 1)},
            sound_effect=sfx_bank[(number - 1) % len(sfx_bank)] if sfx_bank else grammar["sound_effect"],
            music_style=music,
            broll=[broll[(number - 1) % len(broll)]] if broll else [],
        )
        scene.visual_scores = score_scene_visuals(scene.to_dict())
        scene.visual_score = scene_visual_score(scene.visual_scores)
        scenes.append(scene)
        cursor += seconds

    return scenes
