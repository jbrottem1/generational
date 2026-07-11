"""RetentionReview scorer — evaluates completed scripts on 7 dimensions + overall.

Each dimension is scored 0-100. The overall score is a weighted composite.
A list of specific, actionable revision notes is returned alongside the scores.
"""

from __future__ import annotations

from services.episode_design.models import RETENTION_SCORE_FIELDS, STRATEGIC_DESIGN_QUESTIONS

# Weights for the weighted composite overall score.
_DIMENSION_WEIGHTS: dict[str, float] = {
    "curiosity_score": 0.20,
    "teaching_clarity_score": 0.18,
    "visual_opportunity_score": 0.12,
    "emotional_engagement_score": 0.15,
    "educational_payoff_score": 0.15,
    "ending_strength_score": 0.10,
    "overall_flow_score": 0.10,
}


def _score_curiosity(item: dict) -> tuple[int, list[str]]:
    """Does the hook create genuine urgency to keep watching?"""
    revisions: list[str] = []
    hook = str(item.get("hook") or "")
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")

    score = 50  # baseline

    if hook and len(hook) >= 10:
        score += 20
    else:
        revisions.append(
            "Opening hook is missing or too short. Add a 1-2 sentence curiosity hook "
            "that challenges what the viewer already thinks they know."
        )

    if hook and "?" in hook:
        score += 10
    elif not ("?" in script[:200] if script else False):
        revisions.append(
            "No question in the opening. The first 7 seconds should pose a question "
            "the viewer feels compelled to answer."
        )

    # Check if script opens with the hook (vs. a slow intro)
    if script and hook and script.strip()[:60].lower() in hook.lower()[:60].lower():
        score += 10
    elif script and len(script.split()) > 10:
        words = script.split()
        if words[0].lower() in ("hello", "hi", "welcome", "today", "in this"):
            score -= 15
            revisions.append(
                "Script opens with a weak greeting/intro ('Hello', 'Welcome', 'Today we…'). "
                "Cut to the hook immediately — no warm-up."
            )

    return min(max(score, 0), 100), revisions


def _score_teaching_clarity(item: dict) -> tuple[int, list[str]]:
    """Is the explanation layered, clear, and jargon-free?"""
    revisions: list[str] = []
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")
    quality_score = int(item.get("quality_score") or 0)

    score = 55  # baseline

    if quality_score >= 75:
        score += 20
    elif quality_score >= 50:
        score += 10
    elif quality_score > 0:
        score -= 10
        revisions.append(
            "Quality score is low — review the explanation for clarity. "
            "Use a simple → complex layering: state the simple model first, "
            "then add depth."
        )

    word_count = len(script.split()) if script else 0
    if word_count > 0:
        # Educational scripts should aim for ~120-180 words for 49s
        if 80 <= word_count <= 220:
            score += 15
        elif word_count > 300:
            score -= 10
            revisions.append(
                f"Script is long ({word_count} words) for a short-form episode. "
                "Trim to 120-180 words; every sentence must earn its place."
            )
        elif word_count < 40:
            score -= 15
            revisions.append(
                f"Script is very short ({word_count} words). Ensure the explanation beat "
                "covers all three layers: simple model → mechanism → insight."
            )

    return min(max(score, 0), 100), revisions


