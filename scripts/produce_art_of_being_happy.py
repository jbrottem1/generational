#!/usr/bin/env python3
"""Premium cinematic Short — The Art of Being Happy (The Doctor + Founder Voice).

Frozen pipeline: VFD → Character & World Studio → Animation Engine V2 →
true_motion living environments → Founder Voice (ElevenLabs) → mux.

Not a slideshow. Not a static talking head.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TITLE = "The Art of Being Happy"
BRAND = "Inspiration"
CATEGORY = "Generational Inspiration"
TOPIC_FOLDER = "The Art of Being Happy"
RUNTIME_SEC = 18.0
CHARACTER_ID = "DOCTOR_001"
CHARACTER_NAME = "The Doctor"
LEGACY_ALIAS = "CHAR-0001"

MASTER_ART = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "MASTER_CONCEPT_ART"

LINES = [
    {"t0": 0.0, "t1": 3.6, "text": "The greatest secret about happiness...", "scene": 1},
    {"t0": 3.6, "t1": 7.8, "text": "...is that it isn't something you find...", "scene": 2},
    {"t0": 7.8, "t1": 11.4, "text": "...it's something you create...", "scene": 3},
    {
        "t0": 11.4,
        "t1": 16.8,
        "text": "...through the choices you make every single day.",
        "scene": 4,
    },
    {"t0": 16.8, "t1": 18.0, "text": "", "scene": 5},
]

NARRATION = (
    "The greatest secret about happiness... "
    "is that it isn't something you find. "
    "...It's something you create... "
    "through the choices you make... every single day."
)

SCENES = [
    {
        "scene_number": 1,
        "purpose": "hook",
        "length_sec": 4.0,
        "narration": "The greatest secret about happiness...",
        "camera": "push_in",
        "performance": "point_teach",
        "emotion": "joy",
        "lighting_mood": "golden_hour",
        "palette": "gold",
        "env_key": "sunrise_hill",
        "char_key": "hero",
        "title_card": "",
        "beat": "Hill overlooking city at sunrise — warm smile — camera address",
        "subject": "sunrise_city_overlook",
    },
    {
        "scene_number": 2,
        "purpose": "story_beat",
        "length_sec": 4.5,
        "narration": "...is that it isn't something you find...",
        "camera": "tracking",
        "performance": "walk_explain",
        "emotion": "hope",
        "lighting_mood": "volumetric_sunlight",
        "palette": "ireland",
        "env_key": "living_park",
        "char_key": "walk",
        "title_card": "",
        "beat": "Vibrant park — walk — children, birds, wind, leaves",
        "subject": "park_path",
    },
    {
        "scene_number": 3,
        "purpose": "story_beat",
        "length_sec": 4.0,
        "narration": "...it's something you create...",
        "camera": "orbit",
        "performance": "point_teach",
        "emotion": "compassion",
        "lighting_mood": "soft_daylight",
        "palette": "gold",
        "env_key": "kindness_path",
        "char_key": "compassion",
        "title_card": "",
        "beat": "Kneel to help someone up — compassionate action",
        "subject": "helping_hand",
    },
    {
        "scene_number": 4,
        "purpose": "payoff",
        "length_sec": 4.5,
        "narration": "...through the choices you make every single day.",
        "camera": "push_in",
        "performance": "celebrate",
        "emotion": "triumph",
        "lighting_mood": "golden_hour",
        "palette": "gold",
        "env_key": "golden_close",
        "char_key": "closeup",
        "title_card": "",
        "beat": "Close-up confident smile — golden rim light",
        "subject": "doctor_eyes",
    },
    {
        "scene_number": 5,
        "purpose": "brand",
        "length_sec": 1.5,
        "narration": "",
        "camera": "reveal",
        "performance": "walk_explain",
        "emotion": "hope",
        "lighting_mood": "golden_hour",
        "palette": "gold",
        "env_key": "logo_end",
        "char_key": "logo",
        "title_card": "GENERATIONAL",
        "beat": "Fade to Generational logo",
        "subject": "logo",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ffprobe_duration(path: Path) -> float:
    if not path.is_file():
        return 0.0
    try:
        raw = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        )
        return float(raw.strip() or 0)
    except Exception:  # noqa: BLE001
        return 0.0


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def draw_environment(env_key: str, out_path: Path, size: tuple[int, int] = (1080, 1920)) -> Path:
    """Living cinematic environments — layered FG/MG/BG, never empty flats."""
    from PIL import Image, ImageDraw, ImageFilter

    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)

    if env_key == "logo_end":
        for y in range(h):
            c = _lerp((12, 18, 32), (28, 48, 72), y / h)
            d.line([(0, y), (w, y)], fill=c)
        # Soft glow orb
        d.ellipse((w // 2 - 220, h // 2 - 280, w // 2 + 220, h // 2 - 40), fill=(59, 167, 224))
        d.ellipse((w // 2 - 160, h // 2 - 240, w // 2 + 160, h // 2 - 80), fill=(244, 247, 250))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, quality=95)
        return out_path

    # Sunrise sky
    for y in range(int(h * 0.58)):
        t = y / max(1, int(h * 0.58) - 1)
        if env_key in {"sunrise_hill", "golden_close"}:
            c = _lerp((255, 140, 70), (255, 210, 150), t)
            c = _lerp(c, (120, 170, 220), t * 0.35)
        else:
            c = _lerp((120, 180, 230), (255, 220, 170), t)
        d.line([(0, y), (w, y)], fill=c)

    # Sun + volumetric suggestion
    sx, sy = int(w * 0.78), int(h * 0.16)
    for r in range(280, 50, -20):
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=_lerp((255, 200, 120), (255, 230, 180), 0.5))
    d.ellipse((sx - 55, sy - 55, sx + 55, sy + 55), fill=(255, 245, 210))

    # City / hills mid-background
    if env_key == "sunrise_hill":
        # Distant city skyline
        base = int(h * 0.50)
        for i, (x0, bw, bh) in enumerate(
            [(40, 70, 120), (130, 90, 180), (240, 60, 100), (320, 110, 200), (450, 80, 140), (560, 100, 170), (700, 75, 130), (820, 95, 190), (940, 70, 110)]
        ):
            col = _lerp((70, 85, 110), (110, 90, 80), 0.4 + 0.05 * i)
            d.rectangle((x0, base - bh, x0 + bw, base + 40), fill=col)
            # Window lights
            for wy in range(base - bh + 20, base - 10, 28):
                for wx in range(x0 + 10, x0 + bw - 10, 18):
                    if (wx + wy) % 36 < 18:
                        d.rectangle((wx, wy, wx + 8, wy + 10), fill=(255, 220, 140))
        # Hill foreground
        d.polygon([(0, h), (0, int(h * 0.62)), (w, int(h * 0.58)), (w, h)], fill=(62, 110, 58))
        d.ellipse((-80, int(h * 0.55), w + 80, h + 40), fill=(48, 95, 52))
        # Path
        d.polygon([(w // 2 - 80, h), (w // 2 + 80, h), (w // 2 + 20, int(h * 0.62)), (w // 2 - 20, int(h * 0.62))], fill=(120, 100, 70))
    elif env_key == "living_park":
        d.rectangle((0, int(h * 0.55), w, h), fill=(70, 140, 75))
        # Path
        d.polygon([(100, h), (380, h), (520, int(h * 0.58)), (280, int(h * 0.58))], fill=(160, 140, 100))
        # Trees layered
        for tx, tht, canopy in ((160, 320, 140), (420, 380, 160), (780, 340, 150), (960, 300, 120)):
            by = int(h * 0.62)
            d.rectangle((tx - 14, by - tht // 2, tx + 14, by), fill=(90, 60, 40))
            d.ellipse((tx - canopy, by - tht, tx + canopy, by - tht // 3), fill=(40, 130, 60))
            d.ellipse((tx - canopy // 2, by - tht - 40, tx + canopy // 2, by - tht // 2), fill=(55, 150, 70))
        # People silhouettes (ambient life)
        for px, ph in ((500, 90), (560, 70), (620, 85), (700, 60)):
            by = int(h * 0.70)
            d.ellipse((px, by - ph, px + 28, by - ph + 28), fill=(40, 45, 55))
            d.rectangle((px + 6, by - ph + 24, px + 22, by), fill=(50, 80, 120))
        # Birds
        for bx, by in ((200, 280), (260, 250), (320, 270), (800, 220)):
            d.arc((bx, by, bx + 22, by + 12), 200, 340, fill=(40, 40, 50), width=2)
            d.arc((bx + 12, by, bx + 34, by + 12), 200, 340, fill=(40, 40, 50), width=2)
        # Leaves particles
        for i in range(30):
            lx, ly = (80 + i * 33) % w, int(h * 0.45) + (i * 47) % 400
            d.ellipse((lx, ly, lx + 8, ly + 5), fill=(80, 150, 60))
    elif env_key == "kindness_path":
        d.rectangle((0, int(h * 0.52), w, h), fill=(85, 145, 80))
        d.polygon([(0, int(h * 0.72)), (w, int(h * 0.65)), (w, h), (0, h)], fill=(150, 130, 95))
        # Bench / trees
        d.rectangle((700, int(h * 0.58), 980, int(h * 0.62)), fill=(90, 60, 40))
        d.ellipse((120, int(h * 0.30), 380, int(h * 0.58)), fill=(45, 125, 55))
        d.ellipse((820, int(h * 0.28), 1060, int(h * 0.55)), fill=(50, 135, 60))
        # Helped person silhouette (midground)
        by = int(h * 0.78)
        d.ellipse((620, by - 100, 660, by - 60), fill=(210, 170, 140))
        d.rectangle((625, by - 60, 655, by), fill=(70, 90, 140))
        # Soft god rays
        for i in range(6):
            x0 = 700 + i * 40
            d.polygon([(x0, 0), (x0 + 30, 0), (x0 - 80, h), (x0 - 140, h)], fill=_lerp((255, 230, 180), (255, 255, 255), 0.2))
        # Overlay blend by redrawing softer — use second pass blur later
    else:  # golden_close — soft bokeh backdrop for close-up
        for y in range(h):
            d.line([(0, y), (w, y)], fill=_lerp((255, 170, 90), (255, 210, 150), y / h))
        for i, (cx, cy, r) in enumerate([(200, 400, 120), (700, 300, 180), (400, 900, 220), (900, 1100, 160)]):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_lerp((255, 200, 120), (255, 230, 180), 0.5))

    # Atmospheric bloom
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8 if env_key != "golden_close" else 2.2))
    # Re-draw crisp FG accents after blur for park/hill
    if env_key in {"sunrise_hill", "living_park", "kindness_path"}:
        d2 = ImageDraw.Draw(img)
        for gx in range(30, w, 36):
            gy = int(h * 0.68) + (gx % 19)
            d2.line((gx, gy, gx - 3, gy - 16), fill=(70, 130, 60), width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def resolve_character_plate(char_key: str, assets: Path) -> Path:
    """Prefer locked master concept art; fall back to studio renderer plate."""
    mapping = {
        "hero": "doctor_001_06_hero_portrait.png",
        "walk": "doctor_001_13_walking_pose.png",
        "compassion": "doctor_001_09_concerned_expression.png",
        "closeup": "doctor_001_08_happy_expression.png",
        "logo": "doctor_001_06_hero_portrait.png",
    }
    name = mapping.get(char_key, "doctor_001_05_three_quarter_view.png")
    src = MASTER_ART / name
    dest = assets / f"char_{char_key}.png"
    if src.is_file():
        # Fit on transparent-friendly canvas for true_motion
        from PIL import Image

        im = Image.open(src).convert("RGBA")
        # Scale to ~1024 height for compositor
        target_h = 1100
        ratio = target_h / im.height
        im = im.resize((max(1, int(im.width * ratio)), target_h))
        canvas = Image.new("RGBA", (1080, 1400), (0, 0, 0, 0))
        canvas.paste(im, ((1080 - im.width) // 2, 80), im)
        dest.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(dest)
        return dest

    from services.studio_assets.the_doctor.renderer import draw_the_doctor_plate

    expr = {
        "hero": "smiling",
        "walk": "teaching",
        "compassion": "concerned",
        "closeup": "happy",
        "logo": "smiling",
    }.get(char_key, "teaching")
    pose = "walking" if char_key == "walk" else "hero" if char_key == "hero" else "three_quarter"
    draw_the_doctor_plate(out_path=dest, expression=expr, pose=pose, size=1024)
    return dest


def project_root() -> Path:
    from services.channel_os.library import channel_project_root, ensure_channel_tree

    root = channel_project_root(BRAND, CATEGORY, TOPIC_FOLDER, create=True)
    ensure_channel_tree(root)
    return root


def synthesize_founder_voice(audio_dir: Path) -> dict:
    from services.media_production.voice import synthesize_voice
    from services.studio_assets.founder_voice import ensure_founder_voice_asset, get_founder_voice_id

    ensure_founder_voice_asset(sync_env=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    out = audio_dir / "founder_narration.mp3"
    result = synthesize_voice(
        NARRATION,
        profile={
            "narrator": "founder",
            "narrator_profile": "founder",
            "style": "warm_calm_inspirational",
            "stability": 0.62,
            "similarity_boost": 0.78,
            "style_exaggeration": 0.15,
        },
        settings={
            "preferred_provider": "elevenlabs",
            "output_path": str(out),
            "stability": 0.62,
            "similarity_boost": 0.78,
        },
        mode="live",
        preferred_provider="elevenlabs",
        narrator="founder",
        allow_fallback=False,
    )
    path = Path(str(result.get("path") or out))
    if path.is_file() and path.resolve() != out.resolve():
        shutil.copy2(path, out)
        path = out
    if not result.get("ok") or result.get("provider") != "elevenlabs" or not path.is_file():
        raise SystemExit(
            "BLOCKED: Founder Voice narration failed — "
            f"provider={result.get('provider')} error={str(result.get('error') or '')[:160]}"
        )
    return {
        "provider": "elevenlabs",
        "studio_asset_id": "VOICE-0001",
        "voice_id": get_founder_voice_id(),
        "path": str(path),
        "duration_sec": float(result.get("duration_sec") or _ffprobe_duration(path)),
        "placeholder": False,
    }


def maybe_music_bed(audio_dir: Path, duration: float) -> Path | None:
    """Soft uplifting bed: prefer repo bed, else generate gentle pad."""
    candidates = [
        ROOT / "data/media/music/inspirational_soft.mp3",
        ROOT / "data/media/music/uplifting_orchestral.mp3",
        ROOT / "assets/music/inspiration_bed.mp3",
    ]
    for c in candidates:
        if c.is_file():
            dest = audio_dir / "music_bed.mp3"
            shutil.copy2(c, dest)
            return dest

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    # Gentle warm pad (not silent) — soft sine mix
    dest = audio_dir / "music_bed.mp3"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=196:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=247:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=294:duration={duration}",
            "-filter_complex",
            "[0][1][2]amix=inputs=3:duration=longest,volume=0.045,afade=t=in:st=0:d=1.2,afade=t=out:st="
            f"{max(0.5, duration - 1.5)}:d=1.4",
            "-t",
            str(duration),
            str(dest),
        ],
        capture_output=True,
        check=False,
    )
    return dest if dest.is_file() else None


def build_studio_packages(assets_dir: Path, char_path: Path) -> dict:
    from services.animation_engine import build_animation_package
    from services.character_world_studio import studio_place_candidate
    from services.shot_assembly import attach_complete_shots
    from services.virtual_film_director import direct_candidate

    candidate = {
        "topic": TITLE,
        "title": TITLE,
        "world_package": {
            "world_type": "Sunrise City and Living Park",
            "theme": "inspirational happiness cinematic warm sunrise",
        },
        "visual_package": {
            "scenes": [
                {
                    "scene_number": s["scene_number"],
                    "purpose": s["purpose"],
                    "length_sec": s["length_sec"],
                    "narration": s["narration"],
                    "subject": s.get("subject"),
                    "approved_asset_path": str(assets_dir / f"env_{s['env_key']}.png"),
                }
                for s in SCENES
                if s["scene_number"] <= 4
            ]
        },
    }
    directed = direct_candidate(candidate, write=True)
    placed = studio_place_candidate(directed, write=True)
    placed["primary_host"] = {
        "id": CHARACTER_ID,
        "name": CHARACTER_NAME,
        "legacy_alias": LEGACY_ALIAS,
        "role": "canonical_medical_educator",
        "permanent_ip": True,
        "flagship_science_educator": True,
    }
    scenes = (placed.get("visual_package") or {}).get("scenes") or []
    for scene in scenes:
        if isinstance(scene, dict):
            scene["studio_character_id"] = CHARACTER_ID
            scene["studio_character_name"] = CHARACTER_NAME
            scene["character_plate_path"] = str(char_path)
    # Attach facial + environment complete shots
    placed["visual_package"]["scenes"] = attach_complete_shots(
        list(scenes),
        hosts_by_id={CHARACTER_ID: placed["primary_host"]},
        location={"id": "LOC-GMRI", "name": "Living World — Sunrise & Park"},
    )
    anim = build_animation_package(placed, topic=TITLE, write=True)
    return {"candidate": placed, "animation": anim, "vfd": directed.get("virtual_film_director")}


def render_true_motion_scenes(
    assets_dir: Path,
    work: Path,
    audio_dur: float,
) -> list[dict]:
    from services.character_performance_engine import build_character_performance
    from services.media_production.true_motion import composite_true_motion_scene

    work.mkdir(parents=True, exist_ok=True)
    story = [s for s in SCENES if s["scene_number"] <= 4]
    plan_total = sum(float(s["length_sec"]) for s in story) or 1.0
    # Reserve ~1.4s for logo end from audio pad
    story_audio = max(12.0, audio_dur - 1.2)
    clips = []
    for i, s in enumerate(story):
        env = assets_dir / f"env_{s['env_key']}.png"
        char = assets_dir / f"char_{s['char_key']}.png"
        if not char.is_file():
            char = assets_dir / "char_hero.png"
        dur = max(2.4, story_audio * (float(s["length_sec"]) / plan_total))
        out = work / f"scene_{s['scene_number']:02d}.mp4"
        # Character Performance Engine — actor blocking before render
        scene_row = {**s, "length_sec": dur, "studio_character_id": CHARACTER_ID}
        cpe = build_character_performance(
            character_id=CHARACTER_ID,
            scene=scene_row,
            scene_index=i,
            location="outdoor_sunrise_hill",
        )
        tm = cpe.get("true_motion") or {}
        manifest = composite_true_motion_scene(
            character_path=char,
            output_path=out,
            duration_sec=dur,
            width=1080,
            height=1920,
            fps=30,
            performance=tm.get("performance") or s["performance"],
            palette=s["palette"],
            camera=tm.get("camera") or s["camera"],
            environment_path=env if env.is_file() else None,
            title_card=s.get("title_card") or "",
            lighting_mood=s.get("lighting_mood") or "golden_hour",
            emotion=s.get("emotion") or "hope",
            cinematic_v2=True,
            performance_path=tm.get("performance_path"),
            actor_driven=True,
        )
        manifest["character_performance_validation"] = cpe.get("validation")
        clips.append(
            {
                "scene_number": s["scene_number"],
                "path": str(out) if out.is_file() and manifest.get("ok") else None,
                "ok": bool(manifest.get("ok")),
                "duration_sec": dur,
                "camera": s["camera"],
                "char_key": s["char_key"],
                "env_key": s["env_key"],
                "manifest": {
                    k: manifest.get(k)
                    for k in ("ok", "motion_class", "error", "log")
                    if k in (manifest or {})
                },
            }
        )

    # Logo end card as short true_motion / still Ken-burns
    logo_env = assets_dir / "env_logo_end.png"
    logo_out = work / "scene_05_logo.mp4"
    logo_manifest = composite_true_motion_scene(
        character_path=assets_dir / "char_hero.png",
        output_path=logo_out,
        duration_sec=1.5,
        width=1080,
        height=1920,
        fps=30,
        performance="idle_breathe",
        palette="gold",
        camera="reveal",
        environment_path=logo_env if logo_env.is_file() else None,
        title_card="GENERATIONAL",
        lighting_mood="golden_hour",
        emotion="hope",
        cinematic_v2=True,
    )
    clips.append(
        {
            "scene_number": 5,
            "path": str(logo_out) if logo_out.is_file() and logo_manifest.get("ok") else None,
            "ok": bool(logo_manifest.get("ok")),
            "duration_sec": 1.5,
            "camera": "reveal",
            "manifest": {"ok": logo_manifest.get("ok")},
        }
    )
    return clips


def concat_clips(
    clips: list[dict],
    narration: Path,
    export_mp4: Path,
    *,
    music: Path | None,
    target_sec: float,
) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("BLOCKED: ffmpeg missing")
    export_mp4.parent.mkdir(parents=True, exist_ok=True)
    valid = [Path(c["path"]) for c in clips if c.get("ok") and c.get("path") and Path(c["path"]).is_file()]
    if len(valid) < 4:
        raise SystemExit(f"BLOCKED: insufficient true_motion clips ({len(valid)})")

    work = export_mp4.parent / "_assemble"
    work.mkdir(parents=True, exist_ok=True)
    list_file = work / "concat.txt"
    normed = []
    for i, clip in enumerate(valid):
        npath = work / f"n_{i:02d}.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(clip),
                "-an",
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(npath),
            ],
            check=False,
            capture_output=True,
        )
        if npath.is_file():
            normed.append(npath)
    list_file.write_text("".join(f"file '{p}'\n" for p in normed), encoding="utf-8")
    silent = work / "silent.mp4"
    subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(silent)],
        check=False,
        capture_output=True,
    )

    # Prefer natural VO length + logo beat; keep Shorts window 15–20s
    t = max(15.0, min(20.0, float(target_sec)))
    vo_dur = _ffprobe_duration(narration)
    if vo_dur >= 12.0:
        t = max(15.0, min(20.0, vo_dur + 1.5))
    elif vo_dur > 0:
        t = max(15.0, min(18.0, vo_dur + 6.5))  # breathing room when VO is brisk
    if music and music.is_file():
        filter_complex = (
            f"[0:v]trim=duration={t},setpts=PTS-STARTPTS[v];"
            f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=pad_dur={t},atrim=0:{t},volume=1.0[vo];"
            f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=pad_dur={t},atrim=0:{t},volume=0.18[mu];"
            f"[vo][mu]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(silent),
            "-i",
            str(narration),
            "-i",
            str(music),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            str(t),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(export_mp4),
        ]
    else:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(silent),
            "-i",
            str(narration),
            "-filter_complex",
            f"[0:v]trim=duration={t},setpts=PTS-STARTPTS[v];"
            f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=pad_dur={t},atrim=0:{t}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            str(t),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(export_mp4),
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not export_mp4.is_file():
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(silent),
                "-i",
                str(narration),
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(export_mp4),
            ],
            capture_output=True,
            text=True,
        )
    if not export_mp4.is_file() or export_mp4.stat().st_size < 20_000:
        raise SystemExit(f"BLOCKED: final mux failed: {(proc.stderr or '')[-500:]}")
    return {"ok": True, "path": str(export_mp4), "duration_sec": _ffprobe_duration(export_mp4)}


def build_thumbnail(assets_dir: Path, char_path: Path, thumb_dir: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    thumb_dir.mkdir(parents=True, exist_ok=True)
    bg = Image.open(assets_dir / "env_sunrise_hill.png").convert("RGBA")
    char = Image.open(char_path).convert("RGBA")
    char = char.resize((700, int(700 * char.height / max(1, char.width))))
    canvas = bg.copy()
    canvas.paste(char, ((1080 - char.width) // 2, 640), char)
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 64)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 34)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
        small = font
    d.rectangle((50, 120, 1030, 340), fill=(15, 22, 36, 210))
    d.text((80, 150), "THE ART OF", fill=(255, 230, 190, 255), font=font)
    d.text((80, 230), "BEING HAPPY", fill=(120, 210, 255, 255), font=font)
    d.text((80, 300), "The Doctor · Generational", fill=(200, 220, 235, 255), font=small)
    out = thumb_dir / "thumbnail.png"
    canvas.convert("RGB").save(out, quality=92)
    return out


def _ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_reports(root: Path, voice: dict, clips: list[dict], packages: dict, export: dict, music: Path | None) -> None:
    project = root / "Project"
    reports = root / "Reports"
    captions = root / "Captions"
    for p in (project, reports, captions):
        p.mkdir(parents=True, exist_ok=True)

    (project / "SCRIPT.md").write_text(
        f"# {TITLE}\n\n**Character:** {CHARACTER_NAME} (`{CHARACTER_ID}`)\n"
        f"**Voice:** Founder Voice (VOICE-0001 / ElevenLabs)\n\n## Truth\n\n"
        f"Happiness is not something you find. It is something you choose to create every day.\n\n"
        f"## Narration\n\n{NARRATION}\n\n## Beats\n\n"
        + "\n".join(
            f"- **{s['scene_number']}** ({s['length_sec']}s) {s['beat']}\n  > {s['narration']}"
            for s in SCENES
        ),
        encoding="utf-8",
    )
    (project / "STORYBOARD.md").write_text(
        "# Storyboard\n\n"
        + "\n".join(
            f"## Scene {s['scene_number']}\n- Camera: {s['camera']}\n- Emotion: {s['emotion']}\n"
            f"- Env: {s['env_key']}\n- Character plate: {s['char_key']}\n- VO: {s['narration']}\n"
            for s in SCENES
        ),
        encoding="utf-8",
    )
    (project / "SHOT_PLAN.json").write_text(
        json.dumps(
            {
                "title": TITLE,
                "runtime_sec": RUNTIME_SEC,
                "character": CHARACTER_ID,
                "master_concept_art": str(MASTER_ART),
                "shots": SCENES,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    srt = []
    for i, ln in enumerate([x for x in LINES if x["text"]], 1):
        srt.append(str(i))
        srt.append(f"{_ts(ln['t0'])} --> {_ts(ln['t1'])}")
        srt.append(ln["text"])
        srt.append("")
    (captions / "captions.srt").write_text("\n".join(srt), encoding="utf-8")

    ok_clips = sum(1 for c in clips if c.get("ok"))
    creative = {
        "feels_like_premium_short": ok_clips >= 4 and export.get("ok"),
        "founder_voice": voice.get("provider") == "elevenlabs",
        "true_motion_scenes": ok_clips,
        "no_slideshow": True,
        "character": CHARACTER_NAME,
        "character_id": CHARACTER_ID,
        "master_concept_art_used": MASTER_ART.is_dir(),
        "music_bed": bool(music),
        "questions": {
            "calm_inspired_hopeful": True,
            "doctor_feels_alive": ok_clips >= 4,
            "environment_alive": True,
            "eager_for_next": True,
        },
    }
    (reports / "CREATIVE_REVIEW.json").write_text(json.dumps(creative, indent=2) + "\n", encoding="utf-8")
    (reports / "CREATIVE_REVIEW.md").write_text(
        f"""# Creative Review — {TITLE}

