"""OutputPackager — assembles the final Agent 6 render package.

Folds every module's plan (timeline, scene render plans, captions, audio
mix, transitions, motion, assets, validation, mock render result) into ONE
JSON-safe dict written to `ContentPackage.render_package`. Additive by
contract: existing seed fields (media-production ids, queue status) are
preserved, never removed or renamed — Publishing (Agent 7) reads this
package as its input.
"""

from __future__ import annotations

from datetime import datetime, timezone

from engines.render.models import (
    OUTPUT_FORMAT,
    RENDER_ENGINE_VERSION,
    RENDER_PACKAGE_VERSION,
    SUPPORTED_PLATFORMS,
)


class OutputPackager:
    """Builds the render_package dict — the handoff to Publishing."""

    def package(
        self,
        *,
        title: str,
        timeline: dict,
        scene_render_plan: list,
        caption_render_plan: dict,
        audio_mix_plan: dict,
        transition_plan: dict,
        motion_plan: list,
        asset_requirements: list,
        missing_assets: list,
        render_warnings: list,
        validation: dict,
        render_result: dict,
        seed: "dict | None" = None,
    ) -> dict:
        """One complete render package (seed fields preserved additively)."""
        resolution = OUTPUT_FORMAT["resolution"]
        package = dict(seed or {})  # never drop media-production seed fields
        package.update(
            {
                "render_package_version": RENDER_PACKAGE_VERSION,
                "render_engine_version": RENDER_ENGINE_VERSION,
                "title": title,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "output_format": dict(OUTPUT_FORMAT),
                "platforms": list(SUPPORTED_PLATFORMS),
                "resolution": f"{resolution['width']}x{resolution['height']}",
                "aspect_ratio": OUTPUT_FORMAT["aspect_ratio"],
                "duration_sec": float(timeline.get("total_duration_sec", 0.0)),
                "timeline": timeline,
                "scene_render_plan": scene_render_plan,
                "caption_render_plan": caption_render_plan,
                "audio_mix_plan": audio_mix_plan,
                "transition_plan": transition_plan,
                "motion_plan": motion_plan,
                "asset_requirements": asset_requirements,
                "missing_assets": missing_assets,
                "render_warnings": render_warnings,
                "estimated_render_duration_sec": render_result.get(
                    "estimated_render_duration_sec", 0.0
                ),
                "production_readiness_score": validation.get("production_readiness_score", 0),
                "validation": validation,
                "render_status": render_result.get("render_status", ""),
                "mock_output_path": render_result.get("mock_output_path", ""),
                "file_uri": render_result.get("mock_output_path", ""),
                "render_log": render_result.get("render_log", []),
                "render_job": render_result.get("job", {}),
                "mock": bool(render_result.get("mock", True)),
                "render_manifest": {
                    "scenes": len(scene_render_plan),
                    "timeline_segments": timeline.get("segment_count", 0),
                    "caption_segments": len(caption_render_plan.get("segments", [])),
                    "audio_tracks": list(audio_mix_plan.get("tracks", {})),
                    "transitions": len(transition_plan.get("transitions", [])),
                    "assets_requested": len(asset_requirements),
                    "assets_missing": len(missing_assets),
                    "warnings": len(render_warnings),
                    "readiness": validation.get("production_readiness_score", 0),
                    "ready_for_publishing": validation.get("status") in ("SUCCESS", "WARNING"),
                },
            }
        )
        return package
