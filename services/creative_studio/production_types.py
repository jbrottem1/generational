"""Production type registry — every visual medium the Creative Studio makes.

One architecture, unlimited visual styles: each production type is one
registered dict (PRODUCTION_TYPE_FIELDS). A future medium — interactive
video, spatial content, whatever comes next — is one more
`register_production_type()` call, never an architectural change.

`select_production_type()` is the Creative Director's medium chooser: it
matches an item's explicit request, keywords, topic, and platform signals
against each type's selection keywords, deterministically.
"""

from __future__ import annotations

PRODUCTION_TYPE_VERSION = "1.0"

DEFAULT_PRODUCTION_TYPE = "cinematic_video"

# type_id → production type dict (PRODUCTION_TYPE_FIELDS).
_TYPES: "dict[str, dict]" = {}


def register_production_type(production_type: dict) -> dict:
    """Register (or replace) one production type. Returns the stored dict."""
    stored = {
        "type_id": production_type["type_id"],
        "label": production_type.get("label", production_type["type_id"]),
        "description": production_type.get("description", ""),
        "default_style": production_type.get("default_style", "minimal"),
        "default_pacing": production_type.get("default_pacing", "dynamic"),
        "complexity": production_type.get("complexity", "standard"),
        "storytelling_style": production_type.get("storytelling_style", "narrative_arc"),
        "techniques": list(production_type.get("techniques", [])),
        "asset_types": list(production_type.get("asset_types", ["ai_image"])),
        "camera_language": production_type.get("camera_language", "cinematic coverage"),
        "keywords": list(production_type.get("keywords", [])),
    }
    _TYPES[stored["type_id"]] = stored
    return stored


def get_production_type(type_id: str) -> "dict | None":
    return _TYPES.get(type_id)


def all_production_types() -> "list[dict]":
    return list(_TYPES.values())


def production_type_ids() -> "list[str]":
    return list(_TYPES.keys())


def select_production_type(item: dict) -> dict:
    """The best production type for one content item (deterministic).

    Priority: an explicit `production_type` request wins; otherwise the
    type whose keywords best match the item's topic/keywords/niche/script;
    ties and no-signal cases fall back to AI cinematic video.
    """
    requested = str(item.get("production_type", "")).strip()
    if requested and requested in _TYPES:
        return dict(_TYPES[requested])

    signals = " ".join(
        str(part).lower()
        for part in (
            item.get("topic", ""),
            item.get("niche", ""),
            item.get("title", ""),
            " ".join(str(k) for k in item.get("keywords", [])),
            str(item.get("script", ""))[:400],
        )
    )

    best_id, best_score = DEFAULT_PRODUCTION_TYPE, 0
    for type_id, production_type in _TYPES.items():
        score = sum(1 for keyword in production_type["keywords"] if keyword in signals)
        if score > best_score:
            best_id, best_score = type_id, score
    return dict(_TYPES[best_id])


# --------------------------------------------------------------- built-ins
# The launch catalog. Real productions extend this freely — the registry
# is the extension point, not this list.

