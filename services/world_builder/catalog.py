"""Catalog of reusable cinematic worlds."""

from __future__ import annotations

import re
from typing import Any

from services.world_builder.models import WORLD_TYPES, empty_object, world_id_for_type


def _contains_hint(blob: str, hint: str) -> bool:
    """Match whole words/phrases; avoid 'ai' hitting 'detail'."""
    h = (hint or "").strip().lower()
    if not h:
        return False
    if " " in h:
        return h in blob
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(h)}(?![a-z0-9])", blob))


# Keyword → world_type for selection
_TOPIC_HINTS: dict[str, tuple[str, ...]] = {
    "Science Lab": ("lab", "experiment", "beaker", "microscope", "chemistry"),
    "Museum": ("museum", "exhibit", "artifact", "gallery"),
    "Ancient Rome": ("rome", "roman", "colosseum", "caesar", "empire"),
    "Outer Space": ("outer space", "nebula", "astronaut", "cosmos", "zero gravity", "spacecraft"),
    "Mars Colony": ("mars", "colony", "red planet", "rover"),
    "Rainforest": ("rainforest", "jungle", "canopy", "amazon"),
    "Ocean Floor": ("ocean", "underwater", "coral", "deep sea", "marine"),
    "Human Cell": ("cell", "mitochondria", "organelle", "cytoplasm"),
    "Hospital": ("hospital", "clinic", "ward", "nurse"),
    "Operating Room": ("surgery", "operating", "scalpel", "operating room"),
    "Factory": ("factory", "manufacturing", "assembly", "industrial"),
    "DNA Interior": ("dna", "helix", "genome", "gene", "chromosome"),
    "Solar System": ("planet", "solar", "orbit", "saturn", "jupiter", "mercury"),
    "Medieval Village": ("medieval", "castle", "knight", "village", "feudal"),
    "Courtroom": ("court", "judge", "trial", "jury", "law"),
    "Stock Exchange": ("stock", "market", "finance", "trading", "wall street", "economy"),
    "Ancient Egypt": ("egypt", "pharaoh", "pyramid", "nile", "hieroglyph"),
    "Future City": ("future", "cyber", "skyline", "neon", "megacity"),
    "Nature Preserve": ("nature", "wildlife", "preserve", "forest", "habitat"),
    "University": ("university", "campus", "lecture", "college"),
    "Library": ("library", "books", "archive", "stacks"),
    "Research Center": ("research", "institute", "study", "analysis"),
    "AI Laboratory": ("ai", "neural", "robot", "machine learning", "algorithm", "pattern learning"),
    "Ocean Research Observatory": ("octopus", "observatory", "aquarium", "marine research", "three hearts", "cephalopod"),
    "Microscopic Biological Environment": ("microscopic", "microbe", "bacteria", "virus particle"),
}


def _base(
    world_type: str,
    *,
    theme: str,
    scale: str,
    historical_accuracy: int,
    environment: str,
    architecture: list[str],
    weather: str,
    objects: list[dict[str, Any]],
    furniture: list[dict[str, Any]],
    background_animations: list[str],
    sound_ambience: list[str],
    camera_boundaries: dict[str, Any],
    color_palette: dict[str, Any],
    lighting_base: str,
    lighting_presets: list[dict[str, Any]],
    camera_anchors: list[dict[str, Any]],
    animation_zones: list[dict[str, Any]],
    transition_anchors: list[dict[str, Any]],
    design_rules: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "world_id": world_id_for_type(world_type),
        "world_type": world_type,
        "name": world_type,
        "theme": theme,
        "scale": scale,
        "historical_accuracy": historical_accuracy,
        "environment": {
            "description": environment,
            "continuity_key": world_id_for_type(world_type),
            "do_not_replace_mid_episode": True,
        },
        "lighting": {
            "base": lighting_base,
            "consistent_key": True,
        },
        "architecture": architecture,
        "weather": weather,
        "objects": objects,
        "furniture": furniture,
        "background_animations": background_animations,
        "sound_ambience": sound_ambience,
        "camera_boundaries": camera_boundaries,
        "color_palette": color_palette,
        "lighting_presets": lighting_presets,
        "camera_anchors": camera_anchors,
        "animation_zones": animation_zones,
        "transition_anchors": transition_anchors,
        "design_rules": design_rules
        or [
            "Keep set geometry continuous across scenes",
            "Vary camera and lighting, not the world itself",
            "Every object must sit on a defined surface",
            "No flat solid full-frame backgrounds",
        ],
    }


def _labish_anchors() -> list[dict[str, Any]]:
    return [
        {"id": "wide_establish", "position": "rear_center", "angle": "eye_level", "lens_hint": "24mm"},
        {"id": "bench_medium", "position": "workbench_front", "angle": "slight_high", "lens_hint": "35mm"},
        {"id": "macro_detail", "position": "instrument_close", "angle": "macro", "lens_hint": "85mm"},
        {"id": "corner_observe", "position": "room_corner", "angle": "observational", "lens_hint": "28mm"},
    ]


def _labish_lights(cool: str = "cool teal key") -> list[dict[str, Any]]:
    return [
        {"id": "day_neutral", "recipe": f"{cool} + soft bounce fill", "mood": "neutral"},
        {"id": "dramatic_rim", "recipe": f"{cool} + hard rim + practical instrument glow", "mood": "dramatic"},
        {"id": "low_key_focus", "recipe": "low-key with luminous subject isolation", "mood": "focus"},
        {"id": "bright_reveal", "recipe": "bright key + lifted shadows for revelation", "mood": "reveal"},
    ]


