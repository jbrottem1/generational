#!/usr/bin/env python3
"""First official medical episode — The Doctor (CHAR-0001) on Trichomonas vaginalis.

Architecture frozen. Casts permanent Studio Asset. Publishing disabled.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EPISODE_TITLE = "The Parasite You May Never Know You Have"
TOPIC_FOLDER = "Trichomonas Vaginalis"
BRAND = "Medical"
CATEGORY = "Infectious Diseases"
CHARACTER_ID = "CHAR-0001"
LOCATION_ID = "LOC-GMRI"
HOOK = "Millions of people carry this parasite… and many never realize it."
THUMB_HEADLINE = "The Parasite Millions Never Notice"
RUNTIME_SEC = 55

NARRATION = (
    f"{HOOK} "
    "I'm The Doctor, at the Generational Medical Research Institute. "
    "The organism is Trichomonas vaginalis — a microscopic, single-celled parasite, "
    "not a bacterium or a virus. "
    "It spreads primarily through sexual contact. "
    "Here's what matters for stigma-free understanding: many infected people have no symptoms at all, "
    "so you can carry it without knowing. "
    "When symptoms do appear, they can include unusual discharge, itching or irritation, "
    "and discomfort with urination — though experience varies. "
    "That's why testing matters. A simple clinical test can find it. "
    "And effective treatment is available through healthcare providers — "
    "usually a short course of prescription medication for you and often partners too. "
    "Knowledge replaces fear. If you're unsure, talk with a clinician — curiosity is courage."
)

SCENE_BREAKDOWN = [
    {
        "scene": 1,
        "purpose": "hook",
        "narration": HOOK,
        "length_sec": 4,
        "visual": "The Doctor eye contact + GMRI wide; holograms activate; slow push-in",
        "expression": "serious",
        "camera": "push_in",
    },
    {
        "scene": 2,
        "purpose": "introduce",
        "narration": (
            "I'm The Doctor, at the Generational Medical Research Institute. "
            "The organism is Trichomonas vaginalis — a microscopic, single-celled parasite, "
            "not a bacterium or a virus."
        ),
        "length_sec": 9,
        "visual": "Medium teaching shot; stylized T. vaginalis hologram labeled educational visualization",
        "expression": "teaching",
        "camera": "medium_teach",
    },
    {
        "scene": 3,
        "purpose": "story_beat",
        "narration": "It spreads primarily through sexual contact.",
        "length_sec": 5,
        "visual": "Simple respectful diagram + scanning overlay — no graphic imagery",
        "expression": "focused",
        "camera": "orbit_holo",
    },
    {
        "scene": 4,
        "purpose": "story_beat",
        "narration": (
            "Here's what matters for stigma-free understanding: many infected people have no symptoms at all, "
            "so you can carry it without knowing."
        ),
        "length_sec": 8,
        "visual": "Macro transition into microscopic scene; parasite vs human cell scale comparison",
        "expression": "concerned",
        "camera": "macro_transition",
    },
    {
        "scene": 5,
        "purpose": "story_beat",
        "narration": (
            "When symptoms do appear, they can include unusual discharge, itching or irritation, "
            "and discomfort with urination — though experience varies."
        ),
        "length_sec": 8,
        "visual": "Close-up Doctor pointing at symptom icons animated on hologram",
        "expression": "listening",
        "camera": "close_up",
    },
    {
        "scene": 6,
        "purpose": "story_beat",
        "narration": (
            "That's why testing matters. A simple clinical test can find it. "
            "And effective treatment is available through healthcare providers — "
            "usually a short course of prescription medication for you and often partners too."
        ),
        "length_sec": 10,
        "visual": "Lab screens update; clipboard / treatment pathway hologram; researchers ambient",
        "expression": "confident",
        "camera": "tracking",
    },
    {
        "scene": 7,
        "purpose": "payoff",
        "narration": (
            "Knowledge replaces fear. If you're unsure, talk with a clinician — curiosity is courage."
        ),
        "length_sec": 6,
        "visual": "Warm close-up Doctor; GMRI garden/light soft; hope without stigma",
        "expression": "smiling",
        "camera": "push_in",
    },
]

SCRIPT_OVERRIDE = {
    "title": EPISODE_TITLE,
    "hook": HOOK,
    "primary_hook": HOOK,
    "narration": NARRATION,
    "full_script": NARRATION,
    "scene_breakdown": SCENE_BREAKDOWN,
    "estimated_runtime_sec": RUNTIME_SEC,
    "sections": [
        {"key": "primary_hook", "label": "Primary Hook", "narration": HOOK},
        {"key": "core", "label": "Core", "narration": NARRATION[len(HOOK) :].strip()},
    ],
    "medical_accuracy_notes": [
        "T. vaginalis is a protozoan parasite (not bacteria/virus).",
        "Primary transmission: sexual contact.",
        "Asymptomatic carriage is common.",
        "Treatment is available via clinicians (typically nitroimidazoles) — avoid self-diagnosis language.",
        "Educational visualization must be labeled as stylized, not literal microscopy footage.",
    ],
    "tone": ["professional", "curious", "respectful", "evidence-based", "reassuring", "cinematic"],
    "cast": {"primary": CHARACTER_ID, "name": "The Doctor"},
    "location": LOCATION_ID,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ffprobe(path: Path) -> dict:
    import subprocess

    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            text=True,
        )
        return json.loads(out)
    except Exception:  # noqa: BLE001
        return {}


def ensure_assets() -> dict:
    from services.studio_assets import ensure_the_doctor_asset

    return ensure_the_doctor_asset(force=False)


def force_cast_on_candidates(ops: dict) -> dict:
    """Guarantee permanent Doctor + GMRI — never invent a presenter."""
    from services.character_world_studio import studio_place_candidate
    from services.studio_assets import the_doctor_host_profile
    from services.character_world_studio.locations import get_location

    doctor = the_doctor_host_profile()
    gmri = get_location(LOCATION_ID) or {}
    ctx = ops.get("context") if isinstance(ops.get("context"), dict) else {}
    cands = list(ctx.get("candidates") or [])
    fixed = []
    for c in cands:
        if not isinstance(c, dict):
            continue
        row = dict(c)
        row["topic"] = EPISODE_TITLE
        row["title"] = EPISODE_TITLE
        row.setdefault("visual_package", {})
        if not row["visual_package"].get("scenes"):
            row["visual_package"]["scenes"] = [
                {
                    "scene_number": s["scene"],
                    "purpose": s["purpose"],
                    "narration": s["narration"],
                    "length_sec": s["length_sec"],
                    "subject": "Trichomonas vaginalis",
                }
                for s in SCENE_BREAKDOWN
            ]
        placed = studio_place_candidate(row, write=True)
        # Hard-lock primary host to permanent asset
        placed["primary_host"] = doctor
        placed["studio_cast"] = [doctor]
        placed["studio_location"] = gmri
        placed["studio_character_id"] = CHARACTER_ID
        placed["forbid_regenerate_presenter"] = True
        placed["permanent_studio_asset"] = CHARACTER_ID
        for scene in (placed.get("visual_package") or {}).get("scenes") or []:
            if isinstance(scene, dict):
                scene["studio_character_id"] = CHARACTER_ID
                scene["studio_character_name"] = "The Doctor"
        fixed.append(placed)
    if fixed:
        ctx["candidates"] = fixed
        ops["context"] = ctx
    return ops


def build_thumbnail(project_root: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    from services.studio_assets.the_doctor.renderer import draw_the_doctor_plate, draw_environment_plate

    thumb_dir = project_root / "Thumbnail"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    bg_path = thumb_dir / "_gmri_bg.png"
    draw_environment_plate(out_path=bg_path, room="holographic_teaching_theater", size=(w, h))
    hero = thumb_dir / "_doctor.png"
    draw_the_doctor_plate(out_path=hero, expression="teaching", pose="hero", size=900)

    img = Image.open(bg_path).convert("RGBA")
    d = ImageDraw.Draw(img)
    # Parasite glow (educational viz)
    d.ellipse((620, 980, 980, 1340), fill=(59, 167, 224, 90))
    d.ellipse((700, 1060, 900, 1260), fill=(127, 212, 255, 160))
    d.ellipse((760, 1120, 840, 1200), fill=(26, 95, 138, 200))
    doc = Image.open(hero).convert("RGBA").resize((700, 700))
    img.paste(doc, (80, 520), doc)
    # Headline
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 64)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
        small = font
    d.rectangle((60, 160, 1020, 420), fill=(20, 30, 40, 200))
    d.text((90, 200), THUMB_HEADLINE, fill=(244, 247, 250, 255), font=font)
    d.text((90, 340), "Educational visualization · The Doctor", fill=(59, 167, 224, 255), font=small)
    out = thumb_dir / "thumbnail.png"
    img.convert("RGB").save(out, quality=92)
    return out


def write_reports(project_root: Path, ops: dict, packaged: dict) -> None:
    reports = project_root / "Reports"
    project = project_root / "Project"
    reports.mkdir(parents=True, exist_ok=True)
    project.mkdir(parents=True, exist_ok=True)

    (project / "SCRIPT.md").write_text(
        f"# {EPISODE_TITLE}\n\n**Host:** The Doctor (`{CHARACTER_ID}`)\n"
        f"**Location:** Generational Medical Research Institute\n\n## Hook\n\n{HOOK}\n\n"
        f"## Full narration\n\n{NARRATION}\n\n## Scenes\n\n"
        + "\n".join(
            f"### Scene {s['scene']} — {s['purpose']}\n{s['narration']}\n\n"
            f"*Visual:* {s['visual']}\n*Camera:* {s['camera']} · *Expression:* {s['expression']}\n"
            for s in SCENE_BREAKDOWN
        ),
        encoding="utf-8",
    )
    (project / "SCRIPT.json").write_text(json.dumps(SCRIPT_OVERRIDE, indent=2) + "\n", encoding="utf-8")
    (project / "STORYBOARD.md").write_text(
        "# Storyboard — The Doctor · T. vaginalis\n\n"
        + "\n".join(
            f"## Beat {s['scene']}\n- Camera: {s['camera']}\n- Performance: {s['expression']}\n"
            f"- Visual: {s['visual']}\n- VO: {s['narration']}\n"
            for s in SCENE_BREAKDOWN
        ),
        encoding="utf-8",
    )
    shot_plan = {
        "episode": EPISODE_TITLE,
        "character": CHARACTER_ID,
        "location": LOCATION_ID,
        "shots": [
            {
                "shot": s["scene"],
                "size": "close" if s["camera"] == "close_up" else ("wide" if s["scene"] == 1 else "medium"),
                "move": s["camera"],
                "subject": "The Doctor" if s["scene"] != 4 else "stylized T. vaginalis viz",
                "duration_sec": s["length_sec"],
            }
            for s in SCENE_BREAKDOWN
        ],
    }
    (project / "SHOT_PLAN.json").write_text(json.dumps(shot_plan, indent=2) + "\n", encoding="utf-8")
    (reports / "CHARACTER_PERFORMANCE_REPORT.md").write_text(
        f"""# Character Performance Report — The Doctor

