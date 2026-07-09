"""Workflow templates and production-type resolution (Agent 21).

Templates select which orchestrator stages to run and which are optional.
They do not redefine engine order — they filter/annotate the canonical
pipeline from `services/orchestrator/stages.py`.
"""

from __future__ import annotations

import re

from services.orchestrator.stages import (
    DISTRIBUTION_STAGES,
    STAGE_GROUPS,
    build_pipeline_plan,
)
from services.workflow_executor.models import (
    STAGE_ALIASES,
    RetryPolicy,
    WorkflowConfig,
    WorkflowStep,
    WorkflowStatus,
)

# Stages that may fail without aborting the whole run (distribution + post).
OPTIONAL_BY_DEFAULT: frozenset[str] = frozenset(
    {
        "character_universe",
        "animation",
        "optimization",
        "analytics",
        "learning",
        "brand_management",
    }
)

# Intelligence stages whose failure stops the run (unless overridden).
HARD_STOP_STAGES: frozenset[str] = frozenset(
    {
        "trend",
        "research",
        "psychology",
        "script",
        "attention",
        "visual",
        "audio",
        "refinement",
        "quality",
        "production",
        "packaging",
    }
)

PRODUCTION_TYPES = {
    "short": {
        "template": "youtube_short",
        "longform_mode": False,
        "target_platform": "youtube_shorts",
        "count": 1,
        "quality_level": "standard",
    },
    "youtube_short": {
        "template": "youtube_short",
        "longform_mode": False,
        "target_platform": "youtube_shorts",
        "count": 1,
        "quality_level": "standard",
    },
    "longform": {
        "template": "longform_video",
        "longform_mode": True,
        "target_platform": "youtube",
        "count": 1,
        "quality_level": "high",
    },
    "documentary": {
        "template": "documentary",
        "longform_mode": True,
        "target_platform": "youtube",
        "count": 1,
        "quality_level": "high",
    },
    "course": {
        "template": "course",
        "longform_mode": True,
        "target_platform": "youtube",
        "count": 3,
        "quality_level": "high",
    },
    "podcast": {
        "template": "podcast",
        "longform_mode": True,
        "target_platform": "youtube",
        "count": 1,
        "quality_level": "standard",
    },
    "animated_episode": {
        "template": "animated_episode",
        "longform_mode": True,
        "target_platform": "youtube",
        "count": 1,
        "quality_level": "high",
    },
    "campaign": {
        "template": "multi_video_campaign",
        "longform_mode": True,
        "target_platform": "youtube_shorts",
        "count": 5,
        "quality_level": "standard",
    },
    "full_production": {
        "template": "full_production",
        "longform_mode": False,
        "target_platform": "youtube_shorts",
        "count": 3,
        "quality_level": "standard",
    },
}

# Template → stages to include (empty = full canonical plan).
# skip_stages are always removed; optional_stages may degrade on failure.
TEMPLATES: dict[str, dict] = {
    "full_production": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT),
        "skip": [],
    },
    "youtube_short": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT | {"character_universe", "animation"}),
        "skip": [],
    },
    "longform_video": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT),
        "skip": [],
        "longform_mode": True,
    },
    "documentary": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT),
        "skip": [],
        "longform_mode": True,
    },
    "course": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT | {"animation"}),
        "skip": [],
        "longform_mode": True,
    },
    "podcast": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT | {"animation", "character_universe", "creative"}),
        "skip": ["animation"],
        "longform_mode": True,
    },
    "animated_episode": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT - {"animation"}),
        "skip": [],
        "longform_mode": True,
    },
    "multi_video_campaign": {
        "include": [],
        "optional": list(OPTIONAL_BY_DEFAULT),
        "skip": [],
        "longform_mode": True,
    },
    "intelligence_only": {
        "include": [
            "trend",
            "research",
            "psychology",
            "script",
            "attention",
            "visual",
            "audio",
            "refinement",
            "quality",
        ],
        "optional": [],
        "skip": [],
    },
}


def resolve_production_type(command: str, explicit: str = "") -> str:
    """Infer production type from an explicit override or the user prompt."""
    if explicit and explicit in PRODUCTION_TYPES:
        return explicit

    text = (command or "").lower()
    rules = [
        (r"\b(documentary|documentaries)\b", "documentary"),
        (r"\b(course|courses|lesson|curriculum)\b", "course"),
        (r"\b(podcast|episode series)\b", "podcast"),
        (r"\b(animated|animation|cartoon)\b", "animated_episode"),
        (r"\b(campaign|series of|multi[- ]video)\b", "campaign"),
        (r"\b(\d+)\s*[- ]?(minute|min|hour|hr)s?\b", "longform"),
        (r"\b(long[- ]?form|feature[- ]?length)\b", "longform"),
        (r"\b(short|shorts|reel|reels|tiktok)\b", "youtube_short"),
        (r"\b(45|30|60)[- ]?second\b", "youtube_short"),
    ]
    for pattern, ptype in rules:
        if re.search(pattern, text):
            # Duration heuristic: only treat as longform when minutes/hours.
            if ptype == "longform":
                match = re.search(r"(\d+)\s*[- ]?(minute|min|hour|hr)s?", text)
                if match:
                    amount = int(match.group(1))
                    unit = match.group(2)
                    if unit.startswith("hour") or unit.startswith("hr") or amount >= 3:
                        return "longform"
                    return "youtube_short"
            return ptype
    return "full_production"


