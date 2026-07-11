"""Phase 20 — Full-system benchmark production.

SEO-informed topic → script → educational review → fluid-motion render → QC → export.
Does not auto-publish.
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
from services.education.director_review import review_lesson
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.quality.content_score import score_production
from services.provider_runtime.config import has_credential
from services.repetition_booster import RepetitionBooster, fingerprint_inputs

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "full_system_benchmark"
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
FILENAME = "Full_System_Benchmark_Mitochondria_Powerhouse.mp4"

TOPIC = "Why mitochondria are called the powerhouse of the cell"
HOOK = "Your body runs on microscopic power plants."
MAIN_CONCEPT = "Mitochondria convert food into usable cellular energy (ATP)."
TAKEAWAY = "Every move you make is fueled by thousands of tiny mitochondria."

BEATS = [
    {"text": HOOK, "pause_after_sec": 0.65},
    {"text": "Inside almost every cell, mitochondria turn fuel into energy.", "pause_after_sec": 0.55},
    {"text": "Watch — this is where food becomes motion.", "pause_after_sec": 0.50},
    {"text": "They break down nutrients and build ATP — the cell's energy currency.", "pause_after_sec": 0.70},
    {"text": "Muscle cells pack in extra mitochondria because they work hardest.", "pause_after_sec": 0.60},
    {"text": TAKEAWAY, "pause_after_sec": 0.65},
]


def verify_mp4(path: Path) -> dict:
    ffmpeg = find_ffmpeg()
    if not ffmpeg or not path.exists():
        return {"ok": False, "error": "missing ffmpeg or file"}
    import subprocess

    proc = subprocess.run(
        [ffmpeg, "-i", str(path), "-hide_banner"],
        capture_output=True,
        text=True,
    )
    text = (proc.stderr or "") + (proc.stdout or "")
    has_video = "Video:" in text
    has_audio = "Audio:" in text
    dur = 0.0
    for line in text.splitlines():
        if "Duration:" in line:
            try:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                dur = int(h) * 3600 + int(m) * 60 + float(s)
            except Exception:  # noqa: BLE001
                pass
    return {
        "ok": has_video and has_audio and path.stat().st_size > 50_000,
        "has_video": has_video,
        "has_audio": has_audio,
        "duration_sec": round(dur, 2),
        "bytes": path.stat().st_size,
    }


def main() -> dict:
    print("=== FULL SYSTEM BENCHMARK ===", flush=True)
    if not find_ffmpeg():
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # SEO-informed keywords (evidence-backed extraction, not fake scores)
    # SEO-informed keywords (lazy import avoids engine bootstrap cycle in scripts)
    from services.seo.keywords import build_keyword_package, flatten_keywords

    kw_pkg = build_keyword_package(TOPIC, hook=HOOK, script=MAIN_CONCEPT, niche="biology")
    seo_keywords = flatten_keywords(kw_pkg, limit=8)
    seo_evidence = {"method": "build_keyword_package", "keywords": seo_keywords, "package_id": kw_pkg.get("package_id")}

    edu = review_lesson(
        hook=HOOK,
        script=" ".join(b["text"] for b in BEATS),
        takeaway=TAKEAWAY,
        main_concept=MAIN_CONCEPT,
        beats=BEATS,
        has_visual_demo=True,
        sources=["generational_biology_curriculum"],
    )
    if not edu.passed:
        raise SystemExit(f"Educational Director blocked: {edu.hard_fails}")

    voice = REPORT_DIR / "narration.mp3"
    print("  TTS + pauses…", flush=True)
    _, dur = build_paused_narration(BEATS, voice, ffmpeg=find_ffmpeg(), voice="nova", model="tts-1-hd")

    fp = fingerprint_inputs({"topic": TOPIC, "beats": BEATS, "demo": "fluid_cells"})
    booster = RepetitionBooster()
    cached = booster.lookup(fp)

    mp4 = REPORT_DIR / "episode.mp4"
    t0 = time.perf_counter()
    render = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=24,
        bg_color=(232, 238, 244),
        demo_id="fluid_cells",
        educator_mode=True,
        max_duration_sec=40.0,
        spec=StickFigureSpec(name="Generational Professor"),
    )
    render_sec = round(time.perf_counter() - t0, 2)
    qc = render.get("qc") or {}

    export_path = EXPORT_DIR / FILENAME
    if export_path.exists():
        export_path = EXPORT_DIR / FILENAME.replace(".mp4", "_v2.mp4")
    shutil.copy2(mp4, export_path)
    verification = verify_mp4(export_path)

    quality = score_production(
        {
            "export_path": str(export_path),
            "export_bytes": export_path.stat().st_size,
            "qc": qc,
            "hook": HOOK,
            "script": {"hook": HOOK, "takeaway": TAKEAWAY},
            "educational_review": edu.to_dict(),
        }
    )

    booster.record(
        fingerprint=fp,
        asset_type="benchmark_video",
        uri=str(export_path),
        approved=quality.passed and verification.get("ok"),
        metadata={"cache_hit": bool(cached), "render_sec": render_sec},
    )

    report = {
        "project": "Full System Benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": TOPIC,
        "seo": seo_evidence,
        "educational_review": edu.to_dict(),
        "render": {
            "ok": render.get("ok"),
            "duration_sec": render.get("duration_sec"),
            "render_time_sec": render_sec,
            "cache_prior": bool(cached),
            "fingerprint": fp,
        },
        "qc": qc,
        "quality": quality.to_dict(),
        "verification": verification,
        "export_path": str(export_path),
        "success": bool(
            render.get("ok")
            and qc.get("passed")
            and verification.get("ok")
            and quality.passed
        ),
    }
    (REPORT_DIR / "FULL_SYSTEM_BENCHMARK_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("success", "export_path", "verification", "quality")}, indent=2), flush=True)
    if not report["success"]:
        raise SystemExit("Benchmark did not pass all gates")
    print(f"\n=== READY → {export_path} ===", flush=True)
    return report


if __name__ == "__main__":
    main()
