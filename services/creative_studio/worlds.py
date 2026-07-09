"""World Engine — persistent worlds productions live inside.

A world is a story-level setting (WORLD_FIELDS): its lighting,
architecture, textures, mood, weather, camera language, and environmental
storytelling persist between productions, so a channel's videos feel like
chapters of one place rather than disconnected clips. Worlds stage scenes
in the reusable environments they contain (environments.py).

`register_world()` adds custom worlds at runtime; `select_world()` casts
deterministically from content signals.
"""

from __future__ import annotations

WORLD_ENGINE_VERSION = "1.0"

DEFAULT_WORLD = "neutral_studio_world"

_WORLDS: "dict[str, dict]" = {}


def register_world(world: dict) -> dict:
    """Register (or replace) one persistent world."""
    stored = {
        "world_id": world["world_id"],
        "label": world.get("label", world["world_id"]),
        "description": world.get("description", ""),
        "lighting": world.get("lighting", ""),
        "architecture": world.get("architecture", ""),
        "textures": world.get("textures", ""),
        "mood": world.get("mood", ""),
        "weather": world.get("weather", ""),
        "camera_language": world.get("camera_language", ""),
        "environmental_storytelling": world.get("environmental_storytelling", ""),
        "environments": list(world.get("environments", [])),
        "keywords": list(world.get("keywords", [])),
        "brand_id": world.get("brand_id", ""),
    }
    _WORLDS[stored["world_id"]] = stored
    return stored


def get_world(world_id: str) -> "dict | None":
    return _WORLDS.get(world_id)


def all_worlds() -> "list[dict]":
    return list(_WORLDS.values())


def world_ids() -> "list[str]":
    return list(_WORLDS.keys())


def select_world(item: dict) -> dict:
    """The persistent world for one item (deterministic).

    Explicit `world_id` request wins; otherwise the best keyword match;
    otherwise the neutral studio world — every production has a world.
    """
    requested = str(item.get("world_id", "")).strip()
    if requested and requested in _WORLDS:
        return dict(_WORLDS[requested])

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
    best_id, best_score = DEFAULT_WORLD, 0
    for world_id, world in _WORLDS.items():
        score = sum(1 for keyword in world["keywords"] if keyword in signals)
        if score > best_score:
            best_id, best_score = world_id, score
    return dict(_WORLDS[best_id])


# --------------------------------------------------------------- built-ins

