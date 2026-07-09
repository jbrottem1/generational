"""Section architecture — the structured cinematic skeleton of every script.

Every script is broken into ordered narrative sections (primary hook,
pattern interrupt, curiosity hook, context, escalation, evidence, emotional
peak, resolution, call to action). Each section is a dict carrying the
narration plus full production direction: estimated duration, emotional
intensity, attention score, visual intent, recommended B-roll type, and
caption emphasis.

Section specs are data, not code — pacing curves, visual direction, and
caption treatment can be tuned (or learned from real analytics) without
touching generation logic. Psychology dimensions from the ViralScore
report shift the intensity/attention curves per idea, so an emotionally
charged concept gets a hotter emotional curve than a data-driven one.
"""

from __future__ import annotations

from engines.heuristics import clamp
from services.scripts.models import SCRIPT_SECTION_KEYS

# Per-section production direction. `share` is the fraction of the body
# word budget given to expandable sections (framing sections use their
# template line as-is, so their share is 0).
SECTION_SPECS = {
    "primary_hook": {
        "label": "Primary Hook",
        "share": 0.0,
        "intensity": 82,
        "attention": 93,
        "visual_intent": "Stop the scroll — bold first frame that visualizes the claim about {subject}",
        "broll_type": "high-impact hero shot / dramatic reveal",
        "caption_emphasis": "bold uppercase, word-by-word pop",
        "camera_style": "tight close-up, eye-level",
        "motion": "fast push-in",
        "transition": "hard cut",
        "voice_direction": "punchy and confident — land every word in the first 3 seconds",
    },
    "pattern_interrupt": {
        "label": "Pattern Interrupt",
        "share": 0.0,
        "intensity": 74,
        "attention": 85,
        "visual_intent": "Break the visual rhythm — unexpected cut or freeze that resets attention",
        "broll_type": "snap-zoom insert / freeze frame",
        "caption_emphasis": "single flashed keyword",
        "camera_style": "snap zoom",
        "motion": "whip pan",
        "transition": "whip cut",
        "voice_direction": "sudden tonal shift — drop volume then snap back",
    },
    "curiosity_hook": {
        "label": "Curiosity Hook",
        "share": 0.0,
        "intensity": 78,
        "attention": 88,
        "visual_intent": "Tease the payoff visually without revealing it — partial view of {subject}",
        "broll_type": "obscured / partial reveal shot",
        "caption_emphasis": "keyword highlight with ellipsis",
        "camera_style": "medium close-up",
        "motion": "slow push-in",
        "transition": "hard cut",
        "voice_direction": "lean in — conspiratorial, slightly slower",
    },
    "context": {
        "label": "Context",
        "share": 0.18,
        "intensity": 56,
        "attention": 64,
        "visual_intent": "Ground the viewer — establish what {subject} looks like before the turn",
        "broll_type": "establishing / lifestyle b-roll",
        "caption_emphasis": "standard lower-third",
        "camera_style": "medium shot",
        "motion": "static with subtle drift",
        "transition": "cross dissolve",
        "voice_direction": "steady and clear — set the scene without rushing",
    },
    "escalation": {
        "label": "Escalation",
        "share": 0.24,
        "intensity": 70,
        "attention": 74,
        "visual_intent": "Raise the stakes — faster cuts as the pattern around {subject} compounds",
        "broll_type": "dynamic action / time-lapse",
        "caption_emphasis": "keyword highlight, rising size",
        "camera_style": "dynamic handheld",
        "motion": "accelerating push-in",
        "transition": "hard cut on beat",
        "voice_direction": "build pace and volume — each sentence tighter than the last",
    },
    "evidence": {
        "label": "Evidence / Explanation",
        "share": 0.28,
        "intensity": 62,
        "attention": 68,
        "visual_intent": "Prove it — data overlays and sources on screen while explaining {subject}",
        "broll_type": "text-on-screen data overlay / archival footage",
        "caption_emphasis": "numbers and sources enlarged",
        "camera_style": "locked-off with inserts",
        "motion": "static, cut to graphic inserts",
        "transition": "graphic wipe",
        "voice_direction": "measured and authoritative — let the facts breathe",
    },
    "emotional_peak": {
        "label": "Emotional Peak",
        "share": 0.18,
        "intensity": 95,
        "attention": 90,
        "visual_intent": "The realization moment — hold on a human face as the meaning of {subject} lands",
        "broll_type": "reaction shot / slow-motion detail",
        "caption_emphasis": "bold uppercase, slow reveal",
        "camera_style": "extreme close-up",
        "motion": "slow dolly-in",
        "transition": "match cut",
        "voice_direction": "peak energy — slow down, hit the key line hard, then pause",
    },
    "resolution": {
        "label": "Resolution",
        "share": 0.12,
        "intensity": 58,
        "attention": 62,
        "visual_intent": "Release the tension — calm, satisfying visual that resolves {subject}",
        "broll_type": "wide settling shot / before-after",
        "caption_emphasis": "standard, softer color",
        "camera_style": "wide settling shot",
        "motion": "slow pull-back",
        "transition": "cross dissolve",
        "voice_direction": "warm and settled — the storm has passed",
    },
    "call_to_action": {
        "label": "Call To Action",
        "share": 0.0,
        "intensity": 66,
        "attention": 60,
        "visual_intent": "Direct address — creator or bold end-card asking for the specific action",
        "broll_type": "direct-address talking head / end card",
        "caption_emphasis": "action verb highlighted with handle",
        "camera_style": "direct-address medium close-up",
        "motion": "static, subject centered",
        "transition": "end-card fade",
        "voice_direction": "friendly and direct — one clear ask, no rush",
    },
}

