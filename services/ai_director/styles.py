"""V5 Style Library — reusable production styles with full creative DNA."""

from __future__ import annotations

STYLE_LIBRARY: dict[str, dict] = {
    "modern_documentary": {
        "label": "Modern Documentary",
        "motion": "slow_push_parallax",
        "typography": "clean_sans_bold",
        "transitions": "cinematic_dissolve",
        "music": "documentary",
        "narration": "documentary_host",
        "colors": {"primary": "#1A1A1A", "accent": "#C4A35A", "bg": "#F5F2EB"},
        "camera": ["slow_push", "orbit", "establishing_wide"],
        "graphics": "subtle_overlays",
        "grade_profile": "science_documentary",
        "opt_visual_style": "science_documentary",
    },
    "minimal_whiteboard": {
        "label": "Minimal Whiteboard",
        "motion": "draw_on_reveal",
        "typography": "hand_marker",
        "transitions": "hard_cut_clean",
        "music": "minimal",
        "narration": "teacher",
        "colors": {"primary": "#111111", "accent": "#2F80ED", "bg": "#FFFFFF"},
        "camera": ["static_hold", "slow_push"],
        "graphics": "line_diagrams",
        "grade_profile": "educational",
        "opt_visual_style": "kinetic_infographic",
    },
    "science_documentary": {
        "label": "Science Documentary",
        "motion": "macro_push_orbit",
        "typography": "editorial_sans",
        "transitions": "cross_dissolve",
        "music": "ambient",
        "narration": "scientist",
        "colors": {"primary": "#0B1F3A", "accent": "#3DDC97", "bg": "#071018"},
        "camera": ["macro_push", "orbit", "rack_focus"],
        "graphics": "scientific_overlays",
        "grade_profile": "science_documentary",
        "opt_visual_style": "science_documentary",
    },
    "kurzgesagt_inspired": {
        "label": "Kurzgesagt Inspired",
        "motion": "bold_vector_motion",
        "typography": "rounded_bold",
        "transitions": "morph_wipe",
        "music": "electronic",
        "narration": "storyteller",
        "colors": {"primary": "#1B1B2F", "accent": "#FF6B6B", "bg": "#16213E"},
        "camera": ["parallax", "crash_zoom", "orbit"],
        "graphics": "flat_infographic_dense",
        "grade_profile": "technology",
        "opt_visual_style": "kinetic_infographic",
    },
    "vox_inspired": {
        "label": "Vox Inspired",
        "motion": "kinetic_type_map_moves",
        "typography": "news_sans",
        "transitions": "whip_pan",
        "music": "technology",
        "narration": "conversational",
        "colors": {"primary": "#111111", "accent": "#E63946", "bg": "#FAFAFA"},
        "camera": ["tracking", "reveal", "slow_push"],
        "graphics": "data_viz_callouts",
        "grade_profile": "educational",
        "opt_visual_style": "kinetic_infographic",
    },
    "apple_keynote": {
        "label": "Apple Keynote",
        "motion": "precision_fade_scale",
        "typography": "sf_display",
        "transitions": "fade_through_black",
        "music": "minimal",
        "narration": "confident",
        "colors": {"primary": "#111111", "accent": "#0071E3", "bg": "#000000"},
        "camera": ["slow_push", "macro_push"],
        "graphics": "product_hero_minimal",
        "grade_profile": "technology",
        "opt_visual_style": "tech_neon",
    },
    "history_channel": {
        "label": "History Channel",
        "motion": "ken_burns_archive",
        "typography": "serif_display",
        "transitions": "fade_through_black",
        "music": "cinematic_orchestra",
        "narration": "documentary_host",
        "colors": {"primary": "#2C1810", "accent": "#D4A373", "bg": "#1A120B"},
        "camera": ["ken_burns", "slow_push", "tilt"],
        "graphics": "timeline_maps",
        "grade_profile": "historical",
        "opt_visual_style": "historical_warm",
    },
    "national_geographic": {
        "label": "National Geographic",
        "motion": "epic_landscape_push",
        "typography": "natgeo_sans",
        "transitions": "cinematic_dissolve",
        "music": "inspirational",
        "narration": "documentary_host",
        "colors": {"primary": "#FFCC00", "accent": "#1A1A1A", "bg": "#0D0D0D"},
        "camera": ["drone_simulation", "orbit", "tracking"],
        "graphics": "map_overlays",
        "grade_profile": "nature",
        "opt_visual_style": "nature_clean",
    },
    "technology_review": {
        "label": "Technology Review",
        "motion": "product_orbit_macro",
        "typography": "tech_sans",
        "transitions": "zoom_transition",
        "music": "technology",
        "narration": "engineer",
        "colors": {"primary": "#00D4FF", "accent": "#FFFFFF", "bg": "#0A0E17"},
        "camera": ["orbit", "macro_push", "parallax"],
        "graphics": "spec_callouts",
        "grade_profile": "technology",
        "opt_visual_style": "tech_neon",
    },
    "space_documentary": {
        "label": "Space Documentary",
        "motion": "orbital_drone_feel",
        "typography": "futura_clean",
        "transitions": "depth_transition",
        "music": "space",
        "narration": "scientist",
        "colors": {"primary": "#E8F1FF", "accent": "#7B61FF", "bg": "#050814"},
        "camera": ["orbit", "reveal", "slow_push"],
        "graphics": "orbital_diagrams",
        "grade_profile": "space",
        "opt_visual_style": "science_documentary",
    },
    "medical_animation": {
        "label": "Medical Animation",
        "motion": "cross_section_reveal",
        "typography": "clinical_sans",
        "transitions": "focus_pull",
        "music": "ambient",
        "narration": "professor",
        "colors": {"primary": "#0E7490", "accent": "#F43F5E", "bg": "#F8FAFC"},
        "camera": ["macro_push", "rack_focus", "orbit"],
        "graphics": "anatomy_overlays",
        "grade_profile": "medical",
        "opt_visual_style": "science_documentary",
    },
    "corporate_explainer": {
        "label": "Corporate Explainer",
        "motion": "clean_ui_motion",
        "typography": "corporate_sans",
        "transitions": "cross_dissolve",
        "music": "inspirational",
        "narration": "confident",
        "colors": {"primary": "#0F172A", "accent": "#2563EB", "bg": "#FFFFFF"},
        "camera": ["slow_push", "parallax"],
        "graphics": "process_flowcharts",
        "grade_profile": "business",
        "opt_visual_style": "science_documentary",
    },
}

