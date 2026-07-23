"""Music provider abstraction — future-ready placeholder with demo path.

Real music vendors (Suno, Udio, etc.) register as ProductionConnector
subclasses without changing engines or the orchestrator.
"""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


class FutureMusicConnector(ProductionConnector):
    """Abstract music backend — available offline for contract testing.

    When MUSIC_PROVIDER_ENDPOINT + MUSIC_PROVIDER_API_KEY are set, posts to
    a generic music generation API. Otherwise returns a structured placeholder
    so pipelines can continue in demo mode via ProviderRuntime fallback.
    """

    name = "music_future"
    label = "Future Music Provider"
    api_key_env = "MUSIC_PROVIDER_API_KEY"
    offline = False
    local = False
    capabilities = (cap.MUSIC,)
    profile = ProviderProfile(quality=70, cost_per_unit=0.08, speed=55, consistency=70, latency_ms=20000)
    implementation_status = "partial"
    base_url = ""

    def is_available(self) -> bool:
        # Always registerable; real calls require endpoint + key.
        from services.provider_runtime.config import has_credential, get_credential

        endpoint = get_credential("MUSIC_PROVIDER_ENDPOINT", self._credential_overrides())
        if endpoint and has_credential(self.api_key_env, self._credential_overrides()):
            return True
        # Soft-available so selection can prefer real vendors first; demo still covers.
        return False

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        from services.provider_runtime.config import get_credential

        prompt = str(
            request.payload.get("prompt")
            or request.payload.get("mood")
            or request.payload.get("description")
            or ""
        )
        if not prompt:
            return self.fail(request, "Missing music prompt/mood")
        endpoint = get_credential("MUSIC_PROVIDER_ENDPOINT", self._credential_overrides())
        if not endpoint:
            return self.fail(request, "MUSIC_PROVIDER_ENDPOINT not configured")
        body = {
            "prompt": prompt,
            "duration_sec": float(request.payload.get("duration_sec") or 30),
            "genre": request.payload.get("genre") or "",
            "bpm": request.payload.get("bpm"),
        }
        resp = self.http(
            "POST",
            "/",
            json_body=body,
            absolute_url=endpoint.rstrip("/") + "/generate",
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"Music provider error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {"raw": resp.body}
        return self.ok(
            request,
            {
                "job_id": data.get("id") or data.get("job_id") or "",
                "audio_url": data.get("url") or data.get("audio_url") or "",
                "prompt": prompt,
                "async": True,
                "provider_abstraction": True,
            },
        )