def build_catalog() -> dict[str, dict[str, Any]]:
    """Return world_id → world definition for all mission world types."""
    worlds: list[dict[str, Any]] = []

    worlds.append(
        _base(
            "Science Lab",
            theme="empirical discovery",
            scale="room",
            historical_accuracy=85,
            environment="Glass-walled research laboratory with instrument benches, polished epoxy floor, and ambient HUD panels",
            architecture=["steel beam grid", "glass partitions", "overhead service rails"],
            weather="indoors_climate_controlled",
            objects=[
                empty_object(name="microscope", surface="desk", x=0.35, y=0.85, z=0.4),
                empty_object(name="reagent_rack", surface="desk", x=0.55, y=0.85, z=0.42),
                empty_object(name="holographic_board", surface="wall", x=0.5, y=1.4, z=0.1),
            ],
            furniture=[
                empty_object(name="lab_bench", surface="floor", x=0.45, y=0.0, z=0.45),
                empty_object(name="stool", surface="floor", x=0.3, y=0.0, z=0.55),
            ],
            background_animations=["particle dust drift", "soft monitor flicker", "vent heat shimmer"],
            sound_ambience=["HVAC hum", "distant centrifuge", "soft beep"],
            camera_boundaries={"min_height": 0.4, "max_height": 2.2, "min_distance": 0.5, "max_distance": 8.0},
            color_palette={"family": "lab", "primary": "#101820", "accent": "#A8DADC", "practical": "#F1FAEE"},
            lighting_base="cool teal key + soft grid bounce",
            lighting_presets=_labish_lights(),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "bench_work", "region": "center_bench"}, {"id": "board_explain", "region": "wall_screen"}],
            transition_anchors=[{"id": "doorway", "to_compatible": ["Research Center", "AI Laboratory", "University"]}],
        )
    )

    worlds.append(
        _base(
            "Museum",
            theme="curated wonder",
            scale="hall",
            historical_accuracy=80,
            environment="Grand museum gallery with spotlighted vitrines, marble floor, and vaulted ceiling",
            architecture=[" колоннада", "glass vitrines", "vaulted skylight"],
            weather="indoors",
            objects=[
                empty_object(name="centerpiece_artifact", surface="floor", x=0.5, y=0.0, z=0.45),
                empty_object(name="info_plinth", surface="floor", x=0.35, y=0.0, z=0.55),
            ],
            furniture=[empty_object(name="bench", surface="floor", x=0.2, y=0.0, z=0.7)],
            background_animations=["dust motes in sunbeams", "soft spotlight sweep"],
            sound_ambience=["quiet footsteps", "hushed hall reverb"],
            camera_boundaries={"min_height": 0.5, "max_height": 4.0, "min_distance": 1.0, "max_distance": 20.0},
            color_palette={"family": "science_core", "primary": "#0B1D36", "accent": "#F4A261"},
            lighting_base="spotlight key on artifacts + soft ambient fill",
            lighting_presets=_labish_lights("warm gallery key"),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "vitrine_focus", "region": "center_hall"}],
            transition_anchors=[{"id": "gallery_arch", "to_compatible": ["Library", "Ancient Egypt", "Ancient Rome"]}],
        )
    )

    # Fix typo in museum architecture - used russian-looking word accidentally
    worlds[-1]["architecture"] = ["column arcade", "glass vitrines", "vaulted skylight"]

    worlds.append(
        _base(
            "Ancient Rome",
            theme="imperial power",
            scale="forum",
            historical_accuracy=75,
            environment="Sunlit Roman forum with marble columns, mosaic floor, and distant amphitheatre silhouette",
            architecture=["doric columns", "forum pavement", "arched aqueduct silhouette"],
            weather="mediterranean_clear",
            objects=[
                empty_object(name="statue", surface="ground", x=0.6, y=0.0, z=0.3),
                empty_object(name="scroll_table", surface="ground", x=0.4, y=0.0, z=0.5),
            ],
            furniture=[empty_object(name="stone_bench", surface="ground", x=0.25, y=0.0, z=0.6)],
            background_animations=["cloth banner ripple", "heat haze", "distant crowd blur"],
            sound_ambience=["forum crowd", "wind through columns"],
            camera_boundaries={"min_height": 0.5, "max_height": 8.0, "min_distance": 1.0, "max_distance": 40.0},
            color_palette={"family": "history", "primary": "#3D2914", "accent": "#C9A66B", "sky": "#87A8C7"},
            lighting_base="harsh mediterranean sun + cool shadow fill",
            lighting_presets=[
                {"id": "noon", "recipe": "hard sun + short shadows", "mood": "power"},
                {"id": "golden", "recipe": "golden hour rim on marble", "mood": "nostalgia"},
                {"id": "torch_night", "recipe": "torch practicals + cool moonlight", "mood": "drama"},
            ],
            camera_anchors=[
                {"id": "forum_wide", "position": "plaza_center", "angle": "low_hero", "lens_hint": "24mm"},
                {"id": "column_track", "position": "colonnade", "angle": "eye_level", "lens_hint": "35mm"},
                {"id": "statue_detail", "position": "plinth_close", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "oratory", "region": "forum_stage"}],
            transition_anchors=[{"id": "forum_gate", "to_compatible": ["Medieval Village", "Ancient Egypt", "Museum"]}],
        )
    )

    worlds.append(
        _base(
            "Outer Space",
            theme="cosmic scale",
            scale="orbital",
            historical_accuracy=70,
            environment="Deep space field with nebula gradients, distant stars, and a framed planetary body",
            architecture=["orbital frame", "station gantry silhouette"],
            weather="vacuum",
            objects=[
                empty_object(name="observation_module", surface="orbit_plane", x=0.5, y=0.5, z=0.4),
                empty_object(name="satellite", surface="orbit_plane", x=0.7, y=0.6, z=0.3),
            ],
            furniture=[],
            background_animations=["starfield parallax", "nebula drift", "solar flare pulse"],
            sound_ambience=["low thruster rumble", "radio static wash"],
            camera_boundaries={"min_height": -20.0, "max_height": 20.0, "min_distance": 2.0, "max_distance": 200.0},
            color_palette={"family": "space", "primary": "#0A1628", "accent": "#7B2CBF", "highlight": "#E0AAFF"},
            lighting_base="low-key with luminous subject isolation",
            lighting_presets=[
                {"id": "cosmic", "recipe": "cosmic low-key + rim on craft", "mood": "awe"},
                {"id": "sunlit", "recipe": "hard solar key + deep black falloff", "mood": "clarity"},
                {"id": "nebula_glow", "recipe": "magenta/cyan nebula fill", "mood": "wonder"},
            ],
            camera_anchors=[
                {"id": "void_wide", "position": "external", "angle": "establishing", "lens_hint": "14mm"},
                {"id": "craft_orbit", "position": "orbit_path", "angle": "orbit", "lens_hint": "35mm"},
                {"id": "porthole", "position": "viewport", "angle": "internal", "lens_hint": "50mm"},
            ],
            animation_zones=[{"id": "void_drift", "region": "open_space"}],
            transition_anchors=[{"id": "airlock", "to_compatible": ["Mars Colony", "Solar System", "AI Laboratory"]}],
        )
    )

    worlds.append(
        _base(
            "Mars Colony",
            theme="frontier survival",
            scale="habitat",
            historical_accuracy=65,
            environment="Pressurized Mars habitat with dusty copper terrain beyond sealed viewports",
            architecture=["geodesic dome", "airlock ring", "solar array pylons"],
            weather="thin_dust_haze",
            objects=[
                empty_object(name="rover", surface="ground", x=0.7, y=0.0, z=0.35),
                empty_object(name="life_support_console", surface="floor", x=0.4, y=0.0, z=0.5),
            ],
            furniture=[empty_object(name="crew_bunk", surface="floor", x=0.2, y=0.0, z=0.7)],
            background_animations=["dust devil distant", "viewport frost pulse"],
            sound_ambience=["habitat fans", "dust scratch on hull"],
            camera_boundaries={"min_height": 0.4, "max_height": 3.5, "min_distance": 0.6, "max_distance": 25.0},
            color_palette={"family": "space", "primary": "#2B1508", "accent": "#C45C26", "interior": "#1B3A4B"},
            lighting_base="warm interior key + cold Mars exterior spill",
            lighting_presets=_labish_lights("warm habitat key"),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "airlock", "region": "entry"}],
            transition_anchors=[{"id": "rover_bay", "to_compatible": ["Outer Space", "Research Center", "Factory"]}],
        )
    )

    worlds.append(
        _base(
            "Rainforest",
            theme="living canopy",
            scale="biome",
            historical_accuracy=80,
            environment="Dense rainforest understory with filtered green light, mossy trunks, and layered canopy",
            architecture=["natural canopy vault", "fallen-log corridors"],
            weather="humid_mist",
            objects=[
                empty_object(name="giant_fern", surface="ground", x=0.3, y=0.0, z=0.4),
                empty_object(name="research_camera_trap", surface="ground", x=0.55, y=0.0, z=0.5),
            ],
            furniture=[],
            background_animations=["leaf sway", "mist drift", "insect particulates"],
            sound_ambience=["insect chorus", "distant rainfall", "bird calls"],
            camera_boundaries={"min_height": 0.2, "max_height": 12.0, "min_distance": 0.4, "max_distance": 30.0},
            color_palette={"family": "nature", "primary": "#0D2818", "accent": "#2D6A4F", "highlight": "#95D5B2"},
            lighting_base="dappled canopy key + cool understory fill",
            lighting_presets=[
                {"id": "dawn", "recipe": "golden shafts through canopy", "mood": "hope"},
                {"id": "storm", "recipe": "cool diffuse under rain", "mood": "tension"},
                {"id": "night_bio", "recipe": "bioluminescent accents", "mood": "mystery"},
            ],
            camera_anchors=[
                {"id": "ground_crawl", "position": "forest_floor", "angle": "low", "lens_hint": "24mm"},
                {"id": "canopy_up", "position": "mid_trunk", "angle": "upward", "lens_hint": "16mm"},
                {"id": "creature_eye", "position": "clearing", "angle": "eye_level", "lens_hint": "50mm"},
            ],
            animation_zones=[{"id": "clearing", "region": "center"}],
            transition_anchors=[{"id": "trailhead", "to_compatible": ["Nature Preserve", "Ocean Floor", "Research Center"]}],
        )
    )

    worlds.append(
        _base(
            "Ocean Floor",
            theme="abyssal wonder",
            scale="seafloor",
            historical_accuracy=75,
            environment="Bioluminescent ocean floor with coral ridges, particulate water column, and soft blue falloff",
            architecture=["coral reef shelves", "rocky trench walls"],
            weather="underwater_current",
            objects=[
                empty_object(name="coral_cluster", surface="waterbed", x=0.45, y=0.0, z=0.4),
                empty_object(name="research_sub_pod", surface="waterbed", x=0.65, y=0.0, z=0.5),
            ],
            furniture=[],
            background_animations=["particulate drift", "caustic light ripples", "fish school wisp"],
            sound_ambience=["muffled water", "sonar ping", "whale-range rumble"],
            camera_boundaries={"min_height": 0.2, "max_height": 15.0, "min_distance": 0.5, "max_distance": 40.0},
            color_palette={"family": "ocean", "primary": "#0D1B1E", "accent": "#2A9D8F", "glow": "#E9C46A"},
            lighting_base="deep navy key + cyan bioluminescent practicals",
            lighting_presets=[
                {"id": "abyss", "recipe": "dash_ocean_glow", "mood": "awe"},
                {"id": "shaft", "recipe": "surface light shaft + particulate", "mood": "reveal"},
                {"id": "macro_life", "recipe": "hard rim on organism + soft haze", "mood": "curiosity"},
            ],
            camera_anchors=[
                {"id": "reef_wide", "position": "open_water", "angle": "establishing", "lens_hint": "16mm"},
                {"id": "coral_orbit", "position": "reef_edge", "angle": "orbit", "lens_hint": "35mm"},
                {"id": "creature_macro", "position": "substrate_close", "angle": "macro", "lens_hint": "100mm"},
            ],
            animation_zones=[{"id": "reef_pass", "region": "coral_lane"}],
            transition_anchors=[{"id": "upwell", "to_compatible": ["Rainforest", "Human Cell", "Research Center"]}],
        )
    )

    worlds.append(
        _base(
            "Human Cell",
            theme="microscopic life",
            scale="cellular",
            historical_accuracy=70,
            environment="Semi-transparent cell interior with organelles, membrane boundary, and cytoplasmic flow",
            architecture=["lipid membrane dome", "cytoskeleton lattice"],
            weather="cytoplasmic_flow",
            objects=[
                empty_object(name="mitochondrion", surface="cytoplasm", x=0.4, y=0.3, z=0.4),
                empty_object(name="nucleus", surface="cytoplasm", x=0.5, y=0.4, z=0.45),
            ],
            furniture=[],
            background_animations=["vesicle transport", "membrane undulation"],
            sound_ambience=["soft organic pulse", "microscopic whoosh"],
            camera_boundaries={"min_height": 0.0, "max_height": 2.0, "min_distance": 0.1, "max_distance": 5.0},
            color_palette={"family": "lab", "primary": "#1B3A4B", "accent": "#F4A261", "membrane": "#A8DADC"},
            lighting_base="macro_science hard rim + shallow DOF",
            lighting_presets=_labish_lights("warm organelle key"),
            camera_anchors=[
                {"id": "membrane_entry", "position": "boundary", "angle": "push_in", "lens_hint": "24mm"},
                {"id": "nucleus_orbit", "position": "core", "angle": "orbit", "lens_hint": "35mm"},
                {"id": "organelle_macro", "position": "mito_close", "angle": "macro", "lens_hint": "100mm"},
            ],
            animation_zones=[{"id": "transport", "region": "cytoplasm"}],
            transition_anchors=[{"id": "membrane_gate", "to_compatible": ["DNA Interior", "Science Lab", "Hospital"]}],
        )
    )

    worlds.append(
        _base(
            "Hospital",
            theme="clinical care",
            scale="wing",
            historical_accuracy=85,
            environment="Modern hospital corridor with nurse station glow, polished linoleum, and soft fluorescents",
            architecture=["corridor modules", "glass nurse station", "ceiling track lights"],
            weather="indoors",
            objects=[
                empty_object(name="vital_monitor", surface="desk", x=0.5, y=0.9, z=0.35),
                empty_object(name="crash_cart", surface="floor", x=0.3, y=0.0, z=0.55),
            ],
            furniture=[empty_object(name="waiting_chair", surface="floor", x=0.2, y=0.0, z=0.7)],
            background_animations=["monitor waveform crawl", "soft door traffic blur"],
            sound_ambience=["distant page", "soft shoe squeak", "equipment hum"],
            camera_boundaries={"min_height": 0.5, "max_height": 2.5, "min_distance": 0.5, "max_distance": 15.0},
            color_palette={"family": "lab", "primary": "#F1FAEE", "accent": "#457B9D", "warn": "#E63946"},
            lighting_base="soft clinical fluorescents + practical monitor glow",
            lighting_presets=_labish_lights("clinical soft key"),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "nurse_desk", "region": "station"}],
            transition_anchors=[{"id": "or_doors", "to_compatible": ["Operating Room", "Research Center", "University"]}],
        )
    )

    worlds.append(
        _base(
            "Operating Room",
            theme="precision under pressure",
            scale="suite",
            historical_accuracy=85,
            environment="Sterile OR with overhead surgical lights, instrument trays, and green drapes",
            architecture=["sealed suite", "boom arms", "laminar flow ceiling"],
            weather="indoors_sterile",
            objects=[
                empty_object(name="surgical_light", surface="ceiling", x=0.5, y=2.4, z=0.45),
                empty_object(name="instrument_tray", surface="desk", x=0.35, y=1.0, z=0.4),
            ],
            furniture=[empty_object(name="operating_table", surface="floor", x=0.5, y=0.0, z=0.45)],
            background_animations=["light boom micro-adjust", "steam sterilizer haze"],
            sound_ambience=["monitor beep", "suction hiss"],
            camera_boundaries={"min_height": 0.6, "max_height": 2.8, "min_distance": 0.4, "max_distance": 6.0},
            color_palette={"family": "lab", "primary": "#0D1B1E", "accent": "#2A9D8F", "cloth": "#1B4332"},
            lighting_base="hard surgical key + cool ambient",
            lighting_presets=[
                {"id": "surgery_focus", "recipe": "concentrated overhead pool", "mood": "precision"},
                {"id": "wide_sterile", "recipe": "even clinical fill", "mood": "calm"},
                {"id": "crisis", "recipe": "high contrast red-biased practicals", "mood": "urgency"},
            ],
            camera_anchors=[
                {"id": "overhead", "position": "light_boom", "angle": "top_down", "lens_hint": "35mm"},
                {"id": "surgeon_pov", "position": "table_side", "angle": "eye_level", "lens_hint": "50mm"},
                {"id": "tray_detail", "position": "instruments", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "table", "region": "center"}],
            transition_anchors=[{"id": "scrub_door", "to_compatible": ["Hospital", "Science Lab"]}],
        )
    )

    worlds.append(
        _base(
            "Factory",
            theme="industrial process",
            scale="plant",
            historical_accuracy=80,
            environment="High-bay factory floor with conveyor lines, safety markings, and sodium-tinged overheads",
            architecture=["steel trusses", "assembly lanes", "catwalks"],
            weather="indoors_industrial",
            objects=[
                empty_object(name="conveyor", surface="floor", x=0.5, y=0.0, z=0.4),
                empty_object(name="robot_arm", surface="floor", x=0.65, y=0.0, z=0.45),
            ],
            furniture=[empty_object(name="control_panel", surface="floor", x=0.25, y=0.0, z=0.55)],
            background_animations=["sparks intermittent", "conveyor motion"],
            sound_ambience=["machinery rhythm", "safety alarm distant"],
            camera_boundaries={"min_height": 0.5, "max_height": 12.0, "min_distance": 1.0, "max_distance": 50.0},
            color_palette={"family": "tech", "primary": "#1A1A1A", "accent": "#F4A261", "safety": "#E9C46A"},
            lighting_base="industrial sodium key + cool skylight spill",
            lighting_presets=_labish_lights("industrial hard key"),
            camera_anchors=[
                {"id": "bay_wide", "position": "catwalk", "angle": "high", "lens_hint": "24mm"},
                {"id": "line_track", "position": "conveyor", "angle": "tracking", "lens_hint": "35mm"},
                {"id": "machine_macro", "position": "arm_close", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "assembly", "region": "line"}],
            transition_anchors=[{"id": "loading_dock", "to_compatible": ["Research Center", "Future City", "AI Laboratory"]}],
        )
    )

    worlds.append(
        _base(
            "DNA Interior",
            theme="genetic architecture",
            scale="molecular",
            historical_accuracy=70,
            environment="Monumental DNA helix corridor with glowing base-pair rungs and molecular fog",
            architecture=["double helix rails", "base-pair bridges"],
            weather="molecular_haze",
            objects=[
                empty_object(name="base_pair_rung", surface="helix", x=0.5, y=0.5, z=0.4),
                empty_object(name="enzyme_motif", surface="helix", x=0.45, y=0.55, z=0.35),
            ],
            furniture=[],
            background_animations=["helix slow rotate", "charge sparkles along rails"],
            sound_ambience=["harmonic drone", "soft click sequencing"],
            camera_boundaries={"min_height": 0.0, "max_height": 10.0, "min_distance": 0.2, "max_distance": 20.0},
            color_palette={"family": "lab", "primary": "#0B1D36", "accent": "#E63946", "pair": "#457B9D"},
            lighting_base="scientific rim + neon pair practicals",
            lighting_presets=_labish_lights("bioluminescent helix key"),
            camera_anchors=[
                {"id": "helix_flythrough", "position": "axis", "angle": "push_in", "lens_hint": "24mm"},
                {"id": "rung_orbit", "position": "mid_helix", "angle": "orbit", "lens_hint": "35mm"},
                {"id": "pair_macro", "position": "rung_close", "angle": "macro", "lens_hint": "100mm"},
            ],
            animation_zones=[{"id": "replication_fork", "region": "mid"}],
            transition_anchors=[{"id": "uncoil", "to_compatible": ["Human Cell", "Science Lab", "Research Center"]}],
        )
    )

    worlds.append(
        _base(
            "Solar System",
            theme="orbital order",
            scale="system",
            historical_accuracy=80,
            environment="Scaled solar system diorama with sun core, planetary orbits, and soft dust plane",
            architecture=["orbital rings", "sun pedestal"],
            weather="vacuum_dust",
            objects=[
                empty_object(name="sun", surface="orbit_plane", x=0.5, y=0.5, z=0.5),
                empty_object(name="earth", surface="orbit_plane", x=0.65, y=0.5, z=0.45),
            ],
            furniture=[],
            background_animations=["orbit paths rotate", "sun prominence flicker"],
            sound_ambience=["deep tonal bed", "soft whoosh"],
            camera_boundaries={"min_height": -5.0, "max_height": 5.0, "min_distance": 1.0, "max_distance": 80.0},
            color_palette={"family": "space", "primary": "#0A1628", "accent": "#F4A261", "ice": "#E0AAFF"},
            lighting_base="sun-centered key with falloff by distance",
            lighting_presets=[
                {"id": "system_wide", "recipe": "even soft fill on orbits", "mood": "overview"},
                {"id": "sun_flare", "recipe": "lens flare solar punch", "mood": "energy"},
                {"id": "planet_night", "recipe": "terminator light on globe", "mood": "focus"},
            ],
            camera_anchors=[
                {"id": "top_down_system", "position": "above_ecliptic", "angle": "overhead", "lens_hint": "16mm"},
                {"id": "earth_approach", "position": "orbit", "angle": "push_in", "lens_hint": "50mm"},
                {"id": "sun_side", "position": "corona", "angle": "side", "lens_hint": "35mm"},
            ],
            animation_zones=[{"id": "ecliptic", "region": "plane"}],
            transition_anchors=[{"id": "jump_gate", "to_compatible": ["Outer Space", "Mars Colony", "Museum"]}],
        )
    )

    worlds.append(
        _base(
            "Medieval Village",
            theme="pre-industrial life",
            scale="village",
            historical_accuracy=75,
            environment="Timber-framed village square with thatched roofs, dirt road, and hearth smoke",
            architecture=["timber frames", "stone well", "market stalls"],
            weather="overcast_cool",
            objects=[
                empty_object(name="market_cart", surface="ground", x=0.4, y=0.0, z=0.45),
                empty_object(name="well", surface="ground", x=0.55, y=0.0, z=0.5),
            ],
            furniture=[empty_object(name="barrel", surface="ground", x=0.3, y=0.0, z=0.55)],
            background_animations=["smoke drift", "banner flap", "chicken flock hint"],
            sound_ambience=["blacksmith distant", "crowd murmur", "wind"],
            camera_boundaries={"min_height": 0.4, "max_height": 6.0, "min_distance": 0.6, "max_distance": 30.0},
            color_palette={"family": "history", "primary": "#2C1810", "accent": "#8B5E34", "sky": "#6B7C8A"},
            lighting_base="soft overcast key + warm hearth practicals",
            lighting_presets=[
                {"id": "day", "recipe": "diffuse sky light", "mood": "everyday"},
                {"id": "dusk", "recipe": "warm hearth + cool blue fill", "mood": "story"},
                {"id": "storm", "recipe": "cool low-key + wet reflections", "mood": "tension"},
            ],
            camera_anchors=[
                {"id": "square_wide", "position": "plaza", "angle": "eye_level", "lens_hint": "24mm"},
                {"id": "street_track", "position": "lane", "angle": "tracking", "lens_hint": "35mm"},
                {"id": "craft_detail", "position": "stall", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "market", "region": "square"}],
            transition_anchors=[{"id": "village_gate", "to_compatible": ["Ancient Rome", "Courtroom", "Nature Preserve"]}],
        )
    )

    worlds.append(
        _base(
            "Courtroom",
            theme="civic judgment",
            scale="chamber",
            historical_accuracy=85,
            environment="Formal courtroom with wood paneling, elevated bench, and seal emblem",
            architecture=["raised bench", "jury box", "aisle columns"],
            weather="indoors",
            objects=[
                empty_object(name="gavel_block", surface="desk", x=0.5, y=1.1, z=0.3),
                empty_object(name="evidence_table", surface="floor", x=0.45, y=0.0, z=0.5),
            ],
            furniture=[
                empty_object(name="witness_stand", surface="floor", x=0.35, y=0.0, z=0.4),
                empty_object(name="gallery_pews", surface="floor", x=0.5, y=0.0, z=0.75),
            ],
            background_animations=["dust in window light", "flag micro-sway"],
            sound_ambience=["room tone", "soft cough", "pen scratch"],
            camera_boundaries={"min_height": 0.5, "max_height": 3.0, "min_distance": 0.8, "max_distance": 12.0},
            color_palette={"family": "history", "primary": "#1A120B", "accent": "#C9A66B", "cloth": "#4A0000"},
            lighting_base="window soft key + warm wood bounce",
            lighting_presets=_labish_lights("formal soft key"),
            camera_anchors=[
                {"id": "bench_hero", "position": "aisle", "angle": "low", "lens_hint": "28mm"},
                {"id": "jury_side", "position": "jury", "angle": "side", "lens_hint": "50mm"},
                {"id": "gavel_macro", "position": "bench", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "arguments", "region": "center_aisle"}],
            transition_anchors=[{"id": "courthouse_door", "to_compatible": ["Library", "University", "Stock Exchange"]}],
        )
    )

    worlds.append(
        _base(
            "Stock Exchange",
            theme="market energy",
            scale="trading_floor",
            historical_accuracy=80,
            environment="Trading floor with ticker walls, pit geometry, and high-contrast screens",
            architecture=["mezzanine ring", "pit steps", "LED ticker wall"],
            weather="indoors",
            objects=[
                empty_object(name="ticker_wall", surface="wall", x=0.5, y=1.5, z=0.1),
                empty_object(name="trader_terminal", surface="desk", x=0.4, y=0.9, z=0.45),
            ],
            furniture=[empty_object(name="pit_desk", surface="floor", x=0.5, y=0.0, z=0.5)],
            background_animations=["ticker scroll", "crowd energy blur"],
            sound_ambience=["bell clamor", "crowd shout wash", "keyboard chatter"],
            camera_boundaries={"min_height": 0.5, "max_height": 8.0, "min_distance": 0.6, "max_distance": 25.0},
            color_palette={"family": "finance", "primary": "#0B1D36", "accent": "#2A9D8F", "alert": "#E63946"},
            lighting_base="cool screen spill + warm overheads",
            lighting_presets=[
                {"id": "open_bell", "recipe": "bright high-energy key", "mood": "surge"},
                {"id": "after_hours", "recipe": "low-key blue screens", "mood": "aftermath"},
                {"id": "crash", "recipe": "red-biased practicals + hard contrast", "mood": "panic"},
            ],
            camera_anchors=[
                {"id": "floor_wide", "position": "mezzanine", "angle": "high", "lens_hint": "24mm"},
                {"id": "pit_track", "position": "pit", "angle": "handheld_energy", "lens_hint": "35mm"},
                {"id": "ticker_macro", "position": "wall", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "pit", "region": "center"}],
            transition_anchors=[{"id": "lobby", "to_compatible": ["Future City", "Courtroom", "University"]}],
        )
    )

    worlds.append(
        _base(
            "Ancient Egypt",
            theme="monumental myth",
            scale="complex",
            historical_accuracy=75,
            environment="Sun-baked temple court with hieroglyph columns, sand floor, and pyramid silhouette",
            architecture=["pylon gates", "obelisks", "columned hypostyle"],
            weather="desert_clear",
            objects=[
                empty_object(name="sphinx_fragment", surface="ground", x=0.35, y=0.0, z=0.4),
                empty_object(name="offering_table", surface="ground", x=0.5, y=0.0, z=0.5),
            ],
            furniture=[],
            background_animations=["sand drift", "heat shimmer", "linen flap"],
            sound_ambience=["desert wind", "distant drum"],
            camera_boundaries={"min_height": 0.4, "max_height": 20.0, "min_distance": 1.0, "max_distance": 80.0},
            color_palette={"family": "history", "primary": "#3D2914", "accent": "#C9A66B", "sky": "#87CEEB"},
            lighting_base="hard desert sun + warm stone bounce",
            lighting_presets=[
                {"id": "noon", "recipe": "hard sun short shadows", "mood": "monumental"},
                {"id": "dusk", "recipe": "golden wash on sandstone", "mood": "mythic"},
                {"id": "torch_crypt", "recipe": "torch practicals + cool blue fill", "mood": "mystery"},
            ],
            camera_anchors=[
                {"id": "pylon_wide", "position": "court", "angle": "low_hero", "lens_hint": "24mm"},
                {"id": "column_track", "position": "hypostyle", "angle": "tracking", "lens_hint": "35mm"},
                {"id": "glyph_macro", "position": "wall", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "ritual_court", "region": "center"}],
            transition_anchors=[{"id": "nile_path", "to_compatible": ["Museum", "Ancient Rome", "Library"]}],
        )
    )

    worlds.append(
        _base(
            "Future City",
            theme="speculative metro",
            scale="metropolitan",
            historical_accuracy=40,
            environment="Neon megacity terraces with maglev ribbons, holographic ads, and rain-slick glass",
            architecture=["spire towers", "skybridges", "vertical gardens"],
            weather="neon_rain",
            objects=[
                empty_object(name="holo_kiosk", surface="ground", x=0.4, y=0.0, z=0.45),
                empty_object(name="drone_pad", surface="ground", x=0.6, y=0.0, z=0.5),
            ],
            furniture=[empty_object(name="transit_bench", surface="ground", x=0.3, y=0.0, z=0.6)],
            background_animations=["traffic light streaks", "rain streaks", "holo flicker"],
            sound_ambience=["rain on glass", "distant transit hum", "ad chatter wash"],
            camera_boundaries={"min_height": 0.5, "max_height": 80.0, "min_distance": 1.0, "max_distance": 120.0},
            color_palette={"family": "tech", "primary": "#0A1628", "accent": "#7B2CBF", "neon": "#00F5D4"},
            lighting_base="neon practicals + wet reflection bounce",
            lighting_presets=[
                {"id": "rain_night", "recipe": "cyan/magenta neon + rain reflections", "mood": "future"},
                {"id": "dawn_clear", "recipe": "cool blue hour on glass", "mood": "hope"},
                {"id": "alert", "recipe": "red emergency beacons", "mood": "crisis"},
            ],
            camera_anchors=[
                {"id": "skyline", "position": "rooftop", "angle": "wide", "lens_hint": "16mm"},
                {"id": "street_chase", "position": "lane", "angle": "handheld_energy", "lens_hint": "28mm"},
                {"id": "holo_macro", "position": "kiosk", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "plaza", "region": "terrace"}],
            transition_anchors=[{"id": "transit_hub", "to_compatible": ["AI Laboratory", "Stock Exchange", "Factory"]}],
        )
    )

    worlds.append(
        _base(
            "Nature Preserve",
            theme="protected wild",
            scale="landscape",
            historical_accuracy=85,
            environment="Open grassland preserve with distant ridgeline, observation path, and golden hour fields",
            architecture=["boardwalk", "observation hut"],
            weather="clear_breeze",
            objects=[
                empty_object(name="viewing_scope", surface="ground", x=0.45, y=0.0, z=0.45),
                empty_object(name="trail_marker", surface="ground", x=0.35, y=0.0, z=0.55),
            ],
            furniture=[empty_object(name="log_bench", surface="ground", x=0.25, y=0.0, z=0.6)],
            background_animations=["grass sway", "cloud drift", "bird flock pass"],
            sound_ambience=["wind in grass", "insect bed", "distant wildlife"],
            camera_boundaries={"min_height": 0.3, "max_height": 15.0, "min_distance": 0.5, "max_distance": 60.0},
            color_palette={"family": "nature", "primary": "#1B4332", "accent": "#95D5B2", "sky": "#A8DADC"},
            lighting_base="golden natural key + soft sky fill",
            lighting_presets=[
                {"id": "golden", "recipe": "warm side light", "mood": "serenity"},
                {"id": "overcast", "recipe": "soft diffuse", "mood": "documentary"},
                {"id": "storm_edge", "recipe": "cool edge light", "mood": "drama"},
            ],
            camera_anchors=[
                {"id": "ridge_wide", "position": "overlook", "angle": "establishing", "lens_hint": "24mm"},
                {"id": "trail_walk", "position": "path", "angle": "follow", "lens_hint": "35mm"},
                {"id": "flora_macro", "position": "ground", "angle": "macro", "lens_hint": "100mm"},
            ],
            animation_zones=[{"id": "meadow", "region": "center"}],
            transition_anchors=[{"id": "trailhead", "to_compatible": ["Rainforest", "University", "Research Center"]}],
        )
    )

    worlds.append(
        _base(
            "University",
            theme="academic inquiry",
            scale="campus",
            historical_accuracy=85,
            environment="Campus quad with lecture hall facade, lawn paths, and warm stone façades",
            architecture=["lecture hall", "colonnade", "library wing link"],
            weather="clear_mild",
            objects=[
                empty_object(name="quad_statue", surface="ground", x=0.5, y=0.0, z=0.4),
                empty_object(name="bike_rack", surface="ground", x=0.3, y=0.0, z=0.55),
            ],
            furniture=[empty_object(name="outdoor_table", surface="ground", x=0.4, y=0.0, z=0.6)],
            background_animations=["leaf fall light", "student traffic soft"],
            sound_ambience=["distant bell", "foot traffic", "birds"],
            camera_boundaries={"min_height": 0.5, "max_height": 10.0, "min_distance": 0.8, "max_distance": 40.0},
            color_palette={"family": "science_core", "primary": "#0B1D36", "accent": "#F4A261", "stone": "#E8F1F8"},
            lighting_base="soft daylight + warm stone bounce",
            lighting_presets=_labish_lights("campus daylight"),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "quad", "region": "lawn"}],
            transition_anchors=[{"id": "hall_doors", "to_compatible": ["Library", "Research Center", "Science Lab"]}],
        )
    )

    worlds.append(
        _base(
            "Library",
            theme="quiet knowledge",
            scale="reading_room",
            historical_accuracy=85,
            environment="Multi-level library with oak stacks, reading lamps, and dust-mote sunbeams",
            architecture=["mezzanine stacks", "vaulted reading room", "iron spiral stair"],
            weather="indoors",
            objects=[
                empty_object(name="atlas_stand", surface="floor", x=0.45, y=0.0, z=0.45),
                empty_object(name="card_catalog", surface="floor", x=0.3, y=0.0, z=0.5),
            ],
            furniture=[
                empty_object(name="reading_table", surface="floor", x=0.5, y=0.0, z=0.55),
                empty_object(name="lamp", surface="desk", x=0.5, y=0.9, z=0.5),
            ],
            background_animations=["dust motes", "page turn hint", "lamp flicker soft"],
            sound_ambience=["quiet room tone", "distant page", "clock soft"],
            camera_boundaries={"min_height": 0.5, "max_height": 6.0, "min_distance": 0.5, "max_distance": 20.0},
            color_palette={"family": "history", "primary": "#2C1810", "accent": "#C9A66B", "paper": "#F1FAEE"},
            lighting_base="warm lamp practicals + cool window shafts",
            lighting_presets=_labish_lights("warm reading key"),
            camera_anchors=[
                {"id": "stacks_wide", "position": "aisle", "angle": "eye_level", "lens_hint": "24mm"},
                {"id": "table_medium", "position": "reading", "angle": "slight_high", "lens_hint": "35mm"},
                {"id": "book_macro", "position": "table", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "reading", "region": "tables"}],
            transition_anchors=[{"id": "archive_door", "to_compatible": ["University", "Museum", "Research Center"]}],
        )
    )

    worlds.append(
        _base(
            "Research Center",
            theme="systematic discovery",
            scale="campus_lab",
            historical_accuracy=85,
            environment="Modern research atrium linking lab wings, glass bridges, and data walls",
            architecture=["glass atrium", "bridge links", "lab wing portals"],
            weather="indoors",
            objects=[
                empty_object(name="data_wall", surface="wall", x=0.5, y=1.6, z=0.1),
                empty_object(name="sample_cart", surface="floor", x=0.4, y=0.0, z=0.5),
            ],
            furniture=[empty_object(name="collaboration_table", surface="floor", x=0.5, y=0.0, z=0.55)],
            background_animations=["data wall pulse", "glass reflection drift"],
            sound_ambience=["atrium reverb", "soft step", "HVAC"],
            camera_boundaries={"min_height": 0.5, "max_height": 12.0, "min_distance": 0.6, "max_distance": 30.0},
            color_palette={"family": "lab", "primary": "#101820", "accent": "#457B9D", "glass": "#A8DADC"},
            lighting_base="cool atrium daylight simulation + practical screens",
            lighting_presets=_labish_lights(),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "atrium", "region": "center"}],
            transition_anchors=[{"id": "lab_wing", "to_compatible": ["Science Lab", "AI Laboratory", "University", "Hospital"]}],
        )
    )

    worlds.append(
        _base(
            "AI Laboratory",
            theme="synthetic cognition",
            scale="server_hall",
            historical_accuracy=50,
            environment="Dim AI lab with rack glow, holographic neural volumes, and black reflective floor",
            architecture=["server aisles", "hologram stage", "observation glass"],
            weather="indoors_cooled",
            objects=[
                empty_object(name="neural_holo", object_id="obj_neural_holo", surface="floor", x=0.5, y=0.0, z=0.45, zone="holo_stage", relationships=["ops_console"]),
                empty_object(name="server_rack", object_id="obj_server_rack", surface="floor", x=0.7, y=0.0, z=0.4, zone="server_aisle", relationships=[]),
                empty_object(name="training_monitor", object_id="obj_training_monitor", surface="desk", x=0.4, y=0.9, z=0.5, zone="workstation"),
            ],
            furniture=[
                empty_object(name="ops_console", object_id="obj_ops_console", surface="floor", x=0.35, y=0.0, z=0.55, zone="holo_stage"),
                empty_object(name="workstation_desk", object_id="obj_workstation_desk", surface="floor", x=0.25, y=0.0, z=0.6, zone="workstation"),
            ],
            background_animations=["rack LED cascade", "holo voxel churn", "cooling fog"],
            sound_ambience=["server whine", "soft UI beeps", "coolant hiss", "AI laboratory hum"],
            camera_boundaries={"min_height": 0.4, "max_height": 4.0, "min_distance": 0.5, "max_distance": 18.0},
            color_palette={"family": "tech", "primary": "#0A1628", "accent": "#00F5D4", "warn": "#7B2CBF"},
            lighting_base="low-key rack practicals + cyan holo glow",
            lighting_presets=[
                {"id": "boot", "recipe": "cascade power-on practicals", "mood": "ignition"},
                {"id": "inference", "recipe": "cyan volumetric holo", "mood": "think"},
                {"id": "alert", "recipe": "magenta fault strobes", "mood": "failure"},
            ],
            camera_anchors=[
                {"id": "hall_wide", "position": "aisle_end", "angle": "establishing", "lens_hint": "24mm"},
                {"id": "holo_orbit", "position": "stage", "angle": "orbit", "lens_hint": "35mm"},
                {"id": "console_macro", "position": "ops", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "holo_stage", "region": "center"}],
            transition_anchors=[{"id": "airlock_lab", "to_compatible": ["Research Center", "Future City", "Science Lab", "Factory"]}],
        )
    )
    # Enrich AI Laboratory with persistent multi-zone layout
    worlds[-1].update(
        {
            "category": "AI Research Laboratory",
            "applicable_topics": ["artificial intelligence", "machine learning", "pattern recognition", "neural networks"],
            "time_periods": ["near_future", "present"],
            "audiences": ["general_public", "students"],
            "visual_styles": ["documentary_lab", "tech_explainer"],
            "scientific_accuracy": 75,
            "scientific_constraints": ["Compute racks remain grounded", "Hologram volume stays at stage center unless moved by state event"],
            "historical_constraints": [],
            "accuracy": {"scientific": 75, "uncertainties": ["Holographic UI is illustrative"]},
            "aesthetic": {"materials": ["matte black metal", "glass", "LED arrays"], "era": "near_future", "design_language": "clean-tech"},
            "ambient_practicals": ["rack LEDs", "holo glow", "console screens"],
            "allowed_subject_positions": [
                {"id": "beside_holo", "zone": "holo_stage", "x": 0.4, "z": 0.5},
                {"id": "at_workstation", "zone": "workstation", "x": 0.3, "z": 0.55},
                {"id": "aisle_observe", "zone": "server_aisle", "x": 0.55, "z": 0.4},
            ],
            "zones": [
                {
                    "id": "holo_stage",
                    "name": "Holographic Model Stage",
                    "description": "Central stage with luminous neural volume",
                    "landmarks": ["neural_holo", "ops_console"],
                    "entrances": ["from_aisle"],
                    "exits": ["to_workstation"],
                    "connections": ["workstation", "server_aisle"],
                    "doors": ["stage_glass"],
                    "allowed_subject_positions": [{"id": "beside_holo", "x": 0.4, "z": 0.5}],
                    "restricted_areas": ["inside_holo_volume"],
                    "ambient_activity": ["holo voxel churn"],
                    "ambience": ["soft UI beeps"],
                },
                {
                    "id": "workstation",
                    "name": "Training Workstation",
                    "description": "Operator desk with training monitors",
                    "landmarks": ["workstation_desk", "training_monitor"],
                    "entrances": ["from_holo_stage"],
                    "exits": ["to_server_aisle"],
                    "connections": ["holo_stage", "server_aisle"],
                    "allowed_subject_positions": [{"id": "at_workstation", "x": 0.3, "z": 0.55}],
                    "restricted_areas": [],
                    "ambient_activity": ["monitor scroll"],
                    "ambience": ["keyboard soft"],
                },
                {
                    "id": "server_aisle",
                    "name": "Server Aisle",
                    "description": "Cooled rack corridor with LED cascade",
                    "landmarks": ["server_rack"],
                    "entrances": ["from_workstation"],
                    "exits": ["to_holo_stage"],
                    "connections": ["holo_stage", "workstation"],
                    "allowed_subject_positions": [{"id": "aisle_observe", "x": 0.55, "z": 0.4}],
                    "restricted_areas": ["rack_interior"],
                    "ambient_activity": ["rack LED cascade", "cooling fog"],
                    "ambience": ["server whine", "coolant hiss"],
                },
            ],
        }
    )

    worlds.append(
        _base(
            "Ocean Research Observatory",
            theme="marine science",
            scale="facility",
            historical_accuracy=80,
            environment="Coastal ocean research observatory with sealed viewing glass, wet-lab benches, and deep-blue water beyond",
            architecture=["observation dome", "pressure-glass wall", "steel catwalk", "display alcove"],
            weather="indoors_coastal",
            objects=[
                empty_object(name="main_aquarium_viewport", object_id="obj_aquarium_viewport", surface="wall", x=0.5, y=1.2, z=0.05, zone="underwater_viewing", relationships=["specimen_label_panel"]),
                empty_object(name="octopus_specimen_tank_marker", object_id="obj_octopus_marker", surface="floor", x=0.55, y=0.0, z=0.35, zone="underwater_viewing"),
                empty_object(name="holographic_anatomy_display", object_id="obj_anatomy_display", surface="desk", x=0.4, y=0.9, z=0.5, zone="scientific_display"),
                empty_object(name="heart_diagram_panel", object_id="obj_heart_panel", surface="wall", x=0.65, y=1.4, z=0.1, zone="scientific_display"),
                empty_object(name="research_console", object_id="obj_research_console", surface="floor", x=0.35, y=0.0, z=0.55, zone="observation_chamber"),
                empty_object(name="diving_lock_marker", object_id="obj_diving_lock", surface="floor", x=0.2, y=0.0, z=0.7, zone="observation_chamber"),
            ],
            furniture=[
                empty_object(name="observation_bench", object_id="obj_obs_bench", surface="floor", x=0.3, y=0.0, z=0.6, zone="observation_chamber"),
                empty_object(name="display_table", object_id="obj_display_table", surface="floor", x=0.45, y=0.0, z=0.5, zone="scientific_display"),
            ],
            background_animations=["caustic water light on glass", "bubble column", "soft monitor waveforms"],
            sound_ambience=["ocean ambience through glass", "laboratory hum", "soft sonar ping"],
            camera_boundaries={"min_height": 0.4, "max_height": 4.0, "min_distance": 0.5, "max_distance": 16.0},
            color_palette={"family": "ocean", "primary": "#0D1B1E", "accent": "#2A9D8F", "glow": "#E9C46A"},
            lighting_base="cool marine spill from viewport + warm console practicals",
            lighting_presets=[
                {"id": "observation", "recipe": "viewport blue spill + soft fill", "mood": "wonder"},
                {"id": "display", "recipe": "panel glow + cool ambient", "mood": "teach"},
                {"id": "deep_view", "recipe": "caustic ripple strength up", "mood": "immersion"},
            ],
            camera_anchors=[
                {"id": "chamber_wide", "position": "observation_chamber", "angle": "eye_level", "lens_hint": "24mm"},
                {"id": "glass_close", "position": "underwater_viewing", "angle": "toward_glass", "lens_hint": "35mm"},
                {"id": "display_detail", "position": "scientific_display", "angle": "macro", "lens_hint": "85mm"},
            ],
            animation_zones=[{"id": "viewport", "region": "glass"}, {"id": "display", "region": "station"}],
            transition_anchors=[{"id": "wet_lab_door", "to_compatible": ["Ocean Floor", "Research Center", "Science Lab"]}],
        )
    )
    worlds[-1].update(
        {
            "category": "Ocean Research Observatory",
            "applicable_topics": ["octopus", "marine biology", "cephalopods", "circulation", "three hearts"],
            "time_periods": ["present"],
            "audiences": ["general_public"],
            "visual_styles": ["science_short", "nature_doc"],
            "scientific_accuracy": 88,
            "scientific_constraints": [
                "Octopus systemic + branchial hearts depiction must remain anatomically labeled as educational model",
                "Viewport glass separates dry observatory from seawater",
                "Equipment stays grounded on benches or floors",
            ],
            "historical_constraints": [],
            "accuracy": {
                "scientific": 88,
                "geographic": "generic coastal observatory (not a named facility)",
                "uncertainties": ["Exact tank geometry is illustrative"],
                "sources": ["standard cephalopod circulatory education models"],
            },
            "aesthetic": {
                "materials": ["glass", "brushed steel", "wet-lab epoxy"],
                "era": "present",
                "design_language": "marine_research",
                "brand_compatibility": "youtube_shorts_science",
            },
            "ambient_practicals": ["viewport caustics", "console LEDs", "display panel glow"],
            "allowed_subject_positions": [
                {"id": "console_side", "zone": "observation_chamber", "x": 0.35, "z": 0.5},
                {"id": "glass_front", "zone": "underwater_viewing", "x": 0.5, "z": 0.35},
                {"id": "display_presenter", "zone": "scientific_display", "x": 0.4, "z": 0.55},
            ],
            "restricted_areas": ["inside_water_volume"],
            "zones": [
                {
                    "id": "observation_chamber",
                    "name": "Observation Chamber",
                    "description": "Dry observatory room with research console facing the facility",
                    "landmarks": ["research_console", "diving_lock_marker", "observation_bench"],
                    "entrances": ["facility_entry"],
                    "exits": ["to_underwater_viewing"],
                    "connections": ["underwater_viewing", "scientific_display"],
                    "doors": ["facility_entry", "viewing_door"],
                    "allowed_subject_positions": [{"id": "console_side", "x": 0.35, "z": 0.5}],
                    "restricted_areas": [],
                    "ambient_activity": ["soft monitor waveforms"],
                    "ambience": ["laboratory hum"],
                },
                {
                    "id": "underwater_viewing",
                    "name": "Underwater Viewing Area",
                    "description": "Pressure-glass wall looking into blue water with specimen markers",
                    "landmarks": ["main_aquarium_viewport", "octopus_specimen_tank_marker"],
                    "entrances": ["from_observation_chamber"],
                    "exits": ["to_scientific_display"],
                    "connections": ["observation_chamber", "scientific_display"],
                    "doors": ["viewing_door"],
                    "allowed_subject_positions": [{"id": "glass_front", "x": 0.5, "z": 0.35}],
                    "restricted_areas": ["inside_water_volume"],
                    "ambient_activity": ["caustic water light on glass", "bubble column"],
                    "ambience": ["ocean ambience through glass", "soft sonar ping"],
                },
                {
                    "id": "scientific_display",
                    "name": "Scientific Display Station",
                    "description": "Anatomy display station with heart diagram and holographic model",
                    "landmarks": ["holographic_anatomy_display", "heart_diagram_panel", "display_table"],
                    "entrances": ["from_underwater_viewing"],
                    "exits": ["to_observation_chamber"],
                    "connections": ["underwater_viewing", "observation_chamber"],
                    "doors": [],
                    "allowed_subject_positions": [{"id": "display_presenter", "x": 0.4, "z": 0.55}],
                    "restricted_areas": [],
                    "ambient_activity": ["display pulse"],
                    "ambience": ["quiet room tone"],
                },
            ],
        }
    )
    # Fix kwargs for empty_object - global is not a param; set after
    for o in worlds[-1]["objects"]:
        if o.get("object_id") == "obj_octopus_marker":
            o["global"] = True

    worlds.append(
        _base(
            "Microscopic Biological Environment",
            theme="microscopic life field",
            scale="microscopic",
            historical_accuracy=70,
            environment="Soft-focus microscopic field with particulate medium and membrane boundaries",
            architecture=["membrane dome", "particulate volume"],
            weather="fluid_medium",
            objects=[
                empty_object(name="focal_microbe", surface="cytoplasm", x=0.5, y=0.4, z=0.45, zone="field_center"),
            ],
            furniture=[],
            background_animations=["particulate brownian drift"],
            sound_ambience=["soft organic pulse"],
            camera_boundaries={"min_height": 0.0, "max_height": 2.0, "min_distance": 0.1, "max_distance": 4.0},
            color_palette={"family": "lab", "primary": "#1B3A4B", "accent": "#F4A261"},
            lighting_base="macro scientific rim",
            lighting_presets=_labish_lights("warm microscopic key"),
            camera_anchors=_labish_anchors(),
            animation_zones=[{"id": "field", "region": "center"}],
            transition_anchors=[{"id": "zoom_out", "to_compatible": ["Human Cell", "DNA Interior", "Science Lab"]}],
        )
    )
    worlds[-1]["zones"] = [
        {
            "id": "field_center",
            "name": "Focal Field",
            "description": "Center of microscopic volume",
            "landmarks": ["focal_microbe"],
            "connections": [],
            "allowed_subject_positions": [{"id": "center", "x": 0.5, "z": 0.45}],
            "restricted_areas": [],
            "ambient_activity": ["particulate brownian drift"],
            "ambience": ["soft organic pulse"],
        }
    ]

    catalog = {w["world_id"]: w for w in worlds}
    # Ensure all mission types present
    for wt in WORLD_TYPES:
        if world_id_for_type(wt) not in catalog:
            raise RuntimeError(f"missing world definition: {wt}")
    return catalog


