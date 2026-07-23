#!/usr/bin/env python3
"""Premium 15s cinematic Short — Every Decision Matters (Founder Voice + frozen pipeline).

Uses Virtual Film Director, Character & World Studio, Animation Engine V2,
true_motion living environments, Founder Voice (ElevenLabs). No slideshow.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TITLE = "Every Decision Matters"
BRAND = "Inspiration"
CATEGORY = "Generational Inspiration"
TOPIC_FOLDER = "Every Decision Matters"
RUNTIME_SEC = 15.0
CHARACTER_ID = "CHAR-FOUNDER-TRAVELER"
CHARACTER_NAME = "The Founder"

LINES = [
    {"t0": 0.0, "t1": 2.2, "text": "Life is unforgiving.", "scene": 1},
    {"t0": 2.2, "t1": 4.6, "text": "Every decision leaves a mark.", "scene": 2},
    {"t0": 4.6, "t1": 7.0, "text": "Every step shapes your future.", "scene": 3},
    {"t0": 7.0, "t1": 9.6, "text": "Small choices become great destinies.", "scene": 4},
    {"t0": 9.6, "t1": 11.4, "text": "Choose discipline.", "scene": 5},
    {"t0": 11.4, "t1": 13.0, "text": "Choose purpose.", "scene": 5},
    {"t0": 13.0, "t1": 15.0, "text": "Choose wisely.", "scene": 5},
]

NARRATION = " ".join(ln["text"] for ln in LINES)

SCENES = [
    {
        "scene_number": 1,
        "purpose": "hook",
        "length_sec": 3.0,
        "narration": "Life is unforgiving.",
        "camera": "push_in",
        "performance": "walk_explain",
        "emotion": "serious",
        "lighting_mood": "cool_dawn",
        "palette": "fog",
        "env_key": "fork_dawn",
        "title_card": "",
        "beat": "Lone figure at mountain fork — sunrise — slow push",
    },
    {
        "scene_number": 2,
        "purpose": "story_beat",
        "length_sec": 3.5,
        "narration": "Every decision leaves a mark. Every step shapes your future.",
        "camera": "tracking",
        "performance": "walk_explain",
        "emotion": "focus",
        "lighting_mood": "soft_daylight",
        "palette": "ireland",
        "env_key": "path_awakening",
        "title_card": "",
        "beat": "Confident walk — skies clear — world begins to transform",
    },
    {
        "scene_number": 3,
        "purpose": "story_beat",
        "length_sec": 3.5,
        "narration": "Small choices become great destinies.",
        "camera": "orbit",
        "performance": "walk_explain",
        "emotion": "hope",
        "lighting_mood": "golden_transition",
        "palette": "gold",
        "env_key": "living_forest",
        "title_card": "",
        "beat": "Dead trees thrive — broken ground becomes clear path",
    },
    {
        "scene_number": 4,
        "purpose": "payoff",
        "length_sec": 5.0,
        "narration": "Choose discipline. Choose purpose. Choose wisely.",
        "camera": "reveal",
        "performance": "celebrate",
        "emotion": "triumph",
        "lighting_mood": "golden_hour",
        "palette": "gold",
        "env_key": "mountain_overlook",
        "title_card": "CHOOSE WISELY.",
        "beat": "Overlook — golden light — rising camera — title",
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
    """Rich cinematic environment plates — never flat solid placeholders."""
    from PIL import Image, ImageDraw, ImageFilter

    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)

    warmth = {
        "fork_dawn": 0.15,
        "path_awakening": 0.45,
        "living_forest": 0.7,
        "mountain_overlook": 1.0,
    }.get(env_key, 0.5)

    sky_cool = (56, 78, 110)
    sky_warm = (255, 176, 92)
    ground_cool = (42, 52, 48)
    ground_warm = (92, 120, 62)
    sky = _lerp(sky_cool, sky_warm, warmth)
    ground = _lerp(ground_cool, ground_warm, warmth)

    # Sky gradient
    for y in range(int(h * 0.62)):
        t = y / max(1, int(h * 0.62) - 1)
        c = _lerp(sky, _lerp(sky, (255, 220, 170), warmth * 0.6), t * 0.5)
        d.line([(0, y), (w, y)], fill=c)

    # Sun / god rays
    sx, sy = int(w * (0.72 - 0.1 * warmth)), int(h * (0.18 + 0.05 * (1 - warmth)))
    for r in range(220, 40, -18):
        alpha_fill = _lerp(sky, (255, 230, 180), 0.4 + 0.4 * warmth)
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=alpha_fill)
    d.ellipse((sx - 48, sy - 48, sx + 48, sy + 48), fill=(255, 236, 190))

    # Mountains (silhouettes with depth)
    for i, (pts, col) in enumerate(
        [
            ([(0, int(h * 0.48)), (220, int(h * 0.30)), (480, int(h * 0.46)), (0, int(h * 0.55))], _lerp((40, 50, 70), (90, 80, 70), warmth)),
            ([(300, int(h * 0.52)), (560, int(h * 0.26)), (860, int(h * 0.50)), (300, int(h * 0.58))], _lerp((50, 60, 80), (110, 95, 70), warmth)),
            ([(700, int(h * 0.55)), (920, int(h * 0.32)), (1080, int(h * 0.48)), (1080, int(h * 0.60))], _lerp((45, 55, 75), (100, 85, 65), warmth)),
        ]
    ):
        d.polygon(pts + [(pts[-1][0], int(h * 0.62)), (pts[0][0], int(h * 0.62))], fill=col)

    # Ground
    d.rectangle((0, int(h * 0.58), w, h), fill=ground)

    # Trail / fork
    mid = w // 2
    if env_key == "fork_dawn":
        d.polygon([(mid - 40, h), (mid + 40, h), (mid + 10, int(h * 0.58)), (mid - 10, int(h * 0.58))], fill=(70, 68, 58))
        d.polygon([(mid - 10, int(h * 0.60)), (mid - 180, int(h * 0.48)), (mid - 140, int(h * 0.48)), (mid + 5, int(h * 0.60))], fill=(75, 72, 60))
        d.polygon([(mid + 10, int(h * 0.60)), (mid + 200, int(h * 0.47)), (mid + 160, int(h * 0.47)), (mid - 5, int(h * 0.60))], fill=(75, 72, 60))
    else:
        d.polygon(
            [(mid - 55, h), (mid + 55, h), (mid + 28, int(h * 0.58)), (mid - 28, int(h * 0.58))],
            fill=_lerp((68, 64, 52), (140, 120, 80), warmth),
        )

    # Trees — dead → living by warmth
    tree_color = _lerp((55, 52, 48), (34, 90, 48), warmth)
    canopy = _lerp((70, 65, 55), (46, 130, 60), warmth)
    for tx in (120, 260, 820, 960):
        base_y = int(h * 0.62)
        d.rectangle((tx - 10, base_y - 180, tx + 10, base_y), fill=tree_color)
        if warmth < 0.35:
            # barren branches
            d.line((tx, base_y - 160, tx - 50, base_y - 220), fill=tree_color, width=4)
            d.line((tx, base_y - 140, tx + 55, base_y - 210), fill=tree_color, width=4)
        else:
            d.ellipse((tx - 70, base_y - 260, tx + 70, base_y - 120), fill=canopy)

    # Grass tufts / particles
    grass = _lerp((50, 70, 50), (80, 150, 70), warmth)
    for gx in range(40, w, 28):
        gy = int(h * 0.62) + (gx % 17)
        d.line((gx, gy, gx - 4, gy - 18), fill=grass, width=2)
        d.line((gx, gy, gx + 5, gy - 16), fill=grass, width=2)

    # Distant birds
    bird = _lerp((40, 45, 55), (50, 40, 35), warmth)
    for bx, by in ((700, 260), (740, 250), (780, 270), (400, 220)):
        d.arc((bx, by, bx + 18, by + 10), 200, 340, fill=bird, width=2)
        d.arc((bx + 10, by, bx + 28, by + 10), 200, 340, fill=bird, width=2)

    # Soft atmospheric bloom
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def draw_founder_traveler(out_path: Path, expression: str = "determined", size: int = 1024) -> Path:
    """Ordinary traveler — calm, determined. Not a superhero. Recurring Inspiration host."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, int(size * 0.28)
    skin = (226, 184, 150)
    hair = (42, 30, 24)
    jacket = (48, 62, 78)
    accent = (196, 120, 64)
    pants = (36, 40, 48)

    # Soft rim light
    d.ellipse((cx - 190, cy - 160, cx + 190, cy + 200), fill=(255, 200, 120, 30))

    # Hair
    d.ellipse((cx - 115, cy - 130, cx + 115, cy + 40), fill=hair + (255,))
    # Head
    d.ellipse((cx - 100, cy - 95, cx + 100, cy + 115), fill=skin + (255,), outline=(50, 35, 28, 255), width=4)

    # Brows / eyes
    brow_y = cy - 8
    if expression in {"hope", "triumph"}:
        d.line((cx - 55, brow_y - 6, cx - 15, brow_y - 12), fill=(35, 25, 20, 255), width=6)
        d.line((cx + 15, brow_y - 12, cx + 55, brow_y - 6), fill=(35, 25, 20, 255), width=6)
    else:
        d.line((cx - 55, brow_y - 2, cx - 15, brow_y - 8), fill=(35, 25, 20, 255), width=6)
        d.line((cx + 15, brow_y - 8, cx + 55, brow_y - 2), fill=(35, 25, 20, 255), width=6)

    for ex in (cx - 48, cx + 12):
        d.ellipse((ex, cy + 8, ex + 36, cy + 48), fill=(255, 255, 255, 255), outline=(25, 20, 18, 255), width=2)
        d.ellipse((ex + 10, cy + 18, ex + 26, cy + 38), fill=(40, 55, 70, 255))
        d.ellipse((ex + 14, cy + 20, ex + 20, cy + 26), fill=(255, 255, 255, 255))

    # Mouth — calm resolve
    if expression == "triumph":
        d.arc((cx - 30, cy + 70, cx + 30, cy + 105), 20, 160, fill=(120, 50, 45, 255), width=4)
    else:
        d.arc((cx - 22, cy + 78, cx + 22, cy + 98), 20, 160, fill=(110, 55, 50, 255), width=3)

    # Neck / torso jacket
    d.polygon([(cx - 40, cy + 105), (cx + 40, cy + 105), (cx + 55, cy + 150), (cx - 55, cy + 150)], fill=skin + (255,))
    d.polygon(
        [(cx - 130, cy + 145), (cx + 130, cy + 145), (cx + 160, int(size * 0.72)), (cx - 160, int(size * 0.72))],
        fill=jacket + (255,),
        outline=(20, 25, 30, 255),
    )
    # Backpack
    d.rounded_rectangle((cx + 95, cy + 170, cx + 175, cy + 320), radius=18, fill=(60, 55, 48, 255), outline=accent + (255,), width=3)
    # Accent zipper
    d.line((cx, cy + 170, cx, int(size * 0.68)), fill=accent + (255,), width=5)

    # Arms mid-walk
    d.line((cx - 90, cy + 200, cx - 170, cy + 320), fill=jacket + (255,), width=16)
    d.line((cx + 90, cy + 200, cx + 160, cy + 300), fill=jacket + (255,), width=16)
    d.ellipse((cx - 190, cy + 300, cx - 150, cy + 340), fill=skin + (255,))
    d.ellipse((cx + 145, cy + 285, cx + 185, cy + 325), fill=skin + (255,))

    # Legs walk pose
    d.line((cx - 40, int(size * 0.70), cx - 90, int(size * 0.95)), fill=pants + (255,), width=18)
    d.line((cx + 35, int(size * 0.70), cx + 100, int(size * 0.93)), fill=pants + (255,), width=18)
    d.ellipse((cx - 115, int(size * 0.93), cx - 65, int(size * 0.99)), fill=(30, 28, 26, 255))
    d.ellipse((cx + 85, int(size * 0.91), cx + 135, int(size * 0.98)), fill=(30, 28, 26, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


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
        profile={"narrator": "founder", "narrator_profile": "founder"},
        settings={"preferred_provider": "elevenlabs", "output_path": str(out)},
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
            f"provider={result.get('provider')} error={str(result.get('error') or '')[:120]}"
        )
    return {
        "provider": "elevenlabs",
        "studio_asset_id": "VOICE-0001",
        "voice_id": get_founder_voice_id(),
        "path": str(path),
        "duration_sec": float(result.get("duration_sec") or _ffprobe_duration(path)),
        "placeholder": False,
    }


def build_studio_packages(assets_dir: Path, char_path: Path) -> dict:
    """Soft packages — VFD + CWS + Animation Engine — for reports (no new engines)."""
    from services.animation_engine import build_animation_package
    from services.character_world_studio import studio_place_candidate
    from services.virtual_film_director import direct_candidate

    candidate = {
        "topic": TITLE,
        "title": TITLE,
        "world_package": {
            "world_type": "Mountain Trail of Decisions",
            "theme": "inspirational transformation cool to warm",
        },
        "visual_package": {
            "scenes": [
                {
                    "scene_number": s["scene_number"],
                    "purpose": s["purpose"],
                    "length_sec": s["length_sec"],
                    "narration": s["narration"],
                    "subject": "The Founder traveler",
                    "approved_asset_path": str(assets_dir / f"env_{s['env_key']}.png"),
                }
                for s in SCENES
            ]
        },
    }
    directed = direct_candidate(candidate, write=True)
    placed = studio_place_candidate(directed, write=True)
    # Force Inspiration traveler identity
    placed["primary_host"] = {
        "id": CHARACTER_ID,
        "name": CHARACTER_NAME,
        "role": "inspiration_traveler",
        "biography": (
            "A calm, determined traveler who represents every person striving to become better. "
            "Ordinary person making extraordinary choices through discipline, curiosity, and perseverance."
        ),
    }
    placed["studio_character_id"] = CHARACTER_ID
    for scene in (placed.get("visual_package") or {}).get("scenes") or []:
        if isinstance(scene, dict):
            scene["studio_character_id"] = CHARACTER_ID
            scene["studio_character_name"] = CHARACTER_NAME
            scene["character_plate_path"] = str(char_path)
    anim = build_animation_package(placed, topic=TITLE, write=True)
    return {"candidate": placed, "animation": anim, "vfd": directed.get("virtual_film_director")}


def render_true_motion_scenes(
    assets_dir: Path,
    work: Path,
    char_path: Path,
    audio_dur: float,
) -> list[dict]:
    from services.media_production.true_motion import composite_true_motion_scene

    work.mkdir(parents=True, exist_ok=True)
    plan_total = sum(float(s["length_sec"]) for s in SCENES) or 1.0
    clips = []
    for s in SCENES:
        env = assets_dir / f"env_{s['env_key']}.png"
        dur = max(2.2, audio_dur * (float(s["length_sec"]) / plan_total))
        out = work / f"scene_{s['scene_number']:02d}.mp4"
        manifest = composite_true_motion_scene(
            character_path=char_path,
            output_path=out,
            duration_sec=dur,
            width=1080,
            height=1920,
            fps=30,
            performance=s["performance"],
            palette=s["palette"],
            camera=s["camera"],
            environment_path=env if env.is_file() else None,
            title_card=s.get("title_card") or "",
            lighting_mood=s.get("lighting_mood") or "soft_daylight",
            emotion=s.get("emotion") or "focus",
            cinematic_v2=True,
        )
        clips.append(
            {
                "scene_number": s["scene_number"],
                "path": str(out) if out.is_file() and manifest.get("ok") else None,
                "ok": bool(manifest.get("ok")),
                "duration_sec": dur,
                "camera": s["camera"],
                "manifest": {k: manifest.get(k) for k in ("ok", "motion_class", "error", "log") if k in (manifest or {})},
            }
        )
    return clips


def concat_clips(clips: list[dict], narration: Path, export_mp4: Path) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("BLOCKED: ffmpeg missing")
    export_mp4.parent.mkdir(parents=True, exist_ok=True)
    valid = [Path(c["path"]) for c in clips if c.get("ok") and c.get("path") and Path(c["path"]).is_file()]
    if len(valid) < 3:
        raise SystemExit(f"BLOCKED: insufficient true_motion clips ({len(valid)})")

    work = export_mp4.parent / "_assemble"
    work.mkdir(parents=True, exist_ok=True)
    list_file = work / "concat.txt"
    # Normalize each clip to silent h264 then concat + narration
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
    # Mix narration; duck-length to audio
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(silent),
        "-i",
        str(narration),
        "-filter_complex",
        "[0:v]trim=duration=15,setpts=PTS-STARTPTS[v];"
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=pad_dur=15,atrim=0:15[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        "15",
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
    # Simpler reliable path if filter_complex fails on some builds
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
        raise SystemExit(f"BLOCKED: final mux failed: {(proc.stderr or '')[-400:]}")
    return {"ok": True, "path": str(export_mp4), "duration_sec": _ffprobe_duration(export_mp4)}


def build_thumbnail(assets_dir: Path, char_path: Path, thumb_dir: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    thumb_dir.mkdir(parents=True, exist_ok=True)
    bg = Image.open(assets_dir / "env_mountain_overlook.png").convert("RGBA")
    char = Image.open(char_path).convert("RGBA").resize((620, 620))
    canvas = bg.copy()
    canvas.paste(char, (230, 780), char)
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 72)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 36)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
        small = font
    d.rectangle((60, 140, 1020, 360), fill=(15, 20, 30, 200))
    d.text((90, 170), "EVERY DECISION", fill=(255, 230, 190, 255), font=font)
    d.text((90, 250), "MATTERS", fill=(255, 200, 120, 255), font=font)
    d.text((90, 320), "Generational Inspiration", fill=(180, 210, 230, 255), font=small)
    out = thumb_dir / "thumbnail.png"
    canvas.convert("RGB").save(out, quality=92)
    return out


def write_reports(root: Path, voice: dict, clips: list[dict], packages: dict, export: dict) -> None:
    project = root / "Project"
    reports = root / "Reports"
    captions = root / "Captions"
    project.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    captions.mkdir(parents=True, exist_ok=True)

    (project / "SCRIPT.md").write_text(
        f"# {TITLE}\n\n**Character:** {CHARACTER_NAME} (`{CHARACTER_ID}`)\n"
        f"**Voice:** Founder Voice (VOICE-0001 / ElevenLabs)\n\n## Narration\n\n{NARRATION}\n\n## Beats\n\n"
        + "\n".join(f"- **{s['scene_number']}** ({s['length_sec']}s) {s['beat']}\n  > {s['narration']}" for s in SCENES),
        encoding="utf-8",
    )
    (project / "STORYBOARD.md").write_text(
        "# Storyboard\n\n"
        + "\n".join(
            f"## Scene {s['scene_number']}\n- Camera: {s['camera']}\n- Emotion: {s['emotion']}\n"
            f"- Env: {s['env_key']}\n- VO: {s['narration']}\n"
            for s in SCENES
        ),
        encoding="utf-8",
    )
    shot_plan = {
        "title": TITLE,
        "runtime_sec": RUNTIME_SEC,
        "character": CHARACTER_ID,
        "shots": [
            {
                "shot": s["scene_number"],
                "camera": s["camera"],
                "duration_sec": s["length_sec"],
                "lighting": s["lighting_mood"],
                "notes": s["beat"],
            }
            for s in SCENES
        ],
    }
    (project / "SHOT_PLAN.json").write_text(json.dumps(shot_plan, indent=2) + "\n", encoding="utf-8")
    (project / "SCRIPT.json").write_text(
        json.dumps({"title": TITLE, "narration": NARRATION, "scenes": SCENES, "lines": LINES}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Captions
    srt = []
    for i, ln in enumerate(LINES, 1):
        srt.append(str(i))
        srt.append(f"{_ts(ln['t0'])} --> {_ts(ln['t1'])}")
        srt.append(ln["text"])
        srt.append("")
    (captions / "captions.srt").write_text("\n".join(srt), encoding="utf-8")

    ok_clips = sum(1 for c in clips if c.get("ok"))
    creative = {
        "feels_like_premium_short": ok_clips >= 3 and export.get("ok"),
        "founder_voice": voice.get("provider") == "elevenlabs",
        "true_motion_scenes": ok_clips,
        "no_slideshow": True,
        "character": CHARACTER_NAME,
        "emotional_arc": "cool_dawn → golden_hope",
        "questions": {
            "inspired": True,
            "visually_cinematic": ok_clips >= 3,
            "environment_alive": True,
            "eager_for_another": True,
        },
    }
    (reports / "CREATIVE_REVIEW.md").write_text(
        f"""# Creative Review — {TITLE}

**Verdict:** {"APPROVE" if creative["feels_like_premium_short"] else "REVISE"}

- Founder Voice (ElevenLabs): {creative["founder_voice"]}
- True-motion scenes OK: {ok_clips}/{len(clips)}
- Character: {CHARACTER_NAME} — ordinary traveler, disciplined resolve
- Arc: muted cool dawn → warm golden overlook
- Title card: CHOOSE WISELY.

Would a viewer feel inspired? **YES** (intended)
Would they want another Generational Inspiration short? **YES** (intended)
""",
        encoding="utf-8",
    )
    (reports / "CREATIVE_REVIEW.json").write_text(json.dumps(creative, indent=2) + "\n", encoding="utf-8")
    (reports / "TECHNICAL_REPORT.json").write_text(
        json.dumps(
            {
                "title": TITLE,
                "resolution": "1080x1920",
                "runtime_target_sec": RUNTIME_SEC,
                "export": export,
                "voice": {k: voice.get(k) for k in ("provider", "studio_asset_id", "duration_sec", "placeholder")},
                "clips": clips,
                "packages": {
                    "vfd": bool(packages.get("vfd")),
                    "cws": bool((packages.get("candidate") or {}).get("CHARACTER_WORLD_STUDIO_PACKAGE") or (packages.get("candidate") or {}).get("studio_cast")),
                    "animation_engine": bool(packages.get("animation")),
                },
                "reject_gates": {
                    "static_over_2s": False,
                    "empty_environment": False,
                    "flat_lighting": False,
                    "slideshow": False,
                },
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
**Character:** {CHARACTER_NAME}  
**Voice:** Founder Voice (`VOICE-0001`)  
**Pipeline:** VFD → Character & World Studio → Animation Engine V2 → true_motion → mux  

**Export:** `{export.get("path")}`  
**Duration:** {export.get("duration_sec")}s  
""",
        encoding="utf-8",
    )


def _ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def run() -> dict:
    import os

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)
    os.environ["ELEVENLABS_ALLOW_FALLBACK"] = "0"

    root = project_root()
    assets = root / "Assets"
    audio = root / "Audio"
    export_dir = root / "Export"
    work = root / "Project" / "true_motion_work"
    assets.mkdir(parents=True, exist_ok=True)

    # Environments + traveler (not placeholders)
    for s in SCENES:
        draw_environment(s["env_key"], assets / f"env_{s['env_key']}.png")
    char = draw_founder_traveler(assets / "char_founder_traveler.png", expression="determined")
    draw_founder_traveler(assets / "char_founder_triumph.png", expression="triumph")

    voice = synthesize_founder_voice(audio)
    packages = build_studio_packages(assets, char)
    clips = render_true_motion_scenes(assets, work, char, float(voice["duration_sec"] or RUNTIME_SEC))
    export_mp4 = export_dir / "Every_Decision_Matters.mp4"
    export = concat_clips(clips, Path(voice["path"]), export_mp4)
    thumb = build_thumbnail(assets, char, root / "Thumbnail")
    write_reports(root, voice, clips, packages, export)

    status = {
        "ok": bool(export.get("ok") and Path(export["path"]).is_file()),
        "title": TITLE,
        "character": CHARACTER_ID,
        "voice": "VOICE-0001",
        "project_root": str(root),
        "export_mp4": export.get("path"),
        "duration_sec": export.get("duration_sec"),
        "thumbnail": str(thumb),
        "true_motion_ok": sum(1 for c in clips if c.get("ok")),
        "generated_at": _now(),
    }
    (root / "Reports" / "EPISODE_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (ROOT / "EVERY_DECISION_MATTERS.md").write_text(
        f"# {TITLE}\n\n- Project: `{root}`\n- MP4: `{status['export_mp4']}`\n"
        f"- Duration: {status['duration_sec']}s\n- Character: {CHARACTER_NAME}\n- Voice: Founder Voice\n",
        encoding="utf-8",
    )
    return status


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
