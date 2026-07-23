"""Recurring persistent locations — worlds that survive across episodes."""

from __future__ import annotations

from typing import Any

LOCATION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "WORLD-GMRI-MEDICAL-LAB": {
        "display_name": "Generational Medical Lab",
        "location_alias": "LOC-GMRI",
        "world_type": "interior_lab",
        "palette_hint": "lab",
        "dimensions_m": {"x": 18.0, "y": 4.2, "z": 14.0},
        "has_stairs": False,
        "outdoor": False,
        "default_weather": "interior_climate",
        "default_lighting": "clinical_warm",
        "furniture": ["teaching_console", "analysis_desk", "stool_chair", "equipment_rack"],
        "props": ["microscope", "hologram", "whiteboard", "door", "medical_scanner"],
        "permanent": True,
        "home_for": ["DOCTOR_001"],
    },
    "WORLD-LECTURE-HALL": {
        "display_name": "Lecture Hall",
        "location_alias": "LOC-LECTURE-HALL",
        "world_type": "interior_auditorium",
        "palette_hint": "gold",
        "dimensions_m": {"x": 22.0, "y": 6.0, "z": 16.0},
        "has_stairs": True,
        "outdoor": False,
        "default_weather": "interior_climate",
        "default_lighting": "stage_key_soft_fill",
        "furniture": ["podium_desk", "tiered_seats", "aisle_rail"],
        "props": ["whiteboard", "microphone_stand", "door", "projector_screen"],
        "permanent": True,
    },
    "WORLD-SCIENCE-MUSEUM": {
        "display_name": "Science Museum",
        "location_alias": "LOC-SCIENCE-MUSEUM",
        "world_type": "interior_atrium",
        "palette_hint": "ocean",
        "dimensions_m": {"x": 30.0, "y": 12.0, "z": 24.0},
        "has_stairs": True,
        "outdoor": False,
        "default_weather": "skylight_cloud_drift",
        "default_lighting": "volumetric_sunlight",
        "furniture": ["exhibit_plinths", "benches"],
        "props": ["exhibit", "hologram", "door", "rotating_globe"],
        "permanent": True,
    },
    "WORLD-LIBRARY": {
        "display_name": "Library",
        "location_alias": "LOC-ANCIENT-LIBRARY",
        "world_type": "interior_archive",
        "palette_hint": "gold",
        "dimensions_m": {"x": 16.0, "y": 5.5, "z": 20.0},
        "has_stairs": True,
        "outdoor": False,
        "default_weather": "interior_climate",
        "default_lighting": "warm_reading_lamps",
        "furniture": ["reading_desk", "chair", "study_carrel"],
        "props": ["bookshelf", "door", "whiteboard", "open_book"],
        "permanent": True,
    },
    "WORLD-FOREST": {
        "display_name": "Forest",
        "location_alias": "LOC-FOREST",
        "world_type": "exterior_nature",
        "palette_hint": "ireland",
        "dimensions_m": {"x": 40.0, "y": 20.0, "z": 40.0},
        "has_stairs": False,
        "outdoor": True,
        "default_weather": "dappled_breeze",
        "default_lighting": "god_rays",
        "furniture": ["fallen_log_bench"],
        "props": ["moss_rock", "trail_marker"],
        "permanent": True,
    },
    "WORLD-CITY-PARK": {
        "display_name": "City Park",
        "location_alias": "LOC-CITY-PARK",
        "world_type": "exterior_urban_nature",
        "palette_hint": "gold",
        "dimensions_m": {"x": 35.0, "y": 15.0, "z": 28.0},
        "has_stairs": True,
        "outdoor": True,
        "default_weather": "clear_breeze",
        "default_lighting": "golden_hour",
        "furniture": ["park_bench", "picnic_table"],
        "props": ["lamp_post", "fountain", "path_sign"],
        "permanent": True,
    },
    "WORLD-SPACE-STATION": {
        "display_name": "Space Station",
        "location_alias": "LOC-SPACE-STATION",
        "world_type": "interior_orbital",
        "palette_hint": "night",
        "dimensions_m": {"x": 14.0, "y": 3.2, "z": 28.0},
        "has_stairs": False,
        "outdoor": False,
        "default_weather": "pressurized_interior",
        "default_lighting": "cool_practicals",
        "furniture": ["console_bay", "observation_seat"],
        "props": ["console", "door", "viewport", "handhold"],
        "permanent": True,
    },
    "WORLD-HOSPITAL": {
        "display_name": "Hospital",
        "location_alias": "LOC-HOSPITAL",
        "world_type": "interior_clinical",
        "palette_hint": "lab",
        "dimensions_m": {"x": 20.0, "y": 3.6, "z": 12.0},
        "has_stairs": True,
        "outdoor": False,
        "default_weather": "interior_climate",
        "default_lighting": "clinical_cool",
        "furniture": ["nurse_desk", "waiting_chair", "gurney_bay"],
        "props": ["door", "monitor_screen", "chart_board", "hand_sanitizer"],
        "permanent": True,
    },
    "WORLD-CLASSROOM": {
        "display_name": "Classroom",
        "location_alias": "LOC-CLASSROOM",
        "world_type": "interior_classroom",
        "palette_hint": "gold",
        "dimensions_m": {"x": 12.0, "y": 3.4, "z": 10.0},
        "has_stairs": False,
        "outdoor": False,
        "default_weather": "interior_climate",
        "default_lighting": "soft_daylight_windows",
        "furniture": ["teacher_desk", "student_desks", "chair"],
        "props": ["whiteboard", "door", "globe", "bookshelf"],
        "permanent": True,
    },
    "WORLD-OCEAN-RESEARCH": {
        "display_name": "Ocean Research Center",
        "location_alias": "LOC-OCEAN-OBSERVATORY",
        "world_type": "interior_observatory",
        "palette_hint": "ocean",
        "dimensions_m": {"x": 16.0, "y": 5.0, "z": 14.0},
        "has_stairs": False,
        "outdoor": False,
        "default_weather": "surface_swell_outside",
        "default_lighting": "caustic_blue",
        "furniture": ["observation_bench", "instrument_console"],
        "props": ["console", "door", "specimen_tray", "binocular_station"],
        "permanent": True,
    },
}


