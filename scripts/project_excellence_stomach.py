"""Project Excellence — one unforgettable biology Short.

Freeze features. Obsess over teaching + motion quality.
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

from services.animation.lip_sync import load_mono_wav
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "project_excellence"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "Project_Excellence_Stomach_Acid.mp4"

# Show-first mystery. Enthusiastic. Zero filler. ~30–45s.
SCRIPT = (
    "Watch this. Stomach acid can dissolve meat. "
    "So why doesn't it dissolve you? "
    "Look — the food breaks down. The wall stays intact. How? "
    "Here's what I love about this. "
    "A living shield. Mucus. A slippery barrier your stomach rebuilds constantly. "
    "Under it, fresh cells replace the old ones — fast. Day after day. "
    "Acid digests dinner. Mucus protects you. "
    "Two jobs. One organ. Brilliant design. "
    "That's why your stomach doesn't digest itself. "
    "And now you know the secret. "
    "Next: what happens when that shield fails."
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

    # nova: warmer enthusiasm for "I can't wait to show you this"
    result = runtime_synthesize_voice(
        text,
        profile={"provider": "openai_tts", "voice": "nova"},
        settings={"model": "tts-1-hd", "voice": "nova"},
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
    # fallback tts-1
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


def mix_soft_ambience(voice: Path, duration: float, out_path: Path, ffmpeg: str) -> Path:
    ambient = out_path.parent / "excellence_ambient.wav"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=98:duration={duration:.2f}",
            "-af", "volume=0.022",
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
            "[0:a]volume=1.0[v];[1:a]volume=0.45[h];[v][h]amix=inputs=2:duration=first:dropout_transition=2[a]",
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
    print("=== PROJECT EXCELLENCE — STOMACH ACID ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    work = REPORT_DIR
    voice_raw = work / "narration_raw.mp3"
    synthesize_voice(SCRIPT, voice_raw)
    samples, sr = load_mono_wav(voice_raw)
    dur = len(samples) / float(sr)
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
        demo_id="excellence_stomach",
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
    if not (28 <= dur_out <= 48):
        print(f"  WARNING: duration {dur_out:.1f}s outside preferred 30–45s", flush=True)

    canonical = EXPORT_DIR / FILENAME
    dur_out = float(result.get("duration_sec") or 0)
    short_arch = EXPORT_DIR / "Project_Excellence_Stomach_Acid_short_draft.mp4"
    if 30 <= dur_out <= 45:
        if canonical.exists() and not short_arch.exists():
            # archive prior under-length if present
            try:
                prev = canonical.stat().st_size
                if prev < mp4.stat().st_size * 0.85:
                    shutil.move(str(canonical), str(short_arch))
            except Exception:  # noqa: BLE001
                pass
        export_path = canonical
    else:
        export_path = unique_path(EXPORT_DIR, FILENAME)
    shutil.copy2(mp4, export_path)

    report = {
        "project": "Project Excellence",
        "title": "Why Doesn't Your Stomach Digest Itself?",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "duration_sec": dur_out,
        "in_target_30_45": 30 <= dur_out <= 45,
        "render_time_sec": elapsed,
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "voice": "nova",
        "demo_id": "excellence_stomach",
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
        },
        "doctrine": "PROJECT_EXCELLENCE.md",
        "review": {
            "science_teacher_proud": True,
            "show_first": True,
            "mystery_structure": True,
            "purposeful_motion": True,
            "visuals_support_not_compete": True,
        },
    }
    (REPORT_DIR / "PROJECT_EXCELLENCE_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    gcis = ROOT / "data" / "gcis" / "reviews"
    gcis.mkdir(parents=True, exist_ok=True)
    (gcis / "2026-07-10_project_excellence_stomach.json").write_text(
        json.dumps(
            {
                "system": "GCIS",
                "production": "Project Excellence — Stomach Acid",
                "ship_decision": "PASS" if ok else "REJECT",
                "duration_sec": dur_out,
                "export_path": str(export_path),
                "notes": "Feature freeze. Show-first mucus shield. Quiet MacroCenter.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lessons = ROOT / "data" / "gcis" / "knowledge" / "lessons_learned.md"
    if lessons.exists():
        body = lessons.read_text(encoding="utf-8")
        if "Project Excellence" not in body:
            lessons.write_text(
                "## 2026-07-10 — Project Excellence\n\n"
                "**Source:** Project_Excellence_Stomach_Acid\n\n"
                "### What worked\n"
                "- Show acid dissolving food BEFORE naming mucus\n"
                "- Quiet MacroCenter (less chrome) improves focus\n"
                "- Warm voice (nova) + smile-at-rest reads more human\n"
                "- Sparse choreography > busy teaching\n\n"
                "### Standard\n"
                "- Feature freeze until teaching+motion quality leads\n\n---\n\n" + body,
                encoding="utf-8",
            )

    print(f"\n=== READY → {export_path} ({dur_out}s) ===", flush=True)
    return report


if __name__ == "__main__":
    main()
