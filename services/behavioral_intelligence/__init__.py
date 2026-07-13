"""Behavioral Intelligence API — a reusable service, not just a scoring engine.

Public API for turning any candidate/idea dict into one standardized,
typed `BehavioralIntelligenceReport` — the unified contract the Psychology &
Virality Engine's three modules (`engines/psychology.py`,
`engines/attention_graph.py`, `engines/threat_detection.py`) synthesize their
scores into, so every other engine reads one report shape instead of three
independently-shaped dicts:

    from services.behavioral_intelligence import build_report

    report = build_report(candidate)
    print(report.viral_score, report.hook_strength, report.recommendations)

    # Round-trip through the JSON-safe workflow context:
    from services.behavioral_intelligence import BehavioralIntelligenceReport
    report = BehavioralIntelligenceReport.from_dict(candidate["behavioral_intelligence"])

The `behavioral_intelligence` key is attached to every candidate by
`engines/psychology.py` (immediately after Psychology scoring — the earliest
point in the pipeline it's available) and refreshed by
`engines/attention_graph.py` and `engines/threat_detection.py` as their
richer data becomes available. See `builder.py` for the graceful-degradation
rules and `adapters.py` for reference examples of Script Generation, Visual
Intelligence, and Voice & Audio consuming the report.
"""

from __future__ import annotations

from services.behavioral_intelligence.adapters import (
    audio_guidance,
    script_generation_guidance,
    visual_guidance,
)
from services.behavioral_intelligence.builder import (
    FIELD_TIPS,
    attach_report,
    build_report,
)
from services.behavioral_intelligence.models import (
    FIELD_DESCRIPTIONS,
    REPORT_FIELDS,
    SCORE_FIELDS,
    BehavioralIntelligenceReport,
)

__all__ = [
    "FIELD_DESCRIPTIONS",
    "FIELD_TIPS",
    "REPORT_FIELDS",
    "SCORE_FIELDS",
    "BehavioralIntelligenceReport",
    "attach_report",
    "audio_guidance",
    "build_report",
    "script_generation_guidance",
    "visual_guidance",
]