_CATALOG: dict[str, dict[str, Any]] | None = None


def get_catalog() -> dict[str, dict[str, Any]]:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = build_catalog()
    return _CATALOG


def get_world(world_id: str = "", world_type: str = "") -> dict[str, Any] | None:
    cat = get_catalog()
    if world_id and world_id in cat:
        return dict(cat[world_id])
    if world_type:
        return dict(cat.get(world_id_for_type(world_type)) or {})
    return None


def list_world_types() -> list[str]:
    return list(WORLD_TYPES)


def select_world_type(*, topic: str = "", niche: str = "", script: str = "", preferred: str = "") -> str:
    """Map topic/niche/script → world type."""
    if preferred and preferred in WORLD_TYPES:
        return preferred
    topic_blob = f"{topic} {script}".lower()
    niche_blob = niche.lower()
    scores: list[tuple[int, str]] = []
    for wt, hints in _TOPIC_HINTS.items():
        topic_score = sum(2 for h in hints if _contains_hint(topic_blob, h))
        niche_score = sum(1 for h in hints if _contains_hint(niche_blob, h))
        score = topic_score + niche_score
        if score:
            scores.append((score, wt))
    if scores:
        scores.sort(key=lambda x: (-x[0], x[1]))
        return scores[0][1]
    niche_map = {
        "biology": "Science Lab",
        "science": "Research Center",
        "history": "Museum",
        "psychology": "University",
        "finance": "Stock Exchange",
        "nature": "Nature Preserve",
        "technology": "AI Laboratory",
        "space": "Outer Space",
        "medicine": "Hospital",
    }
    for k, wt in niche_map.items():
        if k in niche_blob:
            return wt
    return "Research Center"
