"""Internal Critic engine — stage 6: adversarial review of every script.

Flags weak hooks, repetition, low retention risk, boring phrasing,
unsupported claims, and poor pacing. Deterministic, so critiques are
reproducible; the revision engine consumes these findings.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import (
    ABSOLUTE_CLAIMS,
    AUTHORITY_WORDS,
    BORING_REPLACEMENTS,
    CURIOSITY_WORDS,
    clamp,
    count_hits,
    has_digit,
    most_repeated_word,
    sentences,
)

logger = get_logger(__name__)

ISSUE_PENALTY = 11


def analyze_script(hook: str, script: str) -> list:
    """Return a list of issue strings; empty list means the script is clean."""
    issues = []

    if count_hits(hook, CURIOSITY_WORDS) == 0 and "?" not in hook:
        issues.append("Weak hook: no curiosity gap or open question in the first line.")
    if len(hook.split()) > 22:
        issues.append("Weak hook: opening line is too long to land in 3 seconds.")

    word, count = most_repeated_word(script)
    if count >= 5:
        issues.append(f"Repetition: the word '{word}' appears {count} times.")

    if "you" not in script.lower():
        issues.append("Low retention: the script never addresses the viewer directly.")

    lower = script.lower()
    boring = [phrase for phrase in BORING_REPLACEMENTS if phrase.strip() and phrase in lower]
    if boring:
        issues.append(f"Boring phrasing: uses filler like '{boring[0].strip()}'.")

    has_absolute = any(claim in lower for claim in ABSOLUTE_CLAIMS)
    if has_absolute and not (has_digit(script) or count_hits(script, AUTHORITY_WORDS)):
        issues.append("Unsupported claim: absolute statement with no data or source to back it.")

    long_sentences = [s for s in sentences(script) if len(s.split()) > 28]
    if long_sentences:
        issues.append("Poor pacing: contains a sentence over 28 words — split it up.")

    return issues


def critic_score(issues: list) -> int:
    return clamp(100 - ISSUE_PENALTY * len(issues), 35, 100)


class CriticEngine(Engine):
    key = "critic"
    label = "Critic"
    icon = "🧐"
    description = "Adversarial review: hooks, repetition, retention, phrasing, claims, pacing."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        flagged = 0
        for idea in selected:
            issues = analyze_script(idea.get("hook", ""), idea.get("script", ""))
            idea["critique"] = {"issues": issues, "score": critic_score(issues)}
            flagged += bool(issues)

        log_event(logger, "critic.reviewed", scripts=len(selected), flagged=flagged)
        return {"selected_ideas": selected}
