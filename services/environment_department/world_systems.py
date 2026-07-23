"""Architecture coherence, materials, vegetation, weather, atmosphere, lighting, set dressing."""

from __future__ import annotations

from typing import Any


def architecture_package(environment: dict[str, Any]) -> dict[str, Any]:
    function = str(environment.get("function") or "general")
    lab = "lab" in function or "diagnosis" in function or "medical" in str(environment.get("environment_id") or "")
    required = (
        [
            "functional_work_zones",
            "circulation_paths",
            "storage",
            "equipment_access",
            "safety_systems",
            "readable_signage",
            "ventilation",
            "lighting_fixtures",
            "doors_and_exits",
            "service_areas",
        ]
        if lab
        else [
            "entrances",
            "circulation",
            "primary_program_spaces",
            "signage",
            "daylight_strategy",
            "service_access",
        ]
    )
    return {
        "environment_id": environment.get("environment_id"),
        "architectural_style": environment.get("architectural_style"),
        "function": function,
        "must_answer": [
            "What is its function?",
            "Who uses it?",
            "How do they enter?",
            "How do they move through it?",
            "Where does equipment go?",
            "Where does light enter?",
            "What safety rules shape it?",
            "What history is visible?",
        ],
        "required_systems": required,
        "reject": ["decorative_shell_only", "impossible_circulation", "no_exits"],
    }


def materials_library() -> dict[str, Any]:
    return {
        "brushed_titanium_medical": {
            "material_id": "brushed_titanium_medical",
            "base_color": [0.78, 0.81, 0.84],
            "metallic": 0.92,
            "roughness": 0.32,
            "specular": 0.68,
            "normal_strength": 0.18,
            "wear": 0.06,
            "fingerprint_visibility": 0.02,
        },
        "medical_floor_polymer": {
            "material_id": "medical_floor_polymer",
            "base_color": [0.88, 0.90, 0.92],
            "metallic": 0.0,
            "roughness": 0.45,
            "wear": 0.12,
            "wetness": 0.0,
        },
        "glass_clear": {
            "material_id": "glass_clear",
            "base_color": [0.95, 0.97, 1.0],
            "metallic": 0.0,
            "roughness": 0.05,
            "transmission": 0.92,
            "opacity": 0.15,
        },
        "leaf_translucent": {
            "material_id": "leaf_translucent",
            "base_color": [0.25, 0.55, 0.28],
            "roughness": 0.55,
            "subsurface_scattering": 0.35,
            "transmission": 0.2,
        },
        "soft_white_polymer_skin": {
            "material_id": "soft_white_polymer_skin",
            "base_color": [0.96, 0.97, 0.98],
            "roughness": 0.45,
            "subsurface_scattering": 0.12,
        },
    }


def vegetation_package(*, biome: str = "controlled_indoor_biophilic", season: str = "year_round") -> dict[str, Any]:
    return {
        "biome": biome,
        "season": season,
        "layers": ["canopy_none_indoor", "shrubs", "grasses_potted", "ground_cover", "moss_accent"],
        "plants": [
            {
                "species": "indoor_ficus",
                "biome": biome,
                "season": season,
                "height_meters": 2.1,
                "wind_response": 0.15,
                "leaf_density": 0.78,
                "health": 0.94,
                "placement_reason": "biophilic_calm_near_teaching_zone",
            },
            {
                "species": "herb_planter_wall",
                "biome": biome,
                "season": season,
                "height_meters": 1.4,
                "wind_response": 0.08,
                "leaf_density": 0.7,
                "health": 0.9,
                "placement_reason": "living_wall_signature",
            },
        ],
        "variation_required": ["scale", "rotation", "density", "health", "color"],
        "forbid_identical_clones": True,
    }


