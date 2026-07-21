"""Production Operations — 16-stage studio map onto existing engines only."""

from __future__ import annotations

from typing import Any

# Ordered Agent-0 ops stages. Engines are existing registry keys — never new agents.
OPERATIONS_STAGES: tuple[dict[str, Any], ...] = (
    {
        "key": "research",
        "label": "Research Engine",
        "engines": ["research", "ideation"],
        "critical": False,
        "max_retries": 2,
    },
    {
        "key": "psychology",
        "label": "Psychology Engine",
        "engines": ["psychology"],
        "critical": False,
        "max_retries": 2,
    },
    {
        "key": "studio_director",
        "label": "AI Studio Director",
        "engines": ["ai_director"],
        "critical": False,
        "max_retries": 2,
    },
    {
        "key": "script_generator",
        "label": "Script Generator",
        "engines": ["script_generation"],
        "critical": False,
        "max_retries": 2,
    },
    {
        "key": "scene_builder",
        "label": "Scene Builder",
        "engines": ["visual_intelligence", "scene_planning", "visual_planning"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "media_collection",
        "label": "Media Collection",
        "engines": ["evidence_intelligence", "image", "asset_manager"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "animation",
        "label": "Animation / Motion Graphics",
        "engines": ["cinematography", "animation"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "voice_generation",
        "label": "Voice Generation",
        "engines": ["voice_audio", "narration", "voice"],
        "critical": False,
        "max_retries": 2,
    },
    {
        "key": "music_sound",
        "label": "Music & Sound Design",
        "engines": [],  # filled from director / voice_audio packages (no duplicate engine)
        "critical": False,
        "max_retries": 0,
        "service_step": "apply_music_direction",
    },
    {
        "key": "captions",
        "label": "Captions",
        "engines": ["subtitle"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "rendering",
        "label": "Rendering",
        "engines": ["timeline", "render_package", "studio_render", "video"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "viewer_retention",
        "label": "Viewer Retention Analysis",
        "engines": ["viewer_retention"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "optimization_lab",
        "label": "Optimization Lab",
        "engines": ["optimization_lab"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "quality_assurance",
        "label": "Quality Assurance",
        "engines": ["quality", "production_qa"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "seo_package",
        "label": "SEO Package",
        "engines": ["seo", "seo_optimization"],
        "critical": False,
        "max_retries": 1,
    },
    {
        "key": "export",
        "label": "Export",
        "engines": [],
        "critical": False,
        "max_retries": 1,
        "service_step": "export_and_validate",
    },
)

STAGE_KEYS: tuple[str, ...] = tuple(s["key"] for s in OPERATIONS_STAGES)

# Platforms the ops layer is future-proofed for (aliases map into engine/platform keys).
SUPPORTED_PLATFORMS: tuple[str, ...] = (
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook_reels",
    "x",
    "linkedin",
    "youtube_long",
    "podcast",
    "course",
    "documentary",
)


def flat_engine_order() -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for stage in OPERATIONS_STAGES:
        for key in stage.get("engines") or []:
            if key not in seen:
                ordered.append(key)
                seen.add(key)
    return ordered
