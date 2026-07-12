"""Weird Science Facts sprint — 5 ready-to-post Shorts.

Uses existing run_asset_production. Redirects final export only to:
  ~/Desktop/AI Start-up/videos/Test run 2 generational/
Filename: YYYY-MM-DD_HH-MM-SS_WeirdScienceFact_Title.mp4
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
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "weird_science_5"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = (
    Path.home()
    / "Desktop"
    / "AI Start-up"
    / "videos"
    / "Test run 2 generational"
)

# Redirect export destination + filename convention for this sprint only.
fe.FINAL_EXPORT_DIR = EXPORT_DIR


def _sprint_export_filename(title: str, *, when: datetime | None = None) -> str:
    stamp = (when or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stamp}_WeirdScienceFact_{fe.sanitize_title(title)}"


fe.build_export_filename = _sprint_export_filename  # type: ignore[assignment]

TOPICS = [
    {
        "asset_id": "ws5_zombie_ants_001",
        "title": "The Fungus That Turns Ants Into Zombies",
        "hook": "A fungus can hijack an ant's body — and force it to climb to its death.",
        "description": (
            "Explain Ophiocordyceps (cordyceps) infection of carpenter ants: behavioral "
            "manipulation, death grip on vegetation, spore release. Ground in peer-reviewed "
            "entomology / parasitology (e.g., Hughes lab and related Ophiocordyceps research). "
            "Do not claim mind-control of humans. Keep scientifically accurate and vivid."
        ),
        "hashtags": ["#WeirdScience", "#cordyceps", "#biology", "#shorts"],
        "keywords": ["Ophiocordyceps", "zombie ant fungus", "parasite behavior"],
        "cta": "Follow for more weird science that is actually true",
        "niche": "science",
        "music_style": "eerie forest documentary",
        "thumbnail_concept": "ant on leaf with fungal stalks, cinematic macro",
        "sources": [
            "Peer-reviewed Ophiocordyceps / carpenter ant behavioral manipulation literature",
            "University entomology summaries of zombie-ant fungus life cycle",
        ],
    },
    {
        "asset_id": "ws5_octopus_rna_001",
        "title": "Octopuses Can Edit Their Own RNA",
        "hook": "Octopuses rewrite genetic messages after DNA is transcribed — and that is rare.",
        "description": (
            "Explain RNA editing (A-to-I) in cephalopods: extensive recoding of neural transcripts. "
            "Cite cephalopod RNA-editing research (e.g., Rosenthal / Liscovitch-Brauer line of work "
            "in Nature/Cell-adjacent literature). Clarify this is RNA editing, not rewriting DNA. "
            "Mark evolutionary trade-offs carefully; no sci-fi overclaims."
        ),
        "hashtags": ["#WeirdScience", "#octopus", "#genetics", "#shorts"],
        "keywords": ["octopus RNA editing", "cephalopod genetics", "A-to-I editing"],
        "cta": "Follow for biology that sounds fake but isn't",
        "niche": "science",
        "music_style": "curious underwater pulse",
        "thumbnail_concept": "octopus and glowing RNA strands, scientific cinematic",
        "sources": [
            "Cephalopod RNA editing studies (Nature / related peer-reviewed work)",
            "Reviews on A-to-I RNA editing in neural transcripts",
        ],
    },
    {
        "asset_id": "ws5_triple_point_001",
        "title": "Water Can Boil and Freeze at the Same Time",
        "hook": "At one exact pressure and temperature, ice, liquid, and vapor coexist.",
        "description": (
            "Explain the triple point of water (~273.16 K at ~611.657 Pa): solid, liquid, and gas "
            "in equilibrium. Educational physics — not a kitchen trick claim. Ground in standard "
            "thermodynamics / NIST-style physical constants education. Avoid implying everyday "
            "conditions achieve this without vacuum apparatus."
        ),
        "hashtags": ["#WeirdScience", "#physics", "#water", "#shorts"],
        "keywords": ["triple point of water", "phase diagram", "thermodynamics"],
        "cta": "Follow for physics that breaks your intuition",
        "niche": "science",
        "music_style": "precise crystalline ambient",
        "thumbnail_concept": "ice water vapor coexistence diagram cinematic",
        "sources": [
            "Standard thermodynamics / phase diagram education",
            "NIST and textbook definitions of the water triple point",
        ],
    },
    {
        "asset_id": "ws5_immortal_jellyfish_001",
        "title": "The Jellyfish That Can Reverse Aging",
        "hook": "Turritopsis dohrnii can turn adults back into polyps — a rare biological reset.",
        "description": (
            "Explain transdifferentiation / life-cycle reversal in Turritopsis dohrnii (immortal "
            "jellyfish). Note it is not invincible: predation and disease still kill individuals. "
            "Ground in marine biology literature on life-cycle reversal. Avoid claiming human "
            "immortality applications."
        ),
        "hashtags": ["#WeirdScience", "#jellyfish", "#biology", "#shorts"],
        "keywords": ["Turritopsis dohrnii", "immortal jellyfish", "transdifferentiation"],
        "cta": "Follow for ocean science that surprises",
        "niche": "science",
        "music_style": "ethereal ocean ambient",
        "thumbnail_concept": "jellyfish lifecycle loop, glowing polyps, cinematic",
        "sources": [
            "Peer-reviewed and university marine biology summaries of Turritopsis dohrnii",
            "Literature on medusa-to-polyp life-cycle reversal",
        ],
    },
    {
        "asset_id": "ws5_banana_radiation_001",
        "title": "Why Bananas Are Naturally Radioactive",
        "hook": "Every banana emits a tiny bit of radiation — and that is completely normal.",
        "description": (
            "Explain potassium-40 naturally present in bananas and the informal 'banana equivalent "
            "dose' teaching concept. Emphasize levels are tiny and not a health scare. Ground in "
            "basic nuclear literacy / health physics education (EPA/CDC-style framing). No fearmongering."
        ),
        "hashtags": ["#WeirdScience", "#physics", "#bananas", "#shorts"],
        "keywords": ["banana equivalent dose", "potassium-40", "natural radioactivity"],
        "cta": "Follow for weird science without the panic",
        "niche": "science",
        "music_style": "playful curious science",
        "thumbnail_concept": "banana with subtle radiation motif, clean educational",
        "sources": [
            "Health physics education on potassium-40 in food",
            "Public science explainers of banana equivalent dose (teaching metaphor)",
        ],
    },
]


def run_one(topic: dict, index: int) -> dict:
    project = {
        "name": f"Weird Science — {topic['title']}",
        "model": "gpt-4o-mini",
        "niche": "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }
    t0 = time.perf_counter()

    def on_progress(event: dict) -> None:
        print(
            f"  [{index}/5][{event.get('status')}] {event.get('label')}: {event.get('message')}",
            flush=True,
        )

    print(f"\n=== WEIRD SCIENCE {index}/5: {topic['title']} ===", flush=True)
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
    mp4 = render.get("mp4_path") or ""
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
        "sources_consulted": topic.get("sources") or [],
        "runtime_sec_wall": elapsed,
        "video_duration_sec": (assembly.get("duration_sec") or render.get("duration_sec") or qc.get("duration_sec")),
        "production_ok": bool(result.get("production_ok")),
        "production_error": result.get("production_error") or "",
        "success": success,
        "qc_score": qc.get("score"),
        "qc_passed": qc.get("passed"),
        "visual_count": assembly.get("visual_count"),
        "color_bed": assembly.get("color_bed"),
        "mp4_path": mp4,
        "final_export_path": export_path,
        "export_confirmed": bool(export_path and Path(export_path).exists()),
        "export_bytes": Path(export_path).stat().st_size if export_path and Path(export_path).exists() else 0,
        "status": "READY_TO_POST" if success else "FAILED",
    }
    out = REPORT_DIR / f"run_{index:02d}_{topic['asset_id']}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        f"  RESULT status={report['status']} qc={qc.get('score')} "
        f"visuals={assembly.get('visual_count')} export={report['export_confirmed']} "
        f"t={elapsed}s",
        flush=True,
    )
    return report


def main() -> dict:
    print("=== WEIRD SCIENCE 5 PREFLIGHT ===", flush=True)
    print("ffmpeg", ffmpeg_available(), flush=True)
    print("openai", has_credential("OPENAI_API_KEY"), flush=True)
    print("export_dir", EXPORT_DIR, flush=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")
    if not ffmpeg_available():
        raise SystemExit("ffmpeg required")

    batch_t0 = time.perf_counter()
    runs = []
    for i, topic in enumerate(TOPICS, start=1):
        runs.append(run_one(topic, i))

    successes = [r for r in runs if r.get("success")]
    agg = {
        "report_type": "Weird Science Facts — 5 Ready-to-Post Shorts",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_directory": str(EXPORT_DIR),
        "requested": 5,
        "completed_ready_to_post": len(successes),
        "success_rate_percent": round(100.0 * len(successes) / max(len(runs), 1), 1),
        "batch_runtime_sec": round(time.perf_counter() - batch_t0, 2),
        "sprint_complete": len(successes) == 5,
        "videos": [
            {
                "title": r["title"],
                "scientific_sources_consulted": r["sources_consulted"],
                "wall_runtime_sec": r["runtime_sec_wall"],
                "video_duration_sec": r.get("video_duration_sec"),
                "quality_score": r.get("qc_score"),
                "qc_passed": r.get("qc_passed"),
                "visual_count": r.get("visual_count"),
                "export_confirmation": r.get("export_confirmed"),
                "file_location": r.get("final_export_path"),
                "production_status": r.get("status"),
            }
            for r in runs
        ],
        "failed": [r["title"] for r in runs if not r.get("success")],
    }
    json_path = REPORT_DIR / "WEIRD_SCIENCE_5_REPORT.json"
    json_path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")

    md = [
        "# Weird Science Facts — Completion Report",
        "",
        f"**Generated:** {agg['generated_at']}",
        f"**Ready-to-post:** {agg['completed_ready_to_post']}/5",
        f"**Export folder:** `{agg['export_directory']}`",
        f"**Sprint complete:** {agg['sprint_complete']}",
        "",
        "| # | Title | QC | Visuals | Status | File |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(runs, start=1):
        md.append(
            f"| {i} | {r['title']} | {r.get('qc_score')} | {r.get('visual_count')} | "
            f"{r.get('status')} | `{Path(r.get('final_export_path') or '').name}` |"
        )
    md.extend(["", "## Sources by video", ""])
    for r in runs:
        md.append(f"### {r['title']}")
        for s in r.get("sources_consulted") or []:
            md.append(f"- {s}")
        md.append("")
    (REPORT_DIR / "WEIRD_SCIENCE_5_REPORT.md").write_text("\n".join(md), encoding="utf-8")

    print("\n=== WEIRD SCIENCE 5 COMPLETE ===", flush=True)
    print("ready_to_post", agg["completed_ready_to_post"], "/5", flush=True)
    print("sprint_complete", agg["sprint_complete"], flush=True)
    print("report", json_path, flush=True)
    return agg


if __name__ == "__main__":
    main()