def get_location_definition(world_id: str) -> dict[str, Any] | None:
    return LOCATION_DEFINITIONS.get(str(world_id or "").upper())


def resolve_world_id(location_or_id: str | dict[str, Any] | None) -> str:
    """Map LOC-* / name / WORLD-* → canonical WORLD-* id."""
    if isinstance(location_or_id, dict):
        for key in ("world_id", "id", "location_alias", "name"):
            if location_or_id.get(key):
                return resolve_world_id(str(location_or_id.get(key)))
        return "WORLD-GMRI-MEDICAL-LAB"

    raw = str(location_or_id or "WORLD-GMRI-MEDICAL-LAB").strip()
    key = raw.upper().replace(" ", "-")
    if key in LOCATION_DEFINITIONS:
        return key
    # Alias lookup
    for wid, defn in LOCATION_DEFINITIONS.items():
        if str(defn.get("location_alias") or "").upper() == key:
            return wid
        if str(defn.get("display_name") or "").upper().replace(" ", "-") == key:
            return wid
        if key in str(defn.get("display_name") or "").upper().replace(" ", "-"):
            return wid
    # Fuzzy mission names
    aliases = {
        "LOC-GMRI": "WORLD-GMRI-MEDICAL-LAB",
        "GMRI": "WORLD-GMRI-MEDICAL-LAB",
        "MEDICAL-LAB": "WORLD-GMRI-MEDICAL-LAB",
        "GENERATIONAL-MEDICAL-LAB": "WORLD-GMRI-MEDICAL-LAB",
        "LECTURE-HALL": "WORLD-LECTURE-HALL",
        "SCIENCE-MUSEUM": "WORLD-SCIENCE-MUSEUM",
        "LIBRARY": "WORLD-LIBRARY",
        "FOREST": "WORLD-FOREST",
        "CITY-PARK": "WORLD-CITY-PARK",
        "SPACE-STATION": "WORLD-SPACE-STATION",
        "HOSPITAL": "WORLD-HOSPITAL",
        "CLASSROOM": "WORLD-CLASSROOM",
        "OCEAN": "WORLD-OCEAN-RESEARCH",
        "OCEAN-RESEARCH": "WORLD-OCEAN-RESEARCH",
        "OCEAN-RESEARCH-CENTER": "WORLD-OCEAN-RESEARCH",
        "LOC-OCEAN-OBSERVATORY": "WORLD-OCEAN-RESEARCH",
    }
    if key in aliases:
        return aliases[key]
    for a, wid in aliases.items():
        if a in key or key in a:
            return wid
    return "WORLD-GMRI-MEDICAL-LAB"


def list_world_ids() -> list[str]:
    return list(LOCATION_DEFINITIONS.keys())
