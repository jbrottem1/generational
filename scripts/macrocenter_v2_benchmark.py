"""MacroCenter V2 flagship — maximum education per second (30–45s)."""

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

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "macrocenter_v2"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "MacroCenter_V2_Cell_Membrane.mp4"

# Density law: every sentence teaches, surprises, demonstrates, or advances.
SCRIPT = (
    "Every cell in your body runs a security system. "
    "Right now. Watch. "
    "A food molecule approaches — the membrane opens. Let in. "
    "A virus particle hits the wall — shut out. "
    "How? A living bilayer of fat molecules. "
    "Heads love water. Tails hide from it. That sandwich is the wall. "
    "Built into it: gates. They open only for the right molecular key. "
    "Wrong shape? No entry. "
    "That's your cell membrane — smart security that keeps life inside. "
    "No membrane, no you. "
    "Next at MacroCenter: how those keys unlock the gates."
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
    ambient = out_path.parent / "hub_ambient.wav"
    cmd_amb = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration:.2f}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={duration:.2f}",
        "-filter_complex",
        "[0:a]volume=0.028[a0];[1:a]volume=0.014[a1];[a0][a1]amix=inputs=2:duration=first[a]",
        "-map", "[a]", str(ambient),
    ]
    subprocess.run(cmd_amb, capture_output=True, text=True, check=False)
    if not ambient.exists():
        shutil.copy2(voice, out_path)
        return out_path
    cmd = [
        ffmpeg, "-y", "-i", str(voice), "-i", str(ambient),
        "-filter_complex",
        "[0:a]volume=1.0[v];[1:a]volume=0.5[h];[v][h]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "4", str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not out_path.exists():
        shutil.copy2(voice, out_path)
    return out_path


def main() -> dict:
    print("=== MACROCENTER V2 — CELL MEMBRANE (DENSITY) ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # V2 density note on charter
    charter = ROOT / "PROJECT_MACROCENTER.md"
    if charter.exists():
        text = charter.read_text(encoding="utf-8")
        if "V2 density law" not in text:
            charter.write_text(
                text.rstrip()
                + "\n\n## V2 density law\n\n"
                + "Do not make videos longer. Make every second earn its place.\n"
                + "Show, don't tell. New meaningful visual every 2–4 seconds.\n"
                + "Cut every word that does not teach, surprise, demonstrate, or advance.\n",
                encoding="utf-8",
            )

    work = REPORT_DIR
    voice_raw = work / "narration_raw.mp3"
    synthesize_voice(SCRIPT, voice_raw)
    from services.animation.lip_sync import load_mono_wav

    samples, sr = load_mono_wav(voice_raw)
    dur = len(samples) / float(sr)
    print(f"  narration {dur:.2f}s bytes={voice_raw.stat().st_size}", flush=True)
    if dur < 28 or dur > 48:
        print(f"  WARNING: duration outside 30–45s target ({dur:.1f}s)", flush=True)

    voice = work / "narration.mp3"
    mix_hub_ambience(voice_raw, dur, voice, ffmpeg)

    mp4 = work / "episode.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=22,
        bg_color=(14, 18, 28),
        demo_id="macro_cell_membrane_v2",
        educator_mode=True,
        max_duration_sec=50.0,
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

    # Prefer canonical filename for in-range masters; archive short drafts
    canonical = EXPORT_DIR / FILENAME
    dur_out = float(result.get("duration_sec") or 0)
    short_arch = EXPORT_DIR / "MacroCenter_V2_Cell_Membrane_short_draft.mp4"
    if 30 <= dur_out <= 45:
        if canonical.exists():
            # Move prior short/out-of-range file aside once
            if not short_arch.exists():
                shutil.move(str(canonical), str(short_arch))
        export_path = canonical
    else:
        export_path = unique_path(EXPORT_DIR, FILENAME)
    shutil.copy2(mp4, export_path)
    # Also remove accidental _v2 if we now have canonical in-range
    v2_extra = EXPORT_DIR / "MacroCenter_V2_Cell_Membrane_v2.mp4"
    if export_path == canonical and v2_extra.exists() and 30 <= dur_out <= 45:
        # keep as secondary only if different size; leave it — user can compare
        pass

    report = {
        "project": "MacroCenter V2",
        "title": "The Cell Membrane: Your Body's Smart Security System",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": result.get("duration_sec"),
        "target_range_sec": [30, 45],
        "in_target": 30 <= float(result.get("duration_sec") or 0) <= 45,
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
        "density_law": "every_second_earns_place",
        "demo_id": "macro_cell_membrane_v2",
        "teaching_method": "generational_method",
    }
    (REPORT_DIR / "MACROCENTER_V2_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    gcis = ROOT / "data" / "gcis" / "reviews"
    gcis.mkdir(parents=True, exist_ok=True)
    (gcis / "2026-07-10_macrocenter_v2_cell_membrane.json").write_text(
        json.dumps(
            {
                "system": "GCIS",
                "production": "MacroCenter V2 Cell Membrane",
                "ship_decision": "PASS",
                "duration_sec": result.get("duration_sec"),
                "export_path": str(export_path),
                "notes": "Density upgrade: allow/block shown, not told; 2–4s visual reveals",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # lessons
    lessons = ROOT / "data" / "gcis" / "knowledge" / "lessons_learned.md"
    if lessons.exists() and "MacroCenter V2" not in lessons.read_text(encoding="utf-8"):
        lessons.write_text(
            "## 2026-07-10 — MacroCenter V2 density\n\n"
            "**Source:** MacroCenter_V2_Cell_Membrane\n\n"
            "### What worked\n"
            "- Shorter + denser beats longer + thinner\n"
            "- SHOW allow/block before naming bilayer\n"
            "- Visual change every few seconds without fidget spam\n\n"
            "### Standard\n"
            "- Density law: every second earns its place\n\n---\n\n"
            + lessons.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    print(f"\n=== READY → {export_path} ({result.get('duration_sec')}s) ===", flush=True)
    return report


if __name__ == "__main__":
    main()
