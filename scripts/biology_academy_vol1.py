"""Generational Biology Academy — Biology Fundamentals Volume 1 (5 episodes).

Uses existing educator lip-sync performer + biology demo overlays.
Does not redesign the animation engine or production pipeline.
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

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "biology_academy_vol1"
SERIES_DIR = ROOT / "data" / "universe" / "series" / "biology_academy"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SERIES_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Biology Academy Test Run"

# Scientific framing notes (current consensus; educational simplification for Shorts)
# Cells: cell theory (Schleiden/Schwann/Virchow lineage) — all organisms composed of cells
# DNA: double helix (Watson/Crick/Franklin); genetic code A/T/C/G
# Immune: innate + adaptive; antigen recognition; antibodies; immunological memory
# Muscle: hypertrophy via mechanical tension / microtrauma → repair & protein synthesis
# Oxygen: pulmonary gas exchange → Hb-bound O2 → systemic delivery → cellular respiration

EPISODES = [
    {
        "ep": 1,
        "filename": "Biology_001_Cells.mp4",
        "title": "Why Every Living Thing Is Made of Cells",
        "demo_id": "bio_cells",
        "script": (
            "What are you made of? Zoom in. Past skin. Past tissue. "
            "You hit cells — tiny living units with a membrane, a control center, and working machinery. "
            "A tree is cells. A bacterium is a cell. A whale is trillions of them. "
            "Cells take in nutrients, make energy, and copy themselves. "
            "That's why biologists say: the cell is the basic unit of life. "
            "Remember this: if it's alive, it's built from cells."
        ),
    },
    {
        "ep": 2,
        "filename": "Biology_002_DNA.mp4",
        "title": "DNA: The Instruction Manual of Life",
        "demo_id": "bio_dna",
        "script": (
            "How does a cell know what to build? It reads DNA — life's instruction manual. "
            "DNA is a double helix: two twisted strands. "
            "Four letters — A, T, C, and G — spell the recipe in sequence. "
            "Same alphabet. Different books. You, an oak tree, a fruit fly — all written in DNA. "
            "Those instructions tell cells which proteins to make, and proteins do the work. "
            "Takeaway: DNA is the written code that runs living things."
        ),
    },
    {
        "ep": 3,
        "filename": "Biology_003_Immune_System.mp4",
        "title": "How Your Immune System Finds Invaders",
        "demo_id": "bio_immune",
        "script": (
            "Something doesn't belong in your body. How do you find it? "
            "Immune cells patrol like security — checking molecular IDs. "
            "When a match looks wrong, they tag the invader with antibodies. "
            "Then other cells destroy it — and some remember the shape for next time. "
            "That's why vaccines work: they train memory without the full fight. "
            "Find. Tag. Eliminate. That's your immune system."
        ),
    },
    {
        "ep": 4,
        "filename": "Biology_004_Muscle_Growth.mp4",
        "title": "Why Muscles Actually Grow",
        "demo_id": "bio_muscle",
        "script": (
            "Lift heavy. Muscle grows. But how? "
            "Training creates tiny controlled stress in muscle fibers — micro-damage. "
            "Your body repairs those fibers… and overbuilds them a little stronger. "
            "Rest and protein feed that repair signal. No recovery, no growth. "
            "So muscles don't grow during the workout — they grow after. "
            "Stress. Repair. Stronger. That's hypertrophy."
        ),
    },
    {
        "ep": 5,
        "filename": "Biology_005_Oxygen_Journey.mp4",
        "title": "The Amazing Journey of Oxygen Through Your Body",
        "demo_id": "bio_oxygen",
        "script": (
            "One breath. Where does the oxygen go? "
            "Into your lungs, across thin membranes, onto red blood cells. "
            "Your heart pumps that oxygen-rich blood out to every tissue. "
            "Cells grab the oxygen and use it to make energy — ATP. "
            "No oxygen delivery, no cellular power. "
            "Air to blood to cells to energy. That's the journey in one breath."
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


def produce_episode(ep: dict, index: int) -> dict:
    print(f"\n=== BIOLOGY {index}/5: {ep['title']} ===", flush=True)
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
        bg_color=(232, 238, 244),
        demo_id=ep["demo_id"],
        educator_mode=True,
        max_duration_sec=60.0,
        spec=StickFigureSpec(name="Stick Educator"),
    )
    elapsed = round(time.perf_counter() - t0, 2)
    qc = result.get("qc") or {}
    ok = bool(result.get("ok") and qc.get("passed"))
    print(
        f"  render ok={result.get('ok')} qc={qc.get('passed')} "
        f"purposeful={qc.get('purposeful_gestures')} idle={qc.get('idle_ratio')} "
        f"walk={qc.get('walk_ratio')} dur={result.get('duration_sec')} t={elapsed}s",
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
        "qc": {
            "passed": qc.get("passed"),
            "purposeful_gestures": qc.get("purposeful_gestures"),
            "idle_ratio": qc.get("idle_ratio"),
            "walk_ratio": qc.get("walk_ratio"),
            "gesture_counts": qc.get("gesture_counts"),
            "speaking_ratio": qc.get("speaking_ratio"),
        },
        "export_path": str(export_path),
        "export_bytes": export_path.stat().st_size,
        "render_time_sec": elapsed,
        "character_id": "CHAR-STICK-001",
        "teaching_method": "generational_method",
    }


def main() -> dict:
    print("=== GENERATIONAL BIOLOGY ACADEMY — VOLUME 1 ===", flush=True)
    if not find_ffmpeg():
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    (SERIES_DIR / "SERIES_BIBLE.md").write_text(
        "\n".join(
            [
                "# Generational Biology Academy",
                "",
                "**Collection:** Biology Fundamentals — Volume 1",
                "**Host:** CHAR-STICK-001 (Generational Educator)",
                "**Doctrine:** GENERATIONAL_METHOD.md",
                "**Style:** Purposeful teaching + lab demos (cells, DNA, immune, muscle, oxygen)",
                "**Tone:** Confident, curious, fast, memorable",
                "",
                "## Volume 1 episodes",
                "1. Why Every Living Thing Is Made of Cells",
                "2. DNA: The Instruction Manual of Life",
                "3. How Your Immune System Finds Invaders",
                "4. Why Muscles Actually Grow",
                "5. The Amazing Journey of Oxygen Through Your Body",
                "",
            ]
        ),
        encoding="utf-8",
    )

    batch_t0 = time.perf_counter()
    runs = [produce_episode(ep, i) for i, ep in enumerate(EPISODES, start=1)]

    ok = [r for r in runs if r.get("success")]
    report = {
        "series": "Generational Biology Academy",
        "collection": "Biology Fundamentals Volume 1",
        "series_id": "biology_academy_vol1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "character_id": "CHAR-STICK-001",
        "teaching_method": "generational_method",
        "requested": 5,
        "completed": len(ok),
        "success": len(ok) == 5,
        "batch_runtime_sec": round(time.perf_counter() - batch_t0, 2),
        "export_directory": str(EXPORT_DIR),
        "episodes": runs,
    }
    (REPORT_DIR / "BIOLOGY_ACADEMY_VOL1_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    lines = [
        "# Biology Fundamentals Volume 1 — Report",
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
    (REPORT_DIR / "BIOLOGY_ACADEMY_VOL1_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n=== BIOLOGY ACADEMY VOL1 COMPLETE ===", flush=True)
    print("completed", len(ok), "/5", flush=True)
    for r in runs:
        print(
            f"  {r.get('ep')}: {r.get('status') or 'FAILED'} → {r.get('export_path') or r.get('error')}",
            flush=True,
        )
    if len(ok) != 5:
        raise SystemExit("Not all episodes passed QC")
    return report


if __name__ == "__main__":
    main()
