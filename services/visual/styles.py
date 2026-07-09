"""Visual style presets — the cinematic identity system.

Every video is directed in exactly one style. A style preset is pure data
(palette, lighting bias, art style, grade, overlay/caption treatment, mood),
so the Cinematic Director never hardcodes a look: scenes, prompts, and
thumbnails all read the resolved preset.

Future engines register new styles at runtime via `register_style()` —
the Visual Intelligence Engine never changes when the style library grows.
"""

from __future__ import annotations

DEFAULT_STYLE = "cinematic"

# The built-in style library. Each preset is one complete art direction.
_STYLE_PRESETS = {
    "documentary": {
        "label": "Documentary",
        "palette": "muted earth tones, archival warmth, natural contrast",
        "lighting_bias": "available-light realism with practical sources",
        "art_style": "handheld documentary realism, 16mm grain",
        "grade": "neutral film emulation, lifted blacks",
        "overlay_style": "typewriter lower-thirds, evidence-tag captions",
        "caption_style": "clean serif captions, understated",
        "mood": "credible, investigative",
    },
    "luxury": {
        "label": "Luxury",
        "palette": "champagne gold, obsidian black, marble white",
        "lighting_bias": "soft glamour key with polished speculars",
        "art_style": "high-end commercial photography, editorial polish",
        "grade": "rich contrast, golden warmth, deep shadows",
        "overlay_style": "thin serif titles with generous letter-spacing",
        "caption_style": "minimal gold-accent captions",
        "mood": "aspirational, exclusive",
    },
    "minimal": {
        "label": "Minimal",
        "palette": "white, soft gray, one restrained accent color",
        "lighting_bias": "flat high-key, shadowless",
        "art_style": "clean studio minimalism, negative space forward",
        "grade": "bright, low-saturation, airy",
        "overlay_style": "single-weight sans-serif, lots of whitespace",
        "caption_style": "small centered captions",
        "mood": "calm, focused",
    },
    "dark_history": {
        "label": "Dark History",
        "palette": "desaturated sepia, candlelight orange, ash gray",
        "lighting_bias": "low-key candlelight with hard falloff",
        "art_style": "archival documentary photography, period grain",
        "grade": "faded film, crushed blacks, vignette",
        "overlay_style": "distressed serif stamps, dossier annotations",
        "caption_style": "aged parchment-tone captions",
        "mood": "ominous, revelatory",
    },
    "cyberpunk": {
        "label": "Cyberpunk",
        "palette": "neon magenta, electric cyan, wet asphalt black",
        "lighting_bias": "neon practicals with colored rim light",
        "art_style": "rain-slicked sci-fi concept art, holographic detail",
        "grade": "high saturation, teal-magenta split tone",
        "overlay_style": "glitch-animated mono-spaced HUD text",
        "caption_style": "neon-stroke captions with scanline flicker",
        "mood": "electric, subversive",
    },
    "corporate": {
        "label": "Corporate",
        "palette": "navy, slate gray, clean white, single brand accent",
        "lighting_bias": "even three-point, boardroom clarity",
        "art_style": "premium B2B editorial, glass and steel textures",
        "grade": "neutral, crisp, low grain",
        "overlay_style": "geometric sans-serif title blocks",
        "caption_style": "high-legibility bottom-third captions",
        "mood": "confident, trustworthy",
    },
    "nature": {
        "label": "Nature",
        "palette": "forest green, sky blue, golden-hour amber",
        "lighting_bias": "natural sunlight, golden-hour warmth",
        "art_style": "BBC-grade wildlife cinematography",
        "grade": "vivid organic saturation, soft highlights",
        "overlay_style": "thin organic-serif labels",
        "caption_style": "soft-shadow white captions",
        "mood": "awe, serenity",
    },
    "science": {
        "label": "Science",
        "palette": "deep blue, cyan highlights, white lab neutrals",
        "lighting_bias": "cool clinical key with volumetric accents",
        "art_style": "photorealistic scientific visualization",
        "grade": "cool clean contrast, precise blacks",
        "overlay_style": "annotated diagram callouts, data labels",
        "caption_style": "mono-spaced data captions",
        "mood": "precise, wondrous",
    },
    "psychology": {
        "label": "Psychology",
        "palette": "warm amber, charcoal, intimate skin tones",
        "lighting_bias": "soft intimate key with deep shadow falloff",
        "art_style": "moody editorial portraiture, shallow focus",
        "grade": "warm mid-tones, gentle contrast curve",
        "overlay_style": "handwritten-accent keywords",
        "caption_style": "conversational sentence-case captions",
        "mood": "intimate, introspective",
    },
    "finance": {
        "label": "Finance",
        "palette": "navy, gold accents, ticker green and red",
        "lighting_bias": "sharp editorial key, skyline backlight",
        "art_style": "premium financial editorial, chart-forward",
        "grade": "polished contrast, metallic highlights",
        "overlay_style": "numeric callouts, rising-graph motifs",
        "caption_style": "bold condensed captions",
        "mood": "sharp, ambitious",
    },
    "horror": {
        "label": "Horror",
        "palette": "sickly green, blood crimson, void black",
        "lighting_bias": "single hard underlight, strobe-adjacent flicker",
        "art_style": "analog horror, VHS artifacts, deep shadow",
        "grade": "crushed shadows, desaturated flesh tones",
        "overlay_style": "scratched jitter text, sudden stamps",
        "caption_style": "unsettling irregular-timing captions",
        "mood": "dread, unease",
    },
    "conspiracy": {
        "label": "Conspiracy",
        "palette": "red-string crimson, corkboard tan, flashlight white",
        "lighting_bias": "flashlight pools in darkness, projector glow",
        "art_style": "investigation-board collage, redacted documents",
        "grade": "gritty contrast, newsprint texture",
        "overlay_style": "redaction bars, red-circle annotations",
        "caption_style": "stamped classified-file captions",
        "mood": "paranoid, magnetic",
    },
    "modern_tech": {
        "label": "Modern Tech",
        "palette": "neon cyan on dark grid, holographic accents",
        "lighting_bias": "screen-glow key with rim separation",
        "art_style": "sleek product-launch concept art",
        "grade": "deep blacks, luminous highlights",
        "overlay_style": "kinetic sans-serif with parallax slide-ins",
        "caption_style": "pill-shaped caption chips",
        "mood": "futuristic, inevitable",
    },
    "motivational": {
        "label": "Motivational",
        "palette": "sunrise orange, steel blue, triumphant gold",
        "lighting_bias": "backlit silhouettes, lens-flare sunrise",
        "art_style": "epic aspirational cinematography",
        "grade": "warm lift, punchy contrast",
        "overlay_style": "massive bold statements, word-by-word reveals",
        "caption_style": "large center-punch captions",
        "mood": "rising, unstoppable",
    },
    "cinematic": {
        "label": "Cinematic",
        "palette": "teal and orange, filmic contrast",
        "lighting_bias": "motivated three-point with rim accent",
        "art_style": "anamorphic film still, shallow depth",
        "grade": "film emulation, halation on highlights",
        "overlay_style": "letterboxed title cards",
        "caption_style": "subtle film-subtitle captions",
        "mood": "grand, immersive",
    },
}

