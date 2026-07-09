"""Shared text-analysis library — pure functions, NOT an engine.

Architecture Directive #1 (see ARCHITECTURE_DIRECTIVES.md) prohibits any
engine from importing another engine. Analysis functions that more than one
engine legitimately needs live here instead — alongside
`engines/heuristics.py`, this is the shared foundation layer every engine
may import freely.

Contents:
- `score_dimensions()` — the 18-dimension psychology scorer. Canonical home
  of the scoring model; the Psychology engine re-exports it, the Attention
  Graph engine derives its overlapping dimensions from it.
- `analyze_script()` / `critic_score()` — the adversarial script critique.
  Used by the Critic engine, the Revision engine (to re-check after
  rewriting), and the research citation service.

Everything here is deterministic and side-effect free: no context access,
no registry access, no engine imports.
"""

from __future__ import annotations

from engines.heuristics import (
    ABSOLUTE_CLAIMS,
    AUTHORITY_WORDS,
    BORING_REPLACEMENTS,
    COMMUNITY_WORDS,
    CONTROVERSY_WORDS,
    CURIOSITY_WORDS,
    EMOTION_WORDS,
    FEAR_WORDS,
    HUMOR_WORDS,
    IDENTITY_WORDS,
    NOVELTY_WORDS,
    SATISFACTION_WORDS,
    SURPRISE_WORDS,
    VISUAL_WORDS,
    clamp,
    content_words,
    count_hits,
    has_digit,
    most_repeated_word,
    sentences,
    stable_jitter,
)

# ---------------------------------------------------------------------------
# Psychology dimension scoring (canonical implementation)
# ---------------------------------------------------------------------------


def _density_score(text: str, word_count: int, jitter: int) -> int:
    """Reward a healthy content-word ratio; penalize both fluff and jargon walls."""
    if word_count == 0:
        return clamp(40 + jitter)
    ratio = len(content_words(text)) / word_count
    deviation = abs(ratio - 0.42)
    return clamp(90 - deviation * 160 + jitter)


def score_dimensions(text: str) -> dict:
    """Score a title+hook text across all 18 ViralScore dimensions (0-100)."""
    lower = text.lower()
    words = text.split()
    word_count = len(words) or 1
    jitter = stable_jitter(text)

    hook_sentences = sentences(text)
    hook_sentence = hook_sentences[0] if hook_sentences else text
    hook_words = hook_sentence.split()
    hook_punch_words = count_hits(hook_sentence, CURIOSITY_WORDS + SURPRISE_WORDS + EMOTION_WORDS)

    raw = {
        "curiosity_gap": 42 + 13 * min(count_hits(text, CURIOSITY_WORDS), 3) + (8 if "?" in text else 0),
        "emotional_intensity": 40 + 15 * min(count_hits(text, EMOTION_WORDS), 3) + (5 if "!" in text else 0),
        "surprise": 38 + 16 * min(count_hits(text, SURPRISE_WORDS), 3),
        "novelty": 40 + 15 * min(count_hits(text, NOVELTY_WORDS), 3) + (6 if has_digit(text) else 0),
        "fear": 32 + 17 * min(count_hits(text, FEAR_WORDS), 3),
        "humor": 32 + 18 * min(count_hits(text, HUMOR_WORDS), 3),
        "satisfaction": 38 + 15 * min(count_hits(text, SATISFACTION_WORDS), 3),
        "retention_potential": (
            44
            + (10 if "you" in lower else 0)
            + (10 if 8 <= word_count <= 28 else 0)
            + (6 if count_hits(text, CURIOSITY_WORDS) else 0)
        ),
        "replay_value": (
            36
            + (14 if has_digit(text) else 0)
            + 10 * min(count_hits(text, CURIOSITY_WORDS) + count_hits(text, SURPRISE_WORDS), 3)
        ),
        "comment_likelihood": (
            34
            + (14 if "?" in text else 0)
            + 12 * min(count_hits(text, CONTROVERSY_WORDS), 3)
            + (6 if count_hits(text, IDENTITY_WORDS) else 0)
        ),
        "share_likelihood": (
            38
            + 9
            * min(
                count_hits(text, CURIOSITY_WORDS)
                + count_hits(text, EMOTION_WORDS)
                + count_hits(text, SURPRISE_WORDS),
                4,
            )
            + (6 if count_hits(text, IDENTITY_WORDS) else 0)
        ),
        "controversy": 28 + 16 * min(count_hits(text, CONTROVERSY_WORDS), 3),
        "visual_hook_strength": (
            36 + 15 * min(count_hits(text, VISUAL_WORDS), 3) + (6 if has_digit(text) else 0)
        ),
        "first_3_second_hook": (
            40
            + (14 if len(hook_words) <= 12 else 0)
            + (10 if hook_sentence.strip().endswith("?") else 0)
            + (8 if hook_punch_words else 0)
        ),
        "dopamine_curve": (
            34
            + (12 if has_digit(text) else 0)
            + 10 * min(count_hits(text, CURIOSITY_WORDS) + count_hits(text, SATISFACTION_WORDS), 3)
        ),
        "audience_identity": 34 + 16 * min(count_hits(text, IDENTITY_WORDS), 3),
        "community_appeal": 34 + 15 * min(count_hits(text, COMMUNITY_WORDS), 3),
    }

    dimensions = {key: clamp(value + jitter) for key, value in raw.items()}
    # Controversy is intentionally bounded — platform safety caps how much a
    # divisive angle can move the score, even with heavy trigger-word usage.
    dimensions["controversy"] = clamp(raw["controversy"] + jitter, high=75)
    dimensions["information_density"] = _density_score(text, word_count, jitter)

    return dimensions


# ---------------------------------------------------------------------------
# Script critique (canonical implementation)
# ---------------------------------------------------------------------------

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
