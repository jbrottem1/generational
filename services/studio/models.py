"""Studio data models — platforms, pipeline stages, and production settings."""

from __future__ import annotations

STUDIO_PIPELINE_STAGES = [
    {"key": "research", "label": "Research", "icon": "🔬", "orchestrator_keys": ("research", "trend")},
    {"key": "script", "label": "Script", "icon": "📝", "orchestrator_keys": ("script", "psychology", "attention")},
    {"key": "creative_studio", "label": "Creative Studio", "icon": "🎨", "orchestrator_keys": ("creative", "ai_director")},
    {"key": "asset_generation", "label": "Asset Generation", "icon": "🖼️", "orchestrator_keys": ("asset_generation",)},
    {"key": "animation", "label": "Animation", "icon": "🎬", "orchestrator_keys": ("animation",)},
    {"key": "voice", "label": "Voice", "icon": "🎙️", "orchestrator_keys": ("voice_audio", "voice")},
    {"key": "music", "label": "Music", "icon": "🎵", "orchestrator_keys": ("audio",)},
    {"key": "post_production", "label": "Post Production", "icon": "✂️", "orchestrator_keys": ("post_production",)},
    {"key": "rendering", "label": "Rendering", "icon": "🎞️", "orchestrator_keys": ("render", "image", "video")},
    {"key": "publishing", "label": "Publishing", "icon": "📤", "orchestrator_keys": ("publish", "publishing", "seo")},
    {"key": "analytics", "label": "Analytics", "icon": "📊", "orchestrator_keys": ("analytics",)},
    {"key": "learning", "label": "Learning", "icon": "🧠", "orchestrator_keys": ("learning",)},
]

STUDIO_PLATFORMS = [
    {"id": "youtube_long", "label": "YouTube Long Form", "icon": "▶️", "category": "video"},
    {"id": "youtube_shorts", "label": "YouTube Shorts", "icon": "📱", "category": "short"},
    {"id": "tiktok", "label": "TikTok", "icon": "🎵", "category": "short"},
    {"id": "instagram_reels", "label": "Instagram Reels", "icon": "📸", "category": "short"},
    {"id": "facebook", "label": "Facebook", "icon": "👥", "category": "social"},
    {"id": "x", "label": "X", "icon": "𝕏", "category": "social"},
    {"id": "linkedin", "label": "LinkedIn", "icon": "💼", "category": "social"},
    {"id": "podcast", "label": "Podcasts", "icon": "🎙️", "category": "audio"},
    {"id": "audiobook", "label": "Audiobooks", "icon": "📚", "category": "audio"},
    {"id": "course", "label": "Courses", "icon": "🎓", "category": "education"},
    {"id": "presentation", "label": "Presentations", "icon": "📊", "category": "education"},
    {"id": "documentary", "label": "Documentaries", "icon": "🎥", "category": "video"},
    {"id": "animated_series", "label": "Animated Series", "icon": "🎞️", "category": "video"},
    {"id": "marketing_campaign", "label": "Marketing Campaigns", "icon": "📣", "category": "campaign"},
    {"id": "multi_platform", "label": "Multi-Platform Campaign", "icon": "🌐", "category": "campaign"},
]

STUDIO_EXAMPLE_PROMPTS = [
    "Create a 60 second YouTube Short explaining why cameras can see infrared.",
    "Create a 12 minute documentary about black holes.",
    "Create a TikTok about how seasons work",
    "Create a 12 minute documentary about ocean conservation",
    "Create ten TikTok videos about productivity hacks",
    "Generate a podcast series on startup psychology",
]

DEFAULT_STUDIO_SETTINGS = {
    "video_length_sec": 60,
    "platform": "youtube_shorts",
    "voice": "ai",
    "narrator": "documentary",
    "visual_style": "cinematic",
    "camera_style": "dynamic",
    "music_style": "uplifting",
    "pacing": "dynamic",
    "target_audience": "general",
    "language": "en",
    "brand": "",
    "character_set": "",
    "creative_style": "narrative_arc",
    "quality_level": "standard",
    "budget_usd": 0.0,
    "preferred_providers": [],
}

STUDIO_PROJECT_METADATA_FIELDS = (
    "folder",
    "tags",
    "platform",
    "archived",
    "studio_settings",
    "pipeline_state",
    "longform_job_id",
    "workflow_run_id",
)


def build_default_settings(platform_id: str = "youtube_shorts") -> dict:
    """Return a copy of default studio settings for one platform."""
    settings = dict(DEFAULT_STUDIO_SETTINGS)
    settings["platform"] = platform_id
    platform = next((p for p in STUDIO_PLATFORMS if p["id"] == platform_id), None)
    if platform:
        if platform["category"] == "short":
            settings["video_length_sec"] = 60
        elif platform["category"] == "video":
            settings["video_length_sec"] = 720
        elif platform["category"] == "audio":
            settings["video_length_sec"] = 1800
        elif platform["category"] == "education":
            settings["video_length_sec"] = 3600
        elif platform["category"] == "campaign":
            settings["video_length_sec"] = 300
    return settings


def platform_label(platform_id: str) -> str:
    match = next((p for p in STUDIO_PLATFORMS if p["id"] == platform_id), None)
    return match["label"] if match else platform_id.replace("_", " ").title()
