"""Script variant generator — builds complete, platform-aware script packages.

Given one content idea (title + hook + angle, already psychology-scored),
the generator produces several *stylistically distinct* variants — each a
full storytelling package with all thirteen required components: hook,
pattern interrupt, curiosity loop, core story, emotional progression,
retention checkpoints, call to action, SEO keywords, B-roll suggestions,
AI visual prompts, sound effects, background music style, and estimated
runtime.

Everything here is deterministic (same input → same output), so the full
Script Engine works in Demo Mode, is unit-testable without an API key, and
gives the LLM path a guaranteed-complete baseline to enhance rather than a
blank page to fail on.
"""

from __future__ import annotations

from engines.heuristics import content_words
from services.editorial import (
    MOTIVATIONAL_PROGRESSION,
    empty_story_beats,
    is_motivational_niche,
)
from services.editorial.pillars import DEFAULT_MOTIVATION_PILLARS
from services.scripts.models import ScriptVariant
from services.scripts.platforms import get_platform_spec

DEFAULT_VARIANT_COUNT = 3

# Flagship motivational archetype — Hook → Struggle → Example → Lesson → Application → Ending.
STRUGGLE_TO_ACTION_STYLE = {
    "key": "struggle_to_action",
    "label": "Struggle to Action",
    "hook": "{hook}",
    "interrupt": "If you've been stuck with {subject}, stay with this — the struggle is the point.",
    "loop": "By the end you'll have one concrete action for {subject} you can take today.",
    "arc": list(MOTIVATIONAL_PROGRESSION),
    "cta": "Do one hard thing for {subject} today. Then follow for the next lesson that builds on this.",
    "music": "low cinematic pulse that rises into quiet resolve — never overpowering speech",
    "sfx": [
        "soft ambient swell under the struggle",
        "distant storm or ocean under the example",
        "clean resolve hit on the final line",
    ],
    "motivational": True,
}

# Narrative archetypes. Each produces a structurally different telling of the
# same idea so the scorer has real alternatives to choose between.
VARIANT_STYLES = [
    {
        "key": "authority_reveal",
        "label": "Authority Reveal",
        "hook": "{hook}",
        "interrupt": "Stop scrolling — this is not what you were taught about {subject}.",
        "loop": "In a moment you'll see the one detail about {subject} almost everyone misses. First, the setup.",
        "arc": ["curiosity", "tension", "revelation", "understanding", "resolve"],
        "cta": "Follow for the next deep dive — tomorrow's video goes further into {subject}.",
        "music": "cinematic tension build with a clean resolve",
        "sfx": ["whoosh on the opening cut", "deep sub-bass hit on the reveal", "soft riser under the payoff"],
    },
    {
        "key": "story_first",
        "label": "Story First",
        "hook": "Here's a true story about {subject} that still doesn't feel real.",
        "interrupt": "And no — it doesn't end the way you think.",
        "loop": "Keep the last line of this story in mind, because it's the part that changes everything.",
        "arc": ["intrigue", "empathy", "shock", "reflection", "connection"],
        "cta": "Share this with someone who needs to hear it — then follow for the next story.",
        "music": "warm narrative underscore with a swelling finish",
        "sfx": ["vinyl stop before the twist", "heartbeat pulse in the middle act", "gentle chime on the closing line"],
    },
    {
        "key": "myth_bust",
        "label": "Myth Bust",
        "hook": "Almost everything you've heard about {subject} is wrong — and here's the proof.",
        "interrupt": "Wait — before you disagree, look at the actual data.",
        "loop": "By the end you'll know the one claim about {subject} that survives the evidence.",
        "arc": ["skepticism", "surprise", "vindication", "clarity", "confidence"],
        "cta": "Comment the myth you believed the longest — and follow so the next one doesn't fool you.",
        "music": "punchy percussive beat with hard stops on each myth",
        "sfx": ["record scratch on each myth", "buzzer on the debunk", "satisfying click on the correction"],
    },
    {
        "key": "countdown_payoff",
        "label": "Countdown Payoff",
        "hook": "There are 3 things about {subject} nobody warns you about. Number 1 is the reason you're stuck.",
        "interrupt": "Number 3 sounds harmless — it isn't.",
        "loop": "Number 1 is last for a reason. Don't skip ahead.",
        "arc": ["anticipation", "recognition", "tension", "surprise", "satisfaction"],
        "cta": "Save this so you can check all 3 later — and follow for the extended list.",
        "music": "ticking rhythmic build that drops at number one",
        "sfx": ["tick transition between items", "riser into number one", "impact hit on the final payoff"],
    },
    STRUGGLE_TO_ACTION_STYLE,
]