def _score_visual_opportunity(item: dict) -> tuple[int, list[str]]:
    """Are there rich visual/demonstration moments?"""
    revisions: list[str] = []
    visual_pkg = item.get("visual_package") or {}
    scenes = visual_pkg.get("scenes") or []
    script_pkg = item.get("script_package") or {}
    scene_breakdown = item.get("scene_breakdown") or script_pkg.get("scene_breakdown") or []

    score = 50

    scene_count = len(scenes) + len(scene_breakdown)
    if scene_count >= 4:
        score += 25
    elif scene_count >= 2:
        score += 12
    else:
        revisions.append(
            "No scene breakdown or visual plan detected. "
            "Map at least one visual demonstration moment per beat. "
            "The demonstration beat (7-17s) must have a concrete visual proof."
        )

    script = str(item.get("script") or script_pkg.get("script") or "")
    visual_cues = sum(
        1 for kw in ("show", "visualize", "imagine", "picture", "look at", "see", "watch")
        if kw in script.lower()
    )
    if visual_cues >= 3:
        score += 15
    elif visual_cues == 0 and script:
        revisions.append(
            "Script lacks visual cue language ('show', 'watch', 'picture this'). "
            "Add at least one explicit visual direction per major beat."
        )

    return min(max(score, 0), 100), revisions


def _score_emotional_engagement(item: dict) -> tuple[int, list[str]]:
    """Does the episode make the viewer feel something?"""
    revisions: list[str] = []
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")
    psych_score = int(item.get("psychology_score") or 0)

    score = 50

    if psych_score >= 75:
        score += 25
    elif psych_score >= 50:
        score += 12
    elif psych_score > 0:
        revisions.append(
            "Psychology score suggests limited emotional resonance. "
            "Add a moment of awe, surprise, or personal relevance — "
            "the viewer should feel something, not just learn something."
        )

    emotional_words = (
        "surprising", "incredible", "shocking", "amazing", "discover",
        "secret", "nobody knows", "most people", "you probably", "imagine",
        "actually", "turns out", "believe it or not", "counterintuitive",
    )
    hits = sum(1 for w in emotional_words if w in script.lower())
    if hits >= 3:
        score += 15
    elif hits == 0 and script:
        score -= 10
        revisions.append(
            "Script lacks emotional language. Add a moment of genuine surprise or wonder — "
            "a fact that challenges intuition or reveals something hidden."
        )

    return min(max(score, 0), 100), revisions


def _score_educational_payoff(item: dict) -> tuple[int, list[str]]:
    """Does the episode deliver genuine learning value?"""
    revisions: list[str] = []
    quality_score = int(item.get("quality_score") or 0)
    research = item.get("research_package") or item.get("research") or {}
    has_research = bool(research)

    score = 55

    if quality_score >= 80:
        score += 25
    elif quality_score >= 60:
        score += 12
    elif quality_score > 0:
        revisions.append(
            "Quality gate score suggests the educational content needs strengthening. "
            "Ensure the explanation beat delivers: (1) the simple model, "
            "(2) why it works, (3) a real-world anchor."
        )

    if has_research:
        score += 10
    else:
        revisions.append(
            "No research package detected. Strong educational payoff requires "
            "at least one surprising cited fact or evidence-backed claim."
        )

    return min(max(score, 0), 100), revisions


def _score_ending_strength(item: dict) -> tuple[int, list[str]]:
    """Does the ending land emotionally + tease the next episode?"""
    revisions: list[str] = []
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")

    score = 50

    if script:
        last_200 = script[-200:].lower()
        has_tease = any(
            kw in last_200
            for kw in ("next", "part", "coming up", "episode", "tomorrow", "what if", "?")
        )
        if has_tease:
            score += 20
        else:
            revisions.append(
                "Ending does not tease the next episode or leave an open curiosity gap. "
                "Add a 2s bridge beat: one unanswered question that makes them want to watch more."
            )

        has_takeaway = any(
            kw in last_200
            for kw in ("remember", "key", "takeaway", "bottom line", "lesson", "insight", "know now")
        )
        if has_takeaway:
            score += 20
        else:
            revisions.append(
                "The powerful takeaway beat may be missing. "
                "Distil the episode into one memorable, shareable sentence before the bridge."
            )

    return min(max(score, 0), 100), revisions