# Which emotion of the variant's 5-beat arc each section expresses.
SECTION_ARC_INDEX = {
    "primary_hook": 0,
    "pattern_interrupt": 0,
    "curiosity_hook": 1,
    "context": 1,
    "escalation": 2,
    "evidence": 2,
    "emotional_peak": 3,
    "resolution": 4,
    "call_to_action": 4,
}

# Sections whose narration is generated against a word budget.
BODY_SECTIONS = tuple(key for key, spec in SECTION_SPECS.items() if spec["share"] > 0)


def _psychology_shift(psychology: dict, key: str) -> "tuple[int, int]":
    """Intensity/attention adjustments derived from the idea's ViralScore dims."""
    if not psychology:
        return 0, 0
    emotional = psychology.get("emotional_intensity", 50)
    attention = (
        psychology.get("first_3_second_hook", 50)
        if key in ("primary_hook", "pattern_interrupt", "curiosity_hook")
        else psychology.get("retention_potential", 50)
    )
    return round((emotional - 50) * 0.2), round((attention - 50) * 0.2)


def build_section(
    key: str,
    narration: str,
    *,
    subject: str,
    words_per_minute: int,
    arc: list,
    psychology: "dict | None" = None,
) -> dict:
    """Assemble one fully annotated section dict from its narration."""
    spec = SECTION_SPECS[key]
    words = len(narration.split())
    intensity_shift, attention_shift = _psychology_shift(psychology or {}, key)
    arc = arc or ["curiosity"]
    return {
        "key": key,
        "label": spec["label"],
        "narration": narration.strip(),
        "estimated_duration_sec": round(words / max(words_per_minute, 1) * 60, 1),
        "emotional_intensity": clamp(spec["intensity"] + intensity_shift, 0, 100),
        "attention_score": clamp(spec["attention"] + attention_shift, 0, 100),
        "emotion": arc[min(SECTION_ARC_INDEX[key], len(arc) - 1)],
        "visual_intent": spec["visual_intent"].format(subject=subject),
        "broll_type": spec["broll_type"],
        "caption_emphasis": spec["caption_emphasis"],
    }


def ordered_sections(sections: list) -> list:
    """Return sections sorted into canonical narrative order."""
    order = {key: index for index, key in enumerate(SCRIPT_SECTION_KEYS)}
    return sorted(sections, key=lambda s: order.get(s.get("key"), 99))
