"""Video production connectors — Veo, Runway, Kling, Pika, Luma."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


def _video_prompt(payload: dict) -> str:
    return str(payload.get("prompt") or payload.get("text") or payload.get("description") or "")


class GoogleVeoConnector(ProductionConnector):
    name = "google_veo"
    label = "Google Veo"
    api_key_env = "GOOGLE_API_KEY"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.MOTION)
    profile = ProviderProfile(quality=92, cost_per_unit=1.50, speed=35, consistency=70, latency_ms=45000)
    default_timeout_sec = 180.0

    def auth_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = _video_prompt(request.payload)
        if not prompt:
            return self.fail(request, "Missing video prompt")
        model = self.resolved_model(request, "veo-2.0-generate-001")
        key = self.api_key()
        url = f"{self.base_url}/models/{model}:predictLongRunning?key={key}"
        body = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "aspectRatio": str(request.payload.get("aspect_ratio") or "9:16"),
                "sampleCount": 1,
            },
        }
        resp = self.http("POST", "/", json_body=body, absolute_url=url, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Google Veo error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("name") or data.get("operation") or "",
                "status": data.get("metadata", {}).get("state") or "submitted",
                "video_url": "",
                "prompt": prompt,
                "model": model,
                "async": True,
            },
            model=model,
        )


class RunwayConnector(ProductionConnector):
    name = "runway"
    label = "Runway"
    api_key_env = "RUNWAY_API_KEY"
    base_url = "https://api.dev.runwayml.com/v1"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.MOTION, cap.LIP_SYNC)
    profile = ProviderProfile(quality=88, cost_per_unit=1.00, speed=45, consistency=68, latency_ms=35000)
    default_timeout_sec = 120.0

    def auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key()}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = _video_prompt(request.payload)
        if not prompt:
            return self.fail(request, "Missing video prompt")
        model = self.resolved_model(request, "gen3a_turbo")
        body = {
            "promptText": prompt,
            "model": model,
            "duration": int(request.payload.get("duration_sec") or 5),
            "ratio": str(request.payload.get("aspect_ratio") or "768:1280"),
        }
        if request.payload.get("image_url"):
            body["promptImage"] = request.payload["image_url"]
        resp = self.http("POST", "/image_to_video", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            # Fallback text-to-video style endpoint naming
            resp = self.http("POST", "/text_to_video", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Runway error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("id") or "",
                "status": data.get("status") or "PENDING",
                "video_url": "",
                "prompt": prompt,
                "model": model,
                "async": True,
            },
            model=model,
        )


class KlingConnector(ProductionConnector):
    name = "kling"
    label = "Kling"
    api_key_env = "KLING_API_KEY"
    base_url = "https://api.klingai.com/v1"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.CHARACTER_CONSISTENCY)
    profile = ProviderProfile(quality=85, cost_per_unit=0.70, speed=40, consistency=66, latency_ms=40000)
    default_timeout_sec = 120.0

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = _video_prompt(request.payload)
        if not prompt:
            return self.fail(request, "Missing video prompt")
        model = self.resolved_model(request, "kling-v1")
        body = {
            "model_name": model,
            "prompt": prompt,
            "duration": str(request.payload.get("duration_sec") or "5"),
            "aspect_ratio": str(request.payload.get("aspect_ratio") or "9:16"),
        }
        resp = self.http("POST", "/videos/text2video", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Kling error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        inner = data.get("data") or data
        return self.ok(
            request,
            {
                "job_id": str(inner.get("task_id") or inner.get("id") or ""),
                "status": str(inner.get("task_status") or "submitted"),
                "video_url": "",
                "prompt": prompt,
                "model": model,
                "async": True,
            },
            model=model,
        )


class PikaConnector(ProductionConnector):
    name = "pika"
    label = "Pika"
    api_key_env = "PIKA_API_KEY"
    base_url = "https://api.pika.art/v1"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION)
    profile = ProviderProfile(quality=80, cost_per_unit=0.45, speed=60, consistency=60, latency_ms=20000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = _video_prompt(request.payload)
        if not prompt:
            return self.fail(request, "Missing video prompt")
        model = self.resolved_model(request, "pika-1.5")
        body = {
            "prompt": prompt,
            "model": model,
            "options": {
                "aspectRatio": str(request.payload.get("aspect_ratio") or "9:16"),
                "frameRate": int(request.payload.get("fps") or 24),
            },
        }
        resp = self.http("POST", "/generate", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Pika error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("id") or data.get("job_id") or "",
                "status": data.get("status") or "submitted",
                "video_url": data.get("url") or "",
                "prompt": prompt,
                "model": model,
                "async": True,
            },
            model=model,
        )


class LumaConnector(ProductionConnector):
    name = "luma"
    label = "Luma Dream Machine"
    api_key_env = "LUMA_API_KEY"
    base_url = "https://api.lumalabs.ai/dream-machine/v1"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.THREE_D_GENERATION)
    profile = ProviderProfile(quality=84, cost_per_unit=0.60, speed=50, consistency=64, latency_ms=30000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = _video_prompt(request.payload)
        if not prompt:
            return self.fail(request, "Missing video prompt")
        model = self.resolved_model(request, "ray-2")
        body = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": str(request.payload.get("aspect_ratio") or "9:16"),
        }
        resp = self.http("POST", "/generations", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Luma error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("id") or "",
                "status": data.get("state") or data.get("status") or "queued",
                "video_url": ((data.get("assets") or {}).get("video") if isinstance(data.get("assets"), dict) else "") or "",
                "prompt": prompt,
                "model": model,
                "async": True,
            },
            model=model,
        )