def weather_state(
    *,
    weather_type: str = "clear",
    intensity: float = 0.1,
    wind_direction: list[float] | None = None,
    wind_speed_mps: float = 1.2,
) -> dict[str, Any]:
    return {
        "type": weather_type,
        "intensity": intensity,
        "wind_direction": wind_direction or [0.2, 0.0, 0.1],
        "wind_speed_mps": wind_speed_mps,
        "gust_strength": 0.1 if weather_type == "clear" else 0.25,
        "humidity": 0.45 if weather_type == "clear" else 0.82,
        "cloud_coverage": 0.15 if weather_type == "clear" else 0.7,
        "surface_wetness": 0.0 if weather_type == "clear" else 0.65,
        "visibility_meters": 2000 if weather_type == "clear" else 900,
        "affects": [
            "hair",
            "clothing",
            "plants",
            "flags",
            "water",
            "particles",
            "reflections",
            "roads",
            "windows",
            "sound",
            "lighting",
            "character_behavior",
        ],
    }


def atmospheric_falloff(distance: float, density: float) -> float:
    return max(0.0, min(1.0, 1.0 - pow(2.718281828, -density * distance)))


def atmosphere_package(*, density: float = 0.035) -> dict[str, Any]:
    return {
        "density": density,
        "effects": ["soft_haze", "volumetric_window_light", "subtle_dust"],
        "near": {"contrast": "high", "detail": "sharp", "saturation": "full"},
        "far": {"contrast": "reduced", "edges": "softer", "haze": True, "motion_amplitude": "reduced"},
        "falloff_samples": {
            "2m": round(atmospheric_falloff(2.0, density), 4),
            "10m": round(atmospheric_falloff(10.0, density), 4),
            "25m": round(atmospheric_falloff(25.0, density), 4),
        },
    }


def lighting_package(*, time_of_day: str = "morning", mood: str = "clinical_warm") -> dict[str, Any]:
    return {
        "time_of_day": time_of_day,
        "mood": mood,
        "key": {
            "type": "sun" if time_of_day in {"morning", "afternoon"} else "skylight",
            "direction": [-0.3, -0.8, -0.4],
            "temperature_kelvin": 5200 if time_of_day == "morning" else 4300,
            "intensity": 1.0,
        },
        "fill": {"type": "sky", "temperature_kelvin": 7200, "intensity": 0.28},
        "rim": {"type": "window_bounce", "temperature_kelvin": 6500, "intensity": 0.22},
        "practicals": [
            {"id": "lab_panel_01", "temperature_kelvin": 4300, "intensity": 0.35},
            {"id": "holo_column", "temperature_kelvin": 7500, "intensity": 0.4, "emission": True},
        ],
        "rules": [
            "motivated_sources_only",
            "avoid_flat_front_lighting",
            "vary_by_time_weather_emotion_beat",
        ],
    }


def set_dressing(*, owner: str = "DOCTOR_001") -> dict[str, Any]:
    props = [
        {
            "prop_id": "diagnostic_scanner_02",
            "function": "cellular_scan",
            "owner": owner,
            "material": "white_ceramic_composite",
            "default_location": [2.4, 1.1, -0.8],
            "interaction_points": ["screen", "handle", "sample_tray"],
            "continuity_required": True,
        },
        {
            "prop_id": "holographic_interface_main",
            "function": "teaching_display",
            "owner": owner,
            "material": "emissive_glass",
            "default_location": [0.0, 1.4, -1.2],
            "interaction_points": ["volume", "pinch_zone"],
            "continuity_required": True,
        },
        {
            "prop_id": "research_notes_board",
            "function": "environmental_storytelling",
            "owner": owner,
            "material": "matte_composite",
            "default_location": [-3.5, 1.6, -4.0],
            "continuity_required": True,
        },
    ]
    return {
        "props": props,
        "storytelling": [
            "worn_floor_near_teaching_console",
            "notes_pinned_beside_monitor",
            "living_plant_wall",
            "personal_care_token_on_desk",
            "unfinished_sample_tray_labeled",
        ],
        "must_contain": [
            "evidence_of_current_activity",
            "evidence_of_past_activity",
            "evidence_of_ownership",
            "evidence_of_function",
            "one_memorable_visual_feature",
        ],
        "ambient_motion": [
            "researchers_working",
            "screens_updating",
            "soft_hvac_ripple",
            "plant_micro_sway",
            "holo_column_pulse",
        ],
        "prop_continuity_rule": "Props must not move between shots without explanation.",
    }
