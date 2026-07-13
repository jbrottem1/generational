"""Additional production connectors — xAI, Fal, Replicate, ComfyUI, Ollama."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


class XAIConnector(ProductionConnector):
    name = "xai"
    label = "xAI (Grok)"
    api_key_env = "XAI_API_KEY"
    base_url = "https://api.x.ai/v1"
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.METADATA)
    profile = ProviderProfile(quality=86, cost_per_unit=0.018, speed=82, consistency=80, latency_ms=3500)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        system = str(request.payload.get("system_prompt") or "You are a helpful assistant.")
        user = str(request.payload.get("prompt") or request.payload.get("user_prompt") or "")
        if not user:
            return self.fail(request, "Missing prompt")
        model = self.resolved_model(request, "grok-2-latest")
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": bool(request.payload.get("stream")),
        }
        if request.payload.get("json"):
            body["response_format"] = {"type": "json_object"}
        resp = self.http("POST", "/chat/completions", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"xAI error: {resp.status} {resp.body}")
        choice = ((resp.body or {}).get("choices") or [{}])[0]
        text = str(((choice.get("message") or {}).get("content")) or "")
        usage = (resp.body or {}).get("usage") or {}
        return self.ok(
            request,
            {"text": text, "content": text, "script": text},
            tokens_used=int(usage.get("total_tokens") or 0),
            model=model,
        )

    def _health_probe(self):
        return self.http("GET", "/models", timeout_sec=15.0, retries=0)


class FalConnector(ProductionConnector):
    name = "fal_ai"
    label = "Fal.ai"
    api_key_env = "FAL_KEY"
    base_url = "https://queue.fal.run"
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.ANIMATION,
        cap.UPSCALING, cap.LIP_SYNC,
    )
    profile = ProviderProfile(quality=83, cost_per_unit=0.06, speed=70, consistency=74, latency_ms=12000)

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Key {self.api_key()}", "Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or "")
        if not prompt:
            return self.fail(request, "Missing prompt")
        model = self.resolved_model(request, "fal-ai/flux/dev")
        is_video = request.operation in ("generate_video", "generate_animation") or request.capability in (
            cap.VIDEO_GENERATION, cap.ANIMATION,
        )
        if is_video:
            model = self.resolved_model(request, "fal-ai/minimax-video")
        path = model if model.startswith("fal-ai/") else f"fal-ai/{model}"
        body = {"prompt": prompt}
        if is_video:
            body["duration"] = str(request.payload.get("duration_sec") or 5)
        resp = self.http("POST", f"/{path}", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Fal.ai error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        images = data.get("images") or []
        image_url = (images[0] or {}).get("url") if images else data.get("image", {}).get("url", "")
        video_url = (data.get("video") or {}).get("url") if isinstance(data.get("video"), dict) else data.get("video_url", "")
        return self.ok(
            request,
            {
                "job_id": data.get("request_id") or data.get("id") or "",
                "image_url": image_url or "",
                "video_url": video_url or "",
                "status": data.get("status") or "completed",
                "prompt": prompt,
                "model": model,
                "async": bool(data.get("request_id") and not (image_url or video_url)),
            },
            model=model,
        )


class ReplicateConnector(ProductionConnector):
    name = "replicate"
    label = "Replicate"
    api_key_env = "REPLICATE_API_TOKEN"
    base_url = "https://api.replicate.com/v1"
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.UPSCALING,
        cap.IMAGE_EDITING, cap.ANIMATION,
    )
    profile = ProviderProfile(quality=80, cost_per_unit=0.08, speed=65, consistency=72, latency_ms=15000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or "")
        if not prompt:
            return self.fail(request, "Missing prompt")
        model = self.resolved_model(request, "black-forest-labs/flux-schnell")
        body = {
            "input": {
                "prompt": prompt,
                "width": int(request.payload.get("width") or 1024),
                "height": int(request.payload.get("height") or 1024),
            }
        }
        # Prefer model versions endpoint when version id provided
        version = str(request.payload.get("version") or "")
        if version:
            resp = self.http(
                "POST", "/predictions",
                json_body={"version": version, "input": body["input"]},
                timeout_sec=request.timeout_sec,
            )
        else:
            resp = self.http(
                "POST", f"/models/{model}/predictions",
                json_body=body,
                timeout_sec=request.timeout_sec,
            )
        if not resp.ok:
            return self.fail(request, f"Replicate error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        output = data.get("output")
        uri = ""
        if isinstance(output, list) and output:
            uri = str(output[0])
        elif isinstance(output, str):
            uri = output
        return self.ok(
            request,
            {
                "job_id": data.get("id") or "",
                "status": data.get("status") or "starting",
                "image_url": uri,
                "uri": uri,
                "prompt": prompt,
                "model": model,
                "async": data.get("status") not in ("succeeded", "completed"),
                "urls": data.get("urls") or {},
            },
            model=model,
        )

    def _health_probe(self):
        return self.http("GET", "/account", timeout_sec=15.0, retries=0)


class ComfyUIConnector(ProductionConnector):
    name = "comfyui"
    label = "ComfyUI"
    api_key_env = "COMFYUI_ENDPOINT"
    offline = True
    local = True
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.UPSCALING,
        cap.IMAGE_EDITING, cap.RENDERING,
    )
    profile = ProviderProfile(quality=78, cost_per_unit=0.0, speed=50, consistency=82, latency_ms=20000)
    implementation_status = "production"

    def is_available(self) -> bool:
        from services.provider_runtime.config import get_credential

        return bool(get_credential(self.api_key_env, self._credential_overrides()))

    def api_key(self) -> str:
        from services.provider_runtime.config import get_credential

        return get_credential(self.api_key_env, self._credential_overrides())

    @property
    def base_url(self) -> str:  # type: ignore[override]
        return self.api_key().rstrip("/")

    def auth_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or "")
        if not prompt:
            return self.fail(request, "Missing prompt")
        endpoint = self.api_key()
        if not endpoint:
            return self.fail(request, "COMFYUI_ENDPOINT not configured")
        # Minimal text-to-image workflow submission
        workflow = request.payload.get("workflow") or {
            "3": {
                "class_type": "KSampler",
                "inputs": {"seed": int(request.payload.get("seed") or 0), "steps": 20},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt},
            },
        }
        resp = self.http(
            "POST",
            "/prompt",
            json_body={"prompt": workflow},
            absolute_url=f"{endpoint.rstrip('/')}/prompt",
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"ComfyUI error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("prompt_id") or "",
                "status": "queued",
                "prompt": prompt,
                "async": True,
                "local": True,
            },
        )

    def _health_probe(self):
        endpoint = self.api_key()
        return self.http("GET", "/system_stats", absolute_url=f"{endpoint.rstrip('/')}/system_stats", timeout_sec=10.0, retries=0)


class OllamaConnector(ProductionConnector):
    name = "ollama"
    label = "Ollama"
    api_key_env = "OLLAMA_HOST"
    offline = True
    local = True
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.METADATA)
    profile = ProviderProfile(quality=70, cost_per_unit=0.0, speed=60, consistency=75, latency_ms=8000)
    implementation_status = "production"

    def is_available(self) -> bool:
        from services.provider_runtime.config import get_credential, has_credential

        # Available when host is configured; default localhost only if explicitly set or offline probe desired.
        host = get_credential(self.api_key_env, self._credential_overrides())
        return bool(host)

    def api_key(self) -> str:
        from services.provider_runtime.config import get_credential

        return get_credential(self.api_key_env, self._credential_overrides()) or "http://127.0.0.1:11434"

    @property
    def base_url(self) -> str:  # type: ignore[override]
        return self.api_key().rstrip("/")

    def auth_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        system = str(request.payload.get("system_prompt") or "")
        user = str(request.payload.get("prompt") or request.payload.get("user_prompt") or "")
        if not user:
            return self.fail(request, "Missing prompt")
        model = self.resolved_model(request, "llama3.2")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = {"model": model, "messages": messages, "stream": bool(request.payload.get("stream", False))}
        resp = self.http(
            "POST",
            "/api/chat",
            json_body=body,
            absolute_url=f"{self.base_url}/api/chat",
            timeout_sec=request.timeout_sec,
        )
        if not resp.ok:
            return self.fail(request, f"Ollama error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        text = str(((data.get("message") or {}).get("content")) or data.get("response") or "")
        return self.ok(request, {"text": text, "content": text, "script": text}, model=model, local=True)

    def _health_probe(self):
        return self.http("GET", "/api/tags", absolute_url=f"{self.base_url}/api/tags", timeout_sec=10.0, retries=0)


PLATFORM_CONNECTOR_CLASSES = (
    XAIConnector,
    FalConnector,
    ReplicateConnector,
    ComfyUIConnector,
    OllamaConnector,
)