def _score_overall_flow(item: dict) -> tuple[int, list[str]]:
    """Does pacing feel natural from start to finish?"""
    revisions: list[str] = []
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")

    score = 60

    if script:
        sentences = [s.strip() for s in script.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_len <= 15:
                score += 20  # short punchy sentences = good pacing
            elif avg_len > 25:
                score -= 10
                revisions.append(
                    f"Average sentence length is long ({avg_len:.0f} words). "
                    "Short-form educational content works best with sentences under 15 words. "
                    "Break long sentences into punchy, standalone beats."
                )

        # Check for a variety of sentence lengths (rhythm)
        lengths = [len(s.split()) for s in sentences]
        if len(lengths) >= 3:
            variance = max(lengths) - min(lengths)
            if variance >= 5:
                score += 10  # good rhythm variety

    return min(max(score, 0), 100), revisions


def _answer_strategic_questions(item: dict) -> dict:
    """Answer the six strategic design questions for this item."""
    topic = str(item.get("topic") or item.get("title") or "this topic")
    hook = str(item.get("hook") or "")
    script = str(item.get("script") or item.get("script_package", {}).get("script") or "")
    niche = str(item.get("niche") or "general")

    return {
        "why_care": (
            f"'{topic}' falls in the '{niche}' niche, which means viewers care because "
            "it connects to their curiosity, identity, or practical life. "
            "Establish the personal stakes in the first 7 seconds."
        ),
        "whats_surprising": (
            f"Identify the most counterintuitive fact or mechanism in '{topic}'. "
            "This is the element that makes viewers say 'I didn't know that' — "
            "it should anchor the interesting_question and explanation beats."
        ),
        "what_first": (
            (f"Hook detected: '{hook[:80]}…'" if hook else f"No hook detected for '{topic}'.") +
            " The first frame should be the most arresting visual or audio element. "
            "Cut straight to action — no intro, no title card."
        ),
        "biggest_reveal": (
            f"The biggest reveal for '{topic}' should land in the final third of the "
            "explanation beat (approx. 27-32s). Build tension through the demonstration "
            "and early explanation layers, then deliver the mechanism or insight."
        ),
        "where_pause": (
            "Natural pause points: (1) after the interesting_question — let the viewer "
            "sit with the question for 0.5s before demonstrating; "
            "(2) after the biggest reveal in the explanation beat — "
            "slow narration pace, hold the visual."
        ),
        "how_end": (
            "End with the powerful_takeaway at full emotional weight (music swell, "
            "text on screen), then immediately open a new curiosity gap in the 2s bridge. "
            "The viewer should feel rewarded AND hungry for more."
        ),
    }


def build_retention_review(item: dict, blueprint: dict | None = None) -> dict:
    """Full RetentionReview for one content item.

    Scores each dimension 0-100, computes a weighted overall score,
    and returns a list of specific, actionable revision notes.
    """
    scorers = [
        ("curiosity_score", _score_curiosity),
        ("teaching_clarity_score", _score_teaching_clarity),
        ("visual_opportunity_score", _score_visual_opportunity),
        ("emotional_engagement_score", _score_emotional_engagement),
        ("educational_payoff_score", _score_educational_payoff),
        ("ending_strength_score", _score_ending_strength),
        ("overall_flow_score", _score_overall_flow),
    ]

    scores: dict[str, int] = {}
    all_revisions: list[str] = []

    for key, fn in scorers:
        s, revisions = fn(item)
        scores[key] = s
        all_revisions.extend(revisions)

    # Weighted composite
    overall = int(round(sum(
        scores[k] * w for k, w in _DIMENSION_WEIGHTS.items()
    )))
    scores["overall_score"] = min(max(overall, 0), 100)

    strategic_answers = _answer_strategic_questions(item)

    return {
        "scores": scores,
        "revision_count": len(all_revisions),
        "revisions": all_revisions,
        "strategic_answers": strategic_answers,
        "score_breakdown": {
            k: {"score": scores[k], "weight": _DIMENSION_WEIGHTS.get(k, 0)}
            for k in RETENTION_SCORE_FIELDS
        },
    }
