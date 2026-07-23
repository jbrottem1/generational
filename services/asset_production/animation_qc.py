"""Animation QC gate — rejects slideshow / static / lifeless productions.

Additive checks for the Animation Studio Department. Wired into asset
production quality stage without redesigning Orchestrator.
"""

from __future__ import annotations

from typing import Any


from services.media_production.true_motion import is_ken_burns_only


MAX_STATIC_SEC = 3.0
MIN_VISUAL_COUNT = 1


def run_animation_qc(asset: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return animation QC report with checks; passed=False on hard failures."""
    asset = asset or {}
    render = asset.get("render_package") or {}
    assembly = render.get("assembly") if isinstance(render.get("assembly"), dict) else {}
    assembly = assembly or {}
    storyboard = asset.get("storyboard_package") or {}
    beats = list(storyboard.get("beats") or [])
    scenes = list(asset.get("scene_breakdown") or [])
    motion_manifest = asset.get("true_motion") or assembly.get("true_motion") or {}

    checks: list[dict[str, Any]] = []

    visual_count = int(assembly.get("visual_count") or 0)
    color_bed = bool(assembly.get("color_bed")) or any(
        "color_bed" in str(x) for x in (assembly.get("log") or render.get("render_log") or [])
    )
    checks.append({
        "name": "no_color_bed",
        "ok": not color_bed,
        "detail": f"color_bed={color_bed}",
        "level": "error",
    })
    checks.append({
        "name": "has_visuals",
        "ok": visual_count >= MIN_VISUAL_COUNT,
        "detail": f"visual_count={visual_count}",
        "level": "error",
    })

    images = [g for g in (asset.get("generated_images") or []) if isinstance(g, dict)]
    placeholders = sum(1 for g in images if g.get("placeholder"))
    checks.append({
        "name": "no_placeholder_visuals",
        "ok": placeholders == 0 and (len(images) >= 1 or visual_count >= 1),
        "detail": f"placeholders={placeholders} images={len(images)}",
        "level": "error",
    })

    # Motion density: scenes longer than MAX_STATIC_SEC need motion intent
    long_static = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        dur = float(scene.get("length_sec") or scene.get("duration_sec") or 0)
        if dur <= MAX_STATIC_SEC:
            continue
        has_motion = bool(
            scene.get("camera_motion")
            or scene.get("camera_preset")
            or scene.get("animation_components")
            or scene.get("environment_fx")
            or scene.get("storyboard_beat")
            or (isinstance(scene.get("effect"), dict) and scene.get("effect"))
        )
        if not has_motion:
            long_static.append(scene.get("scene_number") or i + 1)
    checks.append({
        "name": "motion_density",
        "ok": not long_static,
        "detail": (
            f"static_over_{MAX_STATIC_SEC}s_scenes={long_static}"
            if long_static
            else f"all scenes have motion intent or duration<={MAX_STATIC_SEC}s"
        ),
        "level": "error",
    })

    has_storyboard = bool(beats) or bool(storyboard.get("beat_count"))
    # Soft-require storyboard when scenes exist (animation-first default)
    checks.append({
        "name": "storyboard_present",
        "ok": has_storyboard or not scenes,
        "detail": f"beats={len(beats)} scenes={len(scenes)}",
        "level": "error" if scenes else "info",
    })

    cameras = [str(b.get("camera") or "") for b in beats if isinstance(b, dict)]
    if not cameras:
        cameras = [
            str(s.get("camera_preset") or s.get("camera_motion") or "")
            for s in scenes
            if isinstance(s, dict)
        ]
    with_camera = sum(1 for c in cameras if c.strip())
    cam_ok = (with_camera >= max(1, int(0.5 * len(cameras)))) if cameras else bool(not scenes)
    checks.append({
        "name": "camera_intent",
        "ok": cam_ok,
        "detail": f"beats_with_camera={with_camera}/{len(cameras) or 0}",
        "level": "error" if scenes else "info",
    })

    env_fx = []
    for b in beats:
        if isinstance(b, dict):
            env_fx.extend(b.get("environment_fx") or [])
    for s in scenes:
        if isinstance(s, dict):
            env_fx.extend(s.get("environment_fx") or [])
    checks.append({
        "name": "env_life",
        "ok": bool(env_fx) or not scenes,
        "detail": f"environment_fx_count={len(env_fx)}",
        "level": "warning" if scenes and not env_fx else "info",
    })

    # Character consistency: if character_id set, expect CHAR- prefix registry style
    char_id = str(
        storyboard.get("character_id")
        or asset.get("character_id")
        or asset.get("series_character_id")
        or ""
    )
    char_ok = (not char_id) or char_id.startswith("CHAR-")
    checks.append({
        "name": "character_consistency",
        "ok": char_ok,
        "detail": f"character_id={char_id or 'unspecified'}",
        "level": "warning" if char_id and not char_ok else "info",
    })

    # True Animation Transition — reject Ken Burns-only slideshows
    effect_names: list[str] = []
    for s in scenes:
        if not isinstance(s, dict):
            continue
        eff = s.get("effect") or {}
        if isinstance(eff, dict):
            effect_names.append(str(eff.get("effect") or ""))
        else:
            effect_names.append(str(eff or s.get("camera_motion") or ""))
    for entry in (assembly.get("log") or []):
        text = str(entry)
        if "effect=" in text:
            effect_names.append(text.split("effect=")[-1].split()[0])
    slideshow = is_ken_burns_only(effect_names)
    true_motion_ok = str(motion_manifest.get("motion_class") or "") == "true_layered_animation"
    has_video_clip = any(
        str((s.get("resolved_asset") or {}).get("path") or "").lower().endswith((".mp4", ".mov", ".webm"))
        for s in scenes
        if isinstance(s, dict)
    )
    # Enforce slideshow reject when we have enough signal (effects logged or true_motion present)
    enforce_slideshow = bool(effect_names) or bool(motion_manifest) or bool(assembly.get("log"))
    checks.append({
        "name": "not_slideshow",
        "ok": (not slideshow) or true_motion_ok or has_video_clip or not enforce_slideshow,
        "detail": (
            f"slideshow={slideshow} true_motion={true_motion_ok} "
            f"video_clips={has_video_clip} effects={effect_names[:8]}"
        ),
        "level": "error" if enforce_slideshow else "warning",
    })
    checks.append({
        "name": "true_motion_or_video",
        "ok": true_motion_ok or has_video_clip or not bool(motion_manifest),
        "detail": f"motion_class={motion_manifest.get('motion_class') or 'unset'} video={has_video_clip}",
        "level": "error" if motion_manifest and not (true_motion_ok or has_video_clip) else "info",
    })

    errors = [
        f"{c['name']}: {c.get('detail')}"
        for c in checks
        if c.get("level") == "error" and not c.get("ok")
    ]
    warnings = [
        f"{c['name']}: {c.get('detail')}"
        for c in checks
        if c.get("level") == "warning" and not c.get("ok")
    ]
    return {
        "gate": "animation_qc",
        "department": "Animation Studio",
        "passed": not errors,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "max_static_sec": MAX_STATIC_SEC,
    }
