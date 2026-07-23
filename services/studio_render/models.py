"""Studio Render & Motion Graphics — contracts (V3.0)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

RENDER_QUALITY_THRESHOLD = 98
MAX_RENDER_REVISIONS = 3

GRADE_PROFILES = (
    "science_documentary",
    "technology",
    "space",
    "nature",
    "medical",
    "business",
    "finance",
    "historical",
    "educational",
)

TRANSITIONS_V3 = (
    "cinematic_dissolve",
    "directional_wipe",
    "match_cut",
    "morph",
    "zoom_transition",
    "whip_pan",
    "speed_ramp",
    "light_flash",
    "object_reveal",
    "parallax_transition",
    "focus_pull",
    "depth_transition",
    "motion_blur",
    "cross_dissolve",
    "fade_through_black",
)

MOTION_GRAPHICS_TYPES = (
    "animated_arrow",
    "callout",
    "highlight_box",
    "animated_label",
    "popup_statistic",
    "data_visualization",
    "timeline_animation",
    "graph_animation",
    "infographic",
    "flow_diagram",
    "comparison_graphic",
    "scientific_overlay",
    "animated_equation",
    "dynamic_text_reveal",
    "kinetic_caption_pop",
    "emphasis_pulse",
    "infographic_callout",
)

VFX_TYPES = (
    "particles",
    "dust",
    "atmosphere",
    "fog",
    "glow",
    "lens_flare",
    "bloom",
    "light_rays",
    "film_grain",
    "depth_of_field",
    "reflections",
    "shadows",
    "ambient_lighting",
    "volumetric_lighting",
)

EXPORT_PRESETS = (
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook_reels",
    "youtube_longform",
    "landscape_1080p",
    "landscape_4k",
    "square_1080",
    "vertical_1080",
    "vertical_4k",
)

RENDER_QUALITY_DIMENSIONS = (
    "visual_beauty",
    "motion_smoothness",
    "camera_quality",
    "graphic_quality",
    "color_consistency",
    "typography",
    "readability",
    "professional_appearance",
    "cinematic_score",
    "viewer_immersion",
)

# Desktop project tree under AI/Media Library (additive to Videos/)
MEDIA_LIBRARY_V3_PARTS = ("Desktop", "AI Start-Up", "AI", "Media Library")
PROJECT_SUBFOLDERS = (
    "Scripts",
    "Voice",
    "Images",
    "B-Roll",
    "Diagrams",
    "Animations",
    "Audio",
    "Assets",
    "Timeline",
    "Final",
    "Reports",
    "Archive",
)


@dataclass
class StudioRenderPackage:
    version: str = "3.0.0"
    overall_score: int = 0
    passed: bool = False
    revision_rounds: int = 0
    master_timeline: dict[str, Any] = field(default_factory=dict)
    motion_graphics: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    color_grade: dict[str, Any] = field(default_factory=dict)
    visual_effects: list[dict[str, Any]] = field(default_factory=list)
    typography: dict[str, Any] = field(default_factory=dict)
    diagrams: list[dict[str, Any]] = field(default_factory=list)
    broll_plan: list[dict[str, Any]] = field(default_factory=list)
    camera_choreography: list[dict[str, Any]] = field(default_factory=list)
    export_plan: dict[str, Any] = field(default_factory=dict)
    quality_scores: dict[str, int] = field(default_factory=dict)
    project_folder: str = ""
    improvements_vs_baseline: dict[str, float] = field(default_factory=dict)
    revision_fixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
