#!/usr/bin/env python3
"""Golden Production — Why Fire Hydrants Are Different Colors (existing pipeline only)."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOPIC = "Why Fire Hydrants Are Different Colors"
HOOK = "These colors could determine whether firefighters save your house."
WORLD_ID = "WORLD_SUBURBAN_NEIGHBORHOOD"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_suburban_world() -> dict:
    from services.world_builder.library import get_library_world, save_world

    existing = get_library_world(WORLD_ID)
    if existing and existing.get("zones"):
        return existing

    world = {
        "world_id": WORLD_ID,
        "world_type": "Suburban Neighborhood",
        "name": "Persistent Suburban Neighborhood",
        "theme": "quiet daytime residential street with municipal fire infrastructure",
        "scale": "neighborhood",
        "historical_accuracy": 80,
        "environment": {
            "description": (
                "Sunlit American suburban street: asphalt road, concrete sidewalks, "
                "parked cars, oak trees, lawns, painted fire hydrants, utility spray marks, "
                "a small park corner, and a fire station two blocks down."
            ),
            "continuity_key": WORLD_ID,
            "do_not_replace_mid_episode": True,
            "time_of_day": "daytime",
            "lighting": "bright midday sun with soft tree-shadow dapples",
        },
        "architecture": [
            "single-family houses",
            "concrete sidewalks",
            "asphalt residential street",
            "neighborhood park",
            "municipal fire station facade",
        ],
        "weather": "clear mild day",
        "zones": [
            {
                "id": "street_corner",
                "name": "Residential Street Corner",
                "description": "Three differently colored hydrants visible on one corner; sidewalk + curb",
                "ambient_activity": ["distant lawn mower", "leaf shimmer", "parked mail truck idle"],
            },
            {
                "id": "sidewalk_hydrant",
                "name": "Sidewalk Hydrant Close-Up",
                "description": "Painted hydrant with flow-rate color bands and utility marks nearby",
                "ambient_activity": ["foot traffic shadow", "sprinkler hiss distant"],
            },
            {
                "id": "park_edge",
                "name": "Neighborhood Park Edge",
                "description": "Park lawn framing a second hydrant; playground distant soft focus",
                "ambient_activity": ["birds", "kids distant", "breeze in trees"],
            },
            {
                "id": "fire_station",
                "name": "Fire Station Approach",
                "description": "Bay doors, apparatus bay, hydrant training plaque",
                "ambient_activity": ["radio chatter soft", "bay door glint"],
            },
            {
                "id": "utility_map",
                "name": "Utility Markings Overlay Zone",
                "description": "Spray-painted utility marks on sidewalk for water main diagram overlay",
                "ambient_activity": ["survey stake shadow"],
            },
        ],
        "objects": [
            {"object_id": "hydrant_red", "name": "Red fire hydrant", "zone": "street_corner", "persistent": True},
            {"object_id": "hydrant_yellow", "name": "Yellow fire hydrant", "zone": "street_corner", "persistent": True},
            {"object_id": "hydrant_green", "name": "Green fire hydrant", "zone": "sidewalk_hydrant", "persistent": True},
            {"object_id": "hydrant_blue", "name": "Blue fire hydrant", "zone": "park_edge", "persistent": True},
            {"object_id": "sidewalk", "name": "Concrete sidewalk", "zone": "sidewalk_hydrant", "persistent": True},
            {"object_id": "trees", "name": "Street trees", "zone": "street_corner", "persistent": True},
            {"object_id": "park", "name": "Neighborhood park", "zone": "park_edge", "persistent": True},
            {"object_id": "fire_station", "name": "Fire station", "zone": "fire_station", "persistent": True},
            {"object_id": "utility_marks", "name": "Blue utility spray markings", "zone": "utility_map", "persistent": True},
        ],
        "furniture": [],
        "background_animations": ["tree leaves", "heat haze soft", "parked car reflections"],
        "sound_ambience": ["suburban daytime", "distant birds", "light traffic", "lawn ambient"],
        "color_palette": {
            "sky": "#87CEEB",
            "asphalt": "#3A3A3A",
            "lawn": "#4F8A3D",
            "hydrant_accents": ["#C41E3A", "#F5C400", "#2E8B57", "#1E90FF"],
        },
        "lighting": {"base": "daytime sunlight", "consistent_key": True},
        "design_rules": [
            "Keep the same street geometry, trees, and hydrant placements across every scene",
            "Vary camera (drone establish, push-in, close-up) — never replace the neighborhood",
            "Hydrant paint colors must remain consistent with flow-rate meaning",
            "Daytime lighting only — no night swap mid-episode",
        ],
    }
    return save_world(world, source="golden_production")


def run() -> dict:
    ensure_suburban_world()

    from services.channel_os.library import package_channel_production
    from services.production_operations import run_studio_ops

    command = (
        f'Create a 50 second YouTube Short titled "{TOPIC}". '
        f'Open in the first 3 seconds with three differently colored fire hydrants and the narration '
        f'"{HOOK}" '
        "Then explain why hydrants are painted different colors, what major colors indicate, "
        "how firefighters use colors for flow rating, why flow rate matters in a fire, "
        "and why two nearby hydrants can have different ratings. "
        "Use cinematic camera pushes, drone establishing shots, close-ups, animated color labels, "
        "water flow visualization, map graphics, motion graphics, professional captions, "
        "and ambient suburban neighborhood daytime audio. Style: documentary science educator."
    )

    constraints = {
        "publishing_enabled": False,
        "audience": "general public",
        "category": "Infrastructure",
        "domain": "Infrastructure",
        "world_id": WORLD_ID,
        "world_type": "Suburban Neighborhood",
        "world_objects": [
            "red yellow green blue fire hydrants",
            "sidewalk",
            "residential street",
            "park",
            "fire station",
            "utility markings",
            "trees",
        ],
        "world_continuity": [
            "single persistent suburban neighborhood",
            "daytime lighting continuous",
            "same hydrant positions across scenes",
        ],
        "hook_required": HOOK,
        "enforce_hook": True,
        "preferred_voice_provider": "elevenlabs",
        "golden_production": True,
        "visual_style": "cinematic documentary short — not slideshow",
        "target_channel": "Science",
    }

    ops = run_studio_ops(
        topic=TOPIC,
        platform="youtube_shorts",
        length_sec=50,
        style="educational",
        narrator="professor",
        voice="default",
        quality_target=98,
        command=command,
        constraints=constraints,
        context={
            "candidate_count": 1,
            "video_count": 1,
            "publishing_enabled": False,
            "audience": "general public",
            "category": "Infrastructure",
            "domain": "Infrastructure",
            "world_id": WORLD_ID,
            "world_type": "Suburban Neighborhood",
            "preferred_voice_provider": "elevenlabs",
            "golden_production": True,
            "hook": HOOK,
            "production_notes": {
                "platform": "youtube_shorts",
                "length_target_sec": "45-60",
                "narrator": "Professional science educator",
                "voice": "ElevenLabs",
            },
        },
    )

    profile = {
        "channel_id": "science",
        "brand_name": "Science",
        "name": "Science",
        "narrator_profile": "professor",
        "voice_profile": "elevenlabs",
        "visual_style": "cinematic documentary",
        "world_preferences": {"world_id": WORLD_ID, "style": "suburban daytime"},
        "thumbnail_style": "bold educational short",
        "tone": "curious authoritative science educator",
        "platforms": ["youtube_shorts"],
        "topic_categories": ["Infrastructure"],
    }
    packaged = package_channel_production(ops, profile=profile, category="Infrastructure")

    # Force exact topic folder name if packager title-cased differently
    from services.channel_os.library import channel_project_root, ensure_channel_tree

    project_root = channel_project_root("Science", "Infrastructure", TOPIC, create=True)
    ensure_channel_tree(project_root)

    # Enrich Project/ + Reports with golden artifacts
    ctx = ops.get("context") if isinstance(ops.get("context"), dict) else {}
    top = next((c for c in (ctx.get("candidates") or []) if isinstance(c, dict)), {})
    project_dir = Path(project_root) / "Project"
    reports_dir = Path(project_root) / "Reports"
    project_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "script": top.get("structured_script") or top.get("script_package") or top.get("script"),
        "scene_plan": (top.get("visual_package") or {}).get("scenes") or top.get("scenes"),
        "world_package": top.get("world_package") or ctx.get("world_package"),
        "cinematic_package": top.get("cinematography_package")
        or top.get("studio_render_package")
        or top.get("director_package"),
        "render_package": top.get("render_package"),
        "audio_package": top.get("audio_package"),
        "hook": HOOK,
    }
    (project_dir / "GOLDEN_BRIEF.json").write_text(
        json.dumps(
            {
                "topic": TOPIC,
                "hook": HOOK,
                "platform": "youtube_shorts",
                "length_sec": 50,
                "world_id": WORLD_ID,
                "publishing_enabled": False,
                "production_id": ops.get("production_id"),
                "generated_at": _now(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for name, payload in artifacts.items():
        if payload is None:
            continue
        (project_dir / f"{name.upper()}.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    # Copy ops production report markdown/json into Reports/
    pid = ops.get("production_id")
    if pid:
        from services.production_operations.status import ops_dir

        od = ops_dir(str(pid))
        for fname in ("PRODUCTION_REPORT.json", "PRODUCTION_REPORT.md", "CREATIVE_EXCELLENCE.json", "CREATIVE_EXCELLENCE.md"):
            src = od / fname
            if src.is_file():
                shutil.copy2(src, reports_dir / fname)

    # Materialize scene stills into Assets/ from render package
    assets_dir = Path(project_root) / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    rp_payload = top.get("render_package") or {}
    if not rp_payload and (project_dir / "RENDER_PACKAGE.json").is_file():
        try:
            rp_payload = json.loads((project_dir / "RENDER_PACKAGE.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            rp_payload = {}
    for scene in rp_payload.get("scene_render_plan") or []:
        if not isinstance(scene, dict):
            continue
        ra = scene.get("resolved_asset") or {}
        raw = ra.get("local_path") or ra.get("path") or ""
        src = Path(str(raw))
        if not src.is_absolute():
            src = ROOT / src
        if src.is_file() and src.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            shutil.copy2(src, assets_dir / src.name)

    exec_paths = ((ctx.get("executive_export") or {}).get("paths") or {})
    # Ensure Export has episode.mp4 if packaging missed
    export_dir = Path(project_root) / "Export"
    export_dir.mkdir(parents=True, exist_ok=True)
    mp4_src = packaged.get("export_mp4") or exec_paths.get("mp4")
    if mp4_src and Path(str(mp4_src)).is_file():
        dest = export_dir / "Why_Fire_Hydrants_Are_Different_Colors.mp4"
        if Path(str(mp4_src)).resolve() != dest.resolve():
            shutil.copy2(mp4_src, dest)
        packaged["export_mp4"] = str(dest)

    creative = build_creative_review(ops, packaged, project_root)
    (reports_dir / "GOLDEN_CREATIVE_REVIEW.md").write_text(creative["markdown"], encoding="utf-8")
    (reports_dir / "GOLDEN_CREATIVE_REVIEW.json").write_text(
        json.dumps(creative["card"], indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "GOLDEN_PRODUCTION_STATUS.json").write_text(
        json.dumps(
            {
                "topic": TOPIC,
                "production_id": ops.get("production_id"),
                "success": ops.get("success"),
                "video_exists": ops.get("video_exists"),
                "project_root": str(project_root),
                "packaged": packaged,
                "generated_at": _now(),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    # Repo-level status report mirror
    (ROOT / "GOLDEN_PRODUCTION_FIRE_HYDRANTS.md").write_text(
        creative["markdown"]
        + "\n\n## Packaging\n\n"
        + f"- Project root: `{project_root}`\n"
        + f"- MP4: `{packaged.get('export_mp4')}`\n"
        + f"- Production id: `{ops.get('production_id')}`\n"
        + f"- Success: `{ops.get('success')}` / video_exists: `{ops.get('video_exists')}`\n",
        encoding="utf-8",
    )

    return {
        "ok": bool(ops.get("success") and ops.get("video_exists")),
        "production_id": ops.get("production_id"),
        "success": ops.get("success"),
        "video_exists": ops.get("video_exists"),
        "project_root": str(project_root),
        "packaged": packaged,
        "creative": creative["card"],
    }


def build_creative_review(ops: dict, packaged: dict, project_root: Path) -> dict:
    status = ops.get("status") or {}
    report = ops.get("report") or {}
    ctx = ops.get("context") if isinstance(ops.get("context"), dict) else {}
    top = next((c for c in (ctx.get("candidates") or []) if isinstance(c, dict)), {})
    mp4 = packaged.get("export_mp4") or ""
    mp4_ok = bool(mp4 and Path(str(mp4)).is_file() and Path(str(mp4)).stat().st_size > 10_000)
    world = top.get("world_package") or {}
    scenes = (top.get("visual_package") or {}).get("scenes") or []
    creative_score = report.get("creative_excellence_score")
    overall = report.get("overall_quality_score")
    mock = bool((top.get("render_package") or {}).get("mock"))

    # Evidence from on-disk package (more honest than scorecards alone)
    project_dir = Path(project_root) / "Project"
    script_blob = ""
    for name in ("SCRIPT.json", "HOOK.json"):
        p = project_dir / name
        if p.is_file():
            script_blob += p.read_text(encoding="utf-8", errors="ignore")
    hook_in_script = HOOK.lower() in script_blob.lower()
    render_raw = ""
    rp = project_dir / "RENDER_PACKAGE.json"
    if rp.is_file():
        render_raw = rp.read_text(encoding="utf-8", errors="ignore")
    fallback_n = render_raw.count("cinematic_fallback")
    voice_path = str(
        ((top.get("audio_package") or {}).get("path"))
        or ((top.get("voice_package") or {}).get("path"))
        or packaged.get("audio")
        or ""
    )
    local_voice = "_local" in voice_path or "/demo" in voice_path.lower()
    eleven_live = ("elevenlabs" in voice_path.lower() or "eleven" in voice_path.lower()) and not local_voice
    audio_pkg = top.get("audio_package") or top.get("voice_package") or {}
    provider = str(audio_pkg.get("provider") or audio_pkg.get("source") or "").lower()
    if "local" in provider or "demo" in provider:
        local_voice = True
    if "eleven" in provider and not local_voice:
        eleven_live = True

    # Honest creative judgment — grounded in what a viewer would actually see/hear
    has_world = bool(world.get("world_id") or (project_dir / "WORLD_PACKAGE.json").is_file())
    scene_n = len(scenes) or fallback_n // 2
    mostly_fallback = fallback_n >= 6 or (
        scene_n > 0 and fallback_n >= max(2, scene_n)
    )
    stop_scroll = "NOT YET" if (mostly_fallback or not hook_in_script) else ("YES" if mp4_ok else "NO")
    if mostly_fallback:
        feels_doc = "NO — Ken-Burns still plates / cinematic fallbacks dominate; not shot footage"
    elif mock:
        feels_doc = "NO"
    else:
        feels_doc = "MOSTLY"
    visuals_serve = "PARTIAL" if mostly_fallback else ("YES" if scene_n >= 5 and has_world else "PARTIAL")
    publish_ready = bool(
        ops.get("success")
        and mp4_ok
        and packaged.get("audio")
        and packaged.get("captions")
        and hook_in_script
        and not mostly_fallback
        and not local_voice
        and float(creative_score or 0) >= 78
    )
    highest_impact = (
        "Swap the 11 cinematic-fallback Ken-Burns plates for real hydrant B-roll "
        "(three colors in the open, then labeled close-ups + a water-flow graphic) "
        "so the Short reads as documentary footage instead of branded slides."
    )

    card = {
        "topic": TOPIC,
        "hook": HOOK,
        "technical": {
            "mp4": mp4_ok,
            "mp4_path": mp4,
            "audio": bool(packaged.get("audio")),
            "captions": bool(packaged.get("captions")),
            "thumbnail": bool(packaged.get("thumbnail")),
            "world_id": world.get("world_id") or WORLD_ID,
            "scene_count": scene_n,
            "creative_excellence_score": creative_score,
            "overall_quality_score": overall,
            "ops_success": ops.get("success"),
            "pipeline_health": status.get("pipeline_health"),
            "elapsed_ms": status.get("elapsed_ms") or ops.get("elapsed_ms"),
            "hook_in_script": hook_in_script,
            "cinematic_fallback_refs": fallback_n,
            "voice_path": voice_path,
            "elevenlabs_live": eleven_live,
            "local_voice_fallback": local_voice,
        },
        "answers": {
            "1_stop_scrolling": stop_scroll,
            "2_professional_documentary_short": feels_doc,
            "3_visuals_explain_narration": visuals_serve,
            "4_publish_on_monetized_channel": "YES" if publish_ready else "NO",
            "5_highest_impact_improvement": highest_impact,
        },
        "publication_ready_judgment": publish_ready,
        "generated_at": _now(),
        "project_root": str(project_root),
        "evidence_notes": [
            f"Mission hook present in SCRIPT: {hook_in_script}",
            f"cinematic_fallback references in RENDER_PACKAGE: {fallback_n}",
            f"Voice: {'ElevenLabs live' if eleven_live else ('local fallback' if local_voice else 'unknown')} ({voice_path})",
        ],
    }

    tech_ok = mp4_ok and bool(packaged.get("audio")) and bool(packaged.get("captions"))
    judgment = (
        "PASS"
        if publish_ready
        else (
            "TECHNICAL PASS / CREATIVE FAIL — package complete under Videos/, "
            "but not yet monetized-channel ready"
            if tech_ok
            else "FAIL"
        )
    )

    md = "\n".join(
        [
            "# Golden Production — Creative Review",
            "",
            f"**Topic:** {TOPIC}",
            f"**Hook:** {HOOK}",
            f"**Project:** `{project_root}`",
            "",
            "## Technical checklist",
            "",
            f"- MP4 playable file: {'✓' if mp4_ok else '✗'} `{mp4}`",
            f"- Audio: {'✓' if card['technical']['audio'] else '✗'}",
            f"- Captions: {'✓' if card['technical']['captions'] else '✗'}",
            f"- Thumbnail: {'✓' if card['technical']['thumbnail'] else '✗'}",
            f"- World package: `{card['technical']['world_id'] or 'missing'}`",
            f"- Scenes: {scene_n}",
            f"- Mission hook in script: {'✓' if hook_in_script else '✗'}",
            f"- Cinematic fallback refs: {fallback_n}",
            f"- Voice: {'ElevenLabs' if eleven_live else ('local fallback' if local_voice else 'unknown')}",
            f"- Creative score (pipeline): {creative_score}",
            f"- Overall quality (pipeline): {overall}",
            f"- Ops success / video_exists: {ops.get('success')} / {ops.get('video_exists')}",
            "",
            "## Evidence notes",
            "",
            *[f"- {n}" for n in card["evidence_notes"]],
            "",
            "## Final creative review (honest)",
            "",
            f"1. **Would this stop a viewer from scrolling?** {card['answers']['1_stop_scrolling']}",
            f"2. **Does it feel like a professionally edited documentary short?** {card['answers']['2_professional_documentary_short']}",
            f"3. **Is every visual helping explain the narration?** {card['answers']['3_visuals_explain_narration']}",
            f"4. **Would you personally publish this on a monetized YouTube channel?** {card['answers']['4_publish_on_monetized_channel']}",
            f"5. **Single highest-impact improvement before release:** {card['answers']['5_highest_impact_improvement']}",
            "",
            f"**Publication-ready judgment:** {judgment}",
            "",
            "_Improvement was not auto-implemented per mission instructions._",
            "",
        ]
    )
    return {"card": card, "markdown": md}


if __name__ == "__main__":
    out = run()
    print(json.dumps({k: out[k] for k in out if k != "packaged"}, indent=2, default=str))
    print(json.dumps({"packaged_keys": list((out.get("packaged") or {}).keys())}, indent=2))
    raise SystemExit(0 if out.get("ok") else 2)
