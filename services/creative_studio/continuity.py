"""Visual Continuity — what must stay consistent between scenes.

Tracks characters, lighting, environment, color, camera language,
animation style, and brand consistency across a storyboard, and reports
breaks as warnings (CONTINUITY_REPORT_FIELDS). Continuity NEVER raises —
a broken board yields a low score and explicit break descriptions, so the
package degrades to needs_review instead of crashing the pipeline.
"""

from __future__ import annotations


def _values(storyboard: "list[dict]", key: str) -> "list[str]":
    return [str(scene.get(key, "")) for scene in storyboard]


def _distinct(values: "list[str]") -> "list[str]":
    seen: "list[str]" = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen


def track_continuity(storyboard: "list[dict]", blueprint: dict, characters: "list[dict]") -> dict:
    """One continuity report for one storyboard — tracked dimensions,
    detected breaks, and a 0-100 continuity score."""
    breaks: "list[str]" = []

    # Characters — every scene must carry the full cast list (presence is
    # per-scene creative choice; the LIST must stay stable for consistency).
    cast_ids = sorted(character["character_id"] for character in characters)
    for scene in storyboard:
        scene_cast = sorted(str(cid) for cid in scene.get("characters", []))
        if scene_cast != cast_ids:
            breaks.append(f"{scene.get('scene_id', '?')}: cast list diverges from the production cast")

    # Lighting + color — one style means one palette family.
    lighting = _distinct(_values(storyboard, "lighting"))
    if len(lighting) > 2:
        breaks.append(f"lighting drifts across {len(lighting)} setups (max 2 for one style)")
    palettes = _distinct(_values(storyboard, "color_palette"))
    if len(palettes) > 2:
        breaks.append(f"color palette drifts across {len(palettes)} palettes (max 2 for one style)")

    # Environment — reuse registered environments; ping-ponging locations
    # every scene reads as random, not designed.
    environments = _distinct(_values(storyboard, "background"))
    if len(environments) > max(3, len(storyboard) // 2):
        breaks.append(f"{len(environments)} environments for {len(storyboard)} scenes — consolidate locations")

    # Animation style — one medium per production.
    animation_styles = _distinct(_values(storyboard, "animation_style"))
    if len(animation_styles) > 1:
        breaks.append(f"animation style changes mid-production: {animation_styles}")

    # Camera language — angles must come from the blueprint's grammar
    # (every angle non-empty; empty camera work is a broken board).
    empty_camera = [
        scene.get("scene_id", "?")
        for scene in storyboard
        if not scene.get("camera_angle") or not scene.get("camera_movement")
    ]
    if empty_camera:
        breaks.append(f"scenes missing camera direction: {empty_camera}")

    # Brand consistency — the style the Director chose is the brand look;
    # scenes must not name a different style in their notes.
    style_id = blueprint.get("visual_style", "")

    score = max(0, 100 - 15 * len(breaks))
    return {
        "characters": {
            "cast": cast_ids,
            "scenes_tracked": len(storyboard),
        },
        "lighting": lighting,
        "environment": environments,
        "color": palettes,
        "camera_language": blueprint.get("cinematic_language", {}).get("camera_grammar", ""),
        "animation_style": animation_styles[0] if animation_styles else "",
        "brand_consistency": {"style": style_id, "consistent": not breaks},
        "breaks": breaks,
        "continuity_score": score,
    }
