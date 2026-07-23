"""Generational Physics Academy — Physics Fundamentals Volume 1 (5 episodes).

Uses existing Stick lip-sync performer + physics demo overlays.
Does not redesign the animation engine.
"""

from __future__ import annotations

import base64
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "physics_academy_vol1"
SERIES_DIR = ROOT / "data" / "universe" / "series" / "physics_academy"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SERIES_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"

EPISODES = [
    {
        "ep": 1,
        "filename": "Physics_001_What_is_Force.mp4",
        "title": "What is Force?",
        "demo_id": "force",
        "script": (
            "What makes anything start moving? Here's the simple answer: a force. "
            "A force is just a push or a pull. Nothing fancy. "
            "Watch this box. When nothing pushes it, it stays still. "
            "But when a force pushes… the box slides. That change in motion is the clue. "
            "Forces can speed things up, slow them down, or change their direction. "
            "You use forces all day long — opening a door, kicking a ball, lifting a backpack, even standing up against the ground. "
            "So if you remember one idea from this lesson, remember this: "
            "a force is a push or a pull that can change how something moves."
        ),
    },
    {
        "ep": 2,
        "filename": "Physics_002_Gravity.mp4",
        "title": "Why Gravity Pulls Everything Down",
        "demo_id": "gravity",
        "script": (
            "Why does everything fall down instead of floating away? Gravity. "
            "Gravity is Earth's pull toward its center. "
            "Drop a ball and gravity accelerates it downward — faster and faster until something stops it. "
            "It pulls on you, on me, on apples, on rain, and even helps keep the Moon in its path. "
            "Heavier and lighter objects both feel gravity; air resistance is what makes feathers drift. "
            "Without gravity, nothing would stay on the ground — and we wouldn't have weight. "
            "So gravity is the invisible pull that keeps our world together, one falling object at a time."
        ),
    },
    {
        "ep": 3,
        "filename": "Physics_003_Velocity.mp4",
        "title": "What is Velocity?",
        "demo_id": "velocity",
        "script": (
            "People say speed and velocity like they're the same. They're close — but not identical. "
            "Speed tells you how fast. Velocity tells you how fast and which way. "
            "Watch these cars. The slower one covers less distance each second. "
            "The faster one has a higher velocity because it covers more distance in the same time. "
            "Direction matters too: ten meters per second east is not the same velocity as ten meters per second west. "
            "On a highway, your velocity is your speed plus your direction of travel. "
            "Remember the idea: velocity equals distance over time — with a direction attached."
        ),
    },
    {
        "ep": 4,
        "filename": "Physics_004_Momentum.mp4",
        "title": "Why Momentum Matters",
        "demo_id": "momentum",
        "script": (
            "Why is a bowling ball harder to stop than a ping pong ball moving at the same speed? "
            "The answer is momentum. "
            "Momentum is mass times velocity — how much 'oomph' motion has. "
            "More mass means more momentum. More speed also means more momentum. "
            "That's why a heavy truck needs a longer distance to brake than a bicycle. "
            "In sports, safety gear, and car design, momentum helps explain impacts and crashes. "
            "Keep this picture: big momentum means you need a bigger push to change the motion."
        ),
    },
    {
        "ep": 5,
        "filename": "Physics_005_Potential_Energy.mp4",
        "title": "Potential Energy Explained",
        "demo_id": "potential_energy",
        "script": (
            "Lift a ball higher into the air — you're doing something important. You're storing energy. "
            "That stored energy is called potential energy: energy waiting to be used. "
            "The higher the ball goes, the more potential energy it has, because it can do more when it falls. "
            "A roller coaster paused at the top of a hill is packed with potential energy. "
            "When it drops, that store turns into motion energy you can feel. "
            "Food, stretched springs, and raised objects all hold potential in different ways. "
            "For today, remember: potential energy is stored energy — ready for action."
        ),
    },
]


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    ext = Path(filename).suffix
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate
        version += 1


def synthesize_voice(text: str, out_path: Path) -> Path:
    from services.provider_runtime.engine_api import runtime_synthesize_voice

    result = runtime_synthesize_voice(
        text,
        profile={"provider": "openai_tts", "voice": "nova"},
        settings={"model": "tts-1", "voice": "nova"},
        mode="ai",
    )
    path = Path(str(result.get("path") or ""))
    if path.exists():
        out_path.write_bytes(path.read_bytes())
        return out_path
    b64 = str(result.get("audio_b64") or "")
    if b64:
        out_path.write_bytes(base64.b64decode(b64))
        return out_path
    raise RuntimeError(f"Voice failed: {result.get('error') or result}")


