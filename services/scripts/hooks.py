"""Hook Engine — multi-style hook candidates, deterministically ranked.

Reusable educational short-form strategies (curiosity gap, pattern interrupt,
contrarian belief, immediate payoff, emotional intrigue, surprise, high-energy)
each produce one opening. Candidates are scored 0-100 and returned best-first.

Studio Director / Script Generator call `choose_hook_strategy` then bias ranking
toward that strategy for the topic — no new engines.
"""

from __future__ import annotations

from core.heuristics import (
    CURIOSITY_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    stable_jitter,
)

# Style key → (label, template). Short punches for first-3-second windows.
HOOK_STYLES = {
    "curiosity": (
        "Curiosity Gap",
        "There's one detail about {subject} almost nobody mentions.",
    ),
    "pattern_interrupt": (
        "Pattern Interrupt",
        "Stop — what you were taught about {subject} is incomplete.",
    ),
    "shock": (
        "Surprise Opening",
        "This fact about {subject} sounds fake. It isn't.",
    ),
    "question": (
        "Curiosity Question",
        "What if your mental model of {subject} has one critical flaw?",
    ),
    "fomo": (
        "Emotional Intrigue",
        "People who get {subject} right rewrite what they do next.",
    ),
    "statistics": (
        "Immediate Stat Payoff",
        "{stat} That number is the key to {subject}.",
    ),
    "contrarian": (
        "Contradict Belief",
        "Everyone repeats the same story about {subject}. They're wrong.",
    ),
    "immediate_payoff": (
        "Immediate Payoff",
        "In ten seconds you'll understand {subject} better than most adults.",
    ),
    "story": (
        "Story Intrigue",
        "A true story about {subject} still doesn't feel real.",
    ),
    "mystery": (
        "Visual Mystery",
        "Something strange is happening with {subject} — watch closely.",
    ),
    "authority": (
        "Authority Flip",
        "After the research landed, experts changed their minds on {subject}.",
    ),
    "high_energy": (
        "High-Energy Open",
        "Here's the fastest way to finally get {subject} — ready?",
    ),
    "urgency": (
        "Urgency",
        "You have a small window to get {subject} right. Most people miss it.",
    ),
}

# Psychology dims that make each strategy land harder.
STYLE_PSYCHOLOGY_AFFINITY = {
    "curiosity": ("curiosity_gap", "first_3_second_hook"),
    "pattern_interrupt": ("surprise", "first_3_second_hook"),
    "shock": ("surprise", "emotional_intensity"),
    "question": ("curiosity_gap", "comment_likelihood"),
    "fomo": ("emotional_intensity", "share_likelihood"),
    "statistics": ("information_density", "novelty"),
    "contrarian": ("controversy", "surprise"),
    "immediate_payoff": ("first_3_second_hook", "satisfaction"),
    "story": ("emotional_intensity", "satisfaction"),
    "mystery": ("curiosity_gap", "novelty"),
    "authority": ("retention_potential", "information_density"),
    "high_energy": ("first_3_second_hook", "emotional_intensity"),
    "urgency": ("fear", "first_3_second_hook"),
}

# Educational short-form preference: strategies that outperform plain narration opens.
STRATEGY_PRIORITY = (
    "immediate_payoff",
    "pattern_interrupt",
    "contrarian",
    "curiosity",
    "shock",
    "statistics",
    "mystery",
    "high_energy",
    "question",
    "story",
    "authority",
    "fomo",
    "urgency",
)


def _first_stat(research: dict) -> str:
    for item in (research or {}).get("statistics", []):
        text = str(item).strip()
        if text:
            return text if text.endswith((".", "!", "?")) else f"{text}."
    return "Researchers measured something nobody expected."


