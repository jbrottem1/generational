"""Produce 3 Dash stick-figure Shorts about fun science experiments worldwide.

Export finished MP4s only to:
  ~/Desktop/AI Start-up/videos/stick test/
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.asset_production import final_export as fe
from services.asset_production import visual_story as vs
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "stick_experiments_3"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = Path.home() / "Desktop" / "AI Start-up" / "videos" / "stick test"
fe.FINAL_EXPORT_DIR = EXPORT_DIR


def _export_filename(title: str, *, when: datetime | None = None) -> str:
    stamp = (when or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stamp}_StickScience_{fe.sanitize_title(title)}"


fe.build_export_filename = _export_filename  # type: ignore[assignment]

PROMPT_LOCK = json.loads(
    (ROOT / "data" / "universe" / "characters" / "CHAR-DASH" / "prompt_lock.json").read_text(
        encoding="utf-8"
    )
)
DASH_POSITIVE = PROMPT_LOCK["positive_lock"]
DASH_NEGATIVE = PROMPT_LOCK["negative_lock"]

_ORIG_CINEMATIC = vs._cinematic_prompt


def _dash_cinematic_prompt(scene: dict, *, niche: str, title: str) -> str:
    """Force Dash stick-figure host into every generated frame (sprint-only)."""
    base = _ORIG_CINEMATIC(scene, niche=niche, title=title)
    return (
        f"{DASH_POSITIVE}. "
        f"Dash is the energetic stick-figure host interacting with the science experiment on screen. "
        f"Smooth modern 2D animation still, soft gradient background with subtle particles — never flat solid. "
        f"Scene: {base} "
        f"Avoid: {DASH_NEGATIVE}"
    )


vs._cinematic_prompt = _dash_cinematic_prompt  # type: ignore[assignment]

# Also bias niche style string used inside prompts.
_ORIG_NICHE = vs._niche_style


def _dash_niche_style(niche: str) -> str:
    return (
        "original educational stick-figure animation featuring Dash mascot, "
        "clean black outline white fill oversized expressive eyes, "
        "energetic teaching motion, soft gradient environments, "
        f"fun science experiment demo style ({_ORIG_NICHE(niche)})"
    )


vs._niche_style = _dash_niche_style  # type: ignore[assignment]

TOPICS = [
    {
        "asset_id": "stick_mentos_geyser_001",
        "title": "The Mentos Geyser Experiment",
        "hook": "Drop Mentos in soda and — boom — a geyser shoots sky-high.",
        "description": (
            "Stick-figure host Dash demonstrates the Mentos and diet soda geyser, a classic "
            "science demo performed at festivals and classrooms worldwide. Explain nucleation: "
            "rough candy surface + dissolved CO2 → rapid bubble growth → fountain. Keep accurate, "
            "fun, and safe (outdoor demo framing). Visual style: Dash stick figure reacting, "
            "pointing, and celebrating beside the geyser."
        ),
        "hashtags": ["#DashScience", "#ScienceExperiment", "#Mentos", "#Shorts", "#FunScience"],
        "keywords": ["Mentos geyser", "nucleation", "soda fountain experiment"],
        "cta": "Follow for more stick-figure science experiments",
        "niche": "science",
        "music_style": "playful explosive curiosity",
        "thumbnail_concept": "Dash shocked beside soda geyser, stick figure, 9:16",
    },
    {
        "asset_id": "stick_elephant_toothpaste_001",
        "title": "Elephant Toothpaste Explained",
        "hook": "This foam tower looks like giant toothpaste — and chemistry makes it erupt.",
        "description": (
            "Dash explains elephant toothpaste: catalyzed decomposition of hydrogen peroxide "
            "(often iodide or yeast catalyst) producing oxygen that inflates dish soap foam. "
            "Popular in science museums and classrooms around the world. Emphasize adult "
            "supervision / safety for concentrated peroxide. Stick-figure Dash climbs, points, "
            "and panics-comedically at the rising foam column."
        ),
        "hashtags": ["#DashScience", "#ElephantToothpaste", "#Chemistry", "#Shorts", "#STEM"],
        "keywords": ["elephant toothpaste", "hydrogen peroxide", "catalyst foam"],
        "cta": "Follow Dash for chemistry that looks like magic",
        "niche": "science",
        "music_style": "bubbly rising synth comedy",
        "thumbnail_concept": "Dash next to towering colorful foam, stick figure, 9:16",
    },
    {
        "asset_id": "stick_oobleck_001",
        "title": "The Weird Science of Oobleck",
        "hook": "This goo is liquid and solid at the same time — and you can punch it.",
        "description": (
            "Dash explores oobleck (cornstarch + water), a non-Newtonian fluid demonstrated in "
            "science centers worldwide. Explain shear thickening: soft when poured, firm when "
            "struck. Show Dash walking/punching comedy beats. Accurate, playful, no overclaims."
        ),
        "hashtags": ["#DashScience", "#Oobleck", "#Physics", "#NonNewtonian", "#Shorts"],
        "keywords": ["oobleck", "non-Newtonian fluid", "cornstarch experiment"],
        "cta": "Follow for weird experiments that feel like magic",
        "niche": "science",
        "music_style": "bouncy curious physics",
        "thumbnail_concept": "Dash punching oobleck puddle, stick figure, 9:16",
    },
]


def run_one(topic: dict, index: int) -> dict:
    project = {
        "name": f"Dash Stick — {topic['title']}",
        "model": "gpt-4o-mini",
        "niche": "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }
    t0 = time.perf_counter()

    def on_progress(event: dict) -> None:
        print(
            f"  [{index}/3][{event.get('status')}] {event.get('label')}: {event.get('message')}",
            flush=True,
        )

    print(f"\n=== STICK EXPERIMENT {index}/3: {topic['title']} ===", flush=True)
    try:
        result = run_asset_production(topic, project, on_progress=on_progress, max_images=6)
    except Exception as exc:  # noqa: BLE001
        result = {
            **topic,
            "production_ok": False,
            "production_error": str(exc),
            "traceback": traceback.format_exc(),
        }

    elapsed = round(time.perf_counter() - t0, 2)
    render = result.get("render_package") or {}
    qc = result.get("production_qc") or {}
    assembly = render.get("assembly") if isinstance(render.get("assembly"), dict) else {}
    export_path = result.get("final_export_path") or qc.get("final_export_path") or ""
    success = bool(
        result.get("production_ok")
        and qc.get("passed")
        and export_path
        and Path(export_path).exists()
        and Path(export_path).stat().st_size > 500
        and not render.get("mock", True)
        and int(assembly.get("visual_count") or 0) >= 1
    )
    report = {
        "run_index": index,
        "title": topic["title"],
        "asset_id": topic["asset_id"],
        "success": success,
        "status": "READY_TO_POST" if success else "FAILED",
        "qc_score": qc.get("score"),
        "visual_count": assembly.get("visual_count"),
        "video_duration_sec": assembly.get("duration_sec") or render.get("duration_sec"),
        "final_export_path": export_path,
        "export_confirmed": bool(export_path and Path(export_path).exists()),
        "wall_runtime_sec": elapsed,
        "error": result.get("production_error") or "",
    }
    (REPORT_DIR / f"run_{index:02d}_{topic['asset_id']}.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print(
        f"  RESULT status={report['status']} qc={report['qc_score']} "
        f"visuals={report['visual_count']} export={report['export_confirmed']} t={elapsed}s",
        flush=True,
    )
    return report


def main() -> dict:
    print("=== STICK EXPERIMENTS 3 PREFLIGHT ===", flush=True)
    print("ffmpeg", ffmpeg_available(), flush=True)
    print("openai", has_credential("OPENAI_API_KEY"), flush=True)
    print("export_dir", EXPORT_DIR, flush=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    if not ffmpeg_available():
        raise SystemExit("ffmpeg required")

    batch_t0 = time.perf_counter()
    runs = [run_one(topic, i) for i, topic in enumerate(TOPICS, start=1)]
    ok = [r for r in runs if r.get("success")]
    agg = {
        "report_type": "Stick Figure Science Experiments — 3 Shorts",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_directory": str(EXPORT_DIR),
        "character": "CHAR-DASH",
        "requested": 3,
        "completed_ready_to_post": len(ok),
        "batch_runtime_sec": round(time.perf_counter() - batch_t0, 2),
        "sprint_complete": len(ok) == 3,
        "videos": runs,
    }
    (REPORT_DIR / "STICK_EXPERIMENTS_3_REPORT.json").write_text(
        json.dumps(agg, indent=2, default=str), encoding="utf-8"
    )
    print("\n=== STICK EXPERIMENTS 3 COMPLETE ===", flush=True)
    print("ready_to_post", len(ok), "/3", flush=True)
    print("export_dir", EXPORT_DIR, flush=True)
    return agg


if __name__ == "__main__":
    main()
