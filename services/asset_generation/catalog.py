"""Asset Type Catalog — every kind of visual asset the platform generates.

Each entry is one registered dict: type id, media class (image / video /
three_d), defaults, and matching keywords. Unlimited expansion:
`register_asset_type()` adds new media at runtime — future formats are
one registration call, never an architectural change.

`resolve_asset_type()` also normalizes the Creative Studio's
`CREATIVE_ASSET_TYPES` vocabulary onto catalog entries, so Agent 12's
asset requirements flow straight into generation. Unknown types resolve
to a safe generic entry of the right class instead of failing.
"""

from __future__ import annotations

CATALOG_VERSION = "1.0"

_CATALOG: "dict[str, dict]" = {}


def register_asset_type(entry: dict) -> dict:
    """Register (or replace) one asset type. Returns the stored dict."""
    stored = {
        "type_id": entry["type_id"],
        "label": entry.get("label", entry["type_id"]),
        "asset_class": entry.get("asset_class", "image"),
        "description": entry.get("description", ""),
        "default_aspect_ratio": entry.get("default_aspect_ratio", "16:9"),
        "default_resolution": entry.get("default_resolution", "1920x1080"),
        "keywords": list(entry.get("keywords", [])),
    }
    _CATALOG[stored["type_id"]] = stored
    return stored


def get_asset_type(type_id: str) -> "dict | None":
    return _CATALOG.get(type_id)


def all_asset_types() -> "list[dict]":
    return list(_CATALOG.values())


def asset_type_ids() -> "list[str]":
    return list(_CATALOG.keys())


# Creative Studio vocabulary (providers/creative_provider.py
# CREATIVE_ASSET_TYPES) → catalog type ids. Additive-only.
_ALIASES = {
    "ai_image": "scene_image",
    "ai_video": "video_clip",
    "animation": "animation",
    "asset_3d": "object_3d",
    "vector_graphic": "illustration",
    "stock_footage": "b_roll",
    "user_asset": "image",
    "brand_asset": "logo",
    "character": "character_sheet",
    "background": "background_plate",
    "object": "prop",
    "vehicle": "vehicle",
    "icon": "icon",
    "logo": "logo",
    "texture": "texture",
    "vfx": "vfx_element",
    "particle_system": "particle_texture",
}

_GENERIC_BY_CLASS = {"image": "image", "video": "video_clip", "three_d": "object_3d"}


def resolve_asset_type(asset_type: str, asset_class_hint: str = "") -> dict:
    """The catalog entry for any requested type — never None.

    Priority: exact catalog match → Creative Studio alias → generic entry
    of the hinted class → generic image. The original request keeps its
    own type id downstream; this only supplies class + defaults.
    """
    requested = str(asset_type or "").strip()
    entry = _CATALOG.get(requested)
    if entry:
        return entry
    alias = _ALIASES.get(requested)
    if alias and alias in _CATALOG:
        return _CATALOG[alias]
    generic = _GENERIC_BY_CLASS.get(asset_class_hint, "image")
    return _CATALOG[generic]


def asset_class_of(asset_type: str) -> str:
    return resolve_asset_type(asset_type)["asset_class"]


# --------------------------------------------------------------- built-ins

def _entry(type_id, label, asset_class, description="", aspect="16:9", resolution="1920x1080", keywords=()):
    return {
        "type_id": type_id,
        "label": label,
        "asset_class": asset_class,
        "description": description,
        "default_aspect_ratio": aspect,
        "default_resolution": resolution,
        "keywords": list(keywords),
    }