# For Motivation niche: lead with Struggle to Action, then Story First / Authority.
MOTIVATIONAL_VARIANT_ORDER = (
    "struggle_to_action",
    "story_first",
    "authority_reveal",
    "myth_bust",
    "countdown_payoff",
)


def _styles_for_niche(niche: str, variant_count: int) -> list:
    """Select archetype order — motivational niche prioritizes Struggle to Action."""
    by_key = {style["key"]: style for style in VARIANT_STYLES}
    if is_motivational_niche(niche):
        ordered = [by_key[key] for key in MOTIVATIONAL_VARIANT_ORDER if key in by_key]
    else:
        ordered = list(VARIANT_STYLES)
    return ordered[: max(1, variant_count)]


def _pick_pillar(idea: dict, niche: str) -> str:
    pillars = idea.get("content_pillars") or idea.get("pillars") or []
    if pillars:
        return str(pillars[0])
    if is_motivational_niche(niche):
        return DEFAULT_MOTIVATION_PILLARS[0]
    return ""


def _fact_lines(research: dict, niche: str) -> list:
    facts = list((research or {}).get("important_facts", []))
    stats = list((research or {}).get("statistics", []))
    lines = [str(item) for item in facts + stats if item]
    if not lines:
        lines = [
            f"Research in {niche.lower() or 'this field'} keeps pointing to one specific driver behind this.",
            "The pattern shows up again and again once you know what to look for.",
        ]
    return lines


def _trim_to_words(text: str, target_words: int) -> str:
    words = text.split()
    if len(words) <= target_words:
        return text
    trimmed = " ".join(words[:target_words])
    if "." in trimmed:
        return trimmed[: trimmed.rfind(".") + 1]
    return trimmed


def _motivational_story_beats(
    idea: dict,
    subject: str,
    facts: list,
    hook: str,
    pillar: str,
) -> dict:
    """Build the six required motivational beats from research-backed facts only."""
    angle = idea.get("angle", "the real work")
    fact = facts[0] if facts else (
        f"People who improve at {subject} do it through repeated, uncomfortable practice — not slogans."
    )
    fact2 = facts[1] if len(facts) > 1 else ""
    pillar_label = pillar.replace("_", " ") if pillar else subject
    beats = empty_story_beats()
    beats["hook"] = hook
    beats["struggle"] = (
        f"You've probably felt this with {subject}: you know what you should do, "
        f"and you still freeze. The struggle isn't a lack of information — it's the "
        f"weight of starting when nobody is watching."
    )
    beats["real_life_example"] = (
        f"{fact} "
        + (f"{fact2} " if fact2 else "")
        + f"That is not a motivational slogan. It is a documented pattern around {subject}."
    )
    beats["lesson"] = (
        f"The lesson behind {angle.lower()} is simple: {pillar_label} is built in private, "
        f"through responsibility you choose when it would be easier to quit."
    )
    beats["application"] = (
        f"Today, take one concrete action on {subject} that takes less than ten minutes — "
        f"then repeat it tomorrow before you negotiate with your mood."
    )
    beats["memorable_ending"] = (
        "You don't need a new personality. You need the next honest action. "
        "Get off the couch. Begin."
    )
    return beats


def _story_from_beats(beats: dict) -> str:
    order = (
        "struggle",
        "real_life_example",
        "lesson",
        "application",
        "memorable_ending",
    )
    return " ".join(str(beats.get(key, "")).strip() for key in order if beats.get(key))


def _infer_story_beats(hook: str, core_story: str, cta: str) -> dict:
    """Best-effort beat map for non-motivational archetypes (quality scoring)."""
    beats = empty_story_beats()
    sentences = [s.strip() for s in core_story.replace("?", ".").split(".") if s.strip()]
    beats["hook"] = hook
    if sentences:
        beats["struggle"] = sentences[0] + "."
    if len(sentences) > 1:
        beats["real_life_example"] = sentences[1] + "."
    if len(sentences) > 2:
        beats["lesson"] = sentences[2] + "."
    if len(sentences) > 3:
        beats["application"] = sentences[3] + "."
    else:
        beats["application"] = cta
    beats["memorable_ending"] = (sentences[-1] + ".") if sentences else cta
    return beats


