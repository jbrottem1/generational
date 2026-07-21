"""Visual Asset Director — constants, style library, score dimensions."""

from __future__ import annotations

PACKAGE_VERSION = "1.0.0"
PACKAGE_TYPE = "visual_asset_direction"

# Rejection taxonomy (mission vocabulary)
REJECTION_REASONS = (
    "low_resolution",
    "blurry_details",
    "deformed_anatomy",
    "incorrect_object_counts",
    "floating_objects",
    "cropped_subjects",
    "watermarks",
    "ai_artifacts",
    "unrealistic_lighting",
    "poor_framing",
    "incorrect_aspect_ratio",
    "low_contrast",
    "oversaturated_colors",
    "empty_compositions",
    "visual_clutter",
    "generic_stock_photo",
    "style_drift",
    "character_mismatch",
    "wrong_environment",
    "perspective_jump",
    "repeated_asset",
    "ai_hallucination",
    "low_educational_clarity",
)

SCORECARD_FIELDS = (
    "resolution",
    "lighting",
    "composition",
    "continuity",
    "character_consistency",
    "environment_consistency",
    "educational_clarity",
    "motion_potential",
    "thumbnail_appeal",
    "overall_professional_quality",
)

COMPOSITION_FIELDS = (
    "rule_of_thirds",
    "subject_clarity",
    "eye_direction",
    "leading_lines",
    "depth",
    "layering",
    "background_separation",
    "visual_hierarchy",
    "negative_space",
    "educational_clarity",
)

STYLE_LIBRARY: dict[str, dict] = {
    "documentary": {
        "label": "Documentary",
        "palette_bias": "natural_desaturated",
        "lighting": "motivated_practical",
        "motion": "observational_push_orbit",
        "notes": "Authentic environments, restrained grade, evidence-forward framing",
    },
    "pixar_inspired_3d": {
        "label": "Pixar-inspired 3D",
        "palette_bias": "warm_appeal",
        "lighting": "soft_key_rim",
        "motion": "character_led_arcs",
        "notes": "Stylized volumes, readable silhouettes, emotional clarity",
    },
    "scientific_illustration": {
        "label": "Scientific Illustration",
        "palette_bias": "clean_educational",
        "lighting": "even_studio",
        "motion": "diagram_reveals",
        "notes": "Labeled anatomy, cutaways, museum-accurate subject forms",
    },
    "photorealistic": {
        "label": "Photorealistic",
        "palette_bias": "camera_natural",
        "lighting": "physically_plausible",
        "motion": "handheld_or_locked",
        "notes": "Real-world materials and scale; avoid cartoon shapes",
    },
    "cinematic_film": {
        "label": "Cinematic Film",
        "palette_bias": "teal_orange_or_niche",
        "lighting": "cinematic_contrast",
        "motion": "motivated_camera",
        "notes": "Depth layers, anamorphic feel within platform crop",
    },
    "animated_educational": {
        "label": "Animated Educational",
        "palette_bias": "high_readability",
        "lighting": "flat_plus_accent",
        "motion": "beat_synced_graphic",
        "notes": "Teaching beats first; playful without clutter",
    },
    "museum_display": {
        "label": "Museum Display",
        "palette_bias": "gallery_neutral",
        "lighting": "spot_on_artifact",
        "motion": "slow_orbit_reveal",
        "notes": "Specimen clarity, plaque-like hierarchy, quiet BG",
    },
    "historical_recreation": {
        "label": "Historical Recreation",
        "palette_bias": "period_grade",
        "lighting": "practical_period",
        "motion": "tableau_to_detail",
        "notes": "Period-accurate wardrobe/props; avoid modern artifacts",
    },
    "futuristic": {
        "label": "Futuristic",
        "palette_bias": "cool_neon_control",
        "lighting": "emissive_accents",
        "motion": "glide_parallax",
        "notes": "Tech surfaces, HUD sparingly, clarity over spectacle",
    },
    "medical_visualization": {
        "label": "Medical Visualization",
        "palette_bias": "clinical_clean",
        "lighting": "soft_clinical",
        "motion": "anatomical_cutaway",
        "notes": "Accurate organ counts/forms; no horror grade",
    },
}

DEFAULT_STYLE = "documentary"

# Hard thresholds (soft enough for synthetic plates; still gate trash)
MIN_WIDTH = 720
MIN_HEIGHT = 720
MIN_LAPLACIAN_VAR = 18.0  # below → blurry
MIN_CONTRAST_STD = 18.0  # underwater / documentary grades may run soft
MAX_SATURATION_MEAN = 0.82
MIN_EDGE_DENSITY = 0.012
MIN_OVERALL_TO_APPROVE = 55.0
TARGET_ASPECTS = {
    "9:16": 9 / 16,
    "16:9": 16 / 9,
    "1:1": 1.0,
    "4:5": 4 / 5,
}
