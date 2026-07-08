"""Voice profile management — AI, recorded, and clone-ready profiles."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from core.production_models import VOICE_PROFILES, VoiceProfile, VoiceSettings

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "voice_profiles"
)
_RECORDINGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "voice_recordings"
)

NICHE_DEFAULT_STYLE = {
    "Science": "science",
    "Finance": "finance",
    "Psychology": "educational",
    "Dark History": "storytelling",
    "Space": "science",
    "Health": "calm",
    "AI & Future Tech": "high_energy",
}


class VoiceProfileManager:
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self.directory = directory
        self.recordings_dir = _RECORDINGS_DIR

    def _ensure_dirs(self) -> None:
        os.makedirs(self.directory, exist_ok=True)
        os.makedirs(self.recordings_dir, exist_ok=True)

    def _path_for(self, profile_id: str) -> str:
        return os.path.join(self.directory, f"{profile_id}.json")

    def create_profile(self, name: str, style: str, mode: str = "ai", **kwargs) -> dict:
        self._ensure_dirs()
        if style not in VOICE_PROFILES:
            style = "documentary"
        profile = VoiceProfile(
            profile_id=f"vp_{uuid.uuid4().hex[:10]}",
            name=name,
            style=style,
            mode=mode,
            settings=VoiceSettings(**kwargs.get("settings", {})),
            recording_path=kwargs.get("recording_path", ""),
        )
        data = profile.to_dict()
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        with open(self._path_for(profile.profile_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log_event(logger, "voice_profile.created", profile_id=profile.profile_id, mode=mode)
        return data

    def get_profile(self, profile_id: str) -> "dict | None":
        path = self._path_for(profile_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def list_profiles(self) -> list:
        self._ensure_dirs()
        profiles = []
        for filename in os.listdir(self.directory):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.directory, filename), "r", encoding="utf-8") as f:
                    profiles.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        return profiles

    def attach_to_project(self, profile_id: str, project_name: str) -> dict:
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile '{profile_id}' not found.")
        attachments = profile.setdefault("project_attachments", [])
        if project_name not in attachments:
            attachments.append(project_name)
        with open(self._path_for(profile_id), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        return profile

    def save_recording_metadata(self, filename: str, profile_id: str, duration_sec: float) -> dict:
        """Store metadata for a user recording (file saved separately by UI upload)."""
        self._ensure_dirs()
        meta = {
            "filename": filename,
            "profile_id": profile_id,
            "duration_sec": duration_sec,
            "path": os.path.join(self.recordings_dir, filename),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        meta_path = os.path.join(self.recordings_dir, f"{filename}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        log_event(logger, "voice_recording.saved", profile_id=profile_id, filename=filename)
        return meta


_manager = VoiceProfileManager()


def get_voice_profile_manager() -> VoiceProfileManager:
    return _manager


def get_default_profile(niche: str) -> dict:
    style = NICHE_DEFAULT_STYLE.get(niche, "documentary")
    return VoiceProfile(
        profile_id="default",
        name=f"{niche} Default",
        style=style,
        mode="ai",
        settings=VoiceSettings(),
    ).to_dict()
