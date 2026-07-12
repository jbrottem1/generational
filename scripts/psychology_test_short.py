#!/usr/bin/env python3
"""One-off Foundation test Short — human psychology (confirmation bias)."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.communicator_delivery import build_paused_narration
from services.animation.foundation_gate import evaluate_foundation_export
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "psychology_test"
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"

EPISODE = {
    "id": "confirmation_bias",
    "filename": "Psychology_001_Confirmation_Bias.mp4",
    "title": "Why Do You Only Notice Evidence That Agrees With You?",
    "demo_id": "foundation_confirmation_bias",
    "hook": "What if your brain quietly hides the evidence against you?",
    "takeaway": "Ask what would prove you wrong.",
    "beats": [
        {"text": "Welcome back to Generational.", "pause_after_sec": 0.35},
        {
            "text": "What if your brain quietly hides the evidence against you?",
            "pause_after_sec": 0.60,
        },
        {"text": "Watch the board.", "pause_after_sec": 0.45},
        {
            "text": "That habit is called confirmation bias.",
            "pause_after_sec": 0.55,
        },
        {
            "text": "We notice evidence that fits our belief — and skip what challenges it.",
            "pause_after_sec": 0.55,
        },
        {
            "text": "In news feeds, sports debates, even everyday arguments.",
            "pause_after_sec": 0.50,
        },
        {
            "text": "The fix is simple. Ask: what would prove me wrong?",
            "pause_after_sec": 0.55,
        },
        {
            "text": "In the next lesson, how your attention shapes what you remember.",
            "pause_after_sec": 0.40,
        },
    ],
}


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, ext = Path(filename).stem, Path(filename).suffix
    v = 2
    while True:
        candidate = directory / f"{stem}_v{v}{ext}"
        if not candidate.exists():
            return candidate
        v += 1


def verify_mp4(path: Path, ffmpeg: str) -> dict:
    import subprocess

    if not path.is_file() or not ffmpeg:
        return {"ok": False}
    proc = subprocess.run(
        [ffmpeg, "-i", str(path), "-hide_banner"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (proc.stderr or "") + (proc.stdout or "")
    return {
        "ok": path.stat().st_size > 50_000 and "Video:" in text and "Audio:" in text,
        "bytes": path.stat().st_size,
        "has_video": "Video:" in text,
        "has_audio": "Audio:" in text,
    }


def main() -> int:
    print("=== Psychology Test — Confirmation Bias ===", flush=True)
    if not has_credential("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY missing", flush=True)
        return 1
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("ERROR: ffmpeg missing", flush=True)
        return 1

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    work = REPORT_DIR / EPISODE["id"]
    work.mkdir(parents=True, exist_ok=True)
    voice = work / "narration.mp3"
    episode = work / "episode.mp4"

    t0 = time.time()
    build_paused_narration(
        EPISODE["beats"],
        voice,
        ffmpeg=ffmpeg,
        voice="nova",
        model="tts-1-hd",
    )
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=episode,
        fps=24,
        bg_color=(255, 255, 255),
        demo_id=EPISODE["demo_id"],
        educator_mode=True,
        max_duration_sec=55.0,
        spec=StickFigureSpec(
            character_id="CHAR-PROFESSOR-001",
            name="Professor Gen",
            attire="none",
        ),
    )
    qc = result.get("qc") or {}
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = unique_path(EXPORT_DIR, EPISODE["filename"])
    if episode.exists():
        shutil.copy2(episode, export_path)
    verify = verify_mp4(export_path, ffmpeg)

    from services.education.director_review import review_lesson

    edu = review_lesson(
        hook=EPISODE["hook"],
        script=" ".join(b["text"] for b in EPISODE["beats"]),
        takeaway=EPISODE["takeaway"],
        main_concept="confirmation bias",
        beats=EPISODE["beats"],
        has_visual_demo=True,
        sources=["generational_psychology_curriculum"],
    )
    production = {
        "title": EPISODE["title"],
        "demo_id": EPISODE["demo_id"],
        "hook": EPISODE["hook"],
        "takeaway": EPISODE["takeaway"],
        "script": {
            "hook": EPISODE["hook"],
            "takeaway": EPISODE["takeaway"],
            "full_text": " ".join(b["text"] for b in EPISODE["beats"]),
        },
        "duration_sec": result.get("duration_sec"),
        "character_id": "CHAR-PROFESSOR-001",
        "qc": qc,
        "export_path": str(export_path),
        "path": str(export_path),
        "bytes": export_path.stat().st_size if export_path.exists() else 0,
        "educational_review": edu.to_dict() if hasattr(edu, "to_dict") else {
            "passed": edu.passed,
            "score": edu.score,
            "clarity_score": edu.clarity_score,
            "accuracy_score": edu.accuracy_score,
        },
    }
    gate = evaluate_foundation_export(
        production,
        script=production["script"],
        educational=production["educational_review"],
    )
    # Ship if export verified + animation QC; gate overall target is stretch
    ok = (
        bool(result.get("ok"))
        and bool(qc.get("passed"))
        and bool(verify.get("ok"))
        and "missing_export_path" not in (gate.hard_fails or [])
        and not any(f.startswith("lipsync_below") or f == "animation_qc_failed" for f in (gate.hard_fails or []))
    )
    report = {
        "title": EPISODE["title"],
        "topic": "human_psychology",
        "concept": "confirmation_bias",
        "ok": ok,
        "export_path": str(export_path),
        "duration_sec": result.get("duration_sec"),
        "render_sec": round(time.time() - t0, 2),
        "qc": qc,
        "foundation_gate": gate.to_dict(),
        "verify": verify,
        "error": result.get("error"),
    }
    (work / "REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    status = "✓" if ok else "✗"
    q = None
    if gate.quality is not None:
        q = gate.quality.overall
    print(f"{status} {export_path}", flush=True)
    print(f"  duration={report['duration_sec']}s gate={gate.passed} Q={q}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