_TOPIC_TO_STYLE = (
    (("space", "nasa", "planet", "galaxy", "orbit"), "space_documentary"),
    (("medical", "cell", "dna", "brain", "health", "virus"), "medical_animation"),
    (("history", "ancient", "war", "empire", "century"), "history_channel"),
    (("nature", "ocean", "wildlife", "forest", "animal"), "national_geographic"),
    (("ai", "chip", "robot", "software", "tech", "computer"), "technology_review"),
    (("business", "startup", "company", "market"), "corporate_explainer"),
    (("physics", "chemistry", "biology", "science", "math"), "science_documentary"),
    (("explained", "how", "why", "myth"), "vox_inspired"),
    (("kids", "simple", "whiteboard"), "minimal_whiteboard"),
)


def list_styles() -> list[dict]:
    return [{"style_id": k, **v} for k, v in STYLE_LIBRARY.items()]


def choose_production_style(candidate: dict, context: dict | None = None) -> dict:
    """Pick a style from topic/audience/platform signals — never random."""
    context = context or {}
    explicit = str(
        candidate.get("production_style")
        or candidate.get("style_id")
        or (candidate.get("creative_style") or {}).get("style_id")
        or ""
    ).strip()
    if explicit in STYLE_LIBRARY:
        style = dict(STYLE_LIBRARY[explicit])
        style["style_id"] = explicit
        style["rationale"] = "Explicit style override"
        return style

    blob = " ".join(
        str(candidate.get(k) or "")
        for k in ("title", "topic", "niche", "category", "hook")
    ).lower()
    audience = str(
        (candidate.get("audience_intelligence") or {}).get("primary_audience")
        or candidate.get("audience")
        or ""
    ).lower()
    blob = f"{blob} {audience}"

    for keys, style_id in _TOPIC_TO_STYLE:
        if any(k in blob for k in keys):
            style = dict(STYLE_LIBRARY[style_id])
            style["style_id"] = style_id
            style["rationale"] = f"Matched topic signals → {style_id}"
            return style

    # Shorts default toward Vox-like kinetic education
    platform = str(candidate.get("platform") or context.get("platform") or "").lower()
    if any(p in platform for p in ("shorts", "tiktok", "reels")):
        style = dict(STYLE_LIBRARY["vox_inspired"])
        style["style_id"] = "vox_inspired"
        style["rationale"] = "Short-form platform default"
        return style

    style = dict(STYLE_LIBRARY["modern_documentary"])
    style["style_id"] = "modern_documentary"
    style["rationale"] = "Default modern documentary"
    return style
