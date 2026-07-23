"""Module 1 — Hook Engine V2: generate ≥5 hooks, score, pick the best.

Aligned with Script Hook strategies (curiosity, pattern interrupt, contrarian,
immediate payoff, surprise, high-energy) so Director / Script / Retention share
one creative standard without duplicating engines.
"""

from __future__ import annotations

from core.heuristics import CURIOSITY_WORDS, SURPRISE_WORDS, clamp, count_hits, has_digit
from services.scripts.hooks import choose_hook_strategy
from services.viewer_retention.models import HOOK_STYLES_V2, HookCandidate

_TEMPLATES = {
    "question": "What if everything you think you know about {subject} is incomplete?",
    "shock_statistic": "{stat} — and that number rewrites how we understand {subject}.",
    "contradiction": "Most people believe the opposite of what {subject} actually does.",
    "visual_mystery": "Look closely — this image of {subject} hides the real story.",
    "impossible_statement": "{subject} shouldn't be possible. Yet it happens every day.",
    "common_myth": "The biggest myth about {subject}? Almost everyone still believes it.",
    "immediate_payoff": "In the next 10 seconds, you'll understand {subject} better than most adults.",
    "open_loop": "There's one detail about {subject} that changes everything — stay with me.",
    "pattern_interrupt": "Stop scrolling — what you were taught about {subject} is incomplete.",
    "high_energy": "Here's the fastest way to finally get {subject} — ready?",
}

# Map Director/Script strategies → V2 template keys
_STRATEGY_TO_V2 = {
    "curiosity": "open_loop",
    "pattern_interrupt": "pattern_interrupt",
    "shock": "impossible_statement",
    "question": "question",
    "statistics": "shock_statistic",
    "contrarian": "contradiction",
    "immediate_payoff": "immediate_payoff",
    "mystery": "visual_mystery",
    "high_energy": "high_energy",
    "story": "open_loop",
    "authority": "common_myth",
    "fomo": "immediate_payoff",
    "urgency": "pattern_interrupt",
}


def _subject(candidate: dict, fallback: str = "") -> str:
    raw = str(
        candidate.get("subject")
        or candidate.get("topic")
        or candidate.get("title")
        or fallback
        or "this"
    ).strip()
    words = raw.split()
    return " ".join(words[:6]) if len(words) > 8 else raw


def _stat(candidate: dict) -> str:
    research = candidate.get("research") or {}
    for item in research.get("statistics") or []:
        text = str(item).strip()
        if text:
            return text if text.endswith((".", "!", "?")) else f"{text}."
    return "Researchers measured something nobody expected."


def score_hook_v2(text: str, style: str, psychology: dict | None = None, preferred: str = "") -> tuple[int, list[str]]:
    psychology = psychology or {}
    words = text.split()
    score = 62
    reasons: list[str] = []

    curiosity = count_hits(text, CURIOSITY_WORDS + SURPRISE_WORDS)
    if curiosity:
        score += min(20, 8 + curiosity * 4)
        reasons.append("curiosity/surprise language")
    if "?" in text:
        score += 9
        reasons.append("question tension")
    if has_digit(text) or style == "shock_statistic":
        score += 11
        reasons.append("concrete statistic signal")
    if "—" in text or ":" in text:
        score += 5
        reasons.append("dramatic pause punctuation")
    if 6 <= len(words) <= 16:
        score += 14
        reasons.append("first-3s length")
    elif len(words) <= 20:
        score += 8
        reasons.append("ideal hook length")
    elif len(words) < 5:
        score -= 8
        reasons.append("too short")
    elif len(words) > 28:
        score -= 10
        reasons.append("too long for first 3s")

    style_boost = {
        "open_loop": 10,
        "immediate_payoff": 12,
        "contradiction": 11,
        "pattern_interrupt": 12,
        "high_energy": 10,
        "visual_mystery": 8,
        "impossible_statement": 9,
        "common_myth": 9,
        "question": 9,
        "shock_statistic": 11,
        "original": 2,
    }.get(style, 0)
    score += style_boost

    if preferred and style == preferred:
        score += 14
        reasons.append(f"director preferred={preferred}")

    hook_dim = float(
        psychology.get("first_3_second_hook")
        or psychology.get("curiosity_gap")
        or 60
    )
    score += int(round((hook_dim - 50) * 0.4))

    return clamp(score, 0, 100), reasons


def generate_hook_candidates_v2(candidate: dict, *, topic: str = "") -> list[HookCandidate]:
    """At least five scored hook candidates; best-first when ranked."""
    subject = _subject(candidate, topic)
    stat = _stat(candidate)
    psych = candidate.get("psychology") or {}
    if isinstance(psych, dict) and "dimensions" in psych:
        psych = psych.get("dimensions") or psych
    psych = psych if isinstance(psych, dict) else {}

    blueprint = candidate.get("production_blueprint") or {}
    preferred_strategy = str(
        (blueprint.get("hook_strategy") or {}).get("strategy")
        or candidate.get("hook_strategy")
        or ""
    )
    preferred_v2 = _STRATEGY_TO_V2.get(preferred_strategy, preferred_strategy)

    # Ensure strategy templates exist even if models HOOK_STYLES_V2 is older
    styles = list(HOOK_STYLES_V2)
    for extra in ("pattern_interrupt", "high_energy"):
        if extra not in styles and extra in _TEMPLATES:
            styles.append(extra)

    hooks: list[HookCandidate] = []
    for style in styles:
        template = _TEMPLATES.get(style)
        if not template:
            continue
        text = template.format(subject=subject, stat=stat).strip()
        score, reasons = score_hook_v2(text, style, psych, preferred=preferred_v2)
        hooks.append(HookCandidate(style=style, text=text, score=score, reasons=reasons))

    existing = str(
        candidate.get("hook")
        or (candidate.get("structured_script") or {}).get("primary_hook")
        or ""
    ).strip()
    if existing:
        score, reasons = score_hook_v2(existing, "original", psych, preferred=preferred_v2)
        hooks.append(HookCandidate(style="original", text=existing, score=score, reasons=reasons + ["existing"]))

    hooks.sort(key=lambda h: h.score, reverse=True)
    return hooks


def select_best_hook(candidate: dict, *, topic: str = "") -> dict:
    # If Director has not chosen yet, choose now so Script + Retention stay aligned.
    if not candidate.get("hook_strategy") and not (candidate.get("production_blueprint") or {}).get("hook_strategy"):
        psych = candidate.get("psychology") or {}
        if isinstance(psych, dict) and "dimensions" in psych:
            psych = psych.get("dimensions") or psych
        competitor = (candidate.get("competitor_analysis") or {}).get("preferred_hook_styles") or []
        strategy = choose_hook_strategy(
            topic=topic or str(candidate.get("title") or ""),
            psychology=psych if isinstance(psych, dict) else {},
            competitor_hook_styles=competitor,
            niche=str(candidate.get("niche") or ""),
        )
        candidate["hook_strategy"] = strategy

    hooks = generate_hook_candidates_v2(candidate, topic=topic)
    best = hooks[0] if hooks else HookCandidate(style="open_loop", text="Stay with me.", score=70)
    return {
        "selected": best.to_dict(),
        "candidates": [h.to_dict() for h in hooks],
        "count": len(hooks),
        "strategy": candidate.get("hook_strategy") or (candidate.get("production_blueprint") or {}).get("hook_strategy"),
    }
