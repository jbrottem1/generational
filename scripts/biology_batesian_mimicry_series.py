#!/usr/bin/env python3
"""Biology benchmark series — Batesian Mimicry (Curiosity Framework).

Three premium educational Shorts. No "Welcome back" openings.
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
from services.animation.foundation_gate import evaluate_foundation_export
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.education.director_review import review_lesson
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "biology_batesian"
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"

# Sources (teaching notes — not on-screen citations)
SOURCES = [
    "Bates (1862) / modern evolutionary biology consensus on Batesian mimicry",
    "University / museum herpetology guidance: do not use color rhymes as ID tools",
    "Monarch–viceroy: historically Batesian; modern work supports more complex (often Müllerian-like) relationship",
]

EPISODES = [
    {
        "id": "batesian_101",
        "filename": "Biology_101_Batesian_Mimicry.mp4",
        "title": "Masters of Deception: Batesian Mimicry",
        "demo_id": "foundation_batesian_101",
        "hook": "What if pretending to be dangerous could save your life?",
        "takeaway": "Safety by resemblance — Batesian mimicry.",
        "main_concept": "Batesian mimicry: harmless species resembles a harmful model",
        "beats": [
            {
                "text": "What if pretending to be dangerous could save your life?",
                "pause_after_sec": 0.55,
            },
            {
                "text": "In nature, some animals look deadly — but aren't.",
                "pause_after_sec": 0.45,
            },
            {
                "text": "By the end of this, you'll understand Batesian mimicry — and why it works.",
                "pause_after_sec": 0.45,
            },
            {"text": "Watch the board.", "pause_after_sec": 0.40},
            {
                "text": "A harmful model — like a stinging wasp — teaches predators: bright pattern means avoid.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "A harmless mimic — like some hoverflies — copies that look, without the sting.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "Predators that learned the hard way skip both. The mimic borrows protection.",
                "pause_after_sec": 0.50,
            },
            {
                "text": "You'll see the same idea in scarlet kingsnakes that resemble coral snakes.",
                "pause_after_sec": 0.50,
            },
            {
                "text": "Safety by resemblance. That's Batesian mimicry.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "Next — could you tell which snake is actually dangerous?",
                "pause_after_sec": 0.40,
            },
        ],
    },
    {
        "id": "coral_102",
        "filename": "Biology_102_Coral_Snake_Imposters.mp4",
        "title": "Can You Spot the Imposter?",
        "demo_id": "foundation_coral_102",
        "hook": "Could you tell which of these snakes is actually dangerous?",
        "takeaway": "Never handle an unknown snake.",
        "main_concept": "Coral snake vs scarlet kingsnake; warning colors; rhyme limitations",
        "beats": [
            {
                "text": "Could you tell which of these snakes is actually dangerous?",
                "pause_after_sec": 0.55,
            },
            {
                "text": "One is a venomous coral snake. The other is a scarlet kingsnake — a mimic.",
                "pause_after_sec": 0.50,
            },
            {
                "text": "You'll see why warning colors work — and why a popular rhyme can mislead you.",
                "pause_after_sec": 0.45,
            },
            {"text": "Watch.", "pause_after_sec": 0.35},
            {
                "text": "Bright bands advertise risk. Predators that learn from painful encounters learn to avoid the pattern.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "The kingsnake benefits by looking similar — classic Batesian mimicry.",
                "pause_after_sec": 0.50,
            },
            {
                "text": "But color rhymes about red and yellow have regional limits. They are not a universal identification tool.",
                "pause_after_sec": 0.60,
            },
            {
                "text": "Never handle an unknown snake. If you're unsure — leave it alone.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "Nature isn't always about strength. Sometimes it's about the bluff.",
                "pause_after_sec": 0.45,
            },
        ],
    },
    {
        "id": "bluffing_103",
        "filename": "Biology_103_Masters_of_Bluffing.mp4",
        "title": "Nature's Masters of Bluffing",
        "demo_id": "foundation_bluffing_103",
        "hook": "What if survival depended on convincing everyone you were something you're not?",
        "takeaway": "Sometimes survival belongs to the best deceiver.",
        "main_concept": "Additional Batesian examples; monarch–viceroy complexity; arms race",
        "beats": [
            {
                "text": "What if survival depended on convincing everyone you were something you're not?",
                "pause_after_sec": 0.55,
            },
            {
                "text": "Evolution has perfected that bluff again and again.",
                "pause_after_sec": 0.45,
            },
            {
                "text": "You'll meet more mimics — and a famous case science has revised.",
                "pause_after_sec": 0.45,
            },
            {"text": "Watch the board.", "pause_after_sec": 0.35},
            {
                "text": "Hoverflies and other bee mimics wear false warning colors — looking armed when they aren't.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "The monarch and viceroy were long taught as a simple Batesian pair. Modern research shows the relationship is more complex than originally believed.",
                "pause_after_sec": 0.65,
            },
            {
                "text": "Meanwhile, predators get better at spotting fakes — and prey refine the disguise. An evolutionary arms race.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "Nature isn't always about being the strongest. Sometimes survival belongs to the best deceiver.",
                "pause_after_sec": 0.55,
            },
            {
                "text": "If evolution can craft this illusion — imagine what else it has hidden in plain sight.",
                "pause_after_sec": 0.45,
            },
        ],
    },
]


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
        "bytes": path.stat().st_size if path.is_file() else 0,
        "has_video": "Video:" in text,
        "has_audio": "Audio:" in text,
    }


def produce(ep: dict) -> dict:
    work = REPORT_DIR / ep["id"]
    work.mkdir(parents=True, exist_ok=True)
    voice = work / "narration.mp3"
    episode = work / "episode.mp4"
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg missing", "id": ep["id"]}
    if not has_credential("OPENAI_API_KEY"):
        return {"ok": False, "error": "openai credentials missing", "id": ep["id"]}

    # Curiosity Framework guard
    first = str(ep["beats"][0]["text"]).lower()
    for banned in ("welcome back", "today we're going", "in this video", "today we are going"):
        if first.startswith(banned) or banned in first[:40]:
            return {"ok": False, "error": f"curiosity_framework_violation:{banned}", "id": ep["id"]}

    t0 = time.time()
    build_paused_narration(ep["beats"], voice, ffmpeg=ffmpeg, voice="nova", model="tts-1-hd")
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=episode,
        fps=24,
        bg_color=(255, 255, 255),
        demo_id=ep["demo_id"],
        educator_mode=True,
        max_duration_sec=60.0,
        spec=StickFigureSpec(
            character_id="CHAR-PROFESSOR-001",
            name="Professor Gen",
            attire="none",
        ),
    )
    qc = result.get("qc") or {}
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = unique_path(EXPORT_DIR, ep["filename"])
    if episode.exists():
        shutil.copy2(episode, export_path)
    verify = verify_mp4(export_path, ffmpeg)

    edu = review_lesson(
        hook=ep["hook"],
        script=" ".join(b["text"] for b in ep["beats"]),
        takeaway=ep["takeaway"],
        main_concept=ep["main_concept"],
        beats=ep["beats"],
        has_visual_demo=True,
        sources=SOURCES,
    )
    production = {
        "title": ep["title"],
        "demo_id": ep["demo_id"],
        "hook": ep["hook"],
        "takeaway": ep["takeaway"],
        "script": {
            "hook": ep["hook"],
            "takeaway": ep["takeaway"],
            "full_text": " ".join(b["text"] for b in ep["beats"]),
        },
        "duration_sec": result.get("duration_sec"),
        "character_id": "CHAR-PROFESSOR-001",
        "qc": qc,
        "export_path": str(export_path),
        "path": str(export_path),
        "bytes": export_path.stat().st_size if export_path.exists() else 0,
        "educational_review": edu.to_dict(),
        "framework": "generational_curiosity_framework",
        "sources": SOURCES,
    }
    gate = evaluate_foundation_export(
        production,
        script=production["script"],
        educational=production["educational_review"],
    )
    hard = gate.hard_fails or []
    ok = (
        bool(result.get("ok"))
        and bool(qc.get("passed"))
        and bool(verify.get("ok"))
        and "missing_export_path" not in hard
        and "animation_qc_failed" not in hard
        and not any(str(f).startswith("lipsync_below") for f in hard)
    )
    report = {
        "id": ep["id"],
        "title": ep["title"],
        "ok": ok,
        "export_path": str(export_path),
        "duration_sec": result.get("duration_sec"),
        "render_sec": round(time.time() - t0, 2),
        "qc": qc,
        "verify": verify,
        "foundation_gate": gate.to_dict(),
        "educational": edu.to_dict(),
        "quality_overall": gate.quality.overall if gate.quality else None,
        "error": result.get("error"),
    }
    (work / "REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None, help="Episode id to render")
    args = parser.parse_args(argv)

    print("=== Biology Benchmark — Batesian Mimicry (Curiosity Framework) ===", flush=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    selected = [e for e in EPISODES if args.only is None or e["id"] == args.only]
    results = []
    for ep in selected:
        print(f"\n--- {ep['title']} ---", flush=True)
        r = produce(ep)
        results.append(r)
        status = "✓" if r.get("ok") else "✗"
        print(
            f"  {status} {r.get('export_path')} "
            f"Q={r.get('quality_overall')} dur={r.get('duration_sec')}s",
            flush=True,
        )
    summary = {
        "series": "batesian_mimicry_biology_benchmark",
        "framework": "generational_curiosity_framework",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success_count": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "episodes": results,
        "sources": SOURCES,
    }
    out = REPORT_DIR / "BATESIAN_SERIES_REPORT.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md = REPORT_DIR / "BATESIAN_SERIES_REPORT.md"
    lines = [
        "# Batesian Mimicry Biology Benchmark",
        "",
        f"**Generated:** {summary['generated_at']}",
        f"**Success:** {summary['success_count']}/{summary['total']}",
        f"**Framework:** Generational Curiosity Framework",
        "",
    ]
    for r in results:
        lines.append(
            f"- **{r.get('title')}** — `{r.get('export_path')}` "
            f"(ok={r.get('ok')}, Q={r.get('quality_overall')}, {r.get('duration_sec')}s)"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n=== DONE {summary['success_count']}/{summary['total']} → {out} ===", flush=True)
    return 0 if summary["success_count"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
