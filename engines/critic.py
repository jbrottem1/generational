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
from services.editorial.integrity import quote_integrity_flags

logger = get_logger(__name__)

ISSUE_PENALTY = 11

HYPE_PHRASES = (
    "crush your goals",
    "unlock your potential",
    "level up your life",
    "become unstoppable",
    "manifest",
    "hustle harder",
)


def analyze_script(hook: str, script: str, story_beats: dict | None = None) -> list:
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

    hype = [phrase for phrase in HYPE_PHRASES if phrase in lower]
    if hype:
        issues.append(f"Empty hype: replace '{hype[0]}' with a concrete struggle or action.")

    has_absolute = any(claim in lower for claim in ABSOLUTE_CLAIMS)
    if has_absolute and not (has_digit(script) or count_hits(script, AUTHORITY_WORDS)):
        issues.append("Unsupported claim: absolute statement with no data or source to back it.")

    long_sentences = [s for s in sentences(script) if len(s.split()) > 28]
    if long_sentences:
        issues.append("Poor pacing: contains a sentence over 28 words — split it up.")

    for flag in quote_integrity_flags(script):
        issues.append(flag)

    if story_beats:
        if not str(story_beats.get("struggle", "")).strip():
            issues.append("Missing struggle beat — viewers must feel understood before inspired.")
        if not str(story_beats.get("application", "")).strip():
            issues.append("Missing application beat — every production needs a concrete next action.")
        if not str(story_beats.get("memorable_ending", "")).strip():
            issues.append("Missing memorable ending — close with a line worth remembering.")

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
            issues = analyze_script(
                idea.get("hook", ""),
                idea.get("script", ""),
                story_beats=idea.get("story_beats"),
            )
            idea["critique"] = {"issues": issues, "score": critic_score(issues)}
            flagged += bool(issues)

        log_event(logger, "critic.reviewed", scripts=len(selected), flagged=flagged)
        return {"selected_ideas": selected}