def choose_hook_strategy(
    *,
    topic: str = "",
    psychology: dict | None = None,
    competitor_hook_styles: list | None = None,
    niche: str = "",
) -> dict:
    """Pick the strongest hook strategy for this topic (Director + Script share this)."""
    psych = psychology or {}
    topic_l = f"{topic} {niche}".lower()
    preferred = list(competitor_hook_styles or [])

    # Topic heuristics — still educational, still short-form proven patterns.
    if any(w in topic_l for w in ("myth", "wrong", "actually", "really", "truth")):
        preferred = ["contrarian", "pattern_interrupt", "curiosity"] + preferred
    elif any(w in topic_l for w in ("how", "works", "made", "train", "build")):
        preferred = ["immediate_payoff", "curiosity", "high_energy"] + preferred
    elif any(w in topic_l for w in ("why", "because", "secret")):
        preferred = ["curiosity", "mystery", "question"] + preferred
    elif any(w in topic_l for w in ("% ", "percent", "number", "rate", "interest")):
        preferred = ["statistics", "shock", "immediate_payoff"] + preferred
    else:
        preferred = list(STRATEGY_PRIORITY[:4]) + preferred

    # Normalize competitor aliases → our styles
    alias = {
        "open_loop": "curiosity",
        "shock_statistic": "statistics",
        "contradiction": "contrarian",
        "common_myth": "contrarian",
        "impossible_statement": "shock",
        "visual_mystery": "mystery",
        "question": "question",
        "immediate_payoff": "immediate_payoff",
    }
    normalized: list[str] = []
    for p in preferred:
        key = alias.get(str(p), str(p))
        if key in HOOK_STYLES and key not in normalized:
            normalized.append(key)

    # Score strategies by psychology affinity
    best_key = normalized[0] if normalized else "curiosity"
    best_score = -1.0
    for key in normalized[:6] or list(STRATEGY_PRIORITY[:6]):
        dims = STYLE_PSYCHOLOGY_AFFINITY.get(key, ())
        if dims:
            affinity = sum(float(psych.get(d, 55)) for d in dims) / len(dims)
        else:
            affinity = 55.0
        # Prefer earlier educational short-form winners slightly
        priority_boost = max(0, 8 - STRATEGY_PRIORITY.index(key)) if key in STRATEGY_PRIORITY else 0
        score = affinity + priority_boost
        if score > best_score:
            best_score = score
            best_key = key

    label, template = HOOK_STYLES[best_key]
    return {
        "strategy": best_key,
        "label": label,
        "template": template,
        "rationale": f"Selected {label} for topic psych/competitor fit",
        "alternates": normalized[:5],
    }


def generate_hook_candidates(idea: dict, subject: str, research: "dict | None" = None) -> list:
    """One hook candidate per style, plus the idea's own hook if it has one."""
    subject = subject or "this topic"
    # Prefer a short, human subject phrase
    if len(subject.split()) > 8:
        subject = " ".join(subject.split()[:6])
    stat = _first_stat(research or {})
    candidates = []
    for style, (label, template) in HOOK_STYLES.items():
        text = template.format(subject=subject, hook=idea.get("hook", ""), stat=stat).strip()
        candidates.append({"style": style, "style_label": label, "text": text})
    original = str(idea.get("hook", "")).strip()
    if original:
        candidates.append({"style": "original", "style_label": "Original Idea Hook", "text": original})
    return candidates


def score_hook(candidate: dict, psychology: "dict | None" = None, preferred_strategy: str = "") -> int:
    """Deterministic 0-100 hook score, boosted by psychology and preferred strategy."""
    text = candidate["text"]
    words = text.split()
    score = 48
    if count_hits(text, CURIOSITY_WORDS + SURPRISE_WORDS):
        score += 16
    if "?" in text:
        score += 8
    if "—" in text or ":" in text or "—" in text:
        score += 5
    if has_digit(text):
        score += 8
    if len(words) <= 12:
        score += 16  # first-3-second survival
    elif len(words) <= 16:
        score += 10
    elif len(words) > 22:
        score -= 12
    if "you" in text.lower() or "your" in text.lower():
        score += 7
    # High-energy / educational openers
    if any(w in text.lower() for w in ("stop", "wrong", "actually", "ready", "ten seconds", "nobody")):
        score += 6

    if psychology:
        dims = STYLE_PSYCHOLOGY_AFFINITY.get(candidate["style"], ())
        if dims:
            affinity = sum(psychology.get(dim, 50) for dim in dims) / len(dims)
            score += round((affinity - 50) * 0.22)

    if preferred_strategy and candidate.get("style") == preferred_strategy:
        score += 12

    return clamp(score + stable_jitter(text, span=3))


def rank_hooks(
    candidates: list,
    psychology: "dict | None" = None,
    preferred_strategy: str = "",
) -> list:
    """Score every candidate and return copies sorted best-first."""
    scored = [
        dict(candidate, score=score_hook(candidate, psychology, preferred_strategy=preferred_strategy))
        for candidate in candidates
    ]
    return sorted(scored, key=lambda c: (c["score"], c["text"]), reverse=True)
