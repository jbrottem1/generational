#!/usr/bin/env python3
"""Promote validated local episode.mp4 files into the canonical Media Library.

Does not re-render. Copies verified worktree exports into:
  ~/Desktop/AI Start-Up/Videos/{Category}/

Usage:
  ./venv/bin/python scripts/migrate_validated_to_media_library.py
  ./venv/bin/python scripts/migrate_validated_to_media_library.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.generational_os.export import export_verified_production

VALIDATION = ROOT / "data" / "productions" / "_validation"

# Highest-value verified productions stranded outside the categorized library.
CATALOG: list[dict] = [
    {
        "project_id": "f_equals_ma",
        "source": VALIDATION / "project_foundation" / "f_equals_ma" / "episode.mp4",
        "filename": "Physics_001_F_Equals_MA_ES001b.mp4",
        "domain": "Physics",
        "series": "Foundation Physics",
        "episode": "001",
        "title": "What Does F = ma Actually Mean?",
        "topic": "F equals ma",
        "demo_id": "foundation_f_equals_ma",
        "keywords": ["newton", "force", "mass", "acceleration", "physics"],
        "qc_score": 79.3,
    },
    {
        "project_id": "force_mass",
        "source": VALIDATION / "project_foundation" / "force_mass" / "episode.mp4",
        "filename": "Physics_002_Force_and_Mass.mp4",
        "domain": "Physics",
        "series": "Foundation Physics",
        "episode": "002",
        "title": "Why Does a Heavy Object Need More Force?",
        "topic": "Force and Mass",
        "demo_id": "foundation_force_mass",
        "keywords": ["newton", "force", "mass", "inertia", "physics"],
    },
    {
        "project_id": "newton_everyday",
        "source": VALIDATION / "project_foundation" / "newton_everyday" / "episode.mp4",
        "filename": "Physics_003_Newtons_Second_Law.mp4",
        "domain": "Physics",
        "series": "Foundation Physics",
        "episode": "003",
        "title": "How Newton's Second Law Explains Everyday Life",
        "topic": "Newtons Second Law",
        "demo_id": "foundation_newton_everyday",
        "keywords": ["newton", "everyday", "force", "physics"],
    },
    {
        "project_id": "batesian_101",
        "source": VALIDATION / "biology_batesian" / "batesian_101" / "episode.mp4",
        "filename": "Biology_101_Batesian_Mimicry.mp4",
        "domain": "Biology",
        "series": "Batesian Mimicry",
        "episode": "101",
        "title": "Batesian Mimicry",
        "topic": "Batesian Mimicry",
        "demo_id": "foundation_batesian_101",
        "keywords": ["mimicry", "evolution", "hoverfly", "biology"],
    },
    {
        "project_id": "coral_102",
        "source": VALIDATION / "biology_batesian" / "coral_102" / "episode.mp4",
        "filename": "Biology_102_Coral_Snake_Imposters.mp4",
        "domain": "Biology",
        "series": "Batesian Mimicry",
        "episode": "102",
        "title": "Coral Snake Imposters",
        "topic": "Coral Snake Imposters",
        "demo_id": "foundation_coral_102",
        "keywords": ["mimicry", "coral snake", "biology"],
    },
    {
        "project_id": "bluffing_103",
        "source": VALIDATION / "biology_batesian" / "bluffing_103" / "episode.mp4",
        "filename": "Biology_103_Masters_of_Bluffing.mp4",
        "domain": "Biology",
        "series": "Batesian Mimicry",
        "episode": "103",
        "title": "Masters of Bluffing",
        "topic": "Masters of Bluffing",
        "demo_id": "foundation_bluffing_103",
        "keywords": ["mimicry", "bluffing", "biology"],
    },
    {
        "project_id": "confirmation_bias",
        "source": VALIDATION / "psychology_test" / "confirmation_bias" / "episode.mp4",
        "filename": "Psychology_001_Confirmation_Bias.mp4",
        "domain": "Psychology",
        "series": "Psychology Foundations",
        "episode": "001",
        "title": "Confirmation Bias",
        "topic": "Confirmation Bias",
        "demo_id": "foundation_confirmation_bias",
        "keywords": ["bias", "psychology", "cognition"],
    },
]


def migrate_one(item: dict, *, dry_run: bool) -> dict:
    source = Path(item["source"])
    payload = {
        "project_id": item["project_id"],
        "source": str(source),
        "exists": source.is_file(),
        "bytes": source.stat().st_size if source.is_file() else 0,
    }
    if not source.is_file():
        return {**payload, "ok": False, "error": "source missing"}
    if dry_run:
        return {**payload, "ok": True, "dry_run": True, "would_export": item["filename"]}

    result = export_verified_production(
        source,
        project_id=item["project_id"],
        filename=item["filename"],
        domain=item["domain"],
        subject=item["title"],
        title=item["title"],
        series=item["series"],
        episode=item["episode"],
        topic=item["topic"],
        demo_id=item.get("demo_id") or "",
        keywords=list(item.get("keywords") or []),
        qc_score=item.get("qc_score"),
        reveal_finder=False,
        print_completion=True,
    )
    return {
        **payload,
        "ok": bool(result.get("ok")),
        "final_status": result.get("final_status"),
        "export_path": result.get("export_path"),
        "domain_folder": result.get("domain_folder") or result.get("category"),
        "error": result.get("error"),
        "completion": result.get("completion"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Limit to project_id (repeatable)",
    )
    args = parser.parse_args()

    selected = CATALOG
    if args.only:
        wanted = set(args.only)
        selected = [c for c in CATALOG if c["project_id"] in wanted]

    results = [migrate_one(item, dry_run=args.dry_run) for item in selected]
    report = {
        "ok": all(r.get("ok") for r in results),
        "dry_run": args.dry_run,
        "migrated": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "results": results,
    }
    out = VALIDATION / "media_library_migration" / "MIGRATION_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nReport: {out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
