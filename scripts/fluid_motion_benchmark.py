"""Project Fluid Motion — 20–30s animation-quality benchmark.

One biological fact. One existing demo. Judge only motion + performance + sync.
"""

from __future__ import annotations

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

from services.animation.communicator_delivery import build_paused_narration
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "fluid_motion"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "Fluid_Motion_Benchmark_You_Are_Made_Of_Cells.mp4"

# Sparse beats — pauses for stillness; ~22–28s with intentional silence
BEATS = [
    {"text": "Here's something strange.", "pause_after_sec": 0.70},
    {"text": "You are not one thing.", "pause_after_sec": 0.55},
    {"text": "You are trillions of tiny living rooms — cells.", "pause_after_sec": 0.75},
    {"text": "Watch.", "pause_after_sec": 0.50},
    {"text": "Each one has a wall, a control center, and machinery that keeps you alive.", "pause_after_sec": 0.65},
    {"text": "Trees. Whales. You.", "pause_after_sec": 0.45},
    {"text": "Same building blocks. Different buildings.", "pause_after_sec": 0.70},
    {"text": "Life's unit is the cell.", "pause_after_sec": 0.55},
]


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    ext = Path(filename).suffix
    v = 2
    while True:
        candidate = directory / f"{stem}_v{v}{ext}"
        if not candidate.exists():
            return candidate
        v += 1


def main() -> dict:
    print("=== PROJECT FLUID MOTION — CELLS BENCHMARK ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    work = REPORT_DIR
    voice = work / "narration.mp3"
    print("  building paused narration…", flush=True)
    _, dur = build_paused_narration(BEATS, voice, ffmpeg=ffmpeg, voice="nova", model="tts-1-hd")
    print(f"  narration {dur:.2f}s", flush=True)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=24,
        bg_color=(232, 238, 244),
        demo_id="fluid_cells",
        educator_mode=True,
        max_duration_sec=35.0,
        spec=StickFigureSpec(name="Generational Professor"),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    qc = result.get("qc") or {}
    ok = bool(result.get("ok") and qc.get("passed"))
    dur_out = float(result.get("duration_sec") or 0)
    print(
        f"  ok={result.get('ok')} qc={qc.get('passed')} purposeful={qc.get('purposeful_gestures')} "
        f"idle={qc.get('idle_ratio')} walk={qc.get('walk_ratio')} gestures={qc.get('gesture_counts')} "
        f"dur={dur_out} t={elapsed}s",
        flush=True,
    )
    if not ok:
        raise SystemExit(f"QC failed: {qc}")

    if 20 <= dur_out <= 30:
        export_path = EXPORT_DIR / FILENAME
        if export_path.exists():
            export_path = unique_path(EXPORT_DIR, FILENAME)
    else:
        export_path = unique_path(EXPORT_DIR, FILENAME)
        print(f"  WARNING: duration {dur_out:.1f}s outside 20–30s target", flush=True)
    shutil.copy2(mp4, export_path)

    report = {
        "project": "Project Fluid Motion",
        "title": "You Are Made of Cells",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": dur_out,
        "in_target_20_30": 20 <= dur_out <= 30,
        "render_time_sec": elapsed,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "demo_id": "fluid_cells",
        "motion_engine": "fluid_motion",
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
        },
        "judge": ["animation", "flow", "performance", "teaching", "synchronization"],
    }
    (REPORT_DIR / "FLUID_MOTION_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    gcis = ROOT / "data" / "gcis" / "reviews"
    gcis.mkdir(parents=True, exist_ok=True)
    (gcis / "2026-07-10_fluid_motion.json").write_text(
        json.dumps(
            {
                "system": "GCIS",
                "production": "Fluid Motion Benchmark — Cells",
                "ship_decision": "PASS" if ok else "FAIL",
                "duration_sec": dur_out,
                "export_path": str(export_path),
                "notes": "Pose blend + anticipation + breath/weight life; existing bio_cells demo",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n=== READY → {export_path} ({dur_out}s) ===", flush=True)
    return report


if __name__ == "__main__":
    main()
