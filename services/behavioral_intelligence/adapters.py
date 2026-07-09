"""Reference adapters: how downstream engines consume a Behavioral Intelligence report.

Each function below takes a typed `BehavioralIntelligenceReport` — never a
raw dict — and returns a small, purpose-specific guidance dict for one
engine family. They exist so Script Generation, Visual Intelligence, and
Voice & Audio (the three consumers named in the Phase 4 brief) each have a
concrete, tested example of consuming the report entirely through typed
attribute access, with zero custom parsing of `psychology`/`attention_graph`/
`threat_report` internals.

None of these are wired into `engines/script_generation.py`,
`engines/visual_intelligence.py`, or `engines/voice_audio.py` — those
engines already work end to end and retrofitting live calls into actively
developed modules is out of scope for this API (see the "Known limitations"
note in the Phase 4 summary). They are the documented, integration-tested
seam those engines (or any future one) can call into when ready:

    from services.behavioral_intelligence import build_report
    from services.behavioral_intelligence.adapters import script_generation_guidance

    report = build_report(candidate)
    guidance = script_generation_guidance(report)
"""

from __future__ import annotations

from services.behavioral_intelligence.models import BehavioralIntelligenceReport


def script_generation_guidance(report: BehavioralIntelligenceReport) -> dict:
    """Guidance for the Script Generation Engine (`engines/script_generation.py`).

    Tells the script generator whether to lead with the curiosity gap, how
    hard to lean on the payoff, and how much narrative arc to build in.
    """
    return {
        "lead_with_curiosity_gap": report.curiosity_score >= 65,
        "needs_stronger_payoff": report.retention_prediction < 55,
        "amplify_emotional_beat": report.emotional_intensity < 55,
        "narrative_tension": report.narrative_tension,
        "confidence": report.confidence,
    }


def visual_guidance(report: BehavioralIntelligenceReport) -> dict:
    """Guidance for the Visual Intelligence Engine (`engines/visual_intelligence.py`).

    Tells the visual planner whether the concept needs a stronger first
    frame / thumbnail concept and whether to build in a mid-video reveal.
    """
    return {
        "prioritize_transformation_shot": report.visual_interest_score < 60,
        "add_reveal_moment": report.curiosity_score >= 65,
        "visual_interest_score": report.visual_interest_score,
        "confidence": report.confidence,
    }


def audio_guidance(report: BehavioralIntelligenceReport) -> dict:
    """Guidance for the Voice & Audio Engine (`engines/voice_audio.py`).

    Tells the narration/pacing planner how energetic to make the read and
    whether the hook line needs extra vocal emphasis.
    """
    return {
        "pacing": "energetic" if report.attention_score >= 65 else "measured",
        "emphasize_hook_line": report.hook_strength < 60,
        "emotional_intensity": report.emotional_intensity,
        "confidence": report.confidence,
    }