_BUILTINS = (
    # ------------------------------------------------------------- images
    _entry("image", "Image", "image", "Generic generated image."),
    _entry("illustration", "Illustration", "image", "Stylized illustration or vector-style artwork."),
    _entry("photorealistic_image", "Photorealistic Image", "image", "Indistinguishable-from-camera realism."),
    _entry("concept_art", "Concept Art", "image", "Exploratory production design artwork.", "16:9", "2048x1152"),
    _entry("character_sheet", "Character Sheet", "image", "Canonical multi-view character reference.", "16:9", "2048x1152", ("character", "reference")),
    _entry("expression_sheet", "Expression Sheet", "image", "One character's named facial expressions.", "16:9", "2048x1152", ("expression",)),
    _entry("pose_sheet", "Pose Sheet", "image", "One character's key poses and silhouettes.", "16:9", "2048x1152", ("pose",)),
    _entry("environment_art", "Environment Art", "image", "Full environment/world design painting.", "16:9", "2048x1152"),
    _entry("world_building", "World Building", "image", "Establishing artwork for a persistent world.", "16:9", "2048x1152"),
    _entry("prop", "Prop", "image", "Isolated object/prop on clean background.", "1:1", "1024x1024"),
    _entry("vehicle", "Vehicle", "image", "Isolated vehicle design.", "16:9", "1920x1080"),
    _entry("architecture", "Architecture", "image", "Building/structure design artwork.", "16:9", "2048x1152"),
    _entry("icon", "Icon", "image", "Flat vector-style icon.", "1:1", "512x512", ("icon", "overlay")),
    _entry("logo", "Logo", "image", "Brand logo lockup on transparent background.", "1:1", "1024x1024", ("brand",)),
    _entry("infographic", "Infographic", "image", "Data made visible — charts, systems, labels.", "9:16", "1080x1920"),
    _entry("chart", "Chart", "image", "One rendered data chart.", "16:9", "1920x1080"),
    _entry("map", "Map", "image", "Stylized map or geographic visualization.", "16:9", "1920x1080"),
    _entry("background_plate", "Background Plate", "image", "Reusable environment plate, no characters.", "9:16", "1080x1920", ("background",)),
    _entry("texture", "Texture", "image", "Tileable overlay texture.", "1:1", "1024x1024", ("tileable",)),
    _entry("thumbnail", "Thumbnail", "image", "Click-optimized video thumbnail.", "16:9", "1280x720", ("thumbnail", "cover")),
    _entry("storyboard_frame", "Storyboard Frame", "image", "One drawn storyboard panel.", "16:9", "1280x720"),
    _entry("scene_image", "Scene Image", "image", "One production scene still.", "9:16", "1080x1920", ("scene",)),
    _entry("marketing_graphic", "Marketing Graphic", "image", "Campaign/social marketing visual.", "1:1", "1080x1080", ("marketing",)),
    _entry("channel_banner", "Channel Banner", "image", "Channel/brand header artwork.", "16:9", "2560x1440", ("branding",)),
    _entry("profile_picture", "Profile Picture", "image", "Channel/brand avatar.", "1:1", "800x800", ("branding",)),
    _entry("cover_image", "Cover Image", "image", "Cover/hero image.", "16:9", "1920x1080"),
    _entry("book_cover", "Book Cover", "image", "Print-style book cover.", "3:4", "1600x2560"),
    _entry("presentation_graphic", "Presentation Graphic", "image", "Slide-ready graphic.", "16:9", "1920x1080"),
    _entry("vfx_element", "VFX Element", "image", "Composable visual-effect element.", "9:16", "1080x1920", ("vfx",)),
    _entry("particle_texture", "Particle Texture", "image", "Sprite/texture for particle systems.", "1:1", "512x512", ("particles",)),
    # ------------------------------------------------------------- video
    _entry("video_clip", "Video Clip", "video", "Short generated video clip.", "9:16", "1080x1920", ("clip",)),
    _entry("cinematic_shot", "Cinematic Shot", "video", "One directed cinematic shot.", "9:16", "1080x1920", ("cinematic",)),
    _entry("animation", "Animation", "video", "Animated sequence.", "9:16", "1080x1920", ("animated",)),
    _entry("looping_clip", "Looping Clip", "video", "Seamlessly looping clip.", "9:16", "1080x1920", ("loop",)),
    _entry("camera_move", "Camera Move", "video", "A single camera movement over a scene.", "9:16", "1080x1920", ("camera",)),
    _entry("scene_transition", "Scene Transition", "video", "Transition element between scenes.", "9:16", "1080x1920", ("transition",)),
    _entry("motion_background", "Motion Background", "video", "Looping ambient background motion.", "9:16", "1080x1920", ("background", "loop")),
    _entry("green_screen_clip", "Green Screen Clip", "video", "Subject on solid chroma background.", "9:16", "1080x1920", ("chroma",)),
    _entry("b_roll", "B-Roll", "video", "Supplementary contextual footage.", "9:16", "1080x1920", ("broll",)),
    # ------------------------------------------- 3D preparation (additive)
    _entry("object_3d", "3D Object", "three_d", "One generated 3D object.", "1:1", "1024x1024"),
    _entry("mesh", "Mesh", "three_d", "Raw 3D mesh geometry.", "1:1", "1024x1024"),
    _entry("material_3d", "3D Material", "three_d", "PBR material/shader set.", "1:1", "1024x1024"),
    _entry("rig", "Rig", "three_d", "Skeleton/rig for a 3D model.", "1:1", "1024x1024"),
    _entry("character_model", "Character Model", "three_d", "Rigged 3D character model.", "1:1", "1024x1024"),
)

for _builtin in _BUILTINS:
    register_asset_type(_builtin)
