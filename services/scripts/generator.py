"""Script variant generator — builds complete, platform-aware script packages.

Given one content idea (title + hook + angle, already psychology-scored),
the generator produces several *stylistically distinct* variants. Each
variant is built section-first: the Hook Engine picks a ranked primary hook
per variant, then the narrative body (context → escalation → evidence →
emotional peak → resolution) is written against the platform's word budget
and annotated with duration, emotional intensity, attention score, visual
intent, B-roll type, and caption emphasis per section.

The flat storytelling fields (hook, pattern_interrupt, curiosity_loop,
core_story, call_to_action, full_script) are derived from the sections, so
every pre-existing consumer — Visual Intelligence, Voice & Audio, Threat
Detection, the fallback ScriptEngine — keeps working unchanged.

Everything here is deterministic (same input → same output), so the full
Script Engine works in Demo Mode, is unit-testable without an API key, and
gives the LLM path a guaranteed-complete baseline to enhance rather than a
blank page to fail on.
"""

from __future__ import annotations

from core.heuristics import content_words
from services.scripts.hooks import choose_hook_strategy, generate_hook_candidates, rank_hooks
from services.scripts.models import Locale, ScriptVariant
from services.scripts.platforms import get_platform_spec
from services.scripts.retention import build_retention_model
from services.scripts.sections import BODY_SECTIONS, SECTION_SPECS, build_section

DEFAULT_VARIANT_COUNT = 3

# How many runner-up hooks travel with each variant as alternates.
ALTERNATE_HOOK_COUNT = 4

