"""Validate Cinematography Engine → Animation handoff."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.cinematography import build_cinematography_plan, cinematography_to_motion_planner_scenes
from services.evidence_intelligence import build_evidence_package


EXAMPLES = [
    "The Earth tilts on its axis.",
    "Notice this fossil in the limestone.",
    "This tiny transistor switches billions of times per second.",
    "Inside the factory, assembly robots build each camera body.",
]


def main() -> int:
    print("=== Narration → Movement ===")
    from services.cinematography import choose_movement

    for line in EXAMPLES:
        m, angle, framing, zoom, pan, reason = choose_movement(line)
        print(f"- {line!r}")
        print(f"  → {m} | {angle}/{framing} zoom={zoom} pan={pan}")
        print(f"  reason: {reason}")

    candidate = {
        "title": "How the seasons work",
        "script": " ".join(EXAMPLES),
        "hook": "Why Earth has seasons",
        "human_attention_score": 70,
    }
    evidence = build_evidence_package(candidate, topic="Seasons", domain="science")
    candidate["evidence_package"] = evidence.to_dict()

    print("\n=== Cinematography Plan ===")
    plan = build_cinematography_plan(candidate)
    print(f"scenes={len(plan.scenes)} attention={plan.overall_attention_score} pacing={plan.pacing_summary}")
    print(plan.reasoning)
    for s in plan.scenes:
        print(
            f"  S{s.scene_number}: {s.movement} | focus=({s.focus_point.x:.2f},{s.focus_point.y:.2f}) "
            f"| easing={s.easing} | transition={s.transition} | attn={s.attention_score}"
        )
        print(f"       graph_keys={len(s.motion_graph)} anim={s.animation_camera}/{s.animation_effect}")

    print("\n=== Engine + Animation handoff ===")
    engine = registry.get_engine("cinematography")
    updates = engine.run({"candidates": [candidate], "subject": "seasons"})
    handoff = updates["candidates"][0]["animation_handoff"]
    print(json.dumps(handoff, indent=2)[:1200])
    mp = cinematography_to_motion_planner_scenes(plan)
    print(f"MotionPlanner scenes: {len(mp)} first_effect_fields={list(mp[0].keys())}")

    status = "SUCCESS" if plan.scenes and handoff.get("scenes") else "PARTIAL"
    out_dir = ROOT / "data" / "productions" / "_validation" / "cinematography"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "examples": [
            {"narration": line, "movement": choose_movement(line)[0]} for line in EXAMPLES
        ],
        "plan": plan.to_dict(),
        "animation_handoff": handoff,
        "summary": updates.get("cinematography_summary"),
    }
    json_path = out_dir / "CINEMATOGRAPHY_E2E.json"
    md_path = out_dir / "CINEMATOGRAPHY_E2E_REPORT.md"
    json_path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Cinematography Engine — E2E",
        "",
        f"Generated: {doc['generated_at']}",
        f"**Status:** {status}",
        "",
        "## Narration → Movement",
    ]
    for row in doc["examples"]:
        lines.append(f"- `{row['narration']}` → **{row['movement']}**")
    lines.extend(
        [
            "",
            f"## Plan: {plan.topic}",
            f"- Scenes: {len(plan.scenes)}",
            f"- Attention: {plan.overall_attention_score}",
            f"- Pacing: {plan.pacing_summary}",
            "",
            "Animation handoff ready (`animation_handoff.scenes`).",
            f"JSON: `{json_path}`",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {md_path}")
    print(f"=== RESULT: {status} ===")
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