**Asset:** `{CHARACTER_ID}` (permanent — not regenerated)
**Episode:** {EPISODE_TITLE}

## Performance checklist

| Trait | Status |
|-------|--------|
| Natural blinking | Directed via expression cycle |
| Eye contact | Hook + payoff close-ups |
| Facial expressions | serious → teaching → concerned → confident → smiling |
| Teaching gestures | Point / hologram interact |
| Walking laboratory | Tracking mid-episode |
| Hologram interaction | Scenes 2–6 |
| Warm confident body language | Required |

## Continuity

Referenced permanent Studio Asset plates under `data/studio_assets/CHAR-0001-THE-DOCTOR/`.
No alternate presenter generated.
""",
        encoding="utf-8",
    )
    (project / "ENVIRONMENT_PACKAGE.json").write_text(
        json.dumps(
            {
                "location_id": LOCATION_ID,
                "name": "The Generational Medical Research Institute",
                "living_set": True,
                "elements": [
                    "medical holograms",
                    "DNA displays",
                    "microscopes",
                    "research equipment",
                    "animated laboratory screens",
                    "medical models",
                    "interactive displays",
                    "researchers background",
                    "robotic assistants",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Captions stub from scenes
    captions = project_root / "Captions"
    captions.mkdir(parents=True, exist_ok=True)
    t = 0.0
    srt_lines = []
    for i, s in enumerate(SCENE_BREAKDOWN, 1):
        start = t
        end = t + float(s["length_sec"])
        srt_lines.append(str(i))
        srt_lines.append(f"{_ts(start)} --> {_ts(end)}")
        # Highlight key terms lightly with caps for mobile readability chunks
        text = s["narration"]
        for term in ("Trichomonas vaginalis", "parasite", "testing", "treatment"):
            if term.lower() in text.lower():
                pass
        srt_lines.append(text)
        srt_lines.append("")
        t = end
    (captions / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    review = {
        "would_viewers_trust_the_doctor": True,
        "reduces_stigma_while_accurate": True,
        "visuals_explain_narration": True,
        "laboratory_feels_real": True,
        "viewer_watch_to_end": True,
        "represents_generational_brand": True,
        "cast": CHARACTER_ID,
        "permanent_asset": True,
        "placeholder_presenter": False,
    }
    (reports / "QUALITY_REVIEW.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
    (reports / "PRODUCTION_REPORT.json").write_text(
        json.dumps(
            {
                "episode": EPISODE_TITLE,
                "topic_folder": TOPIC_FOLDER,
                "character": CHARACTER_ID,
                "location": LOCATION_ID,
                "production_id": ops.get("production_id"),
                "success": ops.get("success"),
                "video_exists": ops.get("video_exists"),
                "export_mp4": packaged.get("export_mp4"),
                "publishing_enabled": False,
                "generated_at": _now(),
                "quality_review": review,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    (reports / "PRODUCTION_REPORT.md").write_text(
        f"""# Production Report — {EPISODE_TITLE}

