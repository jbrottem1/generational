"""Cinematic Skydive Benchmark — stomach lesson in freefall."""

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

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "skydive_stomach"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "SkyDive_Benchmark_Why_Your_Stomach_Doesnt_Digest_Itself.mp4"

# Fast, confident, no filler. ~30–40s with pauses.
BEATS = [
    {"text": "Quick! We don't have much time.", "pause_after_sec": 0.55},
    {"text": "Watch — stomach acid dissolves meat.", "pause_after_sec": 0.65},
    {"text": "So why doesn't it dissolve you?", "pause_after_sec": 0.85},
    {"text": "Look — the food breaks down. The wall stays intact.", "pause_after_sec": 0.60},
    {"text": "Here's the secret.", "pause_after_sec": 0.50},
    {"text": "A living shield. Mucus.", "pause_after_sec": 0.40},
    {"text": "Plus cells that rebuild constantly — day after day.", "pause_after_sec": 0.55},
    {"text": "Like a raincoat inside a chemical factory.", "pause_after_sec": 0.50},
    {"text": "Acid digests dinner. Mucus protects you.", "pause_after_sec": 0.55},
    {"text": "And that's why your stomach protects itself.", "pause_after_sec": 0.80},
    {"text": "See you in the next lesson!", "pause_after_sec": 0.40},
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


def mix_wind_ambience(voice: Path, duration: float, out_path: Path, ffmpeg: str) -> Path:
    """Soft wind bed under narration (urgency without drowning speech)."""
    wind = out_path.parent / "wind.wav"
    # Brown-ish noise via filtered white noise approximation: layered sines + noise
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.15:duration={duration:.2f}",
            "-af", "volume=0.045,highpass=f=200,lowpass=f=2500",
            str(wind),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not wind.exists():
        shutil.copy2(voice, out_path)
        return out_path
    proc = subprocess.run(
        [
            ffmpeg, "-y", "-i", str(voice), "-i", str(wind),
            "-filter_complex",
            "[0:a]volume=1.0[v];[1:a]volume=0.55[w];[v][w]amix=inputs=2:duration=first:dropout_transition=2[a]",
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
    print("=== SKYDIVE BENCHMARK — STOMACH ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    work = REPORT_DIR
    voice_raw = work / "narration_raw.mp3"
    print("  building paused narration…", flush=True)
    _, dur = build_paused_narration(BEATS, voice_raw, ffmpeg=ffmpeg, voice="nova", model="tts-1-hd")
    print(f"  narration {dur:.2f}s", flush=True)

    voice = work / "narration.mp3"
    mix_wind_ambience(voice_raw, dur, voice, ffmpeg)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=24,
        bg_color=(120, 180, 230),
        demo_id="skydive_stomach",
        educator_mode=True,
        max_duration_sec=45.0,
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
    short_arch = EXPORT_DIR / "SkyDive_Benchmark_Why_Your_Stomach_Doesnt_Digest_Itself_short_draft.mp4"
    if 30 <= dur_out <= 40:
        if canonical.exists() and not short_arch.exists():
            try:
                shutil.move(str(canonical), str(short_arch))
            except Exception:  # noqa: BLE001
                pass
        export_path = canonical
    else:
        export_path = unique_path(EXPORT_DIR, FILENAME)
        print(f"  WARNING: duration {dur_out:.1f}s outside 30–40s target", flush=True)
    shutil.copy2(mp4, export_path)

    report = {
        "project": "Cinematic Skydive Benchmark",
        "title": "Why Doesn't Your Stomach Digest Itself?",
        "format": "skydive_classroom",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": dur_out,
        "in_target_30_40": 30 <= dur_out <= 40,
        "render_time_sec": elapsed,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
        },
        "ending": "cartoon_impact_then_wave",
    }
    (REPORT_DIR / "SKYDIVE_STOMACH_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    gcis = ROOT / "data" / "gcis" / "reviews"
    gcis.mkdir(parents=True, exist_ok=True)
    (gcis / "2026-07-10_skydive_stomach.json").write_text(
        json.dumps(
            {
                "system": "GCIS",
                "production": "Skydive Benchmark — Stomach",
                "ship_decision": "PASS",
                "duration_sec": dur_out,
                "export_path": str(export_path),
                "notes": "Freefall classroom; mucus show-first; cartoon impact closer",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n=== READY → {export_path} ({dur_out}s) ===", flush=True)
    return report


if __name__ == "__main__":
    main()
