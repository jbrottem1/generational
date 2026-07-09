"""Narration engine — voice synthesis via ProviderRuntime."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import VOICE_PROFILES, VoiceSettings
from engines.base import Engine
from providers.voice.base import NarrationResult, VoiceMode
from services.provider_runtime.engine_api import runtime_synthesize_voice
from services.voice_profiles import get_default_profile, get_voice_profile_manager

logger = get_logger(__name__)


class NarrationEngine(Engine):
    key = "narration"
    label = "Narration"
    icon = "🎙️"
    description = "Generate narration tracks via AI, recorded, or clone voice providers."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        packages = context.get("production_packages") or []
        niche = context.get("niche", "")
        voice_mode = context.get("voice_mode", VoiceMode.AI)
        profile_id = context.get("voice_profile_id", "")
        manager = get_voice_profile_manager()

        if profile_id:
            profile = manager.get_profile(profile_id) or get_default_profile(niche)
        else:
            profile = get_default_profile(niche)

        settings = profile.get("settings", VoiceSettings().to_dict())

        for pkg in packages:
            tracks = []
            for scene in pkg.get("scenes", []):
                raw = runtime_synthesize_voice(
                    scene.get("narration", ""), profile, settings, mode=voice_mode,
                )
                result = NarrationResult(
                    asset_id=str(raw.get("asset_id") or ""),
                    duration_sec=float(raw.get("duration_sec") or 0),
                    path=str(raw.get("path") or ""),
                    mode=str(raw.get("mode") or voice_mode),
                    placeholder=bool(raw.get("placeholder", True)),
                    metadata=dict(raw.get("metadata") or {}),
                )
                tracks.append(
                    {
                        "scene_id": scene["scene_id"],
                        "text": scene.get("narration", ""),
                        "duration_sec": result.duration_sec,
                        "mode": result.mode,
                        "profile_id": profile.get("profile_id", ""),
                        "asset_id": result.asset_id,
                        "placeholder": result.placeholder,
                        "path": result.path,
                        "provider": raw.get("provider", ""),
                    }
                )
            pkg["narration_tracks"] = tracks

        log_event(logger, "narration.completed", packages=len(packages), mode=voice_mode)
        return {"production_packages": packages, "voice_profile": profile}
