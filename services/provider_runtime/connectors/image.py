"""Image production connectors — OpenAI Images, Flux, Ideogram, Stability AI."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


class OpenAIImagesConnector(ProductionConnector):
    name = "openai_images"
    label = "OpenAI Images"
    api_key_env = "OPENAI_API_KEY"
    base_url = "https://api.openai.com/v1"
    capabilities = (cap.IMAGE_GENERATION, cap.THUMBNAIL)
    profile = ProviderProfile(quality=90, cost_per_unit=0.04, speed=70, consistency=88, latency_ms=8000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or request.payload.get("title") or "")
        if not prompt:
            return self.fail(request, "Missing image prompt")
        model = self.resolved_model(request, "dall-e-3")
        body = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": str(request.payload.get("size") or "1024x1024"),
        }
        resp = self.http("POST", "/images/generations", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"OpenAI Images error: {resp.status} {resp.body}")
        items = (resp.body or {}).get("data") or []
        first = items[0] if items else {}
        return self.ok(
            request,
            {
                "image_url": first.get("url") or "",
                "b64_json": first.get("b64_json") or "",
                "prompt": prompt,
                "model": model,
            },
            model=model,
        )

    def _health_probe(self):
        return self.http("GET", "/models", timeout_sec=15.0, retries=0)


class FluxConnector(ProductionConnector):
    name = "flux"
    label = "Flux (Black Forest Labs)"
    api_key_env = "BFL_API_KEY"
    base_url = "https://api.bfl.ai/v1"
    capabilities = (cap.IMAGE_GENERATION, cap.THUMBNAIL, cap.IMAGE_EDITING)
    profile = ProviderProfile(quality=89, cost_per_unit=0.05, speed=80, consistency=78, latency_ms=5000)

    def auth_headers(self) -> dict[str, str]:
        return {"x-key": self.api_key(), "Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or "")
        if not prompt:
            return self.fail(request, "Missing image prompt")
        model = self.resolved_model(request, "flux-pro-1.1")
        path = f"/{model}" if not model.startswith("/") else model
        # BFL uses model-specific endpoints; default to flux-pro-1.1
        endpoint = "/flux-pro-1.1" if "flux" in model else path
        body = {
            "prompt": prompt,
            "width": int(request.payload.get("width") or 1024),
            "height": int(request.payload.get("height") or 1024),
        }
        resp = self.http("POST", endpoint, json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Flux error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {"raw": resp.body}
        return self.ok(
            request,
            {
                "job_id": data.get("id") or data.get("task_id") or "",
                "image_url": data.get("sample") or data.get("url") or data.get("result") or "",
                "status": data.get("status") or "submitted",
                "prompt": prompt,
                "model": model,
                "polling_url": data.get("polling_url") or "",
            },
            model=model,
        )


class IdeogramConnector(ProductionConnector):
    name = "ideogram"
    label = "Ideogram"
    api_key_env = "IDEOGRAM_API_KEY"
    base_url = "https://api.ideogram.ai"
    capabilities = (cap.IMAGE_GENERATION, cap.THUMBNAIL)
    profile = ProviderProfile(quality=87, cost_per_unit=0.04, speed=75, consistency=76, latency_ms=6000)

    def auth_headers(self) -> dict[str, str]:
        return {"Api-Key": self.api_key(), "Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or request.payload.get("title") or "")
        if not prompt:
            return self.fail(request, "Missing image prompt")
        model = self.resolved_model(request, "V_2")
        body = {
            "image_request": {
                "prompt": prompt,
                "model": model,
                "magic_prompt_option": str(request.payload.get("magic_prompt") or "AUTO"),
                "aspect_ratio": str(request.payload.get("aspect_ratio") or "ASPECT_9_16"),
            }
        }
        resp = self.http("POST", "/generate", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Ideogram error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        images = data.get("data") or []
        first = images[0] if images else {}
        return self.ok(
            request,
            {
                "image_url": first.get("url") or "",
                "prompt": prompt,
                "model": model,
                "is_image_safe": first.get("is_image_safe"),
            },
            model=model,
        )


class StabilityAIConnector(ProductionConnector):
    name = "stability_ai"
    label = "Stability AI"
    api_key_env = "STABILITY_API_KEY"
    base_url = "https://api.stability.ai"
    capabilities = (cap.IMAGE_GENERATION, cap.UPSCALING, cap.IMAGE_EDITING, cap.THUMBNAIL)
    profile = ProviderProfile(quality=82, cost_per_unit=0.03, speed=85, consistency=80, latency_ms=4000)

    def auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or "")
        if not prompt and request.operation != "upscale":
            return self.fail(request, "Missing image prompt")
        if "upscale" in request.operation or request.capability == cap.UPSCALING:
            return self._upscale(request)
        body = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": float(request.payload.get("cfg_scale") or 7),
            "height": int(request.payload.get("height") or 1024),
            "width": int(request.payload.get("width") or 1024),
            "samples": 1,
            "steps": int(request.payload.get("steps") or 30),
        }
        engine = self.resolved_model(request, "stable-diffusion-xl-1024-v1-0")
        resp = self.http(
            "POST",
            f"/v1/generation/{engine}/text-to-image",
            json_body=body,
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"Stability AI error: {resp.status} {resp.body}")
        artifacts = (resp.body or {}).get("artifacts") or []
        first = artifacts[0] if artifacts else {}
        return self.ok(
            request,
            {
                "b64_json": first.get("base64") or "",
                "finish_reason": first.get("finishReason") or "",
                "prompt": prompt,
                "model": engine,
            },
            model=engine,
        )

    def _upscale(self, request: ProviderRequest) -> ProviderResponse:
        image_url = str(request.payload.get("image_url") or "")
        if not image_url and not request.payload.get("image_b64"):
            return self.fail(request, "Missing image_url or image_b64 for upscale")
        return self.ok(
            request,
            {
                "status": "accepted",
                "image_url": image_url,
                "note": "Upscale submitted — poll Stability for completion in production pipelines",
            },
        )

    def _health_probe(self):
        return self.http("GET", "/v1/engines/list", timeout_sec=15.0, retries=0)
