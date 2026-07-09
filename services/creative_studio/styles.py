"""Style Library — the Creative Studio's visual identity presets.

Each style is one registered dict (STYLE_FIELDS). Unlimited expansion:
`register_style()` adds new looks at runtime — brand-specific styles,
seasonal styles, experimental styles — without touching this file.

`select_style()` is deterministic: an explicit request wins, then the
production type's default, then a keyword match, then minimal.
"""

from __future__ import annotations

STYLE_LIBRARY_VERSION = "1.0"

DEFAULT_STYLE = "minimal"

_STYLES: "dict[str, dict]" = {}


def register_style(style: dict) -> dict:
    """Register (or replace) one visual style. Returns the stored dict."""
    stored = {
        "style_id": style["style_id"],
        "label": style.get("label", style["style_id"]),
        "description": style.get("description", ""),
        "color_palette": style.get("color_palette", ""),
        "lighting": style.get("lighting", ""),
        "typography": style.get("typography", ""),
        "camera_language": style.get("camera_language", ""),
        "motion_language": style.get("motion_language", ""),
        "texture": style.get("texture", ""),
        "mood": style.get("mood", ""),
        "suited_production_types": list(style.get("suited_production_types", [])),
    }
    _STYLES[stored["style_id"]] = stored
    return stored


def get_style(style_id: str) -> "dict | None":
    return _STYLES.get(style_id)


def all_styles() -> "list[dict]":
    return list(_STYLES.values())


def style_ids() -> "list[str]":
    return list(_STYLES.keys())


def select_style(item: dict, production_type: dict) -> dict:
    """The visual style for one item (deterministic).

    Priority: explicit `visual_style` request → production type default →
    topic/niche keyword match → minimal.
    """
    requested = str(item.get("visual_style", "")).strip()
    if requested and requested in _STYLES:
        return dict(_STYLES[requested])

    signals = " ".join(
        str(part).lower()
        for part in (item.get("topic", ""), item.get("niche", ""), item.get("title", ""))
    )
    for style_id, style in _STYLES.items():
        if style_id in signals or (style["mood"] and style["mood"] in signals):
            return dict(style)

    default = production_type.get("default_style", DEFAULT_STYLE)
    return dict(_STYLES.get(default) or _STYLES[DEFAULT_STYLE])


# --------------------------------------------------------------- built-ins

