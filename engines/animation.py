"""Cinematic Animation Engine V2 — live planning enhancement.

Quality evolution of V1: motivated camera, living worlds, immersion gates.
Does not render final video pixels — hands instructions to MotionPlanner,
true_motion, and the existing assembler/renderer.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.animation_engine import attach_animation_package, build_animation_package

logger = get_logger(__name__)


class AnimationEngine(Engine):
    key = "animation"
    label = "Cinematic Animation Engine V2"
    icon = "🎥"
    description = (
        "Elevate every scene into cinematic storytelling — motivated cameras, "
        "living environments, expressive performance intents, immersion tests, "
        "and Animation Excellence — without replacing the renderer."
    )
    version = "2.0.0"
    input_contract = ["candidates", "visual_package", "cinematography_plan"]
    output_contract = ["animation_summary", "animation_packages", "ANIMATION_PACKAGE"]
    dependencies = ["cinematography", "visual_intelligence"]
    capabilities = [
        "animation-planning",
        "cinematics",
        "camera-planning",
        "character-motion",
        "world-animation",
        "motion-graphics",
        "animation-excellence",
        "quality-gate",
        "immersion-test",
        "motivated-camera",
        "environmental-depth",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            return {"animation_status": "NO_CANDIDATES"}

        packages = []
        topic = str(context.get("topic") or "")
        pid = str(context.get("production_id") or "")
        for i, cand in enumerate(candidates):
            if not isinstance(cand, dict):
                continue
            t = topic or str(cand.get("topic") or cand.get("title") or "")
            pkg = build_animation_package(
                cand,
                topic=t,
                production_id=pid,
                write=True,
            )
            candidates[i] = attach_animation_package(cand, pkg)
            packages.append(pkg)

        context["candidates"] = candidates
        top = packages[0] if packages else {}
        summary = {
            "animation_status": "READY",
            "version": "2.0.0",
            "packages": len(packages),
            "animation_excellence_score": (top.get("animation_excellence") or {}).get(
                "animation_excellence_score"
            ),
            "quality_gate": (top.get("quality_gate") or {}).get("decision"),
            "immersion_pass_ratio": ((top.get("quality_gate") or {}).get("metrics") or {}).get(
                "immersion_pass_ratio"
            ),
            "re_render_scenes": (top.get("quality_gate") or {}).get("re_render_scenes") or [],
            "path": top.get("path"),
        }
        log_event(
            logger,
            "animation_engine.completed",
            packages=len(packages),
            excellence=summary.get("animation_excellence_score"),
            gate=summary.get("quality_gate"),
            version="2.0.0",
        )
        return {
            "animation_summary": summary,
            "animation_packages": packages,
            "ANIMATION_PACKAGE": top,
            "animation_excellence_score": summary.get("animation_excellence_score"),
        }