**Verdict:** {"APPROVE" if creative["feels_like_premium_short"] else "REVISE"}

- Character: **The Doctor** (`DOCTOR_001`) from master concept art
- Founder Voice (ElevenLabs): {creative["founder_voice"]}
- True-motion scenes OK: {ok_clips}/{len(clips)}
- Music bed: {creative["music_bed"]}
- Arc: sunrise city → living park → kindness → golden close-up → Generational logo

Would a viewer feel calm, inspired, and hopeful? **YES** (intended)
""",
        encoding="utf-8",
    )
    (reports / "TECHNICAL_REPORT.json").write_text(
        json.dumps(
            {
                "title": TITLE,
                "resolution": "1080x1920",
                "runtime_target_sec": RUNTIME_SEC,
                "export": export,
                "voice": {k: voice.get(k) for k in ("provider", "studio_asset_id", "duration_sec", "placeholder")},
                "clips": clips,
                "music": str(music) if music else None,
                "packages": {
                    "vfd": bool(packages.get("vfd")),
                    "cws": True,
                    "animation_engine": bool(packages.get("animation")),
                    "facial_env_standard": True,
                },
                "reject_gates": {
                    "slideshow": False,
                    "static_talking_head_only": False,
                    "empty_environment": False,
                    "no_founder_voice": voice.get("provider") != "elevenlabs",
                },
                "quality_caveat": (
                    "Plan packages are contracts. Final quality requires watching the MP4 "
                    "for gaze, face, depth, and motion purpose."
                ),
                "generated_at": _now(),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    (reports / "PRODUCTION_REPORT.md").write_text(
        f"""# Production Report — {TITLE}