_BUILTINS = (
    {
        "style_id": "minimal",
        "label": "Minimal",
        "description": "Clean, restrained, whitespace-driven design.",
        "color_palette": "white, soft gray, one accent color",
        "lighting": "flat, even, shadowless",
        "typography": "geometric sans-serif, generous tracking",
        "camera_language": "static, centered compositions",
        "motion_language": "gentle eases, no overshoot",
        "texture": "none — pure flat surfaces",
        "mood": "calm",
        "suited_production_types": ["educational_explainer", "whiteboard", "product_demo", "podcast_visualization"],
    },
    {
        "style_id": "luxury",
        "label": "Luxury",
        "description": "Premium restraint — gold accents, deep blacks, macro texture.",
        "color_palette": "charcoal black, champagne gold, ivory",
        "lighting": "low-key with sculpted rim light",
        "typography": "high-contrast serif, wide letter-spacing",
        "camera_language": "slow gliding dollies, macro close-ups",
        "motion_language": "long slow eases, weightless drift",
        "texture": "silk, brushed metal, glass reflections",
        "mood": "exclusive",
        "suited_production_types": ["luxury_branding", "commercial_ad"],
    },
    {
        "style_id": "corporate",
        "label": "Corporate",
        "description": "Confident, trustworthy business communication.",
        "color_palette": "navy, white, corporate accent blue",
        "lighting": "bright, clean, high-key",
        "typography": "neutral sans-serif, clear hierarchy",
        "camera_language": "stable symmetric framing",
        "motion_language": "crisp professional transitions",
        "texture": "subtle gradients, glass panels",
        "mood": "confident",
        "suited_production_types": ["corporate_presentation", "ai_presenter", "infographic"],
    },
    {
        "style_id": "scientific",
        "label": "Scientific",
        "description": "Precise, wonder-driven visualization of the natural world.",
        "color_palette": "deep space blue, cyan, white highlights",
        "lighting": "directional with volumetric glow",
        "typography": "technical sans-serif with data labels",
        "camera_language": "slow push-ins, orbital reveals",
        "motion_language": "physics-accurate, simulation-like",
        "texture": "particles, fields, translucent structures",
        "mood": "wonder",
        "suited_production_types": ["science_visualization", "animation_3d", "documentary"],
    },
    {
        "style_id": "medical",
        "label": "Medical",
        "description": "Clinical clarity — anatomy rendered clean and trustworthy.",
        "color_palette": "clinical white, arterial red, vein blue",
        "lighting": "soft even studio light",
        "typography": "clean sans-serif with anatomical labels",
        "camera_language": "steady dollies through anatomy",
        "motion_language": "smooth, deliberate, never jarring",
        "texture": "translucent tissue, subsurface scattering",
        "mood": "trust",
        "suited_production_types": ["medical_animation", "educational_explainer"],
    },
    {
        "style_id": "space",
        "label": "Space",
        "description": "Cosmic scale — nebulae, starfields, planetary bodies.",
        "color_palette": "black, nebula purple, star white, sun orange",
        "lighting": "single hard key (sunlight) with deep shadow",
        "typography": "thin extended sans-serif",
        "camera_language": "vast slow drifts, scale-revealing pull-backs",
        "motion_language": "weightless inertia",
        "texture": "starfields, gas clouds, planetary surfaces",
        "mood": "awe",
        "suited_production_types": ["science_visualization", "cinematic_video", "documentary"],
    },
    {
        "style_id": "cyberpunk",
        "label": "Cyberpunk",
        "description": "Neon-noir futures — rain, glass, holograms.",
        "color_palette": "neon magenta, electric cyan, black",
        "lighting": "neon practicals, hard contrast",
        "typography": "glitch-accented technical type",
        "camera_language": "low angles, dutch tilts, drone sweeps",
        "motion_language": "speed ramps, digital glitches",
        "texture": "wet asphalt, holographic shimmer, scanlines",
        "mood": "electric",
        "suited_production_types": ["gaming_video", "cinematic_video", "commercial_ad"],
    },
    {
        "style_id": "finance",
        "label": "Finance",
        "description": "Markets and money — charts, tickers, momentum.",
        "color_palette": "dark slate, bull green, bear red, gold",
        "lighting": "screen-glow ambience",
        "typography": "tabular numerals, ticker type",
        "camera_language": "chart fly-throughs, data zooms",
        "motion_language": "count-ups, momentum-driven graphs",
        "texture": "grid lines, candlesticks, glass dashboards",
        "mood": "urgency",
        "suited_production_types": ["infographic", "educational_explainer", "ai_presenter"],
    },
    {
        "style_id": "history",
        "label": "History",
        "description": "Period texture — parchment, archival grain, aged palettes.",
        "color_palette": "sepia, parchment, oxblood, faded gold",
        "lighting": "candlelight warmth, window shafts",
        "typography": "engraved serif, aged labels",
        "camera_language": "slow reveals over maps and artifacts",
        "motion_language": "parallaxed stills, ken burns drift",
        "texture": "parchment, film grain, canvas",
        "mood": "gravitas",
        "suited_production_types": ["historical_reconstruction", "documentary"],
    },
    {
        "style_id": "nature",
        "label": "Nature",
        "description": "Blue-chip natural history — organic light and life.",
        "color_palette": "forest green, earth brown, sky blue, golden hour amber",
        "lighting": "natural golden-hour and dappled light",
        "typography": "understated humanist sans-serif",
        "camera_language": "patient telephoto, aerial sweeps",
        "motion_language": "organic, wind-driven, breathing",
        "texture": "foliage, water, fur, feathers",
        "mood": "serenity",
        "suited_production_types": ["nature_video", "documentary", "cinematic_video"],
    },
    {
        "style_id": "kids",
        "label": "Kids",
        "description": "Bright, round, friendly shapes for young audiences.",
        "color_palette": "primary red, yellow, blue, grass green",
        "lighting": "flat bright cheerfulness",
        "typography": "rounded chunky display type",
        "camera_language": "front-on staging, gentle bounces",
        "motion_language": "bouncy squash-and-stretch",
        "texture": "paper cutout, soft plush",
        "mood": "joy",
        "suited_production_types": ["kids_educational", "cartoon", "animation_2d"],
    },
    {
        "style_id": "anime_inspired",
        "label": "Anime-Inspired",
        "description": "Expressive anime-inspired drama — light, speed, emotion.",
        "color_palette": "sunset gradients, deep blues, cherry accents",
        "lighting": "dramatic backlight, lens flares",
        "typography": "bold display type with impact frames",
        "camera_language": "dramatic angles, held close-ups",
        "motion_language": "speed lines, dramatic holds, sakuga bursts",
        "texture": "painted skies, cel shading",
        "mood": "intensity",
        "suited_production_types": ["anime_inspired", "animation_2d"],
    },
    {
        "style_id": "comic",
        "label": "Comic",
        "description": "Inked panels, halftones, and bold graphic storytelling.",
        "color_palette": "bold primaries, black inks, halftone dots",
        "lighting": "graphic hard shadows",
        "typography": "hand-lettered captions, onomatopoeia",
        "camera_language": "panel-to-panel jumps, dramatic angles",
        "motion_language": "snap cuts, freeze frames",
        "texture": "halftone dots, ink lines, paper",
        "mood": "punchy",
        "suited_production_types": ["comic_style", "cartoon"],
    },
    {
        "style_id": "psychology",
        "label": "Psychology",
        "description": "The interior world — abstract minds, symbolism, depth.",
        "color_palette": "deep teal, warm amber, soft violet",
        "lighting": "moody chiaroscuro",
        "typography": "thoughtful serif/sans pairing",
        "camera_language": "slow push-ins on symbolic subjects",
        "motion_language": "dreamlike dissolves, floating elements",
        "texture": "smoke, ink in water, silhouettes",
        "mood": "introspective",
        "suited_production_types": ["educational_explainer", "cinematic_video", "documentary"],
    },
    {
        "style_id": "motivational",
        "label": "Motivational",
        "description": "High-energy aspiration — grit, triumph, momentum.",
        "color_palette": "black, fire orange, steel gray",
        "lighting": "hard dramatic key with haze",
        "typography": "condensed bold uppercase",
        "camera_language": "low hero angles, punch-ins",
        "motion_language": "impact cuts, slow-motion payoffs",
        "texture": "sweat, rain, dust in light",
        "mood": "drive",
        "suited_production_types": ["reaction_video", "commercial_ad", "cinematic_video"],
    },
    {
        "style_id": "pixar_inspired",
        "label": "Pixar-Inspired",
        "description": "Warm stylized 3D — appeal, subsurface glow, heart.",
        "color_palette": "warm saturated hues with complementary pops",
        "lighting": "soft key with warm bounce, gentle rim light",
        "typography": "rounded friendly display type",
        "camera_language": "character-height coverage, gentle emotional push-ins",
        "motion_language": "appealing overshoot, anticipation, follow-through",
        "texture": "soft subsurface skin, felt, polished plastic",
        "mood": "heartfelt",
        "suited_production_types": ["animation_3d", "kids_educational", "cartoon"],
    },
    {
        "style_id": "photorealistic",
        "label": "Photorealistic",
        "description": "Indistinguishable-from-camera realism.",
        "color_palette": "true-to-life, filmic contrast curve",
        "lighting": "physically plausible natural and practical sources",
        "typography": "restrained cinematic titles",
        "camera_language": "real-lens grammar — 24/35/50/85mm equivalents",
        "motion_language": "physically accurate weight and inertia",
        "texture": "real-world materials, imperfections included",
        "mood": "grounded",
        "suited_production_types": ["cinematic_video", "documentary", "commercial_ad"],
    },
    {
        "style_id": "watercolor",
        "label": "Watercolor",
        "description": "Soft washes, blooming pigment, paper grain.",
        "color_palette": "translucent washes, muted pastels, white paper light",
        "lighting": "diffuse — light lives in the unpainted paper",
        "typography": "hand-inked serif captions",
        "camera_language": "gentle drifts across painted planes",
        "motion_language": "blooms, bleeds, wet-edge dissolves",
        "texture": "cold-press paper grain, pigment granulation",
        "mood": "tender",
        "suited_production_types": ["kids_educational", "educational_explainer", "animation_2d"],
    },
    {
        "style_id": "oil_painting",
        "label": "Oil Painting",
        "description": "Impasto brushwork and old-master light.",
        "color_palette": "rich earth tones, deep shadow, golden highlights",
        "lighting": "chiaroscuro — single warm key from darkness",
        "typography": "engraved classical serif",
        "camera_language": "slow parallax through painted depth",
        "motion_language": "brushstroke reveals, living canvas shimmer",
        "texture": "impasto ridges, varnish sheen, canvas weave",
        "mood": "timeless",
        "suited_production_types": ["historical_reconstruction", "documentary", "luxury_branding"],
    },
    {
        "style_id": "paper_animation",
        "label": "Paper Animation",
        "description": "Cutout layers, folds, and stop-motion charm.",
        "color_palette": "construction-paper primaries, kraft neutrals",
        "lighting": "raked light that casts real paper shadows",
        "typography": "cut-letter and stamped type",
        "camera_language": "top-down craft table and layered dioramas",
        "motion_language": "stop-motion steps, hinge folds, slide-ins",
        "texture": "paper fiber, torn edges, visible tape",
        "mood": "handmade",
        "suited_production_types": ["kids_educational", "educational_explainer", "whiteboard"],
    },
    {
        "style_id": "motion_design",
        "label": "Motion Design",
        "description": "Contemporary motion graphics — shape, type, rhythm.",
        "color_palette": "bold flat fields with one electric accent",
        "lighting": "flat — depth from scale and overlap",
        "typography": "kinetic grotesque type as the hero",
        "camera_language": "flat 2D camera, grid-locked scale moves",
        "motion_language": "tight easing curves, morphs, choreographed beats",
        "texture": "none — vector purity, occasional grain pass",
        "mood": "energetic",
        "suited_production_types": ["motion_graphics", "infographic", "commercial_ad"],
    },
    {
        "style_id": "infographic",
        "label": "Infographic",
        "description": "Data made visible — charts, icons, systems.",
        "color_palette": "categorical palette on neutral ground",
        "lighting": "flat, dashboard-clean",
        "typography": "tabular numerals, labeled axes",
        "camera_language": "chart fly-throughs, zooms into data points",
        "motion_language": "count-ups, growing bars, drawing lines",
        "texture": "grid lines, subtle card shadows",
        "mood": "clarity",
        "suited_production_types": ["infographic", "educational_explainer", "corporate_presentation"],
    },
    {
        "style_id": "educational",
        "label": "Educational",
        "description": "Diagram-first teaching clarity with friendly warmth.",
        "color_palette": "chalkboard green, paper white, highlighter accents",
        "lighting": "bright even classroom light",
        "typography": "legible humanist sans with labeled callouts",
        "camera_language": "board-centric framing, progressive zoom-ins",
        "motion_language": "draw-on reveals, step-by-step builds",
        "texture": "chalk dust, notebook paper",
        "mood": "curious",
        "suited_production_types": ["educational_explainer", "kids_educational", "whiteboard"],
    },
    {
        "style_id": "documentary",
        "label": "Documentary",
        "description": "Grounded realism — natural light, honest frames.",
        "color_palette": "true-to-life with lifted shadows",
        "lighting": "available light, practical sources",
        "typography": "quiet lower-thirds, archival captions",
        "camera_language": "handheld verite + composed interviews",
        "motion_language": "observational, unforced",
        "texture": "film grain, archival artifacts",
        "mood": "authentic",
        "suited_production_types": ["documentary", "cinematic_video", "nature_video"],
    },
)

for _style in _BUILTINS:
    register_style(_style)