_BUILTINS = (
    {
        "world_id": "neutral_studio_world",
        "label": "The Studio",
        "description": "A neutral, infinitely reconfigurable production stage.",
        "lighting": "controllable three-point setups",
        "architecture": "seamless volumes, modular set pieces",
        "textures": "matte surfaces, soft fabric, brushed metal",
        "mood": "neutral",
        "weather": "none — interior",
        "camera_language": "any framing; default eye-level coverage",
        "environmental_storytelling": "the brand's craft — clean, intentional, premium",
        "environments": ["studio"],
        "keywords": ["studio", "presenter", "review", "podcast"],
    },
    {
        "world_id": "metropolis",
        "label": "Metropolis",
        "description": "A living modern city — streets, towers, motion.",
        "lighting": "daylight canyons, neon and sodium at night",
        "architecture": "glass towers, brick side streets, transit layers",
        "textures": "concrete, glass, wet asphalt, steam",
        "mood": "kinetic",
        "weather": "clear days, rain-slicked nights",
        "camera_language": "drone sweeps, street-level tracking",
        "environmental_storytelling": "scale and speed — the individual inside the machine",
        "environments": ["city", "office"],
        "keywords": ["city", "urban", "business", "startup", "street"],
    },
    {
        "world_id": "everwood",
        "label": "Everwood",
        "description": "An untouched natural world — forest, river, mountain.",
        "lighting": "golden hour, dappled canopy, moonlit clearings",
        "architecture": "none — geology and growth",
        "textures": "bark, moss, water, fur, stone",
        "mood": "serene",
        "weather": "seasonal cycles — mist, rain, snow, summer haze",
        "camera_language": "patient telephoto, aerial establishers",
        "environmental_storytelling": "time and life at nature's pace",
        "environments": ["nature"],
        "keywords": ["nature", "wildlife", "animal", "forest", "ocean", "planet"],
    },
    {
        "world_id": "meridian_station",
        "label": "Meridian Station",
        "description": "A sci-fi orbital habitat above a blue world.",
        "lighting": "hard sunlight, cool interior panels, planet glow",
        "architecture": "rotating rings, glass observation decks, service corridors",
        "textures": "brushed alloy, composite panels, holographic displays",
        "mood": "awe",
        "weather": "none — vacuum outside, climate control inside",
        "camera_language": "weightless drifts, vast pull-backs",
        "environmental_storytelling": "humanity's reach — fragile life in engineered shells",
        "environments": ["space", "laboratory"],
        "keywords": ["space", "sci-fi", "future", "orbit", "mars", "galaxy", "quantum"],
    },
    {
        "world_id": "old_dominion",
        "label": "The Old Dominion",
        "description": "A historical world of empires, manuscripts, and candlelight.",
        "lighting": "candlelight, oil lamps, cathedral shafts",
        "architecture": "stone halls, timber markets, fortress walls",
        "textures": "parchment, wrought iron, aged textiles",
        "mood": "gravitas",
        "weather": "smoke, fog, harvest sun",
        "camera_language": "slow reveals over maps and artifacts",
        "environmental_storytelling": "every object outlived its owner",
        "environments": ["historical", "classroom"],
        "keywords": ["history", "ancient", "empire", "war", "medieval", "rome", "egypt"],
    },
    {
        "world_id": "clearline",
        "label": "Clearline",
        "description": "A minimalist abstract world of shape, light, and idea.",
        "lighting": "flat, even, shadowless",
        "architecture": "geometry — planes, grids, floating forms",
        "textures": "none — pure flat color",
        "mood": "calm",
        "weather": "none — conceptual space",
        "camera_language": "locked frames, precise scale moves",
        "environmental_storytelling": "clarity itself — nothing exists but the idea",
        "environments": ["studio", "classroom"],
        "keywords": ["explain", "how", "concept", "idea", "minimal", "data"],
    },
    {
        "world_id": "atrium",
        "label": "The Atrium",
        "description": "A corporate world of glass, daylight, and quiet confidence.",
        "lighting": "daylight through curtain walls, warm evening interiors",
        "architecture": "atriums, boardrooms, open studios",
        "textures": "glass, wood veneer, wool, steel",
        "mood": "confident",
        "weather": "city daylight through glass",
        "camera_language": "stable symmetric framing, walking-and-talking dollies",
        "environmental_storytelling": "competence made visible",
        "environments": ["office", "studio"],
        "keywords": ["corporate", "company", "strategy", "finance", "brand"],
    },
    {
        "world_id": "wonderrealm",
        "label": "Wonderrealm",
        "description": "A fantasy world of floating islands and glowing forests.",
        "lighting": "bioluminescence, god rays, twin moons",
        "architecture": "grown structures, ancient ruins, sky bridges",
        "textures": "crystal, luminous flora, weathered stone",
        "mood": "enchantment",
        "weather": "aurora skies, drifting spores, sudden storms",
        "camera_language": "sweeping impossible camera paths",
        "environmental_storytelling": "magic has consequences — every ruin is a lesson",
        "environments": ["fantasy", "nature"],
        "keywords": ["fantasy", "magic", "dragon", "myth", "kids", "story"],
    },
    {
        "world_id": "academy",
        "label": "The Academy",
        "description": "An educational world where every space teaches.",
        "lighting": "bright even daylight, warm lamp-lit studies",
        "architecture": "lecture halls, labs, libraries, courtyards",
        "textures": "chalk, paper, wood, brass instruments",
        "mood": "curious",
        "weather": "campus seasons",
        "camera_language": "board-centric framing, discovery push-ins",
        "environmental_storytelling": "knowledge accumulating in layers",
        "environments": ["classroom", "laboratory"],
        "keywords": ["learn", "education", "school", "science", "lesson", "tutorial"],
    },
)

for _world in _BUILTINS:
    register_world(_world)