def normalize_stage_name(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "_").replace("-", "_")
    return STAGE_ALIASES.get(key, key)


def _canonical_stage_plan() -> list[tuple[str, list[str]]]:
    """Full stage plan: intelligence → production → packaging → distribution → analytics."""
    plan = list(build_pipeline_plan())
    plan.append(("production", list(STAGE_GROUPS.get("production", []))))
    plan.append(("packaging", []))
    for stage in DISTRIBUTION_STAGES:
        plan.append((stage, list(STAGE_GROUPS.get(stage, []))))
    # Post-publish stages (orchestrator runners exist; not in DISTRIBUTION_STAGES).
    for stage in ("analytics", "learning"):
        plan.append((stage, list(STAGE_GROUPS.get(stage, []))))
    return plan


def build_stage_plan(config: WorkflowConfig) -> list[tuple[str, list[str], bool]]:
    """Return (stage, engine_keys, optional) triples for this config."""
    template = TEMPLATES.get(config.template, TEMPLATES["full_production"])
    include = [normalize_stage_name(s) for s in (config.stage_order or template.get("include") or [])]
    optional = {
        normalize_stage_name(s)
        for s in (config.optional_stages or template.get("optional") or [])
    }
    skip = {
        normalize_stage_name(s)
        for s in (config.skip_stages or template.get("skip") or [])
    }
    required_override = {
        normalize_stage_name(s) for s in (config.required_stages or [])
    }

    full = _canonical_stage_plan()
    if include:
        order_index = {name: i for i, (name, _) in enumerate(full)}
        selected = []
        for name in include:
            engines = STAGE_GROUPS.get(name, [])
            if name == "packaging":
                engines = []
            elif name == "production":
                engines = list(STAGE_GROUPS.get("production", [])) or engines
            # Prefer engines from the canonical plan when present.
            for pname, pengines in full:
                if pname == name:
                    engines = pengines
                    break
            selected.append((name, list(engines), order_index.get(name, 999)))
        selected.sort(key=lambda row: row[2])
        plan_rows = [(n, e) for n, e, _ in selected]
    else:
        plan_rows = full

    result: list[tuple[str, list[str], bool]] = []
    for stage, engines in plan_rows:
        if stage in skip:
            continue
        is_optional = stage in optional and stage not in required_override
        if stage in HARD_STOP_STAGES and stage not in optional:
            is_optional = False
        result.append((stage, list(engines), is_optional))
    return result


def build_workflow_steps(config: WorkflowConfig) -> list[WorkflowStep]:
    """Materialize WorkflowStep objects from config + templates."""
    policy = config.retry_policy or RetryPolicy()
    max_attempts = max(1, policy.max_retries + 1)
    steps: list[WorkflowStep] = []
    for stage, engines, optional in build_stage_plan(config):
        steps.append(
            WorkflowStep(
                stage=stage,
                engine_keys=engines,
                required=not optional,
                optional=optional,
                status=WorkflowStatus.PENDING,
                max_attempts=max_attempts,
            )
        )
    return steps


def apply_production_defaults(command: str, config: WorkflowConfig | None = None) -> WorkflowConfig:
    """Resolve production type and fill template defaults onto a config."""
    cfg = config or WorkflowConfig()
    explicit = cfg.production_type if cfg.production_type not in ("", "short") else ""
    ptype = resolve_production_type(command, explicit)
    defaults = PRODUCTION_TYPES.get(ptype, PRODUCTION_TYPES["full_production"])
    cfg.production_type = ptype

    # Apply template from production type when caller left the default template.
    if cfg.template in ("", "full_production") and defaults.get("template"):
        cfg.template = defaults["template"]

    cfg.longform_mode = bool(defaults.get("longform_mode", False) or cfg.longform_mode)
    if cfg.target_platform in ("", "youtube_shorts") and defaults.get("target_platform"):
        cfg.target_platform = defaults["target_platform"]
    if cfg.count == 3 and "count" in defaults:
        cfg.count = int(defaults["count"])
    if cfg.quality_level in ("", "standard") and defaults.get("quality_level"):
        cfg.quality_level = defaults["quality_level"]

    template_meta = TEMPLATES.get(cfg.template, TEMPLATES["full_production"])
    if template_meta.get("longform_mode"):
        cfg.longform_mode = True
    if not cfg.optional_stages:
        cfg.optional_stages = list(template_meta.get("optional", []))
    if not cfg.skip_stages:
        cfg.skip_stages = list(template_meta.get("skip", []))
    return cfg
