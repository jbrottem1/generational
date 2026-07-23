"""Generational Professor — communicator benchmark: brain energy.

Delivery-first: hooks, pauses, punchlines. Show then explain.
"""

from __future__ import annotations

import json
import shutil
import subprocess
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

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "communicator_brain_energy"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "Generational_Benchmark_Brain_Energy.mp4"

# Curiosity → question → show → reveal → explain → real-world → punchline
# Pauses are intentional silence (not filler words).
BEATS = [
    {
        "text": "Your body is doing something incredible right now.",
        "pause_after_sec": 0.60,
    },
    {
        "text": "Watch where the energy goes.",
        "pause_after_sec": 0.75,
    },
    {
        "text": "See that? Your brain is pulling fuel like a magnet.",
        "pause_after_sec": 0.50,
    },
    {
        "text": "Wait. What?",
        "pause_after_sec": 1.15,
    },
    {
        "text": "Two percent of your body weight.",
        "pause_after_sec": 0.45,
    },
    {
        "text": "About twenty percent of your resting energy.",
        "pause_after_sec": 0.65,
    },
    {
        "text": "Here's why. Billions of neurons. Never fully off. Every signal costs energy.",
        "pause_after_sec": 0.45,
    },
    {
        "text": "Thinking is expensive. Focus. Memory. Even daydreaming.",
        "pause_after_sec": 0.50,
    },
    {
        "text": "Your brain is a power-hungry genius.",
        "pause_after_sec": 0.40,
    },
    {
        "text": "Small organ. Huge energy bill.",
        "pause_after_sec": 0.55,
    },
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


def mix_soft_ambience(voice: Path, duration: float, out_path: Path, ffmpeg: str) -> Path:
    ambient = out_path.parent / "amb.wav"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=92:duration={duration:.2f}",
            "-af", "volume=0.018",
            str(ambient),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not ambient.exists():
        shutil.copy2(voice, out_path)
        return out_path
    proc = subprocess.run(
        [
            ffmpeg, "-y", "-i", str(voice), "-i", str(ambient),
            "-filter_complex",
            "[0:a]volume=1.0[v];[1:a]volume=0.4[h];[v][h]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "3", str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not out_path.exists():
        shutil.copy2(voice, out_path)
    return out_path


def main() -> dict:
    print("=== COMMUNICATOR BENCHMARK — BRAIN ENERGY ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Brief doctrine note
    note = ROOT / "PROJECT_EXCELLENCE.md"
    if note.exists():
        text = note.read_text(encoding="utf-8")
        if "Communicator delivery" not in text:
            note.write_text(
                text.rstrip()
                + "\n\n## Communicator delivery\n\n"
                + "People remember how information made them feel.\n"
                + "Hook → show → pause → reveal → explain → punchline.\n"
                + "Use intentional silence. Never dump definitions first.\n",
                encoding="utf-8",
            )

    work = REPORT_DIR
    voice_raw = work / "narration_raw.mp3"
    print("  building paused narration…", flush=True)
    _, dur = build_paused_narration(BEATS, voice_raw, ffmpeg=ffmpeg, voice="nova", model="tts-1-hd")
    print(f"  narration {dur:.2f}s", flush=True)

    voice = work / "narration.mp3"
    mix_soft_ambience(voice_raw, dur, voice, ffmpeg)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=24,
        bg_color=(14, 18, 28),
        demo_id="excellence_brain_energy",
        educator_mode=True,
        max_duration_sec=50.0,
        spec=StickFigureSpec(name="Generational Professor"),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    qc = result.get("qc") or {}
    ok = bool(result.get("ok") and qc.get("passed"))
    dur_out = float(result.get("duration_sec") or 0)
    print(
        f"  ok={result.get('ok')} qc={qc.get('passed')} purposeful={qc.get('purposeful_gestures')} "
        f"idle={qc.get('idle_ratio')} walk={qc.get('walk_ratio')} dur={dur_out} t={elapsed}s",
        flush=True,
    )
    if not ok:
        raise SystemExit(f"QC failed: {qc}")

    canonical = EXPORT_DIR / FILENAME
    short_arch = EXPORT_DIR / "Generational_Benchmark_Brain_Energy_short_draft.mp4"
    if 30 <= dur_out <= 45:
        if canonical.exists() and not short_arch.exists():
            try:
                shutil.move(str(canonical), str(short_arch))
            except Exception:  # noqa: BLE001
                pass
        export_path = canonical
    else:
        export_path = unique_path(EXPORT_DIR, FILENAME)
        print(f"  WARNING: duration {dur_out:.1f}s outside 30–45s", flush=True)
    shutil.copy2(mp4, export_path)

    report = {
        "project": "Generational Professor — Communicator Upgrade",
        "title": "Why Your Brain Uses So Much Energy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": dur_out,
        "in_target_30_45": 30 <= dur_out <= 45,
        "render_time_sec": elapsed,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "delivery": {
            "voice": "nova",
            "model": "tts-1-hd",
            "paused_beats": len(BEATS),
            "structure": "curiosity→show→reveal→explain→punchline",
        },
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
        },
        "science_note": "Brain ~2% body mass, ~20% resting metabolic rate (oxygen/glucose for neural signaling)",
    }
    (REPORT_DIR / "COMMUNICATOR_BRAIN_ENERGY_REPORT.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    gcis = ROOT / "data" / "gcis" / "reviews"
    gcis.mkdir(parents=True, exist_ok=True)
    (gcis / "2026-07-10_communicator_brain_energy.json").write_text(
        json.dumps(
            {
                "system": "GCIS",
                "production": "Communicator Benchmark — Brain Energy",
                "ship_decision": "PASS" if ok else "REJECT",
                "duration_sec": dur_out,
                "export_path": str(export_path),
                "notes": "Paused beat delivery; show energy drain before 2%/20% reveal",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lessons = ROOT / "data" / "gcis" / "knowledge" / "lessons_learned.md"
    if lessons.exists():
        body = lessons.read_text(encoding="utf-8")
        if "Communicator delivery" not in body and "brain energy" not in body.lower():
            lessons.write_text(
                "## 2026-07-10 — Communicator delivery\n\n"
                "**Source:** Generational_Benchmark_Brain_Energy\n\n"
                "### What worked\n"
                "- Intentional silence between beats > continuous TTS dump\n"
                "- 'Wait. What?' pause before the 2%/20% punchline\n"
                "- Show energy particles into brain BEFORE stating the statistic\n\n"
                "### Standard\n"
                "- Use `communicator_delivery.build_paused_narration` for flagship Shorts\n\n---\n\n"
                + body,
                encoding="utf-8",
            )

    print(f"\n=== READY → {export_path} ({dur_out}s) ===", flush=True)
    return report


if __name__ == "__main__":
    main()
