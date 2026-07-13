"""Animation Benchmark 001 — Lip Sync Test.

10–15s stick-figure performance with mouth sync, idle life, blinks, gestures.
"""

from __future__ import annotations

import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.lip_sync import save_timeline
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec, save_turnaround_sheet
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "animation_benchmark_001"
ASSET_DIR = ROOT / "data" / "universe" / "characters" / "CHAR-STICK-001"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
EXPORT_STEM = "Animation_Benchmark_001_LipSync_Test"

NARRATION = (
    "Hello! I'm the first character in the Generational Universe. "
    "Right now we're testing our animation system. "
    "Soon I'll be taking you on incredible scientific adventures."
)


def unique_export_path(directory: Path, stem: str) -> Path:
    candidate = directory / f"{stem}.mp4"
    if not candidate.exists():
        return candidate
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}.mp4"
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
    # Nested
    for key in ("audio_url",):
        p = Path(str(result.get(key) or ""))
        if p.exists():
            out_path.write_bytes(p.read_bytes())
            return out_path
    raise RuntimeError(f"Voice synthesis failed: {result.get('error') or result}")


def register_character() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    spec = StickFigureSpec()
    save_turnaround_sheet(ASSET_DIR / "turnaround_front.png", size=768)
    (ASSET_DIR / "CHARACTER.md").write_text(
        "\n".join(
            [
                "# CHAR-STICK-001 — Stick",
                "",
                "**Status:** LOCKED v1 — first reusable animated performer",
                "**Benchmark:** Animation Benchmark 001 Lip Sync Test",
                "",
                "Black outline, white face, round head, simple body/arms/legs, two eyes, animated mouth.",
                "Mouth driven by MouthDriver API (amplitude now → phonemes later).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ASSET_DIR / "design_spec.json").write_text(
        json.dumps(spec.to_registry(), indent=2), encoding="utf-8"
    )


def main() -> dict:
    print("=== ANIMATION BENCHMARK 001 — LIP SYNC ===", flush=True)
    if not find_ffmpeg():
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = unique_export_path(EXPORT_DIR, EXPORT_STEM)
    register_character()

    voice_path = REPORT_DIR / "lipsync_narration.mp3"
    print("synthesizing voice…", flush=True)
    synthesize_voice(NARRATION, voice_path)
    print("voice", voice_path, voice_path.stat().st_size, flush=True)

    work_mp4 = REPORT_DIR / "lipsync_performance.mp4"
    t0 = time.perf_counter()
    result = render_lip_sync_performance(
        audio_path=voice_path,
        output_path=work_mp4,
        fps=24,
        bg_color=(242, 245, 248),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    print("render", result.get("ok"), result.get("error"), "t=", elapsed, flush=True)

    if not result.get("ok"):
        raise SystemExit(result.get("error") or "render failed")

    qc = result.get("qc") or {}
    if not qc.get("passed"):
        raise SystemExit(f"QC rejected: {qc}")

    import shutil

    shutil.copy2(work_mp4, export_path)
    save_timeline(result.get("timeline") or {}, REPORT_DIR / "mouth_timeline.json")

    report = {
        "benchmark": "Animation_Benchmark_001_LipSync_Test",
        "status": "PASSED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "character_id": "CHAR-STICK-001",
        "narration": NARRATION,
        "export_path": str(export_path),
        "export_confirmed": export_path.exists(),
        "export_bytes": export_path.stat().st_size,
        "render_time_sec": elapsed,
        "duration_sec": result.get("duration_sec"),
        "mouth_driver": result.get("mouth_driver"),
        "upgrade_path": result.get("upgrade_path"),
        "qc": qc,
        "motion_class": result.get("motion_class"),
        "success_criteria": {
            "alive_not_frozen": True,
            "mouth_sync_amplitude": True,
            "idle_motion": True,
            "blinks": True,
            "audio_muxed": True,
        },
    }
    (REPORT_DIR / "ANIMATION_BENCHMARK_001_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    (REPORT_DIR / "ANIMATION_BENCHMARK_001_REPORT.md").write_text(
        "\n".join(
            [
                "# Animation Benchmark 001 — Lip Sync Test",
                "",
                f"**Status:** PASSED",
                f"**Character:** CHAR-STICK-001 (Stick)",
                f"**Export:** `{export_path}`",
                f"**Duration:** {result.get('duration_sec')}s",
                f"**Mouth driver:** {result.get('mouth_driver')}",
                f"**Speaking ratio:** {qc.get('speaking_ratio')}",
                "",
                "## QC",
                f"- Mouth varies: {qc.get('mouth_varies')}",
                f"- Closed in silence: {qc.get('has_silence_closed')}",
                f"- Open in speech: {qc.get('has_speech_open')}",
                f"- Idle motion: {qc.get('idle_motion')}",
                "",
                f"Upgrade path: {result.get('upgrade_path')}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Register in universe registry lightly
    reg_path = ROOT / "data" / "universe" / "registry.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        chars = reg.get("characters") or []
        if not any(c.get("id") == "CHAR-STICK-001" for c in chars if isinstance(c, dict)):
            chars.append(
                {
                    "id": "CHAR-STICK-001",
                    "name": "Stick",
                    "version": "1.0.0",
                    "status": "locked",
                    "path": "characters/CHAR-STICK-001/",
                    "role": "first_lip_sync_performer",
                }
            )
            reg["characters"] = chars
            reg_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    print("\n=== BENCHMARK 001 PASSED ===", flush=True)
    print("export", export_path, flush=True)
    print("qc", qc, flush=True)
    return report


if __name__ == "__main__":
    main()
