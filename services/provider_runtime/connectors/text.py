"""Text / LLM production connectors — OpenAI, Anthropic, Google Gemini."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


def _text_prompt(payload: dict) -> tuple[str, str]:
    system = str(payload.get("system_prompt") or payload.get("system") or "You are a helpful assistant.")
    user = str(
        payload.get("prompt")
        or payload.get("text")
        or payload.get("script")
        or payload.get("content")
        or ""
    )
    return system, user


def _extract_text_data(operation: str, text: str, payload: dict) -> dict:
    data = {"text": text, "content": text}
    if operation in ("generate_script",) or "script" in operation:
        data["script"] = text
    if operation in ("generate_caption",):
        data["caption"] = text
    if operation in ("generate_subtitles",):
        data["subtitles"] = text
    if operation in ("generate_metadata",):
        data["metadata_text"] = text
        data["title"] = payload.get("title") or text.split("\n", 1)[0][:120]
    return data


class OpenAIConnector(ProductionConnector):
    name = "openai"
    label = "OpenAI"
    api_key_env = "OPENAI_API_KEY"
    base_url = "https://api.openai.com/v1"
    capabilities = (
        cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE,
        cap.METADATA, cap.IMAGE_GENERATION,
    )
    profile = ProviderProfile(quality=92, cost_per_unit=0.02, speed=80, consistency=85, latency_ms=3000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        if request.operation == "generate_image" or request.capability == cap.IMAGE_GENERATION:
            return self._generate_image(request)
        return self._chat(request)

    def _chat(self, request: ProviderRequest) -> ProviderResponse:
        system, user = _text_prompt(request.payload)
        if not user:
            return self.fail(request, "Missing prompt/text in payload")
        model = self.resolved_model(request, "gpt-4o-mini")
        if request.payload.get("stream"):
            from services.provider_runtime.streaming import stream_chat_completions, streaming_response

            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": float(request.payload.get("temperature", 0.7)),
            }
            text, usage = stream_chat_completions(
                f"{self.base_url}/chat/completions",
                headers=self.auth_headers(),
                body=body,
                timeout_sec=request.timeout_sec,
            )
            return streaming_response(
                request, self.name, text,
                tokens_used=int(usage.get("total_tokens") or 0),
                model=model,
            )
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": float(request.payload.get("temperature", 0.7)),
        }
        if request.payload.get("json"):
            body["response_format"] = {"type": "json_object"}
        resp = self.http("POST", "/chat/completions", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"OpenAI chat error: {resp.status} {resp.body}")
        choice = (resp.body or {}).get("choices") or [{}]
        message = (choice[0] or {}).get("message") or {}
        text = str(message.get("content") or "")
        usage = (resp.body or {}).get("usage") or {}
        tokens = int(usage.get("total_tokens") or 0)
        return self.ok(
            request,
            _extract_text_data(request.operation, text, request.payload),
            tokens_used=tokens,
            model=model,
        )

    def _generate_image(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or request.payload.get("text") or "")
        if not prompt:
            return self.fail(request, "Missing image prompt")
        width = int(request.payload.get("width") or 1024)
        height = int(request.payload.get("height") or 1024)
        preferred = str(request.payload.get("model") or "gpt-image-1")
        # Ignore chat/LLM model ids leaked from Studio project settings
        if not preferred.startswith(("gpt-image", "dall-e", "chatgpt-image")):
            preferred = "gpt-image-1"
        models = [preferred] + [m for m in ("gpt-image-1", "dall-e-3", "dall-e-2") if m != preferred]
        last_error = ""
        for model in models:
            if model.startswith("gpt-image"):
                size = "1024x1536" if height >= width else "1536x1024"
            elif model == "dall-e-3":
                size = "1024x1792" if height >= width else "1792x1024"
            else:
                size = "1024x1024"
            explicit = str(request.payload.get("size") or "")
            if explicit in {"1024x1024", "1024x1536", "1536x1024", "1024x1792", "1792x1024", "256x256", "512x512"}:
                # Only apply explicit size when compatible; vertical dall-e-3 needs 1024x1792
                if model == "dall-e-3" and height >= width:
                    size = "1024x1792"
                elif model.startswith("gpt-image") and height >= width:
                    size = "1024x1536"
                else:
                    size = explicit
            body = {
                "model": model,
                "prompt": prompt[:3900],
                "n": 1,
                "size": size,
            }
            resp = self.http("POST", "/images/generations", json_body=body, timeout_sec=request.timeout_sec)
            if not resp.ok:
                last_error = f"OpenAI image error ({model}/{size}): {resp.status} {resp.body}"
                body_text = str(resp.body or "").lower()
                if "does not exist" in body_text or "invalid" in body_text or resp.status in {400, 404}:
                    continue
                return self.fail(request, last_error)
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
        return self.fail(request, last_error or "OpenAI image failed for all models")

    def _health_probe(self):
        return self.http("GET", "/models", timeout_sec=15.0, retries=0)


class AnthropicConnector(ProductionConnector):
    name = "anthropic"
    label = "Anthropic"
    api_key_env = "ANTHROPIC_API_KEY"
    base_url = "https://api.anthropic.com/v1"
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE, cap.METADATA)
    profile = ProviderProfile(quality=91, cost_per_unit=0.025, speed=75, consistency=84, latency_ms=3500)

    def auth_headers(self) -> dict[str, str]:
        key = self.api_key()
        ver = self._version_manager.get(self.name).api_version
        return {
            "x-api-key": key,
            "anthropic-version": ver or "2023-06-01",
            "content-type": "application/json",
        }

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        system, user = _text_prompt(request.payload)
        if not user:
            return self.fail(request, "Missing prompt/text in payload")
        # Ignore cross-vendor model ids (e.g. gpt-4o-mini) from shared Studio settings.
        payload_model = str(request.payload.get("model") or "")
        if payload_model.startswith(("gpt-", "o1", "o3", "gemini-", "grok-")):
            model = "claude-haiku-4-5-20251001"
        else:
            model = self.resolved_model(request, "claude-haiku-4-5-20251001")
        body = {
            "model": model,
            "max_tokens": int(request.payload.get("max_tokens") or 2048),
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        resp = self.http("POST", "/messages", json_body=body, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Anthropic error: {resp.status} {resp.body}")
        content = (resp.body or {}).get("content") or []
        text_parts = [str(block.get("text") or "") for block in content if isinstance(block, dict)]
        text = "".join(text_parts)
        usage = (resp.body or {}).get("usage") or {}
        tokens = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
        return self.ok(
            request,
            _extract_text_data(request.operation, text, request.payload),
            tokens_used=tokens,
            model=model,
        )

    def _health_probe(self):
        # Anthropic has no cheap public ping; credential presence is the gate.
        from services.provider_runtime.http_client import HttpResponse

        return HttpResponse(status=200, body={"status": "credential_present"})


class GoogleGeminiConnector(ProductionConnector):
    name = "google_gemini"
    label = "Google Gemini"
    api_key_env = "GOOGLE_API_KEY"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    capabilities = (
        cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE,
        cap.METADATA, cap.IMAGE_GENERATION,
    )
    profile = ProviderProfile(quality=88, cost_per_unit=0.015, speed=78, consistency=80, latency_ms=4000)

    def auth_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        system, user = _text_prompt(request.payload)
        if not user and request.operation != "generate_image":
            return self.fail(request, "Missing prompt/text in payload")
        if request.operation == "generate_image" or request.capability == cap.IMAGE_GENERATION:
            # Gemini image generation uses the same generateContent path with image modality when available.
            prompt = str(request.payload.get("prompt") or user)
            return self._generate_content(request, prompt, image_mode=True)
        return self._generate_content(request, f"{system}\n\n{user}" if system else user)

    def _generate_content(self, request: ProviderRequest, prompt: str, image_mode: bool = False) -> ProviderResponse:
        model = self.resolved_model(request, "gemini-1.5-flash")
        key = self.api_key()
        url = f"{self.base_url}/models/{model}:generateContent?key={key}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if image_mode:
            body["generationConfig"] = {"responseModalities": ["TEXT", "IMAGE"]}
        resp = self.http("POST", "/", json_body=body, absolute_url=url, timeout_sec=request.timeout_sec)
        if not resp.ok:
            return self.fail(request, f"Gemini error: {resp.status} {resp.body}")
        candidates = (resp.body or {}).get("candidates") or []
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or []) if candidates else []
        text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
        image_b64 = ""
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            if inline.get("data"):
                image_b64 = str(inline["data"])
                break
        data = _extract_text_data(request.operation, text, request.payload)
        if image_b64:
            data["b64_json"] = image_b64
            data["image_url"] = ""
        usage = (resp.body or {}).get("usageMetadata") or {}
        tokens = int(usage.get("totalTokenCount") or 0)
        return self.ok(request, data, tokens_used=tokens, model=model)

    def _health_probe(self):
        key = self.api_key()
        url = f"{self.base_url}/models?key={key}"
        return self.http("GET", "/", absolute_url=url, timeout_sec=15.0, retries=0)
