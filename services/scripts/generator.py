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
from services.scripts.models import ScriptVariant
from services.scripts.platforms import get_platform_spec

DEFAULT_VARIANT_COUNT = 3

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
]


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

    story = " ".join(beats)
    words = story.split()
    if len(words) > target_words:
        # Trim on a sentence boundary near the budget, keeping the takeaway.
        story = " ".join(words[:target_words])
        if "." in story:
            story = story[: story.rfind(".") + 1]
    return story


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
    variants = []

    for index, style in enumerate(VARIANT_STYLES[: max(1, variant_count)]):
        hook = style["hook"].format(hook=idea.get("hook", ""), subject=subject).strip()
        hook = hook or f"What nobody tells you about {subject}."
        interrupt = style["interrupt"].format(subject=subject)
        loop = style["loop"].format(subject=subject)
        cta = style["cta"].format(subject=subject)
        # The core story gets whatever word budget the framing doesn't use,
        # so total spoken words land near the platform's target runtime.
        overhead = len(" ".join((hook, interrupt, loop, cta)).split())
        story_budget = max(40, spec.target_words - overhead)
        variant = ScriptVariant(
            variant_id=f"{style['key']}_{index + 1}",
            style=style["key"],
            style_label=style["label"],
            platform=spec.key,
            hook=hook,
            pattern_interrupt=interrupt,
            curiosity_loop=loop,
            core_story=_core_story(idea, subject, facts, story_budget, style),
            emotional_progression=list(style["arc"]),
            call_to_action=cta,
            seo_keywords=_seo_keywords(idea, subject, niche),
            broll_suggestions=_broll_suggestions(subject, niche),
            visual_prompts=_visual_prompts(subject, niche, style),
            sound_effects=list(style["sfx"]),
            music_style=f"{style['music']} ({spec.tone})",
            source="heuristic",
        )
        variant.retention_checkpoints = _retention_checkpoints(spec.target_runtime_sec, subject)
        finalize_variant(variant, spec.words_per_minute)
        variants.append(variant)

    return variants
