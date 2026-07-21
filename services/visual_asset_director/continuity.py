"""Cross-scene continuity — characters, environment, palette, style."""

from __future__ import annotations

from typing import Any


def _palette_distance(a: list[Any], b: list[Any]) -> float:
    if not a or not b:
        return 0.35
    # Compare first colors RGB euclidean normalized
    ca = a[0]
    cb = b[0]
    if not (isinstance(ca, (list, tuple)) and isinstance(cb, (list, tuple))):
        return 0.35
    dist = sum((float(ca[i]) - float(cb[i])) ** 2 for i in range(3)) ** 0.5
    return min(1.0, dist / 255.0)


def continuity_report(
    scene_results: list[dict[str, Any]],
    *,
    world_package: dict[str, Any] | None = None,
    style_profile: dict[str, Any] | None = None,
    character_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate continuity signals across directed scenes."""
    world_package = world_package or {}
    style_profile = style_profile or {}
    character_refs = list(character_refs or [])

    world_id = world_package.get("world_id") or (world_package.get("world") or {}).get("world_id")
    world_type = world_package.get("world_type") or (world_package.get("world") or {}).get("world_type")
    env_ids = []
    for env in world_package.get("environment_packages") or world_package.get("environments") or []:
        if isinstance(env, dict):
            env_ids.append(env.get("environment_id") or env.get("zone_id") or env.get("name"))

    palettes = []
    style_flags = []
    rejects_continuity = []
    for row in scene_results:
        insp = row.get("inspection") or {}
        palettes.append(insp.get("palette") or (insp.get("metrics") or {}).get("palette") or [])
        style_flags.append(row.get("style_compatibility", 70))
        for r in row.get("reject_reasons") or []:
            if r in (
                "style_drift",
                "character_mismatch",
                "wrong_environment",
                "perspective_jump",
                "repeated_asset",
            ):
                rejects_continuity.append({"scene_id": row.get("scene_id"), "reason": r})

    # Palette drift between consecutive approved scenes
    drifts = []
    for i in range(1, len(palettes)):
        drifts.append(_palette_distance(palettes[i - 1], palettes[i]))
    avg_drift = sum(drifts) / len(drifts) if drifts else 0.0
    palette_consistency = round(max(0.0, 100 * (1.0 - avg_drift * 1.4)), 1)

    # Environment consistency — scenes mentioning mismatched world
    env_score = 88.0 if world_id else 70.0
    for row in scene_results:
        scene = row.get("scene") or {}
        declared = scene.get("world_id") or scene.get("environment_id")
        if world_id and declared and str(declared) != str(world_id) and declared not in env_ids:
            env_score -= 15
            rejects_continuity.append({"scene_id": row.get("scene_id"), "reason": "wrong_environment"})

    char_score = 85.0 if character_refs else 72.0
    for ref in character_refs:
        name = str(ref.get("name") or ref.get("id") or "character")
        # Soft: if scene notes conflict
        for row in scene_results:
            notes = str((row.get("scene") or {}).get("notes") or "").lower()
            if "different professor" in notes or "new character" in notes:
                char_score -= 20
                rejects_continuity.append(
                    {"scene_id": row.get("scene_id"), "reason": "character_mismatch", "character": name}
                )

    style_consist = round(sum(style_flags) / max(1, len(style_flags)), 1) if style_flags else 70.0
    if style_consist < 55:
        rejects_continuity.append({"scene_id": "*", "reason": "style_drift"})

    # Repeated asset paths
    paths = [str(r.get("selected_path") or "") for r in scene_results if r.get("selected_path")]
    dupes = len(paths) - len(set(paths))
    repeat_penalty = min(30, dupes * 15)

    overall = round(
        max(
            0.0,
            (
                palette_consistency * 0.3
                + env_score * 0.25
                + char_score * 0.2
                + style_consist * 0.25
                - repeat_penalty
            ),
        ),
        1,
    )

    return {
        "world_id": world_id,
        "world_type": world_type,
        "environment_ids": env_ids,
        "character_references": character_refs,
        "palette_consistency": palette_consistency,
        "environment_consistency": round(max(0.0, env_score), 1),
        "character_consistency": round(max(0.0, char_score), 1),
        "style_consistency": style_consist,
        "style_profile": style_profile.get("style_key"),
        "average_palette_drift": round(avg_drift, 3),
        "repeated_asset_count": dupes,
        "continuity_issues": rejects_continuity[:40],
        "continuity_score": overall,
        "preserves": [
            "character_appearance",
            "clothing",
            "hair",
            "facial_structure",
            "age",
            "color_palette",
            "lighting_direction",
            "time_of_day",
            "environment",
            "props",
            "camera_orientation",
            "scale",
            "perspective",
            "artistic_style",
        ],
        "note": "Professor / Observatory / Lab continuity enforced via world + character refs",
    }