_BUILTINS = (
    {
        "type_id": "cinematic_video",
        "label": "AI Cinematic Video",
        "description": "Photorealistic AI-generated cinematic footage with full camera grammar.",
        "default_style": "documentary",
        "default_pacing": "dynamic",
        "complexity": "advanced",
        "storytelling_style": "narrative_arc",
        "techniques": ["ai_video_generation", "camera_moves", "color_grading", "sound_design"],
        "asset_types": ["ai_video", "ai_image", "stock_footage"],
        "camera_language": "cinematic coverage — establishing, medium, close-up progression",
        "keywords": ["cinematic", "film", "story", "drama"],
    },
    {
        "type_id": "animation_2d",
        "label": "2D Animation",
        "description": "Flat 2D character and scene animation.",
        "default_style": "kids",
        "default_pacing": "dynamic",
        "complexity": "standard",
        "storytelling_style": "character_journey",
        "techniques": ["keyframe_animation", "squash_and_stretch", "layered_backgrounds"],
        "asset_types": ["animation", "vector_graphic"],
        "camera_language": "flat staging with multiplane parallax",
        "keywords": ["2d", "animated", "animation"],
    },
    {
        "type_id": "animation_3d",
        "label": "3D Animation",
        "description": "Full 3D rendered animation with virtual cinematography.",
        "default_style": "scientific",
        "default_pacing": "measured",
        "complexity": "flagship",
        "storytelling_style": "narrative_arc",
        "techniques": ["3d_modeling", "rigging", "virtual_camera", "physically_based_lighting"],
        "asset_types": ["asset_3d", "ai_image"],
        "camera_language": "free virtual camera — orbits, dollies, crane moves",
        "keywords": ["3d", "render", "cgi"],
    },
    {
        "type_id": "cartoon",
        "label": "Cartoon",
        "description": "Exaggerated, gag-driven cartoon productions.",
        "default_style": "kids",
        "default_pacing": "rapid",
        "complexity": "standard",
        "storytelling_style": "gag_structure",
        "techniques": ["exaggeration", "smears", "impact_frames"],
        "asset_types": ["animation", "vector_graphic"],
        "camera_language": "snappy staging, whip pans between gags",
        "keywords": ["cartoon", "funny", "gag", "silly"],
    },
    {
        "type_id": "anime_inspired",
        "label": "Anime-Inspired Production",
        "description": "Anime-inspired visual storytelling — dramatic lighting, expressive characters.",
        "default_style": "anime_inspired",
        "default_pacing": "dynamic",
        "complexity": "advanced",
        "storytelling_style": "emotional_beats",
        "techniques": ["dramatic_holds", "speed_lines", "sakuga_moments", "expressive_eyes"],
        "asset_types": ["animation", "ai_image"],
        "camera_language": "dramatic angles, dutch tilts, held close-ups",
        "keywords": ["anime", "manga"],
    },
    {
        "type_id": "motion_graphics",
        "label": "Motion Graphics",
        "description": "Kinetic typography, shapes, and data-driven graphic motion.",
        "default_style": "minimal",
        "default_pacing": "rapid",
        "complexity": "standard",
        "storytelling_style": "point_by_point",
        "techniques": ["kinetic_typography", "shape_morphing", "easing_curves"],
        "asset_types": ["vector_graphic", "animation"],
        "camera_language": "flat 2D camera with scale/position moves",
        "keywords": ["motion graphics", "kinetic", "typography"],
    },
    {
        "type_id": "whiteboard",
        "label": "Whiteboard Video",
        "description": "Hand-drawn whiteboard explanation with a visible drawing hand.",
        "default_style": "minimal",
        "default_pacing": "measured",
        "complexity": "simple",
        "storytelling_style": "problem_solution",
        "techniques": ["draw_on_reveal", "hand_sync", "sketch_style"],
        "asset_types": ["vector_graphic", "animation"],
        "camera_language": "locked-off top-down board with occasional zooms",
        "keywords": ["whiteboard", "sketch", "draw"],
    },
    {
        "type_id": "educational_explainer",
        "label": "Educational Explainer",
        "description": "Clear step-by-step teaching content with diagrams and callouts.",
        "default_style": "minimal",
        "default_pacing": "measured",
        "complexity": "standard",
        "storytelling_style": "problem_solution",
        "techniques": ["diagram_callouts", "progressive_disclosure", "recap_frames"],
        "asset_types": ["vector_graphic", "ai_image", "animation"],
        "camera_language": "centered subjects, generous negative space",
        "keywords": ["explain", "how", "learn", "education", "tutorial", "guide"],
    },
    {
        "type_id": "science_visualization",
        "label": "Science Visualization",
        "description": "Accurate visualization of scientific phenomena and scale.",
        "default_style": "scientific",
        "default_pacing": "measured",
        "complexity": "advanced",
        "storytelling_style": "discovery_journey",
        "techniques": ["scale_transitions", "cutaway_views", "simulation_style_motion"],
        "asset_types": ["ai_image", "ai_video", "asset_3d"],
        "camera_language": "slow push-ins, orbital reveals, macro-to-cosmic zooms",
        "keywords": ["science", "physics", "biology", "chemistry", "quantum", "ocean", "brain"],
    },
    {
        "type_id": "medical_animation",
        "label": "Medical Animation",
        "description": "Anatomy and mechanism-of-action visualization to clinical standards.",
        "default_style": "medical",
        "default_pacing": "measured",
        "complexity": "advanced",
        "storytelling_style": "mechanism_walkthrough",
        "techniques": ["anatomical_cutaways", "cellular_zooms", "labeled_structures"],
        "asset_types": ["asset_3d", "ai_image", "vector_graphic"],
        "camera_language": "clinical steadiness — slow dollies through anatomy",
        "keywords": ["medical", "anatomy", "health", "disease", "body"],
    },
    {
        "type_id": "historical_reconstruction",
        "label": "Historical Reconstruction",
        "description": "Period-accurate reconstruction of historical events and places.",
        "default_style": "history",
        "default_pacing": "measured",
        "complexity": "advanced",
        "storytelling_style": "chronological_epic",
        "techniques": ["period_grading", "archival_blends", "map_animations"],
        "asset_types": ["ai_image", "ai_video", "stock_footage"],
        "camera_language": "sweeping establishing shots, slow reveals",
        "keywords": ["history", "ancient", "war", "empire", "century"],
    },
    {
        "type_id": "infographic",
        "label": "Infographic",
        "description": "Data-first visual storytelling — charts, stats, comparisons.",
        "default_style": "corporate",
        "default_pacing": "dynamic",
        "complexity": "simple",
        "storytelling_style": "point_by_point",
        "techniques": ["animated_charts", "count_ups", "icon_systems"],
        "asset_types": ["vector_graphic", "animation"],
        "camera_language": "flat camera, grid-locked layouts",
        "keywords": ["data", "statistics", "chart", "numbers", "infographic"],
    },
    {
        "type_id": "corporate_presentation",
        "label": "Corporate Presentation",
        "description": "Polished business communication and brand storytelling.",
        "default_style": "corporate",
        "default_pacing": "measured",
        "complexity": "standard",
        "storytelling_style": "executive_summary",
        "techniques": ["clean_transitions", "brand_lockups", "lower_thirds"],
        "asset_types": ["vector_graphic", "stock_footage", "brand_asset"],
        "camera_language": "stable, symmetric, confident framing",
        "keywords": ["business", "corporate", "company", "strategy"],
    },
    {
        "type_id": "commercial_ad",
        "label": "Commercial Advertisement",
        "description": "High-impact short-form product and service advertising.",
        "default_style": "luxury",
        "default_pacing": "rapid",
        "complexity": "advanced",
        "storytelling_style": "desire_arc",
        "techniques": ["hero_shots", "fast_cuts", "cta_endcards"],
        "asset_types": ["ai_video", "ai_image", "brand_asset"],
        "camera_language": "hero product angles, dramatic push-ins",
        "keywords": ["ad", "commercial", "sale", "product launch"],
    },
    {
        "type_id": "luxury_branding",
        "label": "Luxury Branding",
        "description": "Premium slow-burn brand films — texture, restraint, elegance.",
        "default_style": "luxury",
        "default_pacing": "slow",
        "complexity": "advanced",
        "storytelling_style": "sensory_immersion",
        "techniques": ["macro_details", "slow_motion", "negative_space"],
        "asset_types": ["ai_video", "ai_image", "brand_asset"],
        "camera_language": "slow gliding moves, macro close-ups",
        "keywords": ["luxury", "premium", "elegant", "exclusive"],
    },
    {
        "type_id": "product_demo",
        "label": "Product Demonstration",
        "description": "Feature-by-feature product walkthroughs and demos.",
        "default_style": "minimal",
        "default_pacing": "measured",
        "complexity": "standard",
        "storytelling_style": "feature_tour",
        "techniques": ["screen_capture_frames", "callout_annotations", "before_after"],
        "asset_types": ["ai_image", "vector_graphic", "user_asset"],
        "camera_language": "clean product-centric framing",
        "keywords": ["demo", "feature", "app", "product", "review"],
    },
    {
        "type_id": "documentary",
        "label": "Documentary",
        "description": "Long-form factual storytelling with interview and archival grammar.",
        "default_style": "documentary",
        "default_pacing": "measured",
        "complexity": "flagship",
        "storytelling_style": "investigative_arc",
        "techniques": ["archival_integration", "interview_framing", "verite_moments"],
        "asset_types": ["ai_video", "stock_footage", "ai_image"],
        "camera_language": "handheld verite mixed with composed interviews",
        "keywords": ["documentary", "investigation", "true story", "untold"],
    },
    {
        "type_id": "nature_video",
        "label": "Nature Video",
        "description": "Wildlife and landscape storytelling in the blue-chip tradition.",
        "default_style": "nature",
        "default_pacing": "slow",
        "complexity": "advanced",
        "storytelling_style": "discovery_journey",
        "techniques": ["golden_hour_grading", "telephoto_compression", "time_lapse"],
        "asset_types": ["ai_video", "stock_footage", "ai_image"],
        "camera_language": "patient telephoto observation, aerial sweeps",
        "keywords": ["nature", "wildlife", "animal", "forest", "planet"],
    },
    {
        "type_id": "kids_educational",
        "label": "Children's Educational Content",
        "description": "Bright, safe, repetition-friendly learning for young audiences.",
        "default_style": "kids",
        "default_pacing": "dynamic",
        "complexity": "standard",
        "storytelling_style": "call_and_response",
        "techniques": ["repetition", "sing_along_cues", "big_friendly_shapes"],
        "asset_types": ["animation", "vector_graphic"],
        "camera_language": "front-on staging, gentle bounces",
        "keywords": ["kids", "children", "abc", "counting", "toddler"],
    },
    {
        "type_id": "ai_presenter",
        "label": "AI Presenter Video",
        "description": "A consistent AI presenter/avatar delivering to camera.",
        "default_style": "corporate",
        "default_pacing": "dynamic",
        "complexity": "standard",
        "storytelling_style": "direct_address",
        "techniques": ["talking_head_framing", "b_roll_cutaways", "gesture_sync"],
        "asset_types": ["ai_video", "ai_image", "brand_asset"],
        "camera_language": "eye-level medium shots, occasional punch-ins",
        "keywords": ["presenter", "avatar", "host", "anchor"],
    },
    {
        "type_id": "reaction_video",
        "label": "Reaction Video",
        "description": "Presenter-plus-source-material reaction format.",
        "default_style": "motivational",
        "default_pacing": "rapid",
        "complexity": "simple",
        "storytelling_style": "commentary_beats",
        "techniques": ["picture_in_picture", "freeze_frames", "zoom_punch"],
        "asset_types": ["user_asset", "stock_footage", "ai_image"],
        "camera_language": "reaction cam + source split framing",
        "keywords": ["reaction", "react", "responds"],
    },
    {
        "type_id": "gaming_video",
        "label": "Gaming Style Video",
        "description": "Gameplay-driven content with HUD-style graphics and energy.",
        "default_style": "cyberpunk",
        "default_pacing": "rapid",
        "complexity": "standard",
        "storytelling_style": "highlight_reel",
        "techniques": ["hud_overlays", "kill_feed_graphics", "speed_ramps"],
        "asset_types": ["user_asset", "vector_graphic", "animation"],
        "camera_language": "in-game camera with dynamic overlays",
        "keywords": ["gaming", "game", "gameplay", "esports"],
    },
    {
        "type_id": "podcast_visualization",
        "label": "Podcast Visualization",
        "description": "Audio-first content visualized — waveforms, speaker cards, quotes.",
        "default_style": "minimal",
        "default_pacing": "slow",
        "complexity": "simple",
        "storytelling_style": "conversation_flow",
        "techniques": ["waveform_animation", "speaker_highlighting", "quote_cards"],
        "asset_types": ["vector_graphic", "animation", "brand_asset"],
        "camera_language": "static compositions with animated accents",
        "keywords": ["podcast", "episode", "conversation", "interview"],
    },
    {
        "type_id": "comic_style",
        "label": "Comic Book Style",
        "description": "Panel-based comic storytelling — halftones, speech bubbles, inks.",
        "default_style": "comic",
        "default_pacing": "dynamic",
        "complexity": "standard",
        "storytelling_style": "panel_sequence",
        "techniques": ["panel_transitions", "speech_bubbles", "onomatopoeia_cards"],
        "asset_types": ["ai_image", "vector_graphic"],
        "camera_language": "panel-to-panel camera with dramatic angles",
        "keywords": ["comic", "superhero", "panel"],
    },
)

for _production_type in _BUILTINS:
    register_production_type(_production_type)
