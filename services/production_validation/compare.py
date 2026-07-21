"""Before/after comparison for content quality improvements."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "productions" / "_validation" / "content_validation"

COMPARE_KEYS = (
    "hook_strength",
    "retention_prediction",
    "completion_prediction",
    "shareability",
    "visual_quality",
    "animation_quality",
    "narration_quality",
    "audio_mix",
    "thumbnail_quality",
    "overall_production_score",
)


def write_comparison_report(
    *,
    before: dict[str, Any],
    after: dict[str, Any],
    out_dir: Path | None = None,
) -> Path:
    out_dir = Path(out_dir or OUT)
    out_dir.mkdir(parents=True, exist_ok=True)

    before_avg = before.get("average_scores") or {}
    after_avg = after.get("average_scores") or {}
    rows = []
    for key in COMPARE_KEYS:
        old = float(before_avg.get(key) or 0)
        new = float(after_avg.get(key) or 0)
        rows.append(
            {
                "metric": key,
                "before": round(old, 2),
                "after": round(new, 2),
                "delta": round(new - old, 2),
            }
        )

    before_ready = float(before.get("publish_ready_pct") or 0)
    after_ready = float(after.get("publish_ready_pct") or 0)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "objective": "Lift validation overall from ~70 toward 90+ via creative quality only",
        "before_publish_ready_pct": before_ready,
        "after_publish_ready_pct": after_ready,
        "publish_ready_delta": round(after_ready - before_ready, 1),
        "metrics": rows,
        "domain_deltas": _domain_deltas(before, after),
    }

    json_path = out_dir / "QUALITY_IMPROVEMENT_COMPARISON.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Content Quality Improvement Comparison",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"- Publish-ready: **{before_ready}% → {after_ready}%** (Δ {payload['publish_ready_delta']})",
        "",
        "## Metric deltas",
        "",
        "| Metric | Before | After | Δ |",
        "|--------|-------:|------:|--:|",
    ]
    for r in rows:
        lines.append(f"| {r['metric']} | {r['before']} | {r['after']} | {r['delta']:+} |")
    lines.extend(["", "## Per-domain overall", ""])
    for d in payload["domain_deltas"]:
        lines.append(
            f"- **{d['domain']}**: {d['before']} → {d['after']} (Δ {d['delta']:+})"
        )
    lines.append("")
    md_path = out_dir / "QUALITY_IMPROVEMENT_COMPARISON.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "QUALITY_IMPROVEMENT_COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    return md_path


def _domain_deltas(before: dict, after: dict) -> list[dict]:
    before_map = {
        e.get("domain"): float((e.get("scores") or {}).get("overall_production_score") or 0)
        for e in (before.get("evaluations") or [])
    }
    rows = []
    for e in after.get("evaluations") or []:
        dom = e.get("domain")
        new = float((e.get("scores") or {}).get("overall_production_score") or 0)
        old = before_map.get(dom, 0.0)
        rows.append({"domain": dom, "before": round(old, 2), "after": round(new, 2), "delta": round(new - old, 2)})
    return rows


def load_baseline_suite(path: Path | None = None) -> dict[str, Any] | None:
    """Load prior suite JSON; prefer explicit baseline snapshot if present."""
    base = Path(path or OUT)
    for name in ("CONTENT_VALIDATION_BASELINE.json", "CONTENT_VALIDATION_SUITE.json"):
        p = base / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return None
