"""Asset Planning — structured requests, never generation.

Expands the per-scene primary visuals (storyboard.py) into the full
categorized asset request list: characters, backgrounds, objects/props,
vehicles, icons, animations, logos, textures, visual effects, and
particle systems. Every request is one ASSET_REQUIREMENT_FIELDS dict with
a `category`, typed by `CREATIVE_ASSET_TYPES` — asset providers fulfil
them later; the studio never generates anything itself.
"""

from __future__ import annotations

# Words in props/descriptions that signal a vehicle asset.
_VEHICLE_SIGNALS = ("car", "vehicle", "spacecraft", "ship", "truck", "train", "drone")

# High-intensity purposes that earn a particle/VFX pass.
_VFX_PURPOSES = ("hook", "escalation", "revelation")


def _request(
    asset_id: str, scene_id: str, asset_type: str, category: str,
    description: str, prompt: str, style: str,
    priority: str = "recommended", reusable: bool = False,
) -> dict:
    return {
        "asset_id": asset_id,
        "scene_id": scene_id,
        "asset_type": asset_type,
        "category": category,
        "description": description,
        "prompt": prompt,
        "style": style,
        "priority": priority,
        "reusable": reusable,
        "status": "planned",
    }


def build_asset_plan(
    storyboard: "list[dict]",
    blueprint: dict,
    characters: "list[dict]",
    base_requirements: "list[dict]",
    item: "dict | None" = None,
) -> "list[dict]":
    """The complete categorized asset request list for one production.

    Starts from the v1.0 requirements (per-scene primaries + character
    reference sheets) and adds backgrounds, props/objects, vehicles,
    icons, logo/brand marks, textures, and VFX/particle requests.
    """
    item = item or {}
    style = blueprint.get("visual_style", "")
    requests = []

    # v1.0 base requirements gain a category (additive key).
    for requirement in base_requirements:
        enriched = dict(requirement)
        enriched.setdefault(
            "category",
            "character" if requirement.get("asset_id", "").startswith("charref_") else "scene_visual",
        )
        requests.append(enriched)

    seen_backgrounds: "set[str]" = set()
    for scene in storyboard:
        scene_id = scene.get("scene_id", "")

        # Backgrounds — one reusable request per distinct environment.
        background = scene.get("background", "")
        if background and background not in seen_backgrounds:
            seen_backgrounds.add(background)
            requests.append(
                _request(
                    f"bg_{background}", scene_id, "background", "background",
                    f"Reusable background plate: {background}",
                    f"{background} environment plate, {scene.get('lighting', '')}, "
                    f"{scene.get('color_palette', '')}, no characters",
                    style, priority="required", reusable=True,
                )
            )

        # Props / objects / vehicles.
        for index, prop in enumerate(scene.get("props", [])):
            prop_text = str(prop).lower()
            is_vehicle = any(signal in prop_text for signal in _VEHICLE_SIGNALS)
            requests.append(
                _request(
                    f"prop_{scene_id}_{index + 1:02d}", scene_id,
                    "vehicle" if is_vehicle else "object",
                    "vehicle" if is_vehicle else "object",
                    f"Scene prop: {prop}",
                    f"{prop}, {style} style, isolated on transparent background",
                    style,
                )
            )

        # Icons for overlay graphics.
        for index, overlay in enumerate(scene.get("overlay_graphics", [])):
            requests.append(
                _request(
                    f"icon_{scene_id}_{index + 1:02d}", scene_id, "icon", "icon",
                    f"Overlay graphic: {overlay}",
                    f"{overlay}, flat vector icon, {style} palette",
                    style,
                )
            )

        # VFX + particles for the board's high-intensity beats.
        if scene.get("purpose") in _VFX_PURPOSES:
            requests.append(
                _request(
                    f"vfx_{scene_id}", scene_id, "vfx", "vfx",
                    f"Visual effect pass for the {scene.get('purpose')} beat",
                    f"subtle {scene.get('emotion', '')} atmosphere effect, {style} style",
                    style,
                )
            )
            requests.append(
                _request(
                    f"particles_{scene_id}", scene_id, "particle_system", "particle_system",
                    f"Particle accent for the {scene.get('purpose')} beat",
                    "light particle system — dust, sparks, or motes matching the scene mood",
                    style, priority="optional",
                )
            )

    # Brand logo — one reusable request per production for the endcard.
    brand = str(item.get("brand_id") or item.get("brand") or "")
    requests.append(
        _request(
            "logo_brand_endcard", "", "logo", "logo",
            f"Brand logo lockup for the endcard ({brand or 'house brand'})",
            "brand logo lockup, transparent background, endcard-ready",
            style, priority="required", reusable=True,
        )
    )

    # Style texture pass — one reusable request when the style defines texture.
    from services.creative_studio.styles import get_style

    style_preset = get_style(style) or {}
    if style_preset.get("texture") and "none" not in style_preset["texture"].lower():
        requests.append(
            _request(
                f"texture_{style}", "", "texture", "texture",
                f"Reusable style texture pass: {style_preset['texture']}",
                f"{style_preset['texture']}, tileable overlay texture",
                style, priority="optional", reusable=True,
            )
        )

    return requests
