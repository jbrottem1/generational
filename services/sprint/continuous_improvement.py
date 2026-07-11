"""6.5-hour continuous improvement sprint — cycle engine."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPRINT_DIR = ROOT / "data" / "productions" / "_validation" / "sprint_6h30"
EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "Test run 2 generational"
ECHOER_LOG = SPRINT_DIR / "echoer_log.jsonl"


@dataclass
class CycleConfig:
    """Per-cycle tunables — improved across sprint."""

    pause_boost: float = 0.0
    voice: str = "nova"
    tts_model: str = "tts-1-hd"
    blend_sec: float = 0.38


@dataclass
class CycleTopic:
    cycle: int
    slug: str
    title: str
    hook: str
    takeaway: str
    main_concept: str
    demo_id: str
    beats: list[dict[str, Any]]
    sources: list[str] = field(default_factory=list)


# Six biology Shorts + one synthesis — existing demos only
CYCLE_TOPICS: list[CycleTopic] = [
    CycleTopic(
        cycle=1,
        slug="dna_instructions",
        title="DNA Stores Life's Instructions",
        hook="Your body runs on a four-letter code.",
        takeaway="DNA is the instruction manual inside every cell.",
        main_concept="DNA sequence encodes biological instructions",
        demo_id="bio_dna",
        sources=["generational_biology_curriculum"],
        beats=[
            {"text": "Your body runs on a four-letter code.", "pause_after_sec": 0.65},
            {"text": "A, T, C, G — four letters. Infinite recipes.", "pause_after_sec": 0.55},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "This helix is DNA — the instruction manual of life.", "pause_after_sec": 0.70},
            {"text": "Same alphabet in you, an oak tree, and a fruit fly.", "pause_after_sec": 0.60},
            {"text": "Different sequences. Different organisms.", "pause_after_sec": 0.55},
            {"text": "DNA is the instruction manual inside every cell.", "pause_after_sec": 0.65},
        ],
    ),
    CycleTopic(
        cycle=2,
        slug="immune_recognition",
        title="How Your Immune System Recognizes Invaders",
        hook="Your body tags intruders like a security system.",
        takeaway="Immune cells match, tag, and remove what doesn't belong.",
        main_concept="Adaptive immune recognition",
        demo_id="bio_immune",
        sources=["generational_biology_curriculum"],
        beats=[
            {"text": "Your body tags intruders like a security system.", "pause_after_sec": 0.65},
            {"text": "White blood cells patrol constantly.", "pause_after_sec": 0.50},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "When they match an invader — they tag it.", "pause_after_sec": 0.65},
            {"text": "Other cells destroy the tagged threat.", "pause_after_sec": 0.55},
            {"text": "That's how you fight infection without friendly fire.", "pause_after_sec": 0.60},
            {"text": "Immune cells match, tag, and remove what doesn't belong.", "pause_after_sec": 0.65},
        ],
    ),
    CycleTopic(
        cycle=3,
        slug="muscle_growth",
        title="Why Muscles Grow After Exercise",
        hook="Lifting weights doesn't build muscle — recovery does.",
        takeaway="Stress, repair, grow — that's muscle adaptation.",
        main_concept="Muscle hypertrophy through damage and repair",
        demo_id="bio_muscle",
        sources=["generational_biology_curriculum"],
        beats=[
            {"text": "Lifting weights doesn't build muscle — recovery does.", "pause_after_sec": 0.70},
            {"text": "Exercise creates tiny tears in muscle fibers.", "pause_after_sec": 0.55},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "Your body repairs them — stronger than before.", "pause_after_sec": 0.65},
            {"text": "Protein and rest fuel the rebuild.", "pause_after_sec": 0.50},
            {"text": "Stress, repair, grow — that's muscle adaptation.", "pause_after_sec": 0.70},
        ],
    ),
    CycleTopic(
        cycle=4,
        slug="oxygen_journey",
        title="How Oxygen Reaches Your Cells",
        hook="What if every breath launched a delivery route?",
        takeaway="Air to lungs to blood to cells — oxygen fuels life.",
        main_concept="Respiratory and circulatory oxygen transport",
        demo_id="bio_oxygen",
        sources=["generational_biology_curriculum"],
        beats=[
            {"text": "What if every breath launched a delivery route?", "pause_after_sec": 0.70},
            {"text": "Oxygen enters your lungs — then your blood.", "pause_after_sec": 0.55},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "Red blood cells carry it to every tissue.", "pause_after_sec": 0.65},
            {"text": "Inside cells, oxygen helps release energy.", "pause_after_sec": 0.55},
            {"text": "Air to lungs to blood to cells — oxygen fuels life.", "pause_after_sec": 0.65},
        ],
    ),
    CycleTopic(
        cycle=5,
        slug="cell_building_blocks",
        title="You Are Made of Cells",
        hook="Did you know — you are not one thing?",
        takeaway="Life's unit is the cell.",
        main_concept="Cell as fundamental unit of life",
        demo_id="fluid_cells",
        sources=["generational_biology_curriculum"],
        beats=[
            {"text": "Did you know — you are not one thing?", "pause_after_sec": 0.70},
            {"text": "You are trillions of tiny living rooms.", "pause_after_sec": 0.55},
            {"text": "Watch.", "pause_after_sec": 0.50},
            {"text": "Each cell has a wall, a control center, and machinery.", "pause_after_sec": 0.65},
            {"text": "Trees. Whales. You. Same building blocks.", "pause_after_sec": 0.55},
            {"text": "Life's unit is the cell.", "pause_after_sec": 0.65},
        ],
    ),
    CycleTopic(
        cycle=6,
        slug="gravity_pull",
        title="Why Things Fall Down",
        hook="Drop anything — it falls. But why?",
        takeaway="Gravity pulls mass toward mass.",
        main_concept="Gravitational attraction toward Earth's center",
        demo_id="gravity_direction",
        sources=["generational_physics_curriculum"],
        beats=[
            {"text": "Drop anything — it falls. But why?", "pause_after_sec": 0.65},
            {"text": "It's not just 'down' — it's toward Earth's center.", "pause_after_sec": 0.55},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "Mass attracts mass. Earth is massive.", "pause_after_sec": 0.65},
            {"text": "You, the apple, the Moon — all pulled.", "pause_after_sec": 0.55},
            {"text": "Gravity pulls mass toward mass.", "pause_after_sec": 0.65},
        ],
    ),
    CycleTopic(
        cycle=7,
        slug="momentum_bowling",
        title="Momentum Keeps You Moving",
        hook="Why does a bowling ball keep rolling after you let go?",
        takeaway="Momentum is mass times velocity — and it persists.",
        main_concept="Conservation of momentum",
        demo_id="bowling_momentum",
        sources=["generational_physics_curriculum"],
        beats=[
            {"text": "Why does a bowling ball keep rolling after you let go?", "pause_after_sec": 0.70},
            {"text": "Heavy and fast means hard to stop.", "pause_after_sec": 0.50},
            {"text": "Watch.", "pause_after_sec": 0.45},
            {"text": "Momentum equals mass times velocity.", "pause_after_sec": 0.65},
            {"text": "More of either — more momentum.", "pause_after_sec": 0.55},
            {"text": "Momentum is mass times velocity — and it persists.", "pause_after_sec": 0.70},
        ],
    ),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_echoer(msg: dict[str, Any], resp: dict[str, Any] | None = None) -> None:
    SPRINT_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"at": _now_iso(), "message": msg, "response": resp}
    with ECHOER_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def verify_mp4(path: Path, ffmpeg: str) -> dict[str, Any]:
    if not path.exists() or not ffmpeg:
        return {"ok": False, "error": "missing file or ffmpeg"}
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


def unique_export(filename: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = EXPORT_DIR / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    ext = Path(filename).suffix
    v = 2
    while True:
        c = EXPORT_DIR / f"{stem}_v{v}{ext}"
        if not c.exists():
            return c
        v += 1


def run_cycle(
    topic: CycleTopic,
    config: CycleConfig,
    *,
    ffmpeg: str,
) -> dict[str, Any]:
    """One full improvement-loop cycle: produce → review → record."""
    from services.animation.communicator_delivery import build_paused_narration
    from services.animation.performer import render_lip_sync_performance
    from services.animation.stick_figure import StickFigureSpec
    from services.echoer.protocol import build_message, EchoerResponse
    from services.education.director_review import review_lesson
    from services.engagement.learning_science_director import (
        apply_recommendations_to_beats,
        LearningScienceDirector,
    )
    from services.gcis import write_review
    from services.quality.content_score import score_production

    cycle_dir = SPRINT_DIR / f"cycle_{topic.cycle:02d}_{topic.slug}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    beats = apply_recommendations_to_beats(
        topic.beats,
        [],
        pause_boost=config.pause_boost,
    )

    # Echoer: task to Agent 3/16/24
    task = build_message(
        msg_type="task",
        from_agent="0",
        to_agent="16",
        objective=f"Produce educator Short: {topic.title}",
        payload={"demo_id": topic.demo_id, "beats": len(beats)},
        cycle_id=str(topic.cycle),
        project_id=f"sprint6h30_{topic.slug}",
    )
    log_echoer(task.to_dict())

    t0 = time.perf_counter()
    voice = cycle_dir / "narration.mp3"
    _, _ = build_paused_narration(
        beats, voice, ffmpeg=ffmpeg, voice=config.voice, model=config.tts_model
    )

    mp4 = cycle_dir / "episode.mp4"
    render = render_lip_sync_performance(
        audio_path=voice,
        output_path=mp4,
        fps=24,
        bg_color=(232, 238, 244),
        demo_id=topic.demo_id,
        educator_mode=True,
        max_duration_sec=40.0,
        spec=StickFigureSpec(name="Generational Professor"),
    )
    render_sec = round(time.perf_counter() - t0, 2)
    qc = render.get("qc") or {}

    safe_title = topic.title.replace(" ", "_").replace("'", "")[:40]
    export_name = f"Sprint6h30_C{topic.cycle:02d}_{safe_title}.mp4"
    export_path = unique_export(export_name)
    shutil.copy2(mp4, export_path)
    verification = verify_mp4(export_path, ffmpeg)

    edu = review_lesson(
        hook=topic.hook,
        script=" ".join(b["text"] for b in beats),
        takeaway=topic.takeaway,
        main_concept=topic.main_concept,
        beats=beats,
        has_visual_demo=True,
        sources=topic.sources,
    )

    aels = LearningScienceDirector().review(
        hook=topic.hook,
        beats=beats,
        takeaway=topic.takeaway,
        duration_sec=float(render.get("duration_sec") or verification.get("duration_sec") or 0),
        qc=qc,
        has_visual_demo=True,
    )

    quality = score_production(
        {
            "export_path": str(export_path),
            "export_bytes": export_path.stat().st_size,
            "qc": qc,
            "hook": topic.hook,
            "script": {"hook": topic.hook, "takeaway": topic.takeaway},
            "educational_review": edu.to_dict(),
        }
    )

    success = bool(
        render.get("ok")
        and qc.get("passed")
        and verification.get("ok")
        and edu.passed
    )

    resp = EchoerResponse(
        in_reply_to=task.msg_id,
        from_agent="16",
        status="ok" if success else "partial",
        summary=f"Cycle {topic.cycle} {'PASS' if success else 'PARTIAL'}: {topic.title}",
        data={
            "export_path": str(export_path),
            "duration_sec": render.get("duration_sec"),
            "quality_overall": quality.overall,
            "aels_engagement": aels.engagement_score,
            "edu_score": edu.score,
        },
        evidence={"verification": verification, "qc": qc},
        duration_sec=render_sec,
    )
    log_echoer(task.to_dict(), resp.to_dict())

    review_payload = {
        "production": f"Sprint 6h30 Cycle {topic.cycle}",
        "title": topic.title,
        "slug": topic.slug,
        "export_path": str(export_path),
        "success": success,
        "scores": {
            "quality_overall": quality.overall,
            "education": edu.score,
            "engagement": aels.engagement_score,
            "retention": aels.retention_score,
            "animation_qc": qc.get("passed"),
        },
        "aels": aels.to_dict(),
        "educational_review": edu.to_dict(),
        "quality": quality.to_dict(),
        "self_review": aels.self_review,
        "recommendations": aels.recommendations,
        "render_time_sec": render_sec,
    }
    write_review(f"2026-07-11_sprint6h30_cycle{topic.cycle:02d}_{topic.slug}", review_payload)
    (cycle_dir / "CYCLE_REPORT.json").write_text(json.dumps(review_payload, indent=2), encoding="utf-8")

    return {
        "cycle": topic.cycle,
        "slug": topic.slug,
        "success": success,
        "export_path": str(export_path),
        "quality_overall": quality.overall,
        "aels_engagement": aels.engagement_score,
        "edu_score": edu.score,
        "recommendations": aels.recommendations,
        "render_sec": render_sec,
        "review": review_payload,
    }


def next_config(prev: dict[str, Any] | None, config: CycleConfig) -> CycleConfig:
    """Apply validated improvements from previous cycle."""
    if not prev:
        return config
    recs = prev.get("recommendations") or []
    review = prev.get("review") or {}
    aels = review.get("aels") or {}
    pause_boost = config.pause_boost
    for rec in recs:
        if "pause" in rec.lower() or "silence" in rec.lower():
            pause_boost = min(pause_boost + 0.08, 0.35)
    if float(aels.get("hook_score") or 100) < 72:
        pause_boost = min(pause_boost + 0.05, 0.35)
    if float(aels.get("pacing_score") or 100) < 75:
        pause_boost = min(pause_boost + 0.05, 0.35)
    return CycleConfig(
        pause_boost=pause_boost,
        voice=config.voice,
        tts_model=config.tts_model,
        blend_sec=config.blend_sec,
    )
