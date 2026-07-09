"""Production mode resolution for Autonomous Production Executor (Agent 23).

Maps user prompts / explicit modes onto WorkflowExecutor production types
and templates. Does not redefine orchestrator stage order.
"""

from __future__ import annotations

import re

from services.workflow_executor.templates import (
    PRODUCTION_TYPES as WF_PRODUCTION_TYPES,
    resolve_production_type,
)

# Public production modes (mission surface).
PRODUCTION_MODES: dict[str, dict] = {
    "single_video": {
        "workflow_production_type": "youtube_short",
        "label": "Single Video",
        "longform": False,
        "unit_count": 1,
        "parallel_units": False,
    },
    "video_series": {
        "workflow_production_type": "campaign",
        "label": "Video Series",
        "longform": True,
        "unit_count": 5,
        "parallel_units": True,
    },
    "podcast": {
        "workflow_production_type": "podcast",
        "label": "Podcast",
        "longform": True,
        "unit_count": 1,
        "parallel_units": False,
    },
    "course": {
        "workflow_production_type": "course",
        "label": "Course",
        "longform": True,
        "unit_count": 3,
        "parallel_units": True,
    },
    "marketing_campaign": {
        "workflow_production_type": "campaign",
        "label": "Marketing Campaign",
        "longform": True,
        "unit_count": 5,
        "parallel_units": True,
    },
    "documentary": {
        "workflow_production_type": "documentary",
        "label": "Documentary",
        "longform": True,
        "unit_count": 1,
        "parallel_units": False,
    },
    "animated_story": {
        "workflow_production_type": "animated_episode",
        "label": "Animated Story",
        "longform": True,
        "unit_count": 1,
        "parallel_units": False,
    },
    "audiobook": {
        "workflow_production_type": "longform",
        "label": "Audiobook",
        "longform": True,
        "unit_count": 1,
        "parallel_units": False,
        "skip_stages": ["animation", "character_universe"],
    },
    "educational_program": {
        "workflow_production_type": "course",
        "label": "Educational Program",
        "longform": True,
        "unit_count": 4,
        "parallel_units": True,
    },
    "full_production": {
        "workflow_production_type": "full_production",
        "label": "Full Production",
        "longform": False,
        "unit_count": 3,
        "parallel_units": False,
    },
}

# Prompt → mode heuristics (checked before workflow type inference).
_MODE_RULES: list[tuple[str, str]] = [
    (r"\b(audiobook|audio[- ]?book)\b", "audiobook"),
    (r"\b(educational\s+program|curriculum|training\s+program)\b", "educational_program"),
    (r"\b(children'?s?\s+animated|animated\s+story|cartoon\s+story)\b", "animated_story"),
    (r"\b(marketing\s+campaign|ad\s+campaign|promo\s+campaign)\b", "marketing_campaign"),
    (r"\b(video\s+series|series\s+of\s+videos|episode\s+series)\b", "video_series"),
    (r"\b(documentary|documentaries)\b", "documentary"),
    (r"\b(course|courses|lesson)\b", "course"),
    (r"\b(podcast)\b", "podcast"),
    (r"\b(animated|animation|cartoon)\b", "animated_story"),
    (r"\b(campaign)\b", "marketing_campaign"),
    (r"\b(short|shorts|reel|reels|tiktok|45[- ]?second|30[- ]?second)\b", "single_video"),
]


def resolve_production_mode(command: str, explicit: str = "") -> str:
    """Infer production mode from an explicit override or the user prompt."""
    if explicit and explicit in PRODUCTION_MODES:
        return explicit
    text = (command or "").lower()
    for pattern, mode in _MODE_RULES:
        if re.search(pattern, text):
            return mode
    # Fall back through WorkflowExecutor type → mode.
    wf_type = resolve_production_type(command)
    reverse = {
        "youtube_short": "single_video",
        "short": "single_video",
        "documentary": "documentary",
        "course": "course",
        "podcast": "podcast",
        "animated_episode": "animated_story",
        "campaign": "marketing_campaign",
        "longform": "documentary",
        "full_production": "full_production",
    }
    return reverse.get(wf_type, "full_production")


def mode_defaults(mode: str) -> dict:
    return dict(PRODUCTION_MODES.get(mode, PRODUCTION_MODES["full_production"]))


def workflow_type_for_mode(mode: str) -> str:
    defaults = mode_defaults(mode)
    wf = defaults.get("workflow_production_type", "full_production")
    if wf not in WF_PRODUCTION_TYPES:
        return "full_production"
    return wf


def detect_content_duration_sec(command: str) -> float:
    """Best-effort content duration from the prompt (not wall-clock runtime)."""
    text = (command or "").lower()
    hour = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?(hour|hr)s?\b", text)
    if hour:
        return float(hour.group(1)) * 3600.0
    minute = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?(minute|min)s?\b", text)
    if minute:
        return float(minute.group(1)) * 60.0
    second = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?seconds?\b", text)
    if second:
        return float(second.group(1))
    mode = resolve_production_mode(command)
    defaults = {
        "single_video": 45.0,
        "podcast": 1800.0,
        "documentary": 900.0,
        "course": 2400.0,
        "audiobook": 7200.0,
        "animated_story": 600.0,
        "video_series": 300.0,
        "marketing_campaign": 60.0,
        "educational_program": 3600.0,
    }
    return float(defaults.get(mode, 180.0))


def build_chapters(command: str, mode: str, *, unit_count: int = 0) -> list[dict]:
    """Chapter plan for long-form / multi-unit productions."""
    defaults = mode_defaults(mode)
    count = unit_count or int(defaults.get("unit_count", 1))
    longform = bool(defaults.get("longform", False))
    duration = detect_content_duration_sec(command)

    if mode in ("course", "educational_program") or (longform and count > 1):
        chapters = []
        per = duration / max(count, 1) if duration else 0.0
        for i in range(count):
            chapters.append(
                {
                    "index": i,
                    "title": f"Chapter {i + 1}",
                    "command": f"{command} — part {i + 1} of {count}",
                    "estimated_duration_sec": round(per, 1),
                    "status": "pending",
                }
            )
        return chapters

    if longform and duration >= 600:
        # Single long-form: split into scene groups / chapters by ~5 min.
        chunk = 300.0
        n = max(1, int(round(duration / chunk)))
        chapters = []
        for i in range(n):
            chapters.append(
                {
                    "index": i,
                    "title": f"Segment {i + 1}",
                    "command": command,
                    "estimated_duration_sec": round(duration / n, 1),
                    "status": "pending",
                    "partial_render": True,
                }
            )
        return chapters

    return [
        {
            "index": 0,
            "title": "Main",
            "command": command,
            "estimated_duration_sec": duration,
            "status": "pending",
        }
    ]


def build_scene_groups(chapters: list[dict]) -> list[dict]:
    """Group chapters into scene groups for incremental checkpoints."""
    groups = []
    for ch in chapters:
        groups.append(
            {
                "group_id": f"sg_{ch.get('index', 0)}",
                "chapter_index": ch.get("index", 0),
                "title": ch.get("title", ""),
                "status": "pending",
            }
        )
    return groups
