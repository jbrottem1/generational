"""Environment System — reusable locations productions are staged in.

Each environment is one registered dict (ENVIRONMENT_FIELDS). New
locations — real, historical, or imaginary — are one
`register_environment()` call. `select_environments()` deterministically
casts environments for a production from its topic/script signals.
"""

from __future__ import annotations

ENVIRONMENT_SYSTEM_VERSION = "1.0"

DEFAULT_ENVIRONMENT = "studio"

_ENVIRONMENTS: "dict[str, dict]" = {}


def register_environment(environment: dict) -> dict:
    """Register (or replace) one reusable environment."""
    stored = {
        "environment_id": environment["environment_id"],
        "label": environment.get("label", environment["environment_id"]),
        "description": environment.get("description", ""),
        "lighting": environment.get("lighting", ""),
        "color_palette": environment.get("color_palette", ""),
        "props": list(environment.get("props", [])),
        "mood": environment.get("mood", ""),
        "camera_notes": environment.get("camera_notes", ""),
        "keywords": list(environment.get("keywords", [])),
    }
    _ENVIRONMENTS[stored["environment_id"]] = stored
    return stored


def get_environment(environment_id: str) -> "dict | None":
    return _ENVIRONMENTS.get(environment_id)


def all_environments() -> "list[dict]":
    return list(_ENVIRONMENTS.values())


def environment_ids() -> "list[str]":
    return list(_ENVIRONMENTS.keys())


def select_environments(item: dict, limit: int = 3) -> "list[dict]":
    """Environments cast for one item, best keyword matches first.

    Always returns at least one environment (the neutral studio), so every
    storyboard has a stage — continuity needs a consistent location, not a
    different backdrop per scene.
    """
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

    scored = []
    for environment in _ENVIRONMENTS.values():
        score = sum(1 for keyword in environment["keywords"] if keyword in signals)
        if score > 0:
            scored.append((score, environment))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["environment_id"]))

    selected = [dict(environment) for _score, environment in scored[:limit]]
    if not selected:
        selected = [dict(_ENVIRONMENTS[DEFAULT_ENVIRONMENT])]
    return selected


# --------------------------------------------------------------- built-ins

_BUILTINS = (
    {
        "environment_id": "studio",
        "label": "Studio",
        "description": "Neutral seamless studio — the universal stage.",
        "lighting": "controllable three-point setup",
        "color_palette": "neutral gray with accent-light color washes",
        "props": ["seamless backdrop", "presenter mark", "product plinth"],
        "mood": "neutral",
        "camera_notes": "any framing works; default eye-level medium",
        "keywords": ["studio", "presenter", "review", "podcast"],
    },
    {
        "environment_id": "office",
        "label": "Office",
        "description": "Modern workplace — glass, desks, city views.",
        "lighting": "daylight through floor-to-ceiling windows",
        "color_palette": "white, wood, corporate blue",
        "props": ["desks", "monitors", "whiteboard", "meeting table"],
        "mood": "productive",
        "camera_notes": "over-shoulder work shots, walking-and-talking dollies",
        "keywords": ["office", "business", "work", "startup", "company", "corporate"],
    },
    {
        "environment_id": "laboratory",
        "label": "Laboratory",
        "description": "Research lab — instruments, glassware, precision.",
        "lighting": "cool fluorescent with instrument glow",
        "color_palette": "white, steel, cyan accents",
        "props": ["microscopes", "beakers", "sample racks", "screens with data"],
        "mood": "precise",
        "camera_notes": "macro instrument close-ups, clean wide establishers",
        "keywords": ["lab", "science", "experiment", "research", "chemistry"],
    },
    {
        "environment_id": "hospital",
        "label": "Hospital",
        "description": "Clinical care setting — wards, scanners, operating rooms.",
        "lighting": "soft clinical white",
        "color_palette": "white, teal scrubs, monitor greens",
        "props": ["hospital bed", "monitors", "scanner", "surgical lights"],
        "mood": "care",
        "camera_notes": "respectful steady framing, shallow depth of field",
        "keywords": ["hospital", "medical", "doctor", "surgery", "patient", "health"],
    },
    {
        "environment_id": "nature",
        "label": "Nature",
        "description": "Forests, rivers, mountains — the living world.",
        "lighting": "golden hour and dappled canopy light",
        "color_palette": "greens, earth tones, sky blue",
        "props": ["trees", "water", "wildlife", "rock formations"],
        "mood": "serene",
        "camera_notes": "telephoto wildlife framing, aerial establishers",
        "keywords": ["nature", "forest", "wildlife", "animal", "river", "mountain", "ocean"],
    },
    {
        "environment_id": "space",
        "label": "Space",
        "description": "Orbit and deep space — stations, planets, starfields.",
        "lighting": "single hard sunlight against black",
        "color_palette": "black, star white, planet blues and ambers",
        "props": ["spacecraft", "planets", "starfield", "station interiors"],
        "mood": "awe",
        "camera_notes": "vast slow drifts, scale-revealing pull-backs",
        "keywords": ["space", "planet", "mars", "orbit", "galaxy", "universe", "cosmos"],
    },
    {
        "environment_id": "city",
        "label": "City",
        "description": "Urban streets and skylines — energy and density.",
        "lighting": "mixed daylight, neon and sodium at night",
        "color_palette": "concrete gray, glass blue, neon accents",
        "props": ["skyline", "traffic", "crowds", "storefronts"],
        "mood": "kinetic",
        "camera_notes": "drone skyline sweeps, street-level tracking",
        "keywords": ["city", "urban", "street", "downtown", "skyline"],
    },
    {
        "environment_id": "classroom",
        "label": "Classroom",
        "description": "Teaching space — boards, desks, learning energy.",
        "lighting": "bright even daylight",
        "color_palette": "warm wood, chalkboard green, paper white",
        "props": ["chalkboard", "desks", "books", "projector"],
        "mood": "curious",
        "camera_notes": "board-centric framing, student-POV reverses",
        "keywords": ["classroom", "school", "teacher", "learn", "lesson", "student"],
    },
    {
        "environment_id": "factory",
        "label": "Factory",
        "description": "Industrial production floor — machines and process.",
        "lighting": "high-bay industrial with sparks and glow",
        "color_palette": "steel gray, safety yellow, furnace orange",
        "props": ["assembly lines", "robotic arms", "conveyors", "control panels"],
        "mood": "industrious",
        "camera_notes": "process-following dollies, macro machine details",
        "keywords": ["factory", "manufacturing", "industrial", "machine", "production line"],
    },
    {
        "environment_id": "historical",
        "label": "Historical",
        "description": "Period-accurate reconstructions of the past.",
        "lighting": "candlelight, oil lamps, natural window shafts",
        "color_palette": "sepia, parchment, aged textiles",
        "props": ["period furniture", "maps", "artifacts", "manuscripts"],
        "mood": "gravitas",
        "camera_notes": "slow reveals over artifacts, painterly wides",
        "keywords": ["history", "ancient", "medieval", "empire", "war", "rome", "egypt"],
    },
    {
        "environment_id": "fantasy",
        "label": "Fantasy",
        "description": "Imagined worlds — floating islands, glowing forests, impossible skies.",
        "lighting": "magical bioluminescence and dramatic god rays",
        "color_palette": "violet skies, emerald glow, gold shimmer",
        "props": ["floating islands", "glowing flora", "ancient ruins", "portals"],
        "mood": "enchantment",
        "camera_notes": "sweeping impossible camera paths",
        "keywords": ["fantasy", "magic", "dragon", "myth", "legend"],
    },
)

for _environment in _BUILTINS:
    register_environment(_environment)