def _core_story(idea: dict, subject: str, facts: list, target_words: int, style: dict) -> str:
    """Assemble a core story sized to the platform's word budget."""
    angle = idea.get("angle", "the real story")
    beats = [
        f"Here's what most people miss about {subject}: the surface story is not the real story.",
        f"{facts[0]}",
        f"That single detail reframes {angle.lower()} completely.",
    ]
    for fact in facts[1:]:
        beats.append(f"{fact}")
        beats.append("And once you see that, you can't unsee it.")
    beats.append(
        f"The practical takeaway: change one small input around {subject} and the whole pattern shifts. "
        f"Watch what happens when you apply this for just one week."
    )

    # Long-form platforms need depth; expand with reflective connective tissue
    # until we approach the word budget instead of padding with filler.
    expanders = [
        f"To understand why, walk through it step by step — because the mechanism behind {subject} is simpler than it looks.",
        "Experts who study this describe the same sequence: a small trigger, a compounding loop, and a tipping point nobody notices until it's passed.",
        f"Compare that with what you were probably taught about {subject}, and the gap explains almost every failed attempt you've seen.",
        "This is also where the data gets interesting, because the effect holds across ages, backgrounds, and skill levels.",
        f"Which raises the real question: if this is true about {subject}, what else in the {style['label'].lower()} category deserves a second look?",
    ]
    index = 0
    while len(" ".join(beats).split()) < target_words * 0.8 and index < len(expanders) * 3:
        beats.insert(-1, expanders[index % len(expanders)])
        index += 1

    return _trim_to_words(" ".join(beats), target_words)


def _motivational_broll(subject: str) -> list:
    return [
        f"Cinematic landscape under changing weather — metaphor for {subject}",
        "Slow pan across mountains, oceans, or storm clouds with subtle camera drift",
        "Documentary footage of craftsmen, athletes, or builders at work — no faces required",
        "Time-lapse of a city waking / a path being walked — progress through effort",
        "Symbolic close-ups: worn tools, training shoes, notebooks, unfinished work",
    ]


def _motivational_visual_prompts(subject: str, pillar: str) -> list:
    pillar_label = pillar.replace("_", " ") if pillar else subject
    return [
        (
            f"Edge-to-edge cinematic landscape at dawn, atmosphere of quiet resolve about {pillar_label}, "
            f"subtle push-in, photorealistic, 9:16 vertical, no text overlays"
        ),
        (
            f"Documentary-style shot of disciplined practice related to {subject}, "
            f"natural light, shallow depth of field, slow pan, no faces"
        ),
        (
            f"Symbolic imagery of responsibility and action — worn path, storm clearing over mountains, "
            f"cinematic color grade, parallax drift, ultra-detailed"
        ),
    ]


def _retention_checkpoints(runtime_sec: int, subject: str) -> list:
    """Retention re-hooks at the classic 25/50/75% drop-off points."""
    techniques = [
        ("open_loop", f"Tease the next beat: 'the next part about {subject} is the one people replay.'"),
        ("visual_switch", "Hard cut to a new visual + on-screen text to reset attention."),
        ("direct_address", "Speak to the viewer: 'if you've watched this far, this next line is for you.'"),
    ]
    checkpoints = []
    for i, (technique, line) in enumerate(techniques, start=1):
        checkpoints.append(
            {
                "time_sec": int(runtime_sec * 0.25 * i),
                "technique": technique,
                "line": line,
            }
        )
    return checkpoints


def _seo_keywords(idea: dict, subject: str, niche: str) -> list:
    keywords = list(
        dict.fromkeys(
            [word for word in subject.lower().split() if len(word) > 2]
            + content_words(idea.get("hook", ""))[:3]
            + content_words(idea.get("title", ""))[:3]
            + [niche.lower()]
        )
    )
    return [k for k in keywords if k][:10]


def _broll_suggestions(subject: str, niche: str) -> list:
    return [
        f"Close-up macro shots relating to {subject}",
        f"Archival / documentary footage that grounds the {niche.lower() or 'topic'} claim",
        "Slow push-in on a person reacting (realization moment)",
        "Overhead time-lapse to compress the 'before and after'",
        "Text-on-screen inserts for every number or statistic",
    ]


