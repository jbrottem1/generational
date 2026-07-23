"""The Doctor's permanent home — Generational Medical Research Institute."""

from __future__ import annotations

from typing import Any

from services.studio_assets.the_doctor.profile import HOME_WORLD_ID

GMRI_ROOMS = [
    "reception",
    "research_laboratories",
    "medical_classrooms",
    "ai_operating_room",
    "dna_laboratory",
    "microscope_room",
    "robotics_lab",
    "holographic_teaching_theater",
    "lecture_hall",
    "medical_museum",
    "future_medical_archive",
    "underground_research_center",
    "observation_deck",
    "drone_landing_area",
    "garden",
    "cafeteria",
    "server_room",
    "offices",
    "living_quarters",
    "emergency_response_center",
]


def gmri_world_package() -> dict[str, Any]:
    return {
        "id": HOME_WORLD_ID,
        "name": "The Generational Medical Research Institute",
        "short_name": "GMRI",
        "owner_character": "CHAR-0001",
        "asset_status": ["permanent", "reusable", "version_controlled"],
        "style": {
            "look": "high_end_cinematic_science_facility",
            "feel": ["warm", "inviting", "beautiful", "futuristic", "highly_detailed", "filled_with_life"],
            "forbid_empty": True,
        },
        "architecture": "tiered_glass_and_titanium_medical_campus_with_gardens",
        "lighting": "soft_warm_clinical + blue_practical_accents + skylight_volumetrics",
        "palette_hint": "lab",
        "textures": ["medical_white", "brushed_titanium", "glass", "warm_wood_accents", "living_plant_walls"],
        "furniture": ["research_benches", "teaching_amphitheater_seats", "observation_consoles", "cafe_tables"],
        "equipment": ["holographic_displays", "microscopes", "dna_sequencers", "surgical_assist_arms", "med_drones"],
        "interactive_props": ["clipboard", "medical_scanner", "holo_anatomy_model", "specimen_tray", "tablet"],
        "ambient_life": [
            "researchers_moving",
            "robots_working",
            "screens_active",
            "plants_growing",
            "medical_equipment_functioning",
            "drones_passing",
        ],
        "weather": "interior_climate + garden_breeze_on_deck",
        "environmental_animation": [
            "monitor_waveforms",
            "holo_spin",
            "plant_sway",
            "dust_motes_in_skylight",
            "drone_approach",
            "door_hiss",
        ],
        "background_characters": ["clinicians", "students", "assist_robots", "visiting_educators"],
        "soundscape": ["soft_beeps", "distant_lectures", "garden_birds", "server_hum", "shoe_squeaks"],
        "detail_dressing": [
            "notes_on_whiteboards",
            "coffee_cups",
            "books_on_shelves",
            "running_computers",
            "plants",
            "reflection_on_glass",
            "charts",
        ],
        "rooms": {room: {"reusable": True, "living_set": True} for room in GMRI_ROOMS},
        "domains": [
            "medicine",
            "biology",
            "science",
            "anatomy",
            "chemistry",
            "health",
            "technology",
            "physics",
        ],
        "world_builder_hint": "WORLD-HOSPITAL",
    }


def lighting_presets() -> dict[str, Any]:
    return {
        "day_teach": {
            "key": "soft_skylight",
            "fill": "warm_bounce",
            "rim": "blue_led_edge",
            "mood": "inviting_clarity",
        },
        "night_research": {
            "key": "cool_monitor_practicals",
            "fill": "low_warm_desk",
            "rim": "accent_blue",
            "mood": "focused_curiosity",
        },
        "emergency": {
            "key": "clinical_overhead",
            "fill": "red_status_pulse",
            "rim": "hard_titanium",
            "mood": "urgent_controlled",
        },
        "theater_holo": {
            "key": "dimmed_house",
            "fill": "holo_cyan",
            "rim": "audience_silhouette",
            "mood": "wonder",
        },
        "garden_walk": {
            "key": "golden_daylight",
            "fill": "leaf_bounce",
            "rim": "soft_blue_accent",
            "mood": "human_warmth",
        },
    }


def prop_library() -> list[dict[str, Any]]:
    return [
        {"id": "PROP-DOC-SCANNER", "name": "Medical Scanner", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-CLIPBOARD", "name": "Digital Clipboard", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-HOLO-ANATOMY", "name": "Holographic Anatomy Model", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-TABLET", "name": "Clinical Tablet", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-STETH-MODULE", "name": "Stethoscope Module", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-SAMPLE-TRAY", "name": "Specimen Tray", "owner": "CHAR-0001", "reusable": True},
        {"id": "PROP-DOC-MED-DRONE", "name": "Assist Med-Drone", "owner": "CHAR-0001", "reusable": True},
    ]


def reusable_objects() -> list[dict[str, Any]]:
    return [
        {"id": "OBJ-GMRI-BENCH", "name": "Research Bench", "rooms": ["research_laboratories", "dna_laboratory"]},
        {"id": "OBJ-GMRI-HOLO-STAGE", "name": "Holo Teaching Stage", "rooms": ["holographic_teaching_theater"]},
        {"id": "OBJ-GMRI-MICROSCOPE", "name": "Grand Microscope", "rooms": ["microscope_room"]},
        {"id": "OBJ-GMRI-SERVER-RACK", "name": "Medical AI Rack", "rooms": ["server_room"]},
        {"id": "OBJ-GMRI-GARDEN-PLANTER", "name": "Healing Garden Planter", "rooms": ["garden"]},
        {"id": "OBJ-GMRI-ARCHIVE-SHELF", "name": "Future Archive Shelf", "rooms": ["future_medical_archive"]},
    ]
