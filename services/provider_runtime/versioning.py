"""Provider API version management — pin and discover adapter API versions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProviderVersion:
    """Pinned API / model version for one provider."""

    provider: str
    api_version: str = "v1"
    model: str = ""
    deprecated: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "api_version": self.api_version,
            "model": self.model,
            "deprecated": self.deprecated,
            "notes": self.notes,
        }


# Default pinned versions — override via runtime config `versions`.
DEFAULT_VERSIONS: dict[str, ProviderVersion] = {
    "openai": ProviderVersion("openai", "v1", "gpt-4o-mini"),
    "openai_images": ProviderVersion("openai_images", "v1", "gpt-image-1"),
    "openai_tts": ProviderVersion("openai_tts", "v1", "tts-1"),
    "anthropic": ProviderVersion("anthropic", "2023-06-01", "claude-haiku-4-5-20251001"),
    "google_gemini": ProviderVersion("google_gemini", "v1beta", "gemini-1.5-flash"),
    "xai": ProviderVersion("xai", "v1", "grok-2-latest"),
    "google_veo": ProviderVersion("google_veo", "v1beta", "veo-2.0-generate-001"),
    "flux": ProviderVersion("flux", "v1", "flux-pro-1.1"),
    "ideogram": ProviderVersion("ideogram", "v1", "V_2"),
    "stability_ai": ProviderVersion("stability_ai", "v2beta", "stable-diffusion-xl-1024-v1-0"),
    "runway": ProviderVersion("runway", "v1", "gen3a_turbo"),
    "pika": ProviderVersion("pika", "v1", "pika-1.5"),
    "kling": ProviderVersion("kling", "v1", "kling-v1"),
    "luma": ProviderVersion("luma", "v1", "ray-2"),
    "elevenlabs": ProviderVersion("elevenlabs", "v1", "eleven_multilingual_v2"),
    "fal_ai": ProviderVersion("fal_ai", "v1", "fal-ai/flux/dev"),
    "replicate": ProviderVersion("replicate", "v1", "black-forest-labs/flux-schnell"),
    "comfyui": ProviderVersion("comfyui", "v1", "local-workflow"),
    "ollama": ProviderVersion("ollama", "v1", "llama3.2"),
    "music_future": ProviderVersion("music_future", "v0", "placeholder"),
}


class VersionManager:
    """Tracks and resolves provider API / model versions."""

    def __init__(self, overrides: "dict[str, dict] | None" = None) -> None:
        self._versions: dict[str, ProviderVersion] = dict(DEFAULT_VERSIONS)
        if overrides:
            for name, cfg in overrides.items():
                base = self._versions.get(name, ProviderVersion(name))
                self._versions[name] = ProviderVersion(
                    provider=name,
                    api_version=str(cfg.get("api_version", base.api_version)),
                    model=str(cfg.get("model", base.model)),
                    deprecated=bool(cfg.get("deprecated", base.deprecated)),
                    notes=str(cfg.get("notes", base.notes)),
                )

    def get(self, provider: str) -> ProviderVersion:
        return self._versions.get(provider, ProviderVersion(provider))

    def set(self, version: ProviderVersion) -> None:
        self._versions[version.provider] = version

    def model_for(self, provider: str, fallback: str = "") -> str:
        ver = self.get(provider)
        return ver.model or fallback

    def catalog(self) -> list[dict]:
        return [v.to_dict() for v in self._versions.values()]

    def pin(self, provider: str, *, api_version: str = "", model: str = "") -> ProviderVersion:
        current = self.get(provider)
        updated = ProviderVersion(
            provider=provider,
            api_version=api_version or current.api_version,
            model=model or current.model,
            deprecated=current.deprecated,
            notes=current.notes,
        )
        self._versions[provider] = updated
        return updated
