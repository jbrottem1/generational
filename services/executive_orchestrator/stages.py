"""Executive production stages — dashboard labels and engine groups."""

from __future__ import annotations

from typing import Any

# Ordered studio stages shown on the live dashboard
EXECUTIVE_STAGES: tuple[str, ...] = (
    "discovery",
    "research",
    "direction",
    "script",
    "evidence",
    "visuals",
    "animation",
    "voice",
    "assembly",
    "qa",
    "export",
    "publishing",
)

STAGE_LABELS = {
    "discovery": "Discovery",
    "research": "Research",
    "direction": "Direction",
    "script": "Script",
    "evidence": "Evidence",
    "visuals": "Visuals",
    "animation": "Animation",
    "voice": "Voice",
    "assembly": "Assembly",
    "qa": "QA",
    "export": "Export",
    "publishing": "Publishing",
}

# Engine keys executed per stage (WorkflowEngine). Empty = service-side step.
STAGE_ENGINES: dict[str, list[str]] = {
    "discovery": ["discovery"],
    "research": [
        "continuous_learning",
        "trend_discovery",
        "opportunity_ranking",
        "trend_forecasting",
        "market_intelligence",
        "research",
        "ideation",
        "psychology",
        "audience_intelligence",
    ],
    "direction": ["ai_director"],
    "script": [
        "script_generation",
        "attention_graph",
        "ranking",
        "script",
        "critic",
        "revision",
        "citation",
        "seo",
        "threat_detection",
        "quality",
    ],
    "evidence": ["evidence_intelligence"],
    "visuals": ["visual_intelligence"],
    "animation": ["cinematography", "viewer_retention", "animation"],  # animation may skip if FutureEngine
    "voice": ["voice_audio", "voice"],
    "assembly": ["image", "video", "scene_planning", "narration", "visual_planning", "asset_manager", "subtitle", "timeline", "render_package", "studio_render"],
    "qa": ["production_qa"],
    "export": ["optimization_lab"],
    "publishing": ["publishing_queue", "scheduler", "publishing"],
}

# Rough ETA seconds for dashboard "estimated remaining" (planning hints)
STAGE_ETA_SEC: dict[str, int] = {
    "discovery": 25,
    "research": 40,
    "direction": 20,
    "script": 35,
    "evidence": 30,
    "visuals": 35,
    "animation": 40,
    "voice": 45,
    "assembly": 90,
    "qa": 15,
    "export": 20,
    "publishing": 15,
}

StageStatusName = str  # pending | running | completed | failed | skipped


def stage_plan() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": STAGE_LABELS[key],
            "engines": list(STAGE_ENGINES.get(key) or []),
            "eta_sec": STAGE_ETA_SEC.get(key, 30),
        }
        for key in EXECUTIVE_STAGES
    ]


def remaining_eta_sec(statuses: dict[str, str]) -> int:
    total = 0
    for key in EXECUTIVE_STAGES:
        st = statuses.get(key, "pending")
        if st in ("pending", "running"):
            total += STAGE_ETA_SEC.get(key, 30)
    return total
