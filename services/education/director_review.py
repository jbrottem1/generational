"""Educational Director — independent teaching-quality review stage.

Does not publish scientifically weak content merely because it is entertaining.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EducationalReview:
    passed: bool = False
    score: float = 0.0
    accuracy_score: float = 0.0
    clarity_score: float = 0.0
    sequencing_score: float = 0.0
    demonstration_score: float = 0.0
    misconception_risks: list[str] = field(default_factory=list)
    audience_level: str = "general"
    learning_payoff: str = ""
    notes: list[str] = field(default_factory=list)
    hard_fails: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_HYPE = re.compile(
    r"\b(shocking|mind[- ]?blowing|you won't believe|doctors hate|secret they don't want)\b",
    re.I,
)
_UNQUALIFIED = re.compile(
    r"\b(proves|always|never|100%|guaranteed|cures|causes cancer)\b",
    re.I,
)


def review_lesson(
    *,
    script: str = "",
    hook: str = "",
    takeaway: str = "",
    main_concept: str = "",
    beats: list[dict[str, Any]] | None = None,
    has_visual_demo: bool = False,
    sources: list[str] | None = None,
) -> EducationalReview:
    """Rule-based Educational Director review (expandable to LLM audit)."""
    text = " ".join(filter(None, [hook, script, takeaway, main_concept]))
    notes: list[str] = []
    risks: list[str] = []
    hard_fails: list[str] = []

    if not main_concept.strip() and not takeaway.strip():
        hard_fails.append("no_clear_concept_or_takeaway")
    if len(text.split()) < 25:
        hard_fails.append("script_too_short_for_lesson")
    if _HYPE.search(text):
        risks.append("empty_hype_language")
        notes.append("Replace hype with demonstration or evidence.")
    if _UNQUALIFIED.search(text) and not sources:
        risks.append("unqualified_absolute_claim")
        notes.append("Qualify absolutes or cite sources.")

    clarity = 70.0
    if hook and len(hook) < 120:
        clarity += 10.0
    if takeaway:
        clarity += 10.0
    if beats and len(beats) >= 3:
        clarity += 5.0

    accuracy = 75.0 if sources else 65.0
    if risks:
        accuracy -= 10.0 * len(risks)

    sequencing = 68.0
    if beats:
        sequencing = min(90.0, 60.0 + len(beats) * 4)

    demonstration = 55.0
    if has_visual_demo:
        demonstration += 25.0
    if "watch" in text.lower() or "look" in text.lower():
        demonstration += 5.0

    score = round((clarity + accuracy + sequencing + demonstration) / 4, 1)
    passed = not hard_fails and score >= 65.0 and accuracy >= 60.0

    return EducationalReview(
        passed=passed,
        score=score,
        accuracy_score=round(accuracy, 1),
        clarity_score=round(clarity, 1),
        sequencing_score=round(sequencing, 1),
        demonstration_score=round(demonstration, 1),
        misconception_risks=risks,
        audience_level="general",
        learning_payoff=takeaway or main_concept,
        notes=notes,
        hard_fails=hard_fails,
    )
