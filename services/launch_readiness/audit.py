"""Generational Launch Readiness Audit — go/no-go for public publishing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "productions" / "_validation" / "launch_readiness"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def run_launch_readiness_audit() -> dict[str, Any]:
    """Score 0–100 readiness; emit blockers or phased rollout plan."""
    checks: list[dict] = []

    # Production reliability — acceptance tests
    acceptance = _load_json(ROOT / "data" / "productions" / "_acceptance" / "ACCEPTANCE_DASHBOARD.json")
    if not acceptance:
        acceptance = _load_json(ROOT / "data" / "productions" / "_acceptance" / "dashboard.json")
    pass_pct = float((acceptance or {}).get("pass_pct") or (acceptance or {}).get("pass_rate") or 0)
    checks.append(_check("production_reliability", pass_pct, 95, weight=15, note="Acceptance pass rate"))

    # Content quality — validation suite
    suite = _load_json(
        ROOT / "data" / "productions" / "_validation" / "content_validation" / "CONTENT_VALIDATION_SUITE.json"
    )
    quality = float(((suite or {}).get("average_scores") or {}).get("overall_production_score") or 0)
    publish_ready = float((suite or {}).get("publish_ready_pct") or 0)
    checks.append(_check("content_quality", quality, 90, weight=18, note="Validation overall score"))
    checks.append(_check("creative_consistency", publish_ready, 90, weight=12, note="Publish-ready rate across domains"))

    # Prediction accuracy / analytics readiness
    calibration = _load_json(ROOT / "data" / "analytics" / "prediction_calibration.json")
    acc = (calibration or {}).get("average_prediction_accuracy_pct")
    videos_cal = int((calibration or {}).get("videos_calibrated") or 0)
    if acc is None:
        # No real publishes yet — partial credit for calibrated infrastructure
        checks.append(
            {
                "id": "prediction_accuracy",
                "score": 70,
                "weight": 12,
                "pass": False,
                "note": "Calibration pipeline ready; awaiting real post-publish actuals",
                "blocker": videos_cal < 1,
            }
        )
    else:
        checks.append(_check("prediction_accuracy", float(acc), 80, weight=12, note="Prediction accuracy vs actuals"))

    intel_path = ROOT / "data" / "analytics" / "intelligence_records.json"
    intel_n = 0
    if intel_path.exists():
        rows = _load_json(intel_path) or []
        intel_n = len(rows) if isinstance(rows, list) else 0
    checks.append(
        {
            "id": "analytics_readiness",
            "score": min(100, 60 + intel_n * 5),
            "weight": 10,
            "pass": intel_n >= 1,
            "note": f"Intelligence records stored: {intel_n}",
            "blocker": intel_n < 1,
        }
    )

    # Publishing readiness — packages / queue
    publishing_jobs = _load_json(ROOT / "data" / "publishing_queue" / "jobs.json") or []
    has_pub_infra = (ROOT / "services" / "publishing" / "package.py").exists()
    pub_score = 85 if has_pub_infra else 40
    if isinstance(publishing_jobs, list) and publishing_jobs:
        pub_score = min(100, pub_score + 10)
    # Intelligence publish packages smoke
    try:
        from services.publishing_intelligence.pipeline import build_complete_publish_packages

        pkg = build_complete_publish_packages({"topic": "Launch audit topic", "title": "Launch audit topic"})
        platforms_ok = len(pkg.get("platforms") or {}) >= 5
        checklist_ok = any((p.get("upload_checklist") for p in (pkg.get("platforms") or {}).values()))
        pub_score = max(pub_score, 92 if platforms_ok and checklist_ok else 75)
    except Exception as exc:  # noqa: BLE001
        pub_score = min(pub_score, 55)
        platforms_ok = False
        checklist_ok = False
        pkg_error = str(exc)
    else:
        pkg_error = None
    checks.append(
        {
            "id": "publishing_readiness",
            "score": pub_score,
            "weight": 15,
            "pass": pub_score >= 90,
            "note": "Multi-platform publish packages + upload checklist",
            "blocker": pub_score < 90,
            "detail": {"platforms_ok": locals().get("platforms_ok"), "error": pkg_error},
        }
    )

    # Recovery resilience — ops never-abort pattern present
    ops_ok = (ROOT / "services" / "production_operations" / "resilience.py").exists()
    checks.append(
        {
            "id": "recovery_resilience",
            "score": 92 if ops_ok else 40,
            "weight": 8,
            "pass": ops_ok,
            "note": "Production ops resilience (retry/continue) available",
            "blocker": not ops_ok,
        }
    )

    # Automation completeness — director + validation + intelligence
    automation_bits = [
        (ROOT / "services" / "ai_director" / "blueprint.py").exists(),
        (ROOT / "services" / "production_validation" / "suite.py").exists(),
        (ROOT / "services" / "publishing_intelligence" / "system.py").exists(),
        (ROOT / "services" / "learning" / "predictions.py").exists(),
    ]
    auto_score = int(100 * sum(1 for b in automation_bits if b) / len(automation_bits))
    checks.append(
        {
            "id": "automation_completeness",
            "score": auto_score,
            "weight": 10,
            "pass": auto_score >= 90,
            "note": "Director + validation + intelligence + learning wired",
            "blocker": auto_score < 90,
        }
    )

    # Weighted score
    total_w = sum(c["weight"] for c in checks) or 1
    launch_score = round(sum(c["score"] * c["weight"] for c in checks) / total_w, 1)
    blockers = [
        {
            "id": c["id"],
            "note": c["note"],
            "score": c["score"],
            "priority": round((100 - c["score"]) * c["weight"] / 10, 1),
        }
        for c in checks
        if c.get("blocker") or not c.get("pass")
    ]
    blockers.sort(key=lambda b: -b["priority"])

    result: dict[str, Any] = {
        "generated_at": _now(),
        "version": "1.0.0",
        "launch_readiness_score": launch_score,
        "ready_for_public_launch": launch_score >= 95,
        "checks": checks,
        "blockers": blockers if launch_score < 95 else [],
    }

    if launch_score >= 95:
        result["recommendation"] = "BEGIN_CONTROLLED_PUBLIC_LAUNCH"
        result["rollout_plan"] = _phased_rollout_plan()
    else:
        result["recommendation"] = "RESOLVE_BLOCKERS_BEFORE_LAUNCH"
        result["prioritized_blockers"] = blockers[:7]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "LAUNCH_READINESS_AUDIT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (OUT_DIR / "LAUNCH_READINESS_AUDIT.md").write_text(_markdown(result), encoding="utf-8")
    (ROOT / "LAUNCH_READINESS_AUDIT.md").write_text(_markdown(result), encoding="utf-8")
    return result


def _check(cid: str, value: float, threshold: float, *, weight: int, note: str) -> dict:
    score = max(0.0, min(100.0, value))
    # Scale relative to threshold for partial credit
    if threshold > 0:
        score = min(100.0, (value / threshold) * 100.0) if value < threshold else min(100.0, 90 + (value - threshold))
    return {
        "id": cid,
        "score": round(score, 1),
        "raw": value,
        "threshold": threshold,
        "weight": weight,
        "pass": value >= threshold,
        "note": note,
        "blocker": value < threshold,
    }


def _phased_rollout_plan() -> dict:
    return {
        "channels": 2,
        "topics_per_channel": 3,
        "cadence": "3–5 shorts / week / channel",
        "phases": {
            "30_days": {
                "goal": "Prove reliability & packaging",
                "success_metrics": [
                    "≥20 videos published without manual pipeline intervention",
                    "Average validation overall ≥90",
                    "Upload checklist pass rate ≥95%",
                    "Zero critical export failures week-over-week",
                ],
            },
            "60_days": {
                "goal": "Prove learning loop with real analytics",
                "success_metrics": [
                    "≥50 published videos with analytics ingested",
                    "Prediction accuracy ≥75% on CTR or completion",
                    "Creative library has ≥10 winning patterns",
                    "One highest-impact improvement applied each week",
                ],
            },
            "90_days": {
                "goal": "Prove scalable growth",
                "success_metrics": [
                    "Expand to 4–6 channels / niches",
                    "Median CTR ≥ niche baseline",
                    "Audience retention ≥ internal prediction −10pts",
                    "Automation rate ≥90% with ≤5 min manual edit average",
                ],
            },
        },
    }


def _markdown(result: dict) -> str:
    lines = [
        "# Launch Readiness Audit",
        "",
        f"Generated: {result.get('generated_at')}",
        f"Launch Readiness Score: **{result.get('launch_readiness_score')}/100**",
        f"Recommendation: **{result.get('recommendation')}**",
        "",
        "## Checks",
        "",
    ]
    for c in result.get("checks") or []:
        status = "PASS" if c.get("pass") else "BLOCKER"
        lines.append(f"- [{status}] **{c['id']}** — {c['score']} ({c['note']})")
    if result.get("prioritized_blockers"):
        lines.extend(["", "## Prioritized blockers", ""])
        for i, b in enumerate(result["prioritized_blockers"], 1):
            lines.append(f"{i}. {b['id']} — {b['note']} (score {b['score']})")
    if result.get("rollout_plan"):
        lines.extend(["", "## Controlled public launch plan", ""])
        plan = result["rollout_plan"]
        lines.append(f"- Channels: {plan.get('channels')}")
        lines.append(f"- Topics/channel: {plan.get('topics_per_channel')}")
        lines.append(f"- Cadence: {plan.get('cadence')}")
        for phase, body in (plan.get("phases") or {}).items():
            lines.append(f"### {phase.replace('_', ' ')}")
            lines.append(f"- Goal: {body.get('goal')}")
            for m in body.get("success_metrics") or []:
                lines.append(f"  - {m}")
    lines.append("")
    return "\n".join(lines)