def produce_episode(ep: dict, index: int) -> dict:
    print(f"\n=== PHYSICS {index}/5: {ep['title']} ===", flush=True)
    work = REPORT_DIR / f"ep{ep['ep']:02d}"
    work.mkdir(parents=True, exist_ok=True)
    voice = work / "narration.mp3"
    synthesize_voice(ep["script"], voice)
    print("  voice", voice.stat().st_size, "bytes", flush=True)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=20,
        bg_color=(236, 242, 248),
        character_scale=0.48,
        character_anchor="left",
        demo_id=ep["demo_id"],
        max_duration_sec=60.0,
        spec=StickFigureSpec(),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    qc = result.get("qc") or {}
    ok = bool(result.get("ok") and qc.get("passed"))
    print(
        f"  render ok={result.get('ok')} qc={qc.get('passed')} "
        f"dur={result.get('duration_sec')} t={elapsed}s",
        flush=True,
    )
    if not ok:
        return {
            "ep": ep["ep"],
            "title": ep["title"],
            "success": False,
            "error": result.get("error") or f"QC failed: {qc}",
            "qc": qc,
        }

    export_path = unique_path(EXPORT_DIR, ep["filename"])
    shutil.copy2(mp4, export_path)
    return {
        "ep": ep["ep"],
        "title": ep["title"],
        "filename": export_path.name,
        "demo_id": ep["demo_id"],
        "success": True,
        "status": "READY",
        "duration_sec": result.get("duration_sec"),
        "speaking_ratio": qc.get("speaking_ratio"),
        "qc": qc,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "render_time_sec": elapsed,
        "character_id": "CHAR-STICK-001",
    }


def main() -> dict:
    print("=== GENERATIONAL PHYSICS ACADEMY — VOLUME 1 ===", flush=True)
    if not find_ffmpeg():
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Series bible stub
    (SERIES_DIR / "SERIES_BIBLE.md").write_text(
        "\n".join(
            [
                "# Generational Physics Academy",
                "",
                "**Collection:** Physics Fundamentals Volume 1",
                "**Host:** CHAR-STICK-001 (Stick)",
                "**Style:** Lip-sync teaching + animated concept demos",
                "**Tone:** Curious, exciting, approachable",
                "",
            ]
        ),
        encoding="utf-8",
    )

    batch_t0 = time.perf_counter()
    runs = []
    for i, ep in enumerate(EPISODES, start=1):
        runs.append(produce_episode(ep, i))

    ok = [r for r in runs if r.get("success")]
    report = {
        "series": "Generational Physics Academy",
        "collection": "Physics Fundamentals Volume 1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "character_id": "CHAR-STICK-001",
        "requested": 5,
        "completed": len(ok),
        "success": len(ok) == 5,
        "batch_runtime_sec": round(time.perf_counter() - batch_t0, 2),
        "export_directory": str(EXPORT_DIR),
        "episodes": runs,
    }
    (REPORT_DIR / "PHYSICS_ACADEMY_VOL1_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    lines = [
        "# Physics Fundamentals Volume 1 — Report",
        "",
        f"**Completed:** {len(ok)}/5",
        f"**Export:** `{EXPORT_DIR}`",
        "",
        "| Ep | Title | Duration | Status | File |",
        "|---|---|---|---|---|",
    ]
    for r in runs:
        lines.append(
            f"| {r.get('ep')} | {r.get('title')} | {r.get('duration_sec')} | "
            f"{'READY' if r.get('success') else 'FAILED'} | `{r.get('filename') or ''}` |"
        )
    (REPORT_DIR / "PHYSICS_ACADEMY_VOL1_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n=== PHYSICS ACADEMY VOL1 COMPLETE ===", flush=True)
    print("completed", len(ok), "/5", flush=True)
    for r in runs:
        print(
            f"  {r.get('ep')}: {r.get('status') or 'FAILED'} → {r.get('export_path') or r.get('error')}",
            flush=True,
        )
    if len(ok) != 5:
        raise SystemExit("Not all episodes passed QC")
    # Soft length check — prefer 30–60s; warn but don't fail under 30 if QC passed
    short = [r for r in ok if float(r.get("duration_sec") or 0) < 28]
    if short:
        print("WARNING short episodes:", [r["title"] for r in short], flush=True)
    return report


if __name__ == "__main__":
    main()
