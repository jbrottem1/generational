"""Validate Evidence & Visual Intelligence → Scene Builder handoff."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.env import load_application_env
from engines import registry
import engines  # noqa: F401
from services.evidence_intelligence import build_evidence_package, scene_builder_payload


def main() -> int:
    load_application_env()
    out_dir = ROOT / "data" / "productions" / "_validation" / "evidence_intelligence"
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate = {
        "title": "How cameras are made",
        "script": (
            "Inside a modern camera factory, glass lenses are ground to micron precision. "
            "The image sensor captures light and converts it into digital signal. "
            "Engineers assemble the shutter, body, and processor before final calibration."
        ),
        "hook": "Stop scrolling — see how a camera is actually built.",
        "human_attention_score": 62,
    }

    print("=== Evidence Package ===")
    package = build_evidence_package(candidate, topic="How cameras are made", domain="science")
    print(f"scenes={len(package.scenes)} authentic={package.authentic_hit_count} "
          f"ai_fallback={package.ai_fallback_count} confidence={package.overall_evidence_confidence}")
    print(f"reasoning={package.reasoning}")

    for scene in package.scenes[:4]:
        print(f"\n--- Scene {scene.scene_number} ---")
        print(f"narration={scene.narration[:100]}")
        print(f"modality={scene.modality.to_dict()}")
        print(f"source={scene.image_source} license={scene.license_status} type={scene.visual_type} conf={scene.evidence_confidence}")
        print(f"motion={scene.motion_plan.camera_motion} zooms={len(scene.motion_plan.suggested_zooms)}")
        print(f"annotations={len(scene.annotation_plan)} attention={scene.expected_attention_score}")
        for ann in scene.annotation_plan:
            print(f"  • {ann.kind} target={ann.target} cue={ann.narration_cue} "
                  f"{ann.start_sec:.2f}-{ann.end_sec:.2f}s")
        sb = scene_builder_payload(scene)
        assert "annotation_plan" in sb and "motion_plan" in sb

    print("\n=== Engine run ===")
    engine = registry.get_engine("evidence_intelligence")
    updates = engine.run({"candidates": [candidate], "niche": "science", "subject": "cameras"})
    summary = updates.get("evidence_intelligence_summary") or {}
    print(summary)
    assert updates["candidates"][0].get("evidence_package")
    assert updates["candidates"][0].get("scene_builder_plans")

    # Optional: bind into visual intelligence if script-like fields exist
    print("\n=== Visual Intelligence bind (if ready) ===")
    vi = registry.get_engine("visual_intelligence")
    # Provide minimal structured fields VI expects
    cand = updates["candidates"][0]
    cand.setdefault("script_variants", [{"full_script": candidate["script"], "score": 70, "estimated_runtime_sec": 45}])
    cand.setdefault("script", candidate["script"])
    try:
        vi_out = vi.run({"candidates": [cand], "target_platform": "youtube_shorts", "niche": "science", "subject": "cameras"})
        scenes = (vi_out.get("candidates") or [{}])[0].get("visual_package", {}).get("scenes") or []
        print(f"VI scenes={len(scenes)}")
        if scenes:
            print(f"first.asset_type={scenes[0].get('asset_type')} evidence_conf={scenes[0].get('evidence_confidence')}")
    except Exception as exc:  # noqa: BLE001
        print(f"VI skipped: {exc}")

    status = "SUCCESS" if package.scenes and summary.get("prefer_real_over_ai") else "PARTIAL"
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "package": package.to_dict(),
        "summary": summary,
    }
    json_path = out_dir / "EVIDENCE_INTELLIGENCE_E2E.json"
    md_path = out_dir / "EVIDENCE_INTELLIGENCE_E2E_REPORT.md"
    json_path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Evidence & Visual Intelligence — E2E",
        "",
        f"Generated: {doc['generated_at']}",
        f"**Status:** {status}",
        "",
        f"## Topic: How cameras are made",
        f"- Scenes: {len(package.scenes)}",
        f"- Authentic hits: {package.authentic_hit_count}",
        f"- AI fallback scenes: {package.ai_fallback_count}",
        f"- Overall confidence: {package.overall_evidence_confidence}",
        "",
        "## Scene Builder samples",
    ]
    for scene in package.scenes[:3]:
        lines.append(f"### Scene {scene.scene_number}")
        lines.append(f"- Source: {scene.image_source or '(AI fallback)'}")
        lines.append(f"- License: {scene.license_status}")
        lines.append(f"- Visual type: {scene.visual_type}")
        lines.append(f"- Confidence: {scene.evidence_confidence}")
        lines.append(f"- Motion: {scene.motion_plan.camera_motion}")
        lines.append(f"- Annotations: {len(scene.annotation_plan)}")
        lines.append(f"- Attention: {scene.expected_attention_score}")
        lines.append("")
    lines.append("Structured JSON only — real evidence preferred over AI.")
    lines.append(f"JSON: `{json_path}`")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {md_path}")
    print(f"=== RESULT: {status} ===")
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
