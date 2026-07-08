"""Narration engine — voice synthesis via the Voice Provider abstraction."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import VOICE_PROFILES, VoiceSettings
from engines.base import Engine
from providers import get_voice_provider
from providers.voice.base import VoiceMode
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

        provider = get_voice_provider(voice_mode)
        settings = profile.get("settings", VoiceSettings().to_dict())

        for pkg in packages:
            tracks = []
            for scene in pkg.get("scenes", []):
                result = provider.synthesize(scene.get("narration", ""), profile, settings)
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
                    }
                )
            pkg["narration_tracks"] = tracks

        log_event(logger, "narration.completed", packages=len(packages), mode=voice_mode)
        return {"production_packages": packages, "voice_profile": profile}
