"""Style Packs — reusable generation-side style vocabulary.

The Creative Studio's Style Library (Agent 12) owns creative *design*
decisions; these style packs own the *generation* side of the same ids —
the prompt and negative-prompt fragments that make a provider actually
render that look. Pack ids align with Creative Studio style ids wherever
they exist, and unknown styles degrade to the raw id (never a failure).

Unlimited expansion: `register_style_pack()` adds future style packs at
runtime — brand styles, seasonal looks, experimental aesthetics — without
touching this file.
"""

from __future__ import annotations

STYLE_PACK_FIELDS = (
    "style_id",
    "label",
    "prompt_fragment",         # appended to every prompt in this style
    "negative_fragment",       # appended to the negative prompt
    "keywords",
)

_STYLE_PACKS: "dict[str, dict]" = {}


def register_style_pack(pack: dict) -> dict:
    """Register (or replace) one style pack. Returns the stored dict."""
    stored = {
        "style_id": pack["style_id"],
        "label": pack.get("label", pack["style_id"]),
        "prompt_fragment": pack.get("prompt_fragment", ""),
        "negative_fragment": pack.get("negative_fragment", ""),
        "keywords": list(pack.get("keywords", [])),
    }
    _STYLE_PACKS[stored["style_id"]] = stored
    return stored


def get_style_pack(style_id: str) -> "dict | None":
    return _STYLE_PACKS.get(style_id)


def all_style_packs() -> "list[dict]":
    return list(_STYLE_PACKS.values())


def style_prompt_fragment(style_id: str) -> str:
    """The prompt fragment for a style — the raw id when no pack exists,
    so any future style still influences the prompt deterministically."""
    pack = _STYLE_PACKS.get(str(style_id or "").strip())
    if pack:
        return pack["prompt_fragment"]
    return str(style_id or "").replace("_", " ").strip()


def style_negative_fragment(style_id: str) -> str:
    pack = _STYLE_PACKS.get(str(style_id or "").strip())
    return pack["negative_fragment"] if pack else ""


# --------------------------------------------------------------- built-ins

_BUILTINS = (
    {
        "style_id": "pixar_inspired",
        "label": "Pixar-Inspired",
        "prompt_fragment": "warm stylized 3D animation, appealing rounded character design, soft subsurface skin, gentle rim light, heartfelt",
        "negative_fragment": "photorealistic skin, uncanny valley, harsh shadows",
        "keywords": ["3d", "family", "heart"],
    },
    {
        "style_id": "anime_inspired",
        "label": "Anime-Inspired",
        "prompt_fragment": "expressive anime style, cel shading, dramatic backlight, painted skies, speed lines on action",
        "negative_fragment": "photorealistic, western cartoon proportions",
        "keywords": ["anime", "cel"],
    },
    {
        "style_id": "comic",
        "label": "Comic",
        "prompt_fragment": "bold comic book art, ink outlines, halftone dots, graphic hard shadows, punchy primary colors",
        "negative_fragment": "photograph, soft gradients, blur",
        "keywords": ["comic", "ink"],
    },
    {
        "style_id": "disney_inspired",
        "label": "Disney-Inspired",
        "prompt_fragment": "classic feature-animation style, expressive large eyes, flowing line of action, storybook color, magical warm glow",
        "negative_fragment": "photorealistic, gritty, desaturated",
        "keywords": ["fairytale", "musical"],
    },
    {
        "style_id": "ghibli_inspired",
        "label": "Ghibli-Inspired",
        "prompt_fragment": "hand-painted watercolor backgrounds, soft natural light, lush nature detail, gentle wind-blown motion, nostalgic warmth",
        "negative_fragment": "3d render, neon, harsh contrast",
        "keywords": ["painterly", "nature"],
    },
    {
        "style_id": "cyberpunk",
        "label": "Cyberpunk",
        "prompt_fragment": "neon-noir cyberpunk, rain-slick streets, holographic signage, electric cyan and magenta, hard contrast",
        "negative_fragment": "daylight pastoral, muted earth tones",
        "keywords": ["neon", "future"],
    },
    {
        "style_id": "photorealistic",
        "label": "Photorealistic",
        "prompt_fragment": "photorealistic, physically accurate lighting, real-lens depth of field, filmic contrast curve, natural material imperfections",
        "negative_fragment": "illustration, cartoon, painting, render artifacts",
        "keywords": ["photo", "realism"],
    },
    {
        "style_id": "oil_painting",
        "label": "Oil Painting",
        "prompt_fragment": "oil painting, impasto brushwork, chiaroscuro old-master lighting, rich earth tones, canvas texture",
        "negative_fragment": "photograph, flat digital art",
        "keywords": ["painterly", "classical"],
    },
    {
        "style_id": "watercolor",
        "label": "Watercolor",
        "prompt_fragment": "watercolor painting, translucent washes, blooming pigment edges, cold-press paper grain, muted pastels",
        "negative_fragment": "hard vector edges, neon saturation",
        "keywords": ["soft", "paper"],
    },
    {
        "style_id": "pencil_sketch",
        "label": "Pencil Sketch",
        "prompt_fragment": "graphite pencil sketch, expressive cross-hatching, visible construction lines, paper tooth texture",
        "negative_fragment": "color, photograph, ink",
        "keywords": ["sketch", "monochrome"],
    },
    {
        "style_id": "minimal",
        "label": "Minimal",
        "prompt_fragment": "minimal clean design, generous whitespace, flat shadowless lighting, one accent color, geometric composition",
        "negative_fragment": "clutter, texture, ornamentation",
        "keywords": ["clean", "flat"],
    },
    {
        "style_id": "corporate",
        "label": "Corporate",
        "prompt_fragment": "confident corporate design, navy and white palette, bright high-key lighting, glass panels, clear hierarchy",
        "negative_fragment": "grunge, chaotic composition",
        "keywords": ["business", "trust"],
    },
    {
        "style_id": "educational",
        "label": "Educational",
        "prompt_fragment": "friendly educational diagram style, bright even light, labeled callouts, chalkboard and paper accents",
        "negative_fragment": "dark moody lighting, abstract ambiguity",
        "keywords": ["teaching", "diagram"],
    },
    {
        "style_id": "luxury",
        "label": "Luxury",
        "prompt_fragment": "premium luxury aesthetic, charcoal black with champagne gold accents, sculpted low-key rim light, macro material detail",
        "negative_fragment": "bright primaries, casual snapshot look",
        "keywords": ["premium", "gold"],
    },
    {
        "style_id": "cinematic",
        "label": "Cinematic",
        "prompt_fragment": "cinematic film still, anamorphic framing, motivated practical lighting, shallow depth of field, graded filmic color",
        "negative_fragment": "flat lighting, smartphone snapshot",
        "keywords": ["film", "drama"],
    },
)

for _pack in _BUILTINS:
    register_style_pack(_pack)
