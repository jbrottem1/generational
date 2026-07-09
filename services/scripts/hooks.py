"""Hook Engine — multi-style hook candidates, deterministically ranked.

Ten hook styles (curiosity, shock, question, FOMO, statistics, contrarian,
story, mystery, authority, urgency) each produce one candidate opening line
for an idea. Candidates are scored 0-100 with the same word-bank heuristics
the Psychology Engine uses — plus a psychology bonus when the candidate's
ViralScore dimensions are available — and returned best-first.

The best hook becomes each variant's Primary Hook; the runners-up travel
with the script as `alternate_hooks` so a human (or the future Learning
Engine) can swap openings without regenerating the script.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    SURPRISE_WORDS,
    clamp,
    count_hits,
    has_digit,
    stable_jitter,
)

# Style key → (label, template). Templates only use {subject}, {hook},
# {stat} placeholders so any idea can fill them deterministically.
HOOK_STYLES = {
    "curiosity": (
        "Curiosity",
        "There's one detail about {subject} that changes everything — and almost nobody mentions it.",
    ),
    "shock": (
        "Shock",
        "What you're about to hear about {subject} sounds fake. It isn't.",
    ),
    "question": (
        "Question",
        "What if everything you believe about {subject} is built on one wrong assumption?",
    ),
    "fomo": (
        "Fear of Missing Out",
        "People who understand {subject} are quietly using it right now — before everyone else catches on.",
    ),
    "statistics": (
        "Statistics",
        "{stat} And that number is the key to {subject}.",
    ),
    "contrarian": (
        "Contrarian",
        "Everyone tells you the same thing about {subject}. Everyone is wrong.",
    ),
    "story": (
        "Story",
        "Here's a true story about {subject} that still doesn't feel real.",
    ),
    "mystery": (
        "Mystery",
        "Something strange happens with {subject} — and even the experts can't fully explain it.",
    ),
    "authority": (
        "Authority",
        "After the research on {subject} came out, the experts changed their minds. Here's why.",
    ),
    "urgency": (
        "Urgency",
        "You have a small window to get {subject} right — and most people miss it.",
    ),
}

# Psychology dimensions that make each hook style land harder. When the
# idea carries ViralScore dimensions, styles aligned with its strengths
# get a bonus so hook selection adapts to the concept's psychology.
STYLE_PSYCHOLOGY_AFFINITY = {
    "curiosity": ("curiosity_gap", "first_3_second_hook"),
    "shock": ("surprise", "emotional_intensity"),
    "question": ("curiosity_gap", "comment_likelihood"),
    "fomo": ("fear", "share_likelihood"),
    "statistics": ("information_density", "novelty"),
    "contrarian": ("controversy", "surprise"),
    "story": ("emotional_intensity", "satisfaction"),
    "mystery": ("curiosity_gap", "novelty"),
    "authority": ("retention_potential", "information_density"),
    "urgency": ("fear", "first_3_second_hook"),
}


def _first_stat(research: dict) -> str:
    for item in (research or {}).get("statistics", []):
        text = str(item).strip()
        if text:
            return text if text.endswith((".", "!", "?")) else f"{text}."
    return "The numbers behind this surprised even the researchers."


def generate_hook_candidates(idea: dict, subject: str, research: "dict | None" = None) -> list:
    """One hook candidate per style, plus the idea's own hook if it has one."""
    subject = subject or "this topic"
    stat = _first_stat(research or {})
    candidates = []
    for style, (label, template) in HOOK_STYLES.items():
        text = template.format(subject=subject, hook=idea.get("hook", ""), stat=stat).strip()
        candidates.append({"style": style, "style_label": label, "text": text})
    original = str(idea.get("hook", "")).strip()
    if original:
        candidates.append({"style": "original", "style_label": "Original Idea Hook", "text": original})
    return candidates


def score_hook(candidate: dict, psychology: "dict | None" = None) -> int:
    """Deterministic 0-100 hook score, boosted by the idea's psychology."""
    text = candidate["text"]
    words = text.split()
    score = 38
    if count_hits(text, CURIOSITY_WORDS + SURPRISE_WORDS):
        score += 14
    if "?" in text:
        score += 6
    if "—" in text or ":" in text:
        score += 4
    if has_digit(text):
        score += 6
    if len(words) <= 14:
        score += 12  # survives the first-3-second window
    elif len(words) > 24:
        score -= 10
    if "you" in text.lower():
        score += 6

    if psychology:
        dims = STYLE_PSYCHOLOGY_AFFINITY.get(candidate["style"], ())
        if dims:
            affinity = sum(psychology.get(dim, 50) for dim in dims) / len(dims)
            # Map 0-100 affinity to a -8..+8 adjustment around the midpoint.
            score += round((affinity - 50) * 0.16)

    return clamp(score + stable_jitter(text, span=4))


def rank_hooks(candidates: list, psychology: "dict | None" = None) -> list:
    """Score every candidate and return copies sorted best-first."""
    scored = [dict(candidate, score=score_hook(candidate, psychology)) for candidate in candidates]
    return sorted(scored, key=lambda c: (c["score"], c["text"]), reverse=True)
