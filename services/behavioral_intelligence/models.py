"""Data model for the Behavioral Intelligence API.

A `BehavioralIntelligenceReport` is the single, typed report object the
Psychology & Virality Engine's three modules (`engines/psychology.py`,
`engines/attention_graph.py`, `engines/threat_detection.py`) synthesize into
one contract any other engine can consume by attribute access — no reaching
into `candidate["psychology"]["curiosity_gap"]` or `candidate["attention_graph"]
["scores"]["shareability"]` required.

It is the concrete implementation of the `PsychologyReport` data object
described in `MASTER_ARCHITECTURE.md` Section 5, unifying what used to be
three independently-shaped dicts (`psychology`, `attention_graph`,
`threat_report`) into one documented schema.

Like every other model in this codebase (`services/scripts/models.py`,
`services/visual/models.py`, `services/audio/models.py`) it is a plain
dataclass that serializes to a JSON-safe dict, because the workflow context
(and everything Streamlit touches) speaks dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The thirteen 0-100 behavioral scores every report carries, in a stable,
# documented order — used by tests and docs to assert schema completeness.
SCORE_FIELDS = (
    "viral_score",
    "attention_score",
    "curiosity_score",
    "emotional_intensity",
    "novelty_score",
    "shareability_score",
    "replay_probability",
    "comment_probability",
    "retention_prediction",
    "hook_strength",
    "identity_resonance",
    "visual_interest_score",
    "narrative_tension",
)

# Every field the report exposes, including the two non-score fields
# (confidence is still a 0-100 number; recommendations is a list of strings).
REPORT_FIELDS = SCORE_FIELDS + ("confidence", "recommendations")

# Plain-English meaning of every field plus which upstream engine(s) feed it.
# This is the schema documentation requirement (Phase 4, item 2/6) made
# machine-readable so tests and README/architecture docs can stay in sync
# with the code instead of drifting.
FIELD_DESCRIPTIONS = {
    "viral_score": (
        "Overall 0-100 ViralScore blended from all 18 Psychology dimensions "
        "(engines/psychology.py::viral_score). The single best summary of "
        "raw viral potential."
    ),
    "attention_score": (
        "Overall 0-100 Attention Score blended from the 12-dimension "
        "Attention Graph (engines/attention_graph.py::attention_score). "
        "Falls back to viral_score before the Attention Graph has run for "
        "this candidate."
    ),
    "curiosity_score": (
        "How strongly the concept opens an information gap the viewer must "
        "watch to close. Sourced from the Psychology curiosity_gap dimension."
    ),
    "emotional_intensity": (
        "How charged the language is / how strong a felt reaction it "
        "provokes. Sourced from the Psychology emotional_intensity dimension."
    ),
    "novelty_score": (
        "How new, first-of-its-kind, or freshly discovered the framing "
        "reads. Sourced from the Psychology novelty dimension."
    ),
    "shareability_score": (
        "Predicted likelihood a viewer forwards this to someone. Prefers "
        "the Attention Graph's shareability dimension; falls back to "
        "Psychology's share_likelihood before the Attention Graph has run."
    ),
    "replay_probability": (
        "Predicted likelihood of a second/third watch. Prefers the "
        "Attention Graph's rewatch_probability dimension; falls back to "
        "Psychology's replay_value."
    ),
    "comment_probability": (
        "Predicted likelihood of a comment/reaction. Prefers the Attention "
        "Graph's comment_likelihood dimension; falls back to Psychology's "
        "comment_likelihood (the same underlying signal, scored once)."
    ),
    "retention_prediction": (
        "Predicted likelihood the viewer watches to the end. Sourced from "
        "the Psychology retention_potential dimension."
    ),
    "hook_strength": (
        "How likely the opening line survives the first-3-second drop-off "
        "window. Prefers the Attention Graph's first_3_second_hook "
        "dimension; falls back to the same-named Psychology dimension "
        "(identical heuristic, scored once upstream)."
    ),
    "identity_resonance": (
        "How clearly the concept names a 'type of person' the viewer can "
        "recognize themselves in. Prefers the Attention Graph's "
        "identity_signaling dimension; falls back to Psychology's "
        "audience_identity."
    ),
    "visual_interest_score": (
        "How strong the first-frame / thumbnail-worthy visual is. Blends "
        "Psychology's visual_hook_strength with the Attention Graph's "
        "visual_novelty when both are available; uses whichever one exists "
        "otherwise."
    ),
    "narrative_tension": (
        "How strong the mini story-arc / turning-point signal is. Sourced "
        "from the Attention Graph's story_tension dimension when available; "
        "before that, approximated from Psychology's surprise + "
        "dopamine_curve (the closest pre-Attention-Graph proxy)."
    ),
    "confidence": (
        "0-100 confidence in this report, not a behavioral score. Rises as "
        "more upstream signal becomes available: Psychology alone is the "
        "baseline; the Attention Graph, a Threat Report, and a generated "
        "script each add confidence. See builder.py::_confidence for the "
        "exact rule and the Extension Points doc for how a learned "
        "calibration model would replace it."
    ),
    "recommendations": (
        "Up to 5 concrete, actionable fixes for this candidate's weakest "
        "scored dimensions, plus any high-severity Threat Report fixes "
        "when a threat report is available. Never custom text to parse — "
        "always a list[str] ready to render or hand to a script/visual/"
        "audio engine as-is."
    ),
}


@dataclass
class BehavioralIntelligenceReport:
    """The unified Behavioral Intelligence report for one content candidate.

    Every score field is an int 0-100 (except `confidence`, also 0-100, and
    `recommendations`, a list of strings). Construct with `build_report()`
    from `services/behavioral_intelligence/builder.py` rather than by hand —
    this class only defines the contract's shape.
    """

    viral_score: int = 50
    attention_score: int = 50
    curiosity_score: int = 50
    emotional_intensity: int = 50
    novelty_score: int = 50
    shareability_score: int = 50
    replay_probability: int = 50
    comment_probability: int = 50
    retention_prediction: int = 50
    hook_strength: int = 50
    identity_resonance: int = 50
    visual_interest_score: int = 50
    narrative_tension: int = 50
    confidence: int = 50
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BehavioralIntelligenceReport":
        """Rebuild a report from a plain dict (e.g. `candidate["behavioral_intelligence"]`).

        Unknown keys are ignored and missing keys fall back to the
        dataclass defaults, so any engine can round-trip the report through
        the JSON-safe context dict without custom parsing.
        """
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