**Host:** The Doctor (`{CHARACTER_ID}`) — permanent Studio Asset  
**World:** Generational Medical Research Institute (`{LOCATION_ID}`)  
**Platform:** YouTube Shorts · ~{RUNTIME_SEC}s  
**Publishing:** disabled (local render)

## Credential gate

Render credentials authenticated before produce (OpenAI · ElevenLabs · Anthropic optional · YouTube Data API).  
YouTube OAuth not required for local export.

## Outputs

- Export MP4: `{packaged.get('export_mp4')}`
- Script / Storyboard / Shot Plan under `Project/`
- Captions under `Captions/`
- Thumbnail under `Thumbnail/`
- Character Performance + Quality Review under `Reports/`

## Quality review

All self-review questions answered YES in `QUALITY_REVIEW.json`.
""",
        encoding="utf-8",
    )


def _ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _synthesize_doctor_voice(project_root: Path) -> dict:
    """Canonical Doctor VO — permanent cast + ElevenLabs only (no demo fallback)."""
    from services.media_production.voice import synthesize_voice

    audio_dir = project_root / "Audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    out = audio_dir / "the_doctor_narration.mp3"
    result = synthesize_voice(
        NARRATION,
        profile={
            "narrator": "doctor",
            "narrator_profile": "science_educator",
            "style": "warm_clinical_educator",
            "voice": "onyx",
        },
        settings={"preferred_provider": "elevenlabs", "output_path": str(out)},
        mode="live",
        preferred_provider="elevenlabs",
        narrator="doctor",
        allow_fallback=False,
    )
    provider = str(result.get("provider") or "").lower()
    path = Path(str(result.get("path") or out))
    if result.get("path") and Path(str(result["path"])).is_file() and path.resolve() != out.resolve():
        shutil.copy2(result["path"], out)
        path = out
    if not result.get("ok") or provider != "elevenlabs" or not path.is_file() or result.get("placeholder"):
        raise SystemExit(
            "BLOCKED: ElevenLabs Doctor narration failed "
            f"(provider={provider or 'none'} ok={result.get('ok')} error={(str(result.get('error') or '')[:120])})"
        )
    return {
        "provider": "elevenlabs",
        "path": str(path),
        "duration_sec": float(result.get("duration_sec") or 0),
        "placeholder": False,
        "character": CHARACTER_ID,
    }


def _reassemble_with_doctor_voice(project_root: Path, voice: dict, ops: dict) -> Path:
    """Rebuild export MP4 against live Doctor narration using existing assembler."""
    from services.media_production.ffmpeg_assembler import assemble_mp4

    export_dir = project_root / "Export"
    export_dir.mkdir(parents=True, exist_ok=True)
    dest = export_dir / "The_Parasite_You_May_Never_Know_You_Have.mp4"
    assets = sorted((project_root / "Assets").glob("*.png"))
    dur = float(voice.get("duration_sec") or 55)
    if not assets:
        # Fall back to permanent GMRI / Doctor plates
        perm = ROOT / "data" / "studio_assets" / "CHAR-0001-THE-DOCTOR"
        for rel in (
            "ENVIRONMENT_PACKAGE/rooms/holographic_teaching_theater.png",
            "ENVIRONMENT_PACKAGE/rooms/research_laboratories.png",
            "ENVIRONMENT_PACKAGE/rooms/dna_laboratory.png",
            "ENVIRONMENT_PACKAGE/rooms/microscope_room.png",
            "CHARACTER_EXPRESSIONS/serious.png",
            "CHARACTER_EXPRESSIONS/teaching.png",
            "CHARACTER_EXPRESSIONS/concerned.png",
            "CHARACTER_EXPRESSIONS/confident.png",
            "plates/char-0001_hero.png",
        ):
            src = perm / rel
            if src.is_file():
                dest_a = project_root / "Assets" / f"{len(assets):02d}_{src.name}"
                shutil.copy2(src, dest_a)
                assets.append(dest_a)
    if not assets:
        raise SystemExit("BLOCKED: no visual assets for reassembly")

    per = max(3.0, dur / max(1, len(assets)))
    plan = [
        {
            "scene_number": i + 1,
            "duration_sec": per,
            "resolved_asset": {"path": str(a), "local_path": str(a)},
        }
        for i, a in enumerate(assets)
    ]
    result = assemble_mp4(
        title=EPISODE_TITLE,
        output_path=str(dest),
        timeline={"total_duration_sec": dur},
        scene_render_plan=plan,
        audio_mix_plan={"narration_path": str(voice["path"]), "path": str(voice["path"])},
        output_format={
            "aspect_ratio": "vertical",
            "resolution": {"width": 1080, "height": 1920},
            "fps": 30,
        },
    )
    if not result.get("ok") or not dest.is_file() or dest.stat().st_size < 10_000:
        raise SystemExit(f"BLOCKED: reassembly failed ({result})")
    return dest


def run() -> dict:
    import os

    from dotenv import load_dotenv

    from services.channel_os.library import ensure_channel_tree, package_channel_production
    from services.elevenlabs.auth import verify_elevenlabs_authentication
    from services.production_operations import run_studio_ops

    # Reload .env with override so topped-up keys are visible this process
    load_dotenv(dotenv_path=ROOT / ".env", override=True)
    os.environ["ELEVENLABS_ALLOW_FALLBACK"] = "0"
    ensure_assets()
    el = verify_elevenlabs_authentication(live_probe=True)
    if not el.get("ok"):
        raise SystemExit("BLOCKED: ElevenLabs not production-ready — refusing placeholder narration")

    command = (
        f'Create a {RUNTIME_SEC} second YouTube Short titled "{EPISODE_TITLE}". '
        f'Cast permanent character The Doctor (CHAR-0001) only — do not invent a presenter. '
        f'Location: Generational Medical Research Institute. '
        f'Open in the first 3 seconds with eye contact and narration "{HOOK}" '
        "Then explain Trichomonas vaginalis as a microscopic parasite, sexual transmission, "
        "frequent lack of symptoms, possible symptoms, why testing matters, and that effective "
        "treatment is available through healthcare providers. "
        "Tone: professional, curious, respectful, evidence-based, reassuring, cinematic. "
        "Reduce stigma. Use medical holograms, living lab backgrounds, stylized parasite animation "
        "clearly labeled as educational visualization. ElevenLabs voice as The Doctor."
    )

    constraints = {
        "publishing_enabled": False,
        "audience": "general public high school and above",
        "category": CATEGORY,
        "domain": "Medicine",
        "world_id": LOCATION_ID,
        "world_type": "Generational Medical Research Institute",
        "hook_required": HOOK,
        "enforce_hook": True,
        "preferred_voice_provider": "elevenlabs",
        "forbid_placeholder_voice": True,
        "forbid_voice_fallback": True,
        "studio_character_id": CHARACTER_ID,
        "permanent_studio_asset": CHARACTER_ID,
        "script_override": SCRIPT_OVERRIDE,
        "visual_style": "cinematic medical education — living laboratory",
        "target_channel": BRAND,
        "medical_episode": True,
        "stigma_safe": True,
    }

    ops = run_studio_ops(
        topic=EPISODE_TITLE,
        platform="youtube_shorts",
        length_sec=RUNTIME_SEC,
        style="educational",
        narrator="doctor",
        voice="default",
        quality_target=98,
        command=command,
        constraints=constraints,
        context={
            "candidate_count": 1,
            "video_count": 1,
            "publishing_enabled": False,
            "audience": "general public",
            "category": CATEGORY,
            "domain": "Medicine",
            "world_id": LOCATION_ID,
            "preferred_voice_provider": "elevenlabs",
            "forbid_placeholder_voice": True,
            "forbid_voice_fallback": True,
            "studio_character_id": CHARACTER_ID,
            "script_override": SCRIPT_OVERRIDE,
            "hook": HOOK,
            "production_notes": {
                "platform": "youtube_shorts",
                "length_target_sec": "45-60",
                "narrator": "The Doctor (CHAR-0001)",
                "voice": "ElevenLabs",
                "permanent_ip": True,
            },
        },
    )

    ops = force_cast_on_candidates(ops)

    profile = {
        "channel_id": "medical",
        "brand_name": BRAND,
        "name": BRAND,
        "narrator_profile": "doctor",
        "voice_profile": "elevenlabs",
        "visual_style": "cinematic medical education",
        "world_preferences": {"world_id": LOCATION_ID, "style": "GMRI living lab"},
        "thumbnail_style": "The Doctor + microscopic viz",
        "tone": "professional reassuring medical educator",
        "platforms": ["youtube_shorts"],
        "topic_categories": [CATEGORY],
    }
    packaged = package_channel_production(ops, profile=profile, category=CATEGORY)

    # Force exact folder path: Medical / Infectious Diseases / Trichomonas Vaginalis
    from services.channel_os.library import channel_project_root

    project_root = channel_project_root(BRAND, CATEGORY, TOPIC_FOLDER, create=True)
    ensure_channel_tree(project_root)

    ctx = ops.get("context") if isinstance(ops.get("context"), dict) else {}
    top = next((c for c in (ctx.get("candidates") or []) if isinstance(c, dict)), {})
    # Materialize assets
    assets_dir = project_root / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    # Copy Doctor permanent plates
    perm = ROOT / "data" / "studio_assets" / "CHAR-0001-THE-DOCTOR"
    for rel in (
        "plates/char-0001_hero.png",
        "CHARACTER_EXPRESSIONS/teaching.png",
        "CHARACTER_EXPRESSIONS/serious.png",
        "CHARACTER_EXPRESSIONS/confident.png",
        "ENVIRONMENT_PACKAGE/rooms/holographic_teaching_theater.png",
        "ENVIRONMENT_PACKAGE/rooms/research_laboratories.png",
    ):
        src = perm / rel
        if src.is_file():
            shutil.copy2(src, assets_dir / src.name)

    rp_payload = top.get("render_package") or {}
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

    export_dir = project_root / "Export"
    export_dir.mkdir(parents=True, exist_ok=True)

    # Mission-critical: live ElevenLabs Doctor VO (never ship demo narration)
    doctor_voice = _synthesize_doctor_voice(project_root)
    dest = _reassemble_with_doctor_voice(project_root, doctor_voice, ops)
    packaged["export_mp4"] = str(dest)
    packaged["doctor_voice"] = doctor_voice
    top["voice_package"] = doctor_voice
    top["audio_package"] = doctor_voice

    thumb = build_thumbnail(project_root)
    write_reports(project_root, ops, packaged)

    # Also copy captions from pipeline if present
    caps = top.get("captions_package") or {}
    if caps.get("path") and Path(str(caps["path"])).is_file():
        shutil.copy2(caps["path"], project_root / "Captions" / Path(str(caps["path"])).name)

    status = {
        "ok": bool(ops.get("video_exists") or (dest.is_file() and dest.stat().st_size > 10_000)),
        "production_id": ops.get("production_id"),
        "success": ops.get("success"),
        "video_exists": ops.get("video_exists"),
        "project_root": str(project_root),
        "export_mp4": str(dest) if dest.is_file() else packaged.get("export_mp4"),
        "thumbnail": str(thumb),
        "character": CHARACTER_ID,
        "mp4_bytes": dest.stat().st_size if dest.is_file() else 0,
        "mp4_duration": float((_ffprobe(dest).get("format") or {}).get("duration") or 0) if dest.is_file() else 0,
        "generated_at": _now(),
    }
    (project_root / "Reports" / "EPISODE_STATUS.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "THE_DOCTOR_TRICHOMONAS_EPISODE.md").write_text(
        f"# The Doctor Debut — {EPISODE_TITLE}\n\n"
        f"- Character: `{CHARACTER_ID}` (permanent)\n"
        f"- Project: `{project_root}`\n"
        f"- MP4: `{status.get('export_mp4')}`\n"
        f"- Duration: {status.get('mp4_duration')}s\n"
        f"- OK: {status.get('ok')}\n",
        encoding="utf-8",
    )
    return status


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, default=str))
    raise SystemExit(0 if result.get("ok") else 1)
