"""Deterministic mock post-production provider — offline end-to-end testing."""

from __future__ import annotations

from providers.post_production_provider import PostProductionProvider


class MockPostProductionProvider(PostProductionProvider):
    """Offline provider that simulates timeline assembly and export."""

    name = "mock"
    label = "Mock Post-Production (Demo Mode)"

    def capabilities(self) -> list:
        return [
            "assemble_timeline", "export", "validate",
            "audio_mix", "caption_burn", "color_grade",
            "motion_graphics", "batch",
        ]

    def assemble(self, package: dict) -> dict:
        timeline = package.get("edit_timeline") or {}
        return {
            "status": "assembled",
            "timeline_id": timeline.get("timeline_id", ""),
            "track_count": len(timeline.get("tracks", [])),
            "duration_sec": timeline.get("total_duration_sec", 0.0),
            "provider": self.name,
        }

    def export(self, package: dict, preset_id: str) -> dict:
        presets = package.get("export_presets") or []
        preset = next((p for p in presets if p.get("preset_id") == preset_id), {})
        return {
            "status": "exported",
            "preset_id": preset_id,
            "resolution": preset.get("resolution", {}),
            "output_path": f"/mock/exports/{preset_id}.mp4",
            "provider": self.name,
        }

    def validate(self, package: dict) -> dict:
        quality = package.get("quality_report") or {}
        return {
            "status": quality.get("status", "pass"),
            "score": quality.get("score", 0),
            "provider": self.name,
        }
