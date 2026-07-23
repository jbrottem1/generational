"""Project MacroCenter — flagship biology benchmark.

Professor teaches from MacroCenter HQ. Additive to existing educator path.
"""

from __future__ import annotations

import base64
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

from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "macrocenter_benchmark_001"
SERIES_DIR = ROOT / "data" / "universe" / "series" / "macrocenter"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SERIES_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "MacroCenter_Biology_001_Cell_Membrane.mp4"

# ~45–60s Generational Method script — MacroCenter open → membrane lesson
SCRIPT = (
    "Welcome to MacroCenter — where knowledge comes to life. "
    "I'm your host. Tonight, one question: why does every living cell need a membrane? "
    "Imagine a city with no walls, no doors, no borders. Chaos. "
    "A cell without a membrane is the same — chemistry spills everywhere, and life can't hold together. "
    "Watch this hologram. Here is a cell. Its membrane is a living wall — "
    "a double layer of fat molecules called phospholipids. "
    "Each molecule has a head that loves water, and tails that hide from water. "
    "Heads face out. Heads face in. Tails tuck together in the middle. "
    "That sandwich seals the cell. "
    "But look closer — it's not a brick wall. It's selective. "
    "Nutrients can enter. Waste can leave. Invaders get blocked. "
    "Rotate the model. See those channels? Tiny gates that decide what passes. "
    "So remember this: the membrane keeps the inside organized — and alive. "
    "That's why every cell on Earth needs one. "
    "Next time at MacroCenter: how those gates open and close."
)


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


def synthesize_voice(text: str, out_path: Path) -> Path:
    from services.provider_runtime.engine_api import runtime_synthesize_voice

    result = runtime_synthesize_voice(
        text,
        profile={"provider": "openai_tts", "voice": "onyx"},
        settings={"model": "tts-1", "voice": "onyx"},
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


def mix_hub_ambience(voice: Path, duration: float, out_path: Path, ffmpeg: str) -> Path:
    """Soft futuristic pad under narration (MacroCenter immersion)."""
    ambient = out_path.parent / "hub_ambient.wav"
    mixed = out_path
    # Low warm pad + quiet high shimmer
    cmd_amb = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration:.2f}",
        "-f", "lavfi",
        "-i", f"sine=frequency=220:duration={duration:.2f}",
        "-filter_complex",
        "[0:a]volume=0.035[a0];[1:a]volume=0.018[a1];[a0][a1]amix=inputs=2:duration=first[a]",
        "-map", "[a]",
        str(ambient),
    ]
    subprocess.run(cmd_amb, capture_output=True, text=True, check=False)
    if not ambient.exists():
        shutil.copy2(voice, mixed)
        return mixed
    cmd = [
        ffmpeg, "-y",
        "-i", str(voice),
        "-i", str(ambient),
        "-filter_complex",
        "[0:a]volume=1.0[v];[1:a]volume=0.55[h];[v][h]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(mixed),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not mixed.exists():
        shutil.copy2(voice, mixed)
    return mixed


def main() -> dict:
    print("=== PROJECT MACROCENTER — FLAGSHIP BENCHMARK ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    (SERIES_DIR / "SERIES_BIBLE.md").write_text(
        "\n".join(
            [
                "# MacroCenter",
                "",
                "**Role:** Permanent Generational Universe headquarters",
                "**Charter:** PROJECT_MACROCENTER.md",
                "**Host:** Generational Professor (CHAR-STICK-001)",
                "**Flagship:** Why Every Cell Needs a Cell Membrane",
                "",
            ]
        ),
        encoding="utf-8",
    )

    char_md = ROOT / "data" / "universe" / "characters" / "CHAR-STICK-001" / "CHARACTER.md"
    char_md.write_text(
        "\n".join(
            [
                "# CHAR-STICK-001 — Generational Professor",
                "",
                "**Role:** Permanent host of MacroCenter",
                "**Status:** LOCKED v2.0 — Professor mode (lab coat, purposeful teaching)",
                "",
                "Home: PROJECT_MACROCENTER.md",
                "Doctrine: GENERATIONAL_METHOD.md",
                "Walks with purpose. Interacts with holograms. Never waves randomly.",
                "Teaches by demonstration inside MacroCenter.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    work = REPORT_DIR
    work.mkdir(parents=True, exist_ok=True)
    voice_raw = work / "narration_raw.mp3"
    synthesize_voice(SCRIPT, voice_raw)
    print("  voice bytes", voice_raw.stat().st_size, flush=True)

    # Probe duration via performer path after mix — estimate from file size roughly; mix with probe
    from services.animation.lip_sync import load_mono_wav

    samples, sr = load_mono_wav(voice_raw)
    dur = len(samples) / float(sr)
    print(f"  narration duration {dur:.2f}s", flush=True)
    if dur < 42:
        print("  WARNING: under 45s target — script may be short", flush=True)
    if dur > 62:
        print("  WARNING: over 60s target", flush=True)

    voice = work / "narration.mp3"
    mix_hub_ambience(voice_raw, dur, voice, ffmpeg)
    print("  mixed hub ambience", flush=True)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=20,
        bg_color=(18, 24, 36),
        demo_id="macro_cell_membrane",
        educator_mode=True,
        max_duration_sec=65.0,
        spec=StickFigureSpec(name="Generational Professor"),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    qc = result.get("qc") or {}
    ok = bool(result.get("ok") and qc.get("passed"))
    print(
        f"  ok={result.get('ok')} qc={qc.get('passed')} purposeful={qc.get('purposeful_gestures')} "
        f"idle={qc.get('idle_ratio')} walk={qc.get('walk_ratio')} "
        f"dur={result.get('duration_sec')} t={elapsed}s",
        flush=True,
    )
    if not ok:
        raise SystemExit(f"QC failed: {qc}")

    export_path = unique_path(EXPORT_DIR, FILENAME)
    # Prefer canonical filename when prior export failed length gate (<45s)
    canonical = EXPORT_DIR / FILENAME
    if canonical.exists() and canonical != export_path:
        # Keep short draft as _short archive, promote new master to canonical name
        short_archive = EXPORT_DIR / "MacroCenter_Biology_001_Cell_Membrane_short_draft.mp4"
        if not short_archive.exists():
            shutil.move(str(canonical), str(short_archive))
        export_path = canonical
    shutil.copy2(mp4, export_path)

    # GCIS review draft
    review = {
        "system": "GCIS",
        "slug": "2026-07-10_macrocenter_cell_membrane",
        "production": "MacroCenter Biology 001 — Cell Membrane",
        "ship_decision": "PASS" if ok else "REJECT",
        "duration_sec": result.get("duration_sec"),
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
        },
        "export_path": str(export_path),
        "project": "PROJECT_MACROCENTER",
    }
    gcis_dir = ROOT / "data" / "gcis" / "reviews"
    gcis_dir.mkdir(parents=True, exist_ok=True)
    (gcis_dir / "2026-07-10_macrocenter_cell_membrane.json").write_text(
        json.dumps(review, indent=2), encoding="utf-8"
    )

    report = {
        "project": "Project MacroCenter",
        "episode": "Why Every Cell Needs a Cell Membrane",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": result.get("duration_sec"),
        "render_time_sec": elapsed,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "qc": qc,
        "character": "CHAR-STICK-001",
        "role": "generational_professor",
        "demo_id": "macro_cell_membrane",
        "teaching_method": "generational_method",
        "environment": "macrocenter",
    }
    (REPORT_DIR / "MACROCENTER_BENCHMARK_001_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(f"\n=== READY → {export_path} ===", flush=True)
    return report


if __name__ == "__main__":
    main()
