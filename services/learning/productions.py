"""Permanent production memory — every video the studio creates.

Append-only JSON store under data/analytics/productions.json.
Never discards historical learning.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger, log_event

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DIR = str(ROOT / "data" / "analytics")
_PRODUCTIONS_FILE = "productions.json"

PRODUCTION_RECORD_FIELDS = (
    "production_id",
    "topic",
    "platform",
    "video_length_sec",
    "script",
    "discovery_score",
    "audience_score",
    "psychology_score",
    "seo_score",
    "evidence_score",
    "visual_score",
    "animation_score",
    "narration_score",
    "qa_score",
    "thumbnail",
    "generation_time_ms",
    "render_time_ms",
    "export_size_bytes",
    "publishing_time",
    "publishing_platform",
    "date",
    "version",
    "pipeline_used",
    "model_versions",
    "prompt_versions",
    "idea_id",
    "run_id",
    "pqa_decision",
    "export_paths",
    "created_at",
)

_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(directory: str | None = None) -> Path:
    d = Path(directory or _DEFAULT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / _PRODUCTIONS_FILE


def _load(directory: str | None = None) -> list[dict]:
    path = _path(directory)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(records: list[dict], directory: str | None = None) -> None:
    path = _path(directory)
    path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")


def _score(item: dict, *keys: str, default: int = 0) -> int:
    for key in keys:
        val = item.get(key)
        if val is None and isinstance(item.get("pqa_report"), dict):
            scores = (item["pqa_report"].get("scores") or {})
            val = scores.get(key)
        if val is None:
            continue
        try:
            n = float(val)
            if n <= 1.0 and key.endswith(("_confidence",)):
                n *= 100
            return int(round(n))
        except (TypeError, ValueError):
            continue
    return default


def extract_production_record(
    item: dict,
    context: dict | None = None,
    *,
    run_id: str = "",
    pipeline_used: str = "intelligence",
) -> dict[str, Any]:
    """Build one permanent production memory row from an idea/candidate."""
    context = context or {}
    pqa = item.get("pqa_report") if isinstance(item.get("pqa_report"), dict) else {}
    scores = pqa.get("scores") if isinstance(pqa.get("scores"), dict) else {}
    evidence = item.get("evidence_package") if isinstance(item.get("evidence_package"), dict) else {}
    visual = item.get("visual_package") if isinstance(item.get("visual_package"), dict) else {}
    audience = item.get("audience_intelligence") if isinstance(item.get("audience_intelligence"), dict) else {}
    script = str(
        item.get("script")
        or (item.get("structured_script") or {}).get("full_script")
        or ""
    )
    thumb = item.get("thumbnail") or item.get("thumbnail_concepts") or visual.get("thumbnails") or {}
    export = context.get("executive_export") or item.get("executive_export") or {}

    return {
        "production_id": f"prod_{uuid.uuid4().hex[:12]}",
        "topic": str(item.get("title") or context.get("subject") or context.get("topic") or ""),
        "platform": str(
            item.get("target_platform")
            or context.get("target_platform")
            or (context.get("platforms") or ["youtube_shorts"])[0]
        ),
        "video_length_sec": int(
            item.get("estimated_runtime_hint_sec")
            or context.get("target_runtime_sec")
            or context.get("video_length_sec")
            or 60
        ),
        "script": script[:8000],
        "discovery_score": _score(
            item,
            "unified_discovery_score",
            default=int((context.get("research") or {}).get("opportunity_score") or 0),
        ),
        "audience_score": _score(
            item,
            "human_attention_score",
            default=int(audience.get("human_attention_score") or 0),
        ),
        "psychology_score": _score(item, "psychology_score", "viral_score"),
        "seo_score": _score(item, "seo_score"),
        "evidence_score": _score(
            item,
            "evidence_confidence",
            default=int(scores.get("evidence") or (float(evidence.get("overall_evidence_confidence") or 0) * 100)),
        ),
        "visual_score": _score(item, "visual_score", default=int(visual.get("visual_score") or scores.get("visuals") or 0)),
        "animation_score": _score(
            item,
            "cinematography_attention_score",
            default=int(scores.get("cinematography") or 0),
        ),
        "narration_score": _score(item, "script_quality", default=int(scores.get("narration") or 0)),
        "qa_score": _score(item, "pqa_score", default=int(pqa.get("overall_score") or 0)),
        "thumbnail": thumb if isinstance(thumb, (dict, list, str)) else str(thumb),
        "generation_time_ms": int(context.get("generation_time_ms") or 0),
        "render_time_ms": int(context.get("render_time_ms") or (item.get("render_package") or {}).get("duration_ms") or 0),
        "export_size_bytes": int(
            (export.get("export_size_bytes") if isinstance(export, dict) else 0)
            or context.get("export_size_bytes")
            or 0
        ),
        "publishing_time": str(item.get("published_at") or context.get("publishing_time") or ""),
        "publishing_platform": str(item.get("publishing_platform") or context.get("publish_platform") or ""),
        "date": _now()[:10],
        "version": str(context.get("os_version") or "1.0.0"),
        "pipeline_used": pipeline_used,
        "model_versions": dict(context.get("model_versions") or {"default": context.get("model") or ""}),
        "prompt_versions": dict(context.get("prompt_versions") or {}),
        "idea_id": str(item.get("id") or item.get("idea_id") or ""),
        "run_id": run_id or str(context.get("executive_run_id") or context.get("run_id") or ""),
        "pqa_decision": str(item.get("pqa_decision") or pqa.get("decision") or ""),
        "export_paths": dict(export.get("paths") or context.get("export_paths") or {}),
        "created_at": _now(),
    }


class ProductionMemory:
    """Append-only permanent production archive."""

    def __init__(self, directory: str | None = None) -> None:
        self.directory = directory

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        with _lock:
            rows = _load(self.directory)
            # Dedup by idea_id + run_id when present
            idea = str(record.get("idea_id") or "")
            run = str(record.get("run_id") or "")
            if idea or run:
                rows = [
                    r
                    for r in rows
                    if not (
                        idea
                        and run
                        and r.get("idea_id") == idea
                        and r.get("run_id") == run
                    )
                ]
            rows.append(record)
            _save(rows, self.directory)
        log_event(
            logger,
            "learning.production_recorded",
            production_id=record.get("production_id"),
            topic=record.get("topic"),
            qa=record.get("qa_score"),
        )
        return record

    def list_records(self, *, limit: int = 500) -> list[dict]:
        with _lock:
            rows = _load(self.directory)
        return list(reversed(rows[-limit:]))

    def find_similar(self, topic: str, *, limit: int = 10) -> list[dict]:
        topic_l = (topic or "").lower()
        tokens = [t for t in topic_l.replace("-", " ").split() if len(t) > 2]
        scored: list[tuple[int, dict]] = []
        for row in self.list_records(limit=1000):
            hay = f"{row.get('topic', '')} {row.get('script', '')[:200]}".lower()
            hits = sum(1 for t in tokens if t in hay)
            if hits or (topic_l and topic_l[:20] in hay):
                scored.append((hits, row))
        scored.sort(key=lambda x: (x[0], int(x[1].get("qa_score") or 0)), reverse=True)
        return [r for _, r in scored[:limit]]

    def count(self) -> int:
        return len(_load(self.directory))


_MEMORY: ProductionMemory | None = None


def get_production_memory(directory: str | None = None) -> ProductionMemory:
    global _MEMORY
    if directory is not None:
        return ProductionMemory(directory)
    if _MEMORY is None:
        _MEMORY = ProductionMemory()
    return _MEMORY


def record_productions_from_context(
    context: dict,
    *,
    pipeline_used: str = "intelligence",
    run_id: str = "",
) -> list[dict]:
    """Persist every idea/candidate from a finished run."""
    items = (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    )
    memory = get_production_memory()
    saved: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        record = extract_production_record(
            item, context, run_id=run_id, pipeline_used=pipeline_used
        )
        memory.add(record)
        item["production_memory_id"] = record["production_id"]
        saved.append(record)
    context["production_memory_count"] = len(saved)
    return saved