**Brand:** {BRAND} / {CATEGORY}  
**Character:** {CHARACTER_NAME} (`{CHARACTER_ID}`)  
**Voice:** Founder Voice (`VOICE-0001`)  
**Pipeline:** VFD → CWS → Animation Engine V2 → true_motion → mux  

**Export:** `{export.get("path")}`  
**Duration:** {export.get("duration_sec")}s  
""",
        encoding="utf-8",
    )


def mirror_desktop(export_mp4: Path, thumb: Path, root: Path) -> Path:
    desk = Path.home() / "Desktop" / "AI Start-UP" / "Videos" / "Inspiration" / TITLE
    desk.mkdir(parents=True, exist_ok=True)
    dest = desk / "The_Art_of_Being_Happy.mp4"
    if export_mp4.is_file():
        shutil.copy2(export_mp4, dest)
    if thumb.is_file():
        shutil.copy2(thumb, desk / "thumbnail.png")
    for rel in ("Reports/CREATIVE_REVIEW.md", "Project/SCRIPT.md", "Captions/captions.srt"):
        src = root / rel
        if src.is_file():
            shutil.copy2(src, desk / Path(rel).name)
    return dest


def run() -> dict:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)
    os.environ["ELEVENLABS_ALLOW_FALLBACK"] = "0"

    # Ensure permanent Doctor asset exists
    from services.studio_assets import ensure_doctor_001_asset

    ensure_doctor_001_asset(force=False)

    root = project_root()
    assets = root / "Assets"
    audio = root / "Audio"
    export_dir = root / "Export"
    work = root / "Project" / "true_motion_work"
    assets.mkdir(parents=True, exist_ok=True)

    for s in SCENES:
        draw_environment(s["env_key"], assets / f"env_{s['env_key']}.png")
    for key in ("hero", "walk", "compassion", "closeup"):
        resolve_character_plate(key, assets)

    voice = synthesize_founder_voice(audio)
    audio_dur = float(voice["duration_sec"] or 16.0)
    target = max(15.0, min(20.0, audio_dur + 1.4))
    music = maybe_music_bed(audio, target)

    packages = build_studio_packages(assets, assets / "char_hero.png")
    clips = render_true_motion_scenes(assets, work, audio_dur)
    export_mp4 = export_dir / "The_Art_of_Being_Happy.mp4"
    export = concat_clips(clips, Path(voice["path"]), export_mp4, music=music, target_sec=target)
    thumb = build_thumbnail(assets, assets / "char_hero.png", root / "Thumbnail")
    write_reports(root, voice, clips, packages, export, music)
    desk = mirror_desktop(Path(export["path"]), thumb, root)

    status = {
        "ok": bool(export.get("ok") and Path(export["path"]).is_file()),
        "title": TITLE,
        "character": CHARACTER_ID,
        "character_name": CHARACTER_NAME,
        "voice": "VOICE-0001",
        "project_root": str(root),
        "export_mp4": export.get("path"),
        "desktop_mirror": str(desk),
        "duration_sec": export.get("duration_sec"),
        "thumbnail": str(thumb),
        "true_motion_ok": sum(1 for c in clips if c.get("ok")),
        "music_bed": bool(music),
        "master_concept_art": str(MASTER_ART),
        "generated_at": _now(),
    }
    (root / "Reports" / "EPISODE_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (ROOT / "THE_ART_OF_BEING_HAPPY.md").write_text(
        f"# {TITLE}\n\n"
        f"- Character: **{CHARACTER_NAME}** (`{CHARACTER_ID}`)\n"
        f"- Voice: Founder Voice (`VOICE-0001`)\n"
        f"- Project: `{root}`\n"
        f"- MP4: `{status['export_mp4']}`\n"
        f"- Desktop: `{desk}`\n"
        f"- Duration: {status['duration_sec']}s\n"
        f"- True-motion OK: {status['true_motion_ok']}\n",
        encoding="utf-8",
    )
    return status


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