def _visual_prompts(subject: str, niche: str, style: dict) -> list:
    mood = style["arc"][0]
    return [
        (
            f"Cinematic {mood} shot of {subject}, dramatic rim lighting, shallow depth of field, "
            f"photorealistic, 9:16 vertical composition"
        ),
        (
            f"Stylized macro illustration representing {subject} in the {niche or 'general'} niche, "
            f"high contrast, single bold accent color, dark background"
        ),
        (
            f"Split-frame before/after visualization of {subject}, documentary style, "
            f"volumetric light, ultra-detailed"
        ),
    ]


def _assemble_full_script(variant: ScriptVariant) -> str:
    parts = [
        variant.hook,
        variant.pattern_interrupt,
        variant.curiosity_loop,
        variant.core_story,
        variant.call_to_action,
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def estimate_runtime_sec(full_script: str, words_per_minute: int) -> int:
    words = len(full_script.split())
    return max(1, round(words / max(words_per_minute, 1) * 60))


def finalize_variant(variant: ScriptVariant, words_per_minute: int) -> ScriptVariant:
    """(Re)assemble the full script and recompute runtime + checkpoints."""
    variant.full_script = _assemble_full_script(variant)
    variant.estimated_runtime_sec = estimate_runtime_sec(variant.full_script, words_per_minute)
    if not variant.retention_checkpoints:
        subject = variant.seo_keywords[0] if variant.seo_keywords else "this"
        variant.retention_checkpoints = _retention_checkpoints(variant.estimated_runtime_sec, subject)
    return variant


def generate_variants(
    idea: dict,
    *,
    platform: str,
    subject: str,
    niche: str,
    research: "dict | None" = None,
    variant_count: int = DEFAULT_VARIANT_COUNT,
) -> "list[ScriptVariant]":
    """Deterministically build `variant_count` complete script variants."""
    spec = get_platform_spec(platform)
    facts = _fact_lines(research or {}, niche)
    subject = subject or "this topic"
    pillar = _pick_pillar(idea, niche)
    motivational = is_motivational_niche(niche) or bool(idea.get("content_pillars"))
    variants = []

    for index, style in enumerate(_styles_for_niche(niche, variant_count)):
        hook = style["hook"].format(hook=idea.get("hook", ""), subject=subject).strip()
        hook = hook or (
            f"The hardest part of {subject} is not knowing what to do — it's doing it when you don't feel ready."
            if style.get("motivational") or motivational
            else f"What nobody tells you about {subject}."
        )
        interrupt = style["interrupt"].format(subject=subject)
        loop = style["loop"].format(subject=subject)
        cta = style["cta"].format(subject=subject)
        # The core story gets whatever word budget the framing doesn't use,
        # so total spoken words land near the platform's target runtime.
        overhead = len(" ".join((hook, interrupt, loop, cta)).split())
        story_budget = max(40, spec.target_words - overhead)

        if style.get("motivational") or (motivational and style["key"] == "struggle_to_action"):
            story_beats = _motivational_story_beats(idea, subject, facts, hook, pillar)
            core_story = _trim_to_words(_story_from_beats(story_beats), story_budget)
            broll = _motivational_broll(subject)
            visuals = _motivational_visual_prompts(subject, pillar)
        else:
            core_story = _core_story(idea, subject, facts, story_budget, style)
            story_beats = _infer_story_beats(hook, core_story, cta) if motivational else empty_story_beats()
            if motivational and story_beats:
                # Keep application concrete even on non-flagship archetypes.
                story_beats["application"] = story_beats.get("application") or (
                    f"Today, take one concrete step on {subject} before the day ends."
                )
            broll = _motivational_broll(subject) if motivational else _broll_suggestions(subject, niche)
            visuals = (
                _motivational_visual_prompts(subject, pillar)
                if motivational
                else _visual_prompts(subject, niche, style)
            )

        variant = ScriptVariant(
            variant_id=f"{style['key']}_{index + 1}",
            style=style["key"],
            style_label=style["label"],
            platform=spec.key,
            hook=hook,
            pattern_interrupt=interrupt,
            curiosity_loop=loop,
            core_story=core_story,
            emotional_progression=list(style["arc"]),
            call_to_action=cta,
            seo_keywords=_seo_keywords(idea, subject, niche),
            broll_suggestions=broll,
            visual_prompts=visuals,
            sound_effects=list(style["sfx"]),
            music_style=f"{style['music']} ({spec.tone})",
            source="heuristic",
            story_beats=story_beats,
            content_pillar=pillar,
        )
        variant.retention_checkpoints = _retention_checkpoints(spec.target_runtime_sec, subject)
        finalize_variant(variant, spec.words_per_minute)
        variants.append(variant)

    return variants