# Narrative archetypes. Each produces a structurally different telling of the
# same idea so the scorer has real alternatives to choose between. The
# primary hook itself comes from the Hook Engine (ranked per variant).
VARIANT_STYLES = [
    {
        "key": "authority_reveal",
        "label": "Authority Reveal",
        "interrupt": "Stop scrolling — this is not what you were taught about {subject}.",
        "loop": "In a moment you'll see the one detail about {subject} almost everyone misses. First, the setup.",
        "lens": "The experts saw this coming — the public version of the story just left it out.",
        "arc": ["curiosity", "tension", "revelation", "understanding", "resolve"],
        "cta": "Share this with someone who still believes the myth — then follow for the next deep dive on {subject}.",
        "music": "cinematic tension build with a clean resolve",
        "sfx": ["whoosh on the opening cut", "deep sub-bass hit on the reveal", "soft riser under the payoff"],
    },
    {
        "key": "story_first",
        "label": "Story First",
        "interrupt": "And no — it doesn't end the way you think.",
        "loop": "Keep the last line of this story in mind, because it's the part that changes everything.",
        "lens": "Every detail of this story is real, and the people involved never expected it to matter.",
        "arc": ["intrigue", "empathy", "shock", "reflection", "connection"],
        "cta": "Tag someone who needs this story — share it before you scroll, then follow for the next one.",
        "music": "warm narrative underscore with a swelling finish",
        "sfx": ["vinyl stop before the twist", "heartbeat pulse in the middle act", "gentle chime on the closing line"],
    },
    {
        "key": "myth_bust",
        "label": "Myth Bust",
        "interrupt": "Wait — before you disagree, look at the actual data.",
        "loop": "By the end you'll know the one claim about {subject} that survives the evidence.",
        "lens": "The myth survives because it sounds right — the data says otherwise.",
        "arc": ["skepticism", "surprise", "vindication", "clarity", "confidence"],
        "cta": "Share the myth you believed longest — tag a friend, then follow so the next one doesn't fool you.",
        "music": "punchy percussive beat with hard stops on each myth",
        "sfx": ["record scratch on each myth", "buzzer on the debunk", "satisfying click on the correction"],
    },
    {
        "key": "countdown_payoff",
        "label": "Countdown Payoff",
        "interrupt": "Number 3 sounds harmless — it isn't.",
        "loop": "Number 1 is last for a reason. Don't skip ahead.",
        "lens": "Each item builds on the last, and the order is the whole point.",
        "arc": ["anticipation", "recognition", "tension", "surprise", "satisfaction"],
        "cta": "Save and share this list — check all 3 later, then follow for the extended cut.",
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


def _fit_to_budget(beats: list, expanders: list, target_words: int) -> str:
    """Grow toward the budget with connective tissue, or shrink to fit.

    Beats are whole sentences (or short sentence groups), so the narration
    is always trimmed on sentence boundaries. The first beat is always
    kept — every section survives even the tightest short-form budget.
    """
    beats = list(beats)
    index = 0
    while len(" ".join(beats).split()) < target_words * 0.8 and index < len(expanders) * 4:
        beats.insert(-1, expanders[index % len(expanders)])
        index += 1

    picked, words = [], 0
    for beat in beats:
        beat_words = len(beat.split())
        if picked and words + beat_words > target_words * 1.3:
            break
        picked.append(beat)
        words += beat_words
    return " ".join(picked)


def _body_narrations(idea: dict, subject: str, facts: list, style: dict, budgets: dict) -> dict:
    """Write the five expandable body sections against their word budgets.

    Each draft leads with a compact beat that stands alone on tight
    short-form budgets; the remaining beats and expanders only join when
    the platform's word budget has room for them.
    """
    angle = idea.get("angle", "the real story")
    fact_pool = list(facts) or ["The pattern shows up again and again once you know what to look for."]
    first = fact_pool[0]
    rest = fact_pool[1:] or [first]

    drafts = {
        "context": [
            "Here's the context most videos skip.",
            f"On the surface, {subject} looks settled. {style['lens']}",
            f"But the surface story is not the real story, and {angle.lower()} is where it starts to crack.",
        ],
        "escalation": [
            f"Then it escalates: {first}",
            "And once that happens, the effect starts compounding — a small trigger, a loop, a tipping point.",
            f"That single detail reframes {angle.lower()} completely.",
        ],
        "evidence": [
            f"The evidence: {rest[0]}",
            *[f"{fact}" for fact in rest[1:]],
            "And once you see that, you can't unsee it.",
        ],
        "emotional_peak": [
            "This is the part that stops people.",
            f"Think about what that means for you — everything you assumed about {subject} flips in one moment, and it was there the whole time.",
        ],
        "resolution": [
            f"The fix: change one small input around {subject}.",
            "The whole pattern shifts — watch what happens when you apply this for just one week.",
        ],
    }
    expanders = {
        "context": [
            f"Compare that with what you were probably taught about {subject}, and the gap explains almost every failed attempt you've seen.",
            f"Most explanations stop at the surface, which is exactly why {subject} keeps getting misread by smart people.",
        ],
        "escalation": [
            "Experts who study this describe the same sequence: a small trigger, a compounding loop, and a tipping point nobody notices until it's passed.",
            f"To understand why, walk through it step by step — because the mechanism behind {subject} is simpler than it looks.",
        ],
        "evidence": [
            "This is also where the data gets interesting, because the effect holds across ages, backgrounds, and skill levels.",
            "Independent teams keep landing on the same result, which is rare enough in this field to take seriously.",
            f"And the numbers around {subject} stay consistent no matter who runs the study or who funds it.",
        ],
        "emotional_peak": [
            f"Which raises the real question: if this is true about {subject}, what else in your routine deserves a second look?",
            "Most people feel this moment once and never forget it — that's what makes this beat land.",
        ],
        "resolution": [
            "The practical takeaway is small on purpose — small inputs are the ones people actually keep doing.",
        ],
    }
    return {
        key: _fit_to_budget(drafts[key], expanders[key], budgets[key])
        for key in drafts
    }


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


def _split_story_for_sections(core_story: str) -> dict:
    """Distribute an unstructured core story across the five body sections.

    Used for AI-written variants that arrive with flat fields only, so they
    carry the same section architecture as heuristic variants.
    """
    parts = [s.strip() for s in core_story.replace("!", ".").replace("?", "?.").split(".") if s.strip()]
    parts = [p if p.endswith(("?", "!")) else f"{p}." for p in parts]
    if not parts:
        parts = [core_story.strip() or "The story speaks for itself."]
    n = len(parts)
    # Cut points roughly matching the body sections' word-budget shares.
    bounds = [0, max(1, round(n * 0.18)), max(2, round(n * 0.42)), max(3, round(n * 0.70)), max(4, round(n * 0.88)), n]
    bounds = sorted(min(b, n) for b in bounds)
    chunks = [" ".join(parts[bounds[i]:bounds[i + 1]]).strip() for i in range(5)]
    fallback = parts[-1]
    return {
        key: chunk or fallback
        for key, chunk in zip(("context", "escalation", "evidence", "emotional_peak", "resolution"), chunks)
    }


def _derive_flat_fields(variant: ScriptVariant) -> None:
    """Keep the legacy flat fields in sync with the section architecture."""
    by_key = {section["key"]: section for section in variant.sections}
    variant.hook = by_key.get("primary_hook", {}).get("narration", variant.hook)
    variant.pattern_interrupt = by_key.get("pattern_interrupt", {}).get("narration", variant.pattern_interrupt)
    variant.curiosity_loop = by_key.get("curiosity_hook", {}).get("narration", variant.curiosity_loop)
    variant.call_to_action = by_key.get("call_to_action", {}).get("narration", variant.call_to_action)
    body = [by_key[key]["narration"] for key in BODY_SECTIONS if key in by_key and by_key[key]["narration"]]
    if body:
        variant.core_story = " ".join(body)
    variant.full_script = " ".join(
        section["narration"] for section in variant.sections if section["narration"].strip()
    )


def _build_sections_from_flat(variant: ScriptVariant, words_per_minute: int) -> list:
    """Reconstruct the section architecture for a variant with flat fields only."""
    subject = variant.seo_keywords[0] if variant.seo_keywords else "this"
    body = _split_story_for_sections(variant.core_story)
    narrations = {
        "primary_hook": variant.hook,
        "pattern_interrupt": variant.pattern_interrupt,
        "curiosity_hook": variant.curiosity_loop,
        **body,
        "call_to_action": variant.call_to_action,
    }
    return [
        build_section(
            key,
            narration,
            subject=subject,
            words_per_minute=words_per_minute,
            arc=variant.emotional_progression,
        )
        for key, narration in narrations.items()
        if narration and narration.strip()
    ]


def estimate_runtime_sec(full_script: str, words_per_minute: int) -> int:
    words = len(full_script.split())
    return max(1, round(words / max(words_per_minute, 1) * 60))


def finalize_variant(
    variant: ScriptVariant,
    words_per_minute: int,
    psychology: "dict | None" = None,
) -> ScriptVariant:
    """(Re)assemble sections, full script, runtime, checkpoints, and retention."""
    if not variant.sections:
        variant.sections = _build_sections_from_flat(variant, words_per_minute)
    _derive_flat_fields(variant)
    variant.estimated_runtime_sec = estimate_runtime_sec(variant.full_script, words_per_minute)
    if not variant.retention_checkpoints:
        subject = variant.seo_keywords[0] if variant.seo_keywords else "this"
        variant.retention_checkpoints = _retention_checkpoints(variant.estimated_runtime_sec, subject)
    variant.retention_model = build_retention_model(variant, psychology)
    return variant


def generate_variants(
    idea: dict,
    *,
    platform: str,
    subject: str,
    niche: str,
    research: "dict | None" = None,
    variant_count: int = DEFAULT_VARIANT_COUNT,
    locale: "Locale | dict | None" = None,
) -> "list[ScriptVariant]":
    """Deterministically build `variant_count` complete script variants."""
    spec = get_platform_spec(platform)
    facts = _fact_lines(research or {}, niche)
    subject = subject or "this topic"
    psychology = idea.get("psychology") or {}
    locale_dict = Locale.from_value(locale).to_dict()

    # Director / competitor hook strategy biases which opening wins.
    preferred = str(
        (idea.get("hook_strategy") or {}).get("strategy")
        or (idea.get("production_blueprint") or {}).get("hook_strategy", {}).get("strategy")
        or ""
    )
    if not preferred:
        competitor = (idea.get("competitor_analysis") or {}).get("preferred_hook_styles") or []
        chosen = choose_hook_strategy(
            topic=str(idea.get("title") or subject),
            psychology=psychology if isinstance(psychology, dict) else {},
            competitor_hook_styles=competitor,
            niche=niche,
        )
        preferred = chosen["strategy"]
        idea["hook_strategy"] = chosen

    # The Hook Engine writes and ranks the openings once per idea; variant N
    # takes the Nth-best primary hook so variants stay stylistically distinct.
    ranked_hooks = rank_hooks(
        generate_hook_candidates(idea, subject, research),
        psychology,
        preferred_strategy=preferred,
    )

    variants = []
    for index, style in enumerate(VARIANT_STYLES[: max(1, variant_count)]):
        primary = ranked_hooks[index % len(ranked_hooks)]
        alternates = [h for h in ranked_hooks if h["text"] != primary["text"]][:ALTERNATE_HOOK_COUNT]
        interrupt = style["interrupt"].format(subject=subject)
        loop = style["loop"].format(subject=subject)
        cta = style["cta"].format(subject=subject)

        # The body gets whatever word budget the framing doesn't use, split
        # across sections by their configured shares, so total spoken words
        # land near the platform's target runtime.
        overhead = len(" ".join((primary["text"], interrupt, loop, cta)).split())
        body_budget = max(40, spec.target_words - overhead)
        total_share = sum(SECTION_SPECS[key]["share"] for key in BODY_SECTIONS)
        budgets = {
            key: max(8, int(body_budget * SECTION_SPECS[key]["share"] / total_share))
            for key in BODY_SECTIONS
        }
        body = _body_narrations(idea, subject, facts, style, budgets)

        narrations = {
            "primary_hook": primary["text"],
            "pattern_interrupt": interrupt,
            "curiosity_hook": loop,
            **body,
            "call_to_action": cta,
        }
        arc = list(style["arc"])
        sections = [
            build_section(
                key,
                narration,
                subject=subject,
                words_per_minute=spec.words_per_minute,
                arc=arc,
                psychology=psychology,
            )
            for key, narration in narrations.items()
        ]

        variant = ScriptVariant(
            variant_id=f"{style['key']}_{index + 1}",
            style=style["key"],
            style_label=style["label"],
            platform=spec.key,
            hook_style=primary["style"],
            alternate_hooks=alternates,
            sections=sections,
            emotional_progression=arc,
            seo_keywords=_seo_keywords(idea, subject, niche),
            broll_suggestions=_broll_suggestions(subject, niche),
            visual_prompts=_visual_prompts(subject, niche, style),
            sound_effects=list(style["sfx"]),
            music_style=f"{style['music']} ({spec.tone})",
            locale=locale_dict,
            source="heuristic",
        )
        variant.retention_checkpoints = _retention_checkpoints(spec.target_runtime_sec, subject)
        finalize_variant(variant, spec.words_per_minute, psychology)
        variants.append(variant)

    return variants
