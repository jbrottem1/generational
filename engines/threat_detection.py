"""Psychology Threat Detection engine — Phase 3: Threat Intelligence.

Where Phase 1 (`engines/psychology.py`) and Phase 2 (`engines/attention_graph.py`)
measure how strongly a concept *pulls* attention, this phase screens the
finished package (hook, script, thumbnail concept, pacing) for the failure
modes that quietly kill watch time, trust, or platform standing even when
the underlying psychology looks strong.

Ten deterministic threat detectors run on every fully-packaged idea:

- Clickbait without payoff — a strong hook that the script never resolves
- Low dopamine pacing — no tease-then-reward beats through the runtime
- Weak hooks — first-3-second opening unlikely to survive the drop-off window
- Viewer fatigue — repetitive language / thin pacing over a long runtime
- Thumbnail mismatch — thumbnail concept doesn't share language with the hook
- Predictable scripting — generic openers, low surprise/novelty
- Retention cliff risk — too few retention checkpoints for the runtime
- Platform policy risk — high-risk language or unbounded controversy
- Manipulative language — pressure tactics and absolute claims
- Repetitive content — near-duplicate of another idea in the same batch

Each idea gets a **Threat Level** (Low/Medium/High), a **Confidence %**
(how much signal backed the assessment), and a **fix recommendation** for
every dimension — surfaced as `threat_report` alongside the existing
psychology report and attention graph.

Runs after SEO (so the thumbnail concept and full script package already
exist) and before the final Quality Gate — purely additive diagnostics; it
does not alter `quality.py`'s publish-gate math.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import (
    ABSOLUTE_CLAIMS,
    GENERIC_OPENER_PHRASES,
    MANIPULATIVE_WORDS,
    PAYOFF_WORDS,
    POLICY_RISK_WORDS,
    clamp,
    content_words,
    count_hits,
    most_repeated_word,
    weighted_blend,
)
from services.behavioral_intelligence import attach_report

logger = get_logger(__name__)

THREAT_KEYS = [
    "clickbait_without_payoff",
    "low_dopamine_pacing",
    "weak_hooks",
    "viewer_fatigue",
    "thumbnail_mismatch",
    "predictable_scripting",
    "retention_cliff_risk",
    "platform_policy_risk",
    "manipulative_language",
    "repetitive_content",
]

THREAT_LABELS = {
    "clickbait_without_payoff": "Clickbait Without Payoff",
    "low_dopamine_pacing": "Low Dopamine Pacing",
    "weak_hooks": "Weak Hooks",
    "viewer_fatigue": "Viewer Fatigue",
    "thumbnail_mismatch": "Thumbnail Mismatch",
    "predictable_scripting": "Predictable Scripting",
    "retention_cliff_risk": "Retention Cliff Risk",
    "platform_policy_risk": "Platform Policy Risk",
    "manipulative_language": "Manipulative Language",
    "repetitive_content": "Repetitive Content",
}

# How much each detector contributes to the overall threat score (0-100,
# higher = riskier). Data, not code — tunable without touching detectors.
# Platform policy risk and weak hooks/cliff risk carry the most weight
# because they most directly threaten distribution and watch time. Sum == 1.0.
THREAT_WEIGHTS = {
    "clickbait_without_payoff": 0.12,
    "low_dopamine_pacing": 0.10,
    "weak_hooks": 0.12,
    "viewer_fatigue": 0.08,
    "thumbnail_mismatch": 0.08,
    "predictable_scripting": 0.10,
    "retention_cliff_risk": 0.12,
    "platform_policy_risk": 0.14,
    "manipulative_language": 0.10,
    "repetitive_content": 0.04,
}

# One concrete fix per threat — always available, surfaced for any dimension
# that crosses the flagging threshold in the report.
THREAT_FIXES = {
    "clickbait_without_payoff": (
        "Deliver on the hook's promise explicitly in the script — add a clear "
        "'here's why / here's how' payoff moment before the midpoint."
    ),
    "low_dopamine_pacing": (
        "Add 2-3 tease-then-reward beats (retention checkpoints) spaced through "
        "the script instead of one flat delivery."
    ),
    "weak_hooks": (
        "Rewrite the opening line to under 10 words with a direct question or a "
        "concrete stat landing in the first 3 seconds."
    ),
    "viewer_fatigue": (
        "Cut repeated words/phrases and vary sentence length — replace any word "
        "used more than a few times with a synonym."
    ),
    "thumbnail_mismatch": (
        "Redesign the thumbnail concept around the same keywords as the hook/title "
        "so the visual promise matches what the video delivers."
    ),
    "predictable_scripting": (
        "Remove generic openers ('in this video...') and add an unexpected twist "
        "or reversal early in the story."
    ),
    "retention_cliff_risk": (
        "Add retention checkpoints roughly every 8-10 seconds to re-hook viewers "
        "before they drop off."
    ),
    "platform_policy_risk": (
        "Soften high-risk language (violence, self-harm, illegal activity framing) "
        "and tone down the controversy angle."
    ),
    "manipulative_language": (
        "Replace absolute claims and pressure language ('act now', 'everyone') "
        "with honest, specific framing."
    ),
    "repetitive_content": (
        "Differentiate the angle and hook from other ideas in this batch so it "
        "isn't a near-duplicate."
    ),
}

# (threshold, level) — highest matching threshold wins. Sorted descending.
LEVEL_THRESHOLDS = ((65, "High"), (35, "Medium"), (0, "Low"))

# Score at/above this is considered "flagged" and surfaced in the report.
FLAG_THRESHOLD = 55


def _level_for(score: int) -> str:
    for threshold, label in LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return LEVEL_THRESHOLDS[-1][1]


def _clickbait_without_payoff(idea: dict) -> int:
    """High hook pull with no explicit resolution language in the script."""
    psychology = idea.get("psychology", {})
    hook_pull = psychology.get("curiosity_gap", 50)
    satisfaction = psychology.get("satisfaction", 50)
    body = idea.get("script") or idea.get("hook", "")
    payoff_hits = count_hits(body, PAYOFF_WORDS)
    gap = max(0, hook_pull - satisfaction)
    raw = 20 + gap * 0.6 - payoff_hits * 14
    return clamp(raw, low=5, high=95)


def _low_dopamine_pacing(idea: dict) -> int:
    """Flat delivery — low dopamine-curve signal and few reward checkpoints."""
    psychology = idea.get("psychology", {})
    dopamine = psychology.get("dopamine_curve", 50)
    checkpoints = idea.get("retention_checkpoints") or []
    checkpoint_relief = min(len(checkpoints), 3) * 8
    raw = (100 - dopamine) - checkpoint_relief
    return clamp(raw, low=5, high=95)


def _weak_hooks(idea: dict) -> int:
    """Directly inverts the first-3-second-hook psychology dimension."""
    psychology = idea.get("psychology", {})
    hook_score = psychology.get("first_3_second_hook", 50)
    return clamp(100 - hook_score, low=5, high=95)


def _viewer_fatigue(idea: dict) -> int:
    """Word repetition density plus thin pacing over a longer runtime."""
    text = idea.get("script") or idea.get("hook", "")
    _, repeat_count = most_repeated_word(text)
    word_total = len(text.split()) or 1
    repetition_ratio = repeat_count / word_total
    checkpoints = idea.get("retention_checkpoints") or []
    runtime = idea.get("estimated_runtime_sec", 0) or 0
    pacing_penalty = 20 if runtime > 20 and len(checkpoints) < 2 else 0
    raw = 15 + repetition_ratio * 260 + pacing_penalty
    return clamp(raw, low=5, high=95)


def _thumbnail_mismatch(idea: dict) -> int:
    """Keyword overlap between the thumbnail concept and the hook/title."""
    thumbnail = idea.get("thumbnail_concept", "")
    if not thumbnail:
        return 50  # no thumbnail packaged yet — neutral, insufficient data
    core_words = set(content_words(f"{idea.get('title', '')} {idea.get('hook', '')}"))
    if not core_words:
        return 40
    thumbnail_words = set(content_words(thumbnail))
    overlap_ratio = len(core_words & thumbnail_words) / len(core_words)
    raw = 80 - overlap_ratio * 90
    return clamp(raw, low=5, high=95)


def _predictable_scripting(idea: dict) -> int:
    """Generic openers plus low surprise/novelty signal."""
    text = idea.get("script") or idea.get("hook", "")
    psychology = idea.get("psychology", {})
    generic_hits = count_hits(text, GENERIC_OPENER_PHRASES)
    surprise = psychology.get("surprise", 50)
    novelty = psychology.get("novelty", 50)
    raw = 20 + generic_hits * 18 + max(0, 55 - surprise) * 0.4 + max(0, 55 - novelty) * 0.3
    return clamp(raw, low=5, high=95)


def _retention_cliff_risk(idea: dict) -> int:
    """Predicts a drop-off cliff from thin retention potential + checkpoints."""
    psychology = idea.get("psychology", {})
    retention_potential = psychology.get("retention_potential", 50)
    checkpoints = idea.get("retention_checkpoints") or []
    runtime = idea.get("estimated_runtime_sec", 0) or 0
    expected_checkpoints = 3 if runtime >= 20 else (2 if runtime >= 12 else 1)
    shortfall = max(0, expected_checkpoints - len(checkpoints))
    raw = (100 - retention_potential) * 0.6 + shortfall * 15
    return clamp(raw, low=5, high=95)


def _platform_policy_risk(idea: dict) -> int:
    """High-risk language or an uncapped controversy/fear angle."""
    text = f"{idea.get('title', '')} {idea.get('hook', '')} {idea.get('script', '')}"
    psychology = idea.get("psychology", {})
    policy_hits = count_hits(text, POLICY_RISK_WORDS)
    controversy = psychology.get("controversy", 30)
    fear = psychology.get("fear", 30)
    raw = policy_hits * 22 + max(0, controversy - 55) * 0.8 + max(0, fear - 65) * 0.4
    return clamp(raw, low=5, high=95)


def _manipulative_language(idea: dict) -> int:
    """Pressure-tactic phrases plus absolute/guaranteed-style claims."""
    text = f"{idea.get('hook', '')} {idea.get('script', '')} {idea.get('cta', '')}"
    manipulative_hits = count_hits(text, MANIPULATIVE_WORDS)
    absolute_hits = sum(1 for phrase in ABSOLUTE_CLAIMS if phrase in text.lower())
    raw = 15 + manipulative_hits * 18 + absolute_hits * 14
    return clamp(raw, low=5, high=95)


def _repetitive_content(idea: dict, batch: list) -> int:
    """Near-duplicate detection against sibling ideas in the same batch."""
    own_words = set(content_words(f"{idea.get('title', '')} {idea.get('hook', '')}"))
    if not own_words:
        return 20
    best_overlap = 0.0
    for other in batch:
        if other is idea:
            continue
        other_words = set(content_words(f"{other.get('title', '')} {other.get('hook', '')}"))
        if not other_words:
            continue
        union = own_words | other_words
        overlap = len(own_words & other_words) / len(union) if union else 0.0
        best_overlap = max(best_overlap, overlap)
    raw = best_overlap * 130
    return clamp(raw, low=5, high=90)


def score_threats(idea: dict, batch: "list | None" = None) -> dict:
    """Score one idea across all 10 threat dimensions (0-100, higher = riskier)."""
    batch = batch if batch is not None else [idea]
    return {
        "clickbait_without_payoff": _clickbait_without_payoff(idea),
        "low_dopamine_pacing": _low_dopamine_pacing(idea),
        "weak_hooks": _weak_hooks(idea),
        "viewer_fatigue": _viewer_fatigue(idea),
        "thumbnail_mismatch": _thumbnail_mismatch(idea),
        "predictable_scripting": _predictable_scripting(idea),
        "retention_cliff_risk": _retention_cliff_risk(idea),
        "platform_policy_risk": _platform_policy_risk(idea),
        "manipulative_language": _manipulative_language(idea),
        "repetitive_content": _repetitive_content(idea, batch),
    }


def overall_threat_score(threats: dict) -> int:
    """Single weighted 0-100 threat score from the 10 dimensions."""
    return weighted_blend(threats, THREAT_WEIGHTS, low=0, high=100)


def _confidence(idea: dict) -> int:
    """How much signal backed this assessment (more packaged fields = higher)."""
    signals_present = sum(
        bool(value)
        for value in (
            idea.get("script"),
            idea.get("psychology"),
            idea.get("retention_checkpoints"),
            idea.get("thumbnail_concept"),
            idea.get("cta"),
        )
    )
    return clamp(55 + signals_present * 8, low=50, high=97)


def build_flagged_threats(threats: dict) -> list:
    """Threats at/above the flag threshold, worst first, each with its fix."""
    flagged = [
        {"key": key, "label": THREAT_LABELS[key], "score": score, "fix": THREAT_FIXES[key]}
        for key, score in threats.items()
        if score >= FLAG_THRESHOLD
    ]
    return sorted(flagged, key=lambda item: item["score"], reverse=True)


def build_threat_report(idea: dict, batch: "list | None" = None) -> dict:
    """Full threat report for one idea: level, confidence, flags, fixes."""
    threats = score_threats(idea, batch)
    score = overall_threat_score(threats)
    level = _level_for(score)
    confidence = _confidence(idea)
    flagged = build_flagged_threats(threats)
    recommendations = {key: THREAT_FIXES[key] for key in threats}

    label = idea.get("title") or idea.get("hook") or "This idea"
    if flagged:
        top_names = ", ".join(item["label"] for item in flagged[:3])
        summary = (
            f"\"{label}\" — {level} threat level ({score}/100, {confidence}% confidence). "
            f"Top concerns: {top_names}."
        )
    else:
        summary = (
            f"\"{label}\" — {level} threat level ({score}/100, {confidence}% confidence). "
            "No major threats detected."
        )

    return {
        "threats": threats,
        "threat_score": score,
        "threat_level": level,
        "confidence": confidence,
        "flagged_threats": flagged,
        "recommendations": recommendations,
        "summary": summary,
    }


class ThreatDetectionEngine(Engine):
    key = "threat_detection"
    label = "Threat Detection"
    icon = "🚨"
    description = (
        "Screen every packaged idea for 10 psychology/production failure modes and "
        "produce a Threat Level (Low/Medium/High), a confidence %, and fix recommendations."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        ideas = context.get("selected_ideas", [])
        if not ideas:
            return {}

        for idea in ideas:
            idea["threat_report"] = build_threat_report(idea, ideas)
            # Final refresh: the richest version of the Behavioral
            # Intelligence report, now informed by flagged threats/fixes too.
            attach_report(idea)

        avg_score = round(sum(idea["threat_report"]["threat_score"] for idea in ideas) / len(ideas), 1)
        level_counts = {"Low": 0, "Medium": 0, "High": 0}
        for idea in ideas:
            level_counts[idea["threat_report"]["threat_level"]] += 1

        log_event(
            logger,
            "threat_detection.scanned",
            scored=len(ideas),
            average_threat_score=avg_score,
            high_threat_count=level_counts["High"],
        )
        return {
            "selected_ideas": ideas,
            "threat_detection_summary": {
                "scored": len(ideas),
                "average_threat_score": avg_score,
                "level_counts": level_counts,
            },
        }
