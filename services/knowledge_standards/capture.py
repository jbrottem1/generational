"""Capture APIs for lessons and experiments (Agent 27)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from services.knowledge_standards.validation import (
    KnowledgeValidationError,
    validate_experiment,
    validate_lesson,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_STANDARDS_DIR = REPO_ROOT / "data" / "knowledge_standards"
EXPERIMENTS_PATH = KNOWLEDGE_STANDARDS_DIR / "experiments.json"
GCIS_LESSONS_PATH = REPO_ROOT / "data" / "gcis" / "knowledge" / "lessons_learned.md"
VALID_DECISIONS = frozenset({"keep", "discard", "iterate"})


def load_experiment_registry(path: Path | None = None) -> dict[str, Any]:
    """Load experiments.json registry."""
    p = path or EXPERIMENTS_PATH
    if not p.is_file():
        raise FileNotFoundError(f"Experiment registry not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "experiments" not in data:
        raise KnowledgeValidationError("Experiment registry missing 'experiments' list")
    if not isinstance(data["experiments"], list):
        raise KnowledgeValidationError("'experiments' must be a list")
    return data


def register_experiment(
    experiment: dict[str, Any],
    *,
    path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Validate and append an experiment to the registry.

    Returns the registered experiment payload. When dry_run=True, validates
    against current registry but does not write.
    """
    validate_experiment(experiment)
    registry = load_experiment_registry(path)
    existing_ids = {
        str(item.get("id", "")) for item in registry["experiments"] if isinstance(item, dict)
    }
    exp_id = str(experiment["id"])
    if exp_id in existing_ids:
        raise KnowledgeValidationError(f"Duplicate experiment id: {exp_id}")

    decision = str(experiment.get("decision", "")).lower()
    if decision not in VALID_DECISIONS:
        raise KnowledgeValidationError(
            f"decision must be one of {sorted(VALID_DECISIONS)}, got {experiment.get('decision')!r}"
        )

    entry = dict(experiment)
    entry["decision"] = decision
    if not dry_run:
        registry["experiments"].append(entry)
        registry["updated"] = date.today().isoformat()
        target = path or EXPERIMENTS_PATH
        target.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry


def record_lesson(
    title: str,
    *,
    source: str,
    what_worked: list[str] | None = None,
    what_failed: list[str] | None = None,
    standard: str | None = None,
    body: str | None = None,
    lessons_path: Path | None = None,
    dry_run: bool = False,
) -> str:
    """Append a lesson entry to the canonical GCIS lessons_learned.md.

    Prefer the GCIS path — Agent 27 indexes; does not maintain a parallel full log.
    Returns the markdown block that was (or would be) appended.
    """
    validate_lesson(title=title, source=source, body=body, what_worked=what_worked, what_failed=what_failed)

    today = date.today().isoformat()
    lines = [
        "",
        f"## {today} — {title.strip()}",
        "",
        f"**Source:** {source.strip()}",
        "",
    ]
    if what_worked:
        lines.append("### What worked")
        for item in what_worked:
            lines.append(f"- {item}")
        lines.append("")
    if what_failed:
        lines.append("### What failed")
        for item in what_failed:
            lines.append(f"- {item}")
        lines.append("")
    if standard:
        lines.append("### Standard")
        lines.append(f"- {standard.strip()}")
        lines.append("")
    if body and body.strip():
        lines.append(body.strip())
        lines.append("")

    block = "\n".join(lines)
    if not dry_run:
        target = lessons_path or GCIS_LESSONS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8") if target.is_file() else "# Lessons Learned (GCIS)\n"
        # Newest-first: insert after the first heading block if file starts with title,
        # otherwise prepend after a capture marker. Simple approach: prepend after line 0.
        stamp = datetime.now(timezone.utc).isoformat()
        header_note = f"\n<!-- captured_by agent_27 at {stamp} -->\n"
        target.write_text(existing.rstrip() + "\n" + header_note + block + "\n", encoding="utf-8")
    return block