# Default style per content niche — data, not code.
NICHE_STYLE_MAP = {
    "Science": "science",
    "Psychology": "psychology",
    "Finance": "finance",
    "Dark History": "dark_history",
    "Space": "cinematic",
    "Health": "nature",
    "AI & Future Tech": "modern_tech",
}


def register_style(key: str, preset: dict) -> dict:
    """Register (or replace) a style preset at runtime.

    Future engines (brand systems, the Learning Engine) add styles here —
    the Visual Intelligence Engine itself never changes.
    """
    required = {"label", "palette", "lighting_bias", "art_style", "grade", "overlay_style", "caption_style", "mood"}
    missing = required - set(preset)
    if missing:
        raise ValueError(f"style preset '{key}' missing fields: {sorted(missing)}")
    _STYLE_PRESETS[key] = dict(preset)
    return _STYLE_PRESETS[key]


def get_style(key: str) -> "dict | None":
    return _STYLE_PRESETS.get(key)


def style_keys() -> list:
    return list(_STYLE_PRESETS)


def resolve_style(*, style_key: str = "", niche: str = "") -> "tuple[str, dict]":
    """Resolve the directing style: explicit override → niche default → cinematic."""
    if style_key and style_key in _STYLE_PRESETS:
        return style_key, _STYLE_PRESETS[style_key]
    niche_key = NICHE_STYLE_MAP.get(niche, DEFAULT_STYLE)
    return niche_key, _STYLE_PRESETS[niche_key]
