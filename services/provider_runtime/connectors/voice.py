"""Voice production connectors — ElevenLabs and OpenAI TTS."""

from __future__ import annotations

import base64
from typing import Any

from services.provider_runtime import capabilities as cap
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse


class ElevenLabsConnector(ProductionConnector):
    name = "elevenlabs"
    label = "ElevenLabs"
    api_key_env = "ELEVENLABS_API_KEY"
    base_url = "https://api.elevenlabs.io/v1"
    capabilities = (cap.SPEECH, cap.VOICE_CLONING, cap.SOUND_EFFECTS, cap.MUSIC)
    profile = ProviderProfile(quality=90, cost_per_unit=0.12, speed=70, consistency=85, latency_ms=6000)

    def auth_headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self.api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        if request.operation == "generate_sound_effects" or request.capability == cap.SOUND_EFFECTS:
            return self._sound_effects(request)
        if request.operation == "generate_music" or request.capability == cap.MUSIC:
            return self._music(request)
        return self._tts(request)

    def _tts(self, request: ProviderRequest) -> ProviderResponse:
        text = str(request.payload.get("text") or request.payload.get("script") or "")
        if not text:
            return self.fail(request, "Missing text for speech synthesis")
        from services.elevenlabs.config import get_elevenlabs_config

        cfg = get_elevenlabs_config()
        voice_id = str(
            request.payload.get("voice_id")
            or request.payload.get("provider_voice_id")
            or cfg["default_voice_id"]
            or "21m00Tcm4TlvDq8ikWAM"
        )
        model = str(request.payload.get("model") or request.payload.get("model_id") or "") or self.resolved_model(
            request, cfg["model_id"]
        )
        stability = float(request.payload.get("stability") or 0.5)
        similarity = float(request.payload.get("similarity_boost") or 0.75)
        with_ts = bool(request.payload.get("with_timestamps", True))

        # Prefer official SDK when enabled; fall back to HTTP connector path.
        if cfg.get("sdk_preferred"):
            sdk_result = self._tts_via_sdk(
                text=text,
                voice_id=voice_id,
                model=model,
                stability=stability,
                similarity=similarity,
                with_timestamps=with_ts,
                request=request,
            )
            if sdk_result is not None:
                return sdk_result

        body = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
            },
        }
        path = f"/text-to-speech/{voice_id}/with-timestamps" if with_ts else f"/text-to-speech/{voice_id}"
        resp = self.http(
            "POST",
            path,
            json_body=body,
            timeout_sec=request.timeout_sec,
            headers={"Accept": "application/json"},
        )
        # Some ElevenLabs responses are binary audio; JSON accept may still return audio bytes.
        if not resp.ok and resp.status != 0:
            # Fall back to non-timestamped endpoint once.
            if with_ts:
                resp = self.http(
                    "POST",
                    f"/text-to-speech/{voice_id}",
                    json_body=body,
                    timeout_sec=request.timeout_sec,
                    headers={"Accept": "audio/mpeg"},
                )
            if not resp.ok and resp.status != 0:
                return self.fail(request, f"ElevenLabs TTS error: {resp.status} {resp.body}")
        return self._pack_tts_response(request, resp, text=text, voice_id=voice_id, model=model)

    def _tts_via_sdk(
        self,
        *,
        text: str,
        voice_id: str,
        model: str,
        stability: float,
        similarity: float,
        with_timestamps: bool,
        request: ProviderRequest,
    ) -> ProviderResponse | None:
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError:
            return None
        try:
            client = ElevenLabs(api_key=self.api_key())
            word_timestamps: list = []
            audio_b64 = ""
            duration = 0.0
            if with_timestamps and hasattr(client.text_to_speech, "convert_with_timestamps"):
                result = client.text_to_speech.convert_with_timestamps(
                    voice_id=voice_id,
                    text=text,
                    model_id=model,
                    voice_settings={
                        "stability": stability,
                        "similarity_boost": similarity,
                    },
                )
                # SDK shapes vary across versions
                audio_b64 = str(getattr(result, "audio_base_64", None) or getattr(result, "audio_base64", None) or "")
                if not audio_b64 and isinstance(result, dict):
                    audio_b64 = str(result.get("audio_base64") or result.get("audio_base_64") or "")
                alignment = (
                    getattr(result, "alignment", None)
                    or getattr(result, "normalized_alignment", None)
                    or (result.get("alignment") if isinstance(result, dict) else None)
                    or {}
                )
                if alignment and not isinstance(alignment, dict):
                    alignment = {
                        "characters": getattr(alignment, "characters", None) or [],
                        "character_start_times_seconds": getattr(alignment, "character_start_times_seconds", None) or [],
                        "character_end_times_seconds": getattr(alignment, "character_end_times_seconds", None) or [],
                    }
                word_timestamps = self._chars_to_words(alignment if isinstance(alignment, dict) else {})
                if word_timestamps:
                    duration = float(word_timestamps[-1].get("end") or 0)
            else:
                stream = client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id=model,
                    output_format="mp3_44100_128",
                    voice_settings={
                        "stability": stability,
                        "similarity_boost": similarity,
                    },
                )
                chunks = []
                if hasattr(stream, "__iter__") and not isinstance(stream, (bytes, bytearray, str)):
                    for chunk in stream:
                        if chunk:
                            chunks.append(chunk if isinstance(chunk, (bytes, bytearray)) else bytes(chunk))
                    raw = b"".join(chunks)
                elif isinstance(stream, (bytes, bytearray)):
                    raw = bytes(stream)
                else:
                    raw = bytes(getattr(stream, "read", lambda: b"")() or b"")
                if not raw:
                    return None
                audio_b64 = base64.b64encode(raw).decode("ascii")
            if not audio_b64:
                return None
            return self.ok(
                request,
                {
                    "audio_b64": audio_b64,
                    "audio_url": "",
                    "voice_id": voice_id,
                    "text": text,
                    "model": model,
                    "format": "mp3",
                    "word_timestamps": word_timestamps,
                    "duration_sec": duration,
                    "ssml": "<speak" in text.lower(),
                    "transport": "sdk",
                },
                model=model,
            )
        except Exception:  # noqa: BLE001 — fall through to HTTP
            return None

    @staticmethod
    def _chars_to_words(alignment: dict) -> list:
        chars = alignment.get("characters") or []
        starts = alignment.get("character_start_times_seconds") or []
        ends = alignment.get("character_end_times_seconds") or []
        word_timestamps: list = []
        if not (chars and starts and ends):
            return word_timestamps
        buf = ""
        w_start = None
        for ch, s, e in zip(chars, starts, ends):
            if str(ch).isspace():
                if buf:
                    word_timestamps.append(
                        {"word": buf, "start": float(w_start or 0), "end": float(e), "index": len(word_timestamps)}
                    )
                    buf = ""
                    w_start = None
            else:
                if w_start is None:
                    w_start = s
                buf += str(ch)
        if buf:
            word_timestamps.append(
                {
                    "word": buf,
                    "start": float(w_start or 0),
                    "end": float(ends[-1] if ends else 0),
                    "index": len(word_timestamps),
                }
            )
        return word_timestamps

    def _pack_tts_response(
        self,
        request: ProviderRequest,
        resp: Any,
        *,
        text: str,
        voice_id: str,
        model: str,
    ) -> ProviderResponse:
        audio_b64 = ""
        audio_url = ""
        word_timestamps: list = []
        if isinstance(resp.body, dict):
            audio_b64 = str(resp.body.get("audio_base64") or "")
            audio_url = str(resp.body.get("url") or "")
            alignment = resp.body.get("alignment") or resp.body.get("normalized_alignment") or {}
            word_timestamps = self._chars_to_words(alignment if isinstance(alignment, dict) else {})
        elif isinstance(resp.raw, (bytes, bytearray)) and resp.raw:
            audio_b64 = base64.b64encode(bytes(resp.raw)).decode("ascii")
        elif isinstance(resp.body, (bytes, bytearray)):
            audio_b64 = base64.b64encode(bytes(resp.body)).decode("ascii")
        duration = 0.0
        if word_timestamps:
            duration = float(word_timestamps[-1].get("end") or 0)
        if not audio_b64 and not audio_url:
            return self.fail(request, "ElevenLabs TTS returned empty audio payload")
        return self.ok(
            request,
            {
                "audio_b64": audio_b64,
                "audio_url": audio_url,
                "voice_id": voice_id,
                "text": text,
                "model": model,
                "format": "mp3",
                "word_timestamps": word_timestamps,
                "duration_sec": duration,
                "ssml": "<speak" in text.lower(),
                "transport": "http",
            },
            model=model,
        )

    def _sound_effects(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or request.payload.get("text") or "")
        if not prompt:
            return self.fail(request, "Missing sound effect prompt")
        body = {
            "text": prompt,
            "duration_seconds": float(request.payload.get("duration_sec") or 2.0),
        }
        resp = self.http(
            "POST",
            "/sound-generation",
            json_body=body,
            timeout_sec=request.timeout_sec,
            headers={"Accept": "application/json"},
        )
        if not resp.ok:
            return self.fail(request, f"ElevenLabs SFX error: {resp.status} {resp.body}")
        audio_b64 = ""
        if isinstance(resp.raw, (bytes, bytearray)) and resp.raw:
            audio_b64 = base64.b64encode(bytes(resp.raw)).decode("ascii")
        return self.ok(request, {"audio_b64": audio_b64, "prompt": prompt, "format": "mp3"})

    def _music(self, request: ProviderRequest) -> ProviderResponse:
        prompt = str(request.payload.get("prompt") or request.payload.get("mood") or "")
        if not prompt:
            return self.fail(request, "Missing music prompt/mood")
        # ElevenLabs music API surface evolves; submit structured request.
        body = {
            "prompt": prompt,
            "music_length_ms": int(float(request.payload.get("duration_sec") or 30) * 1000),
        }
        resp = self.http(
            "POST",
            "/music",
            json_body=body,
            timeout_sec=request.timeout_sec,
            headers={"Accept": "application/json"},
        )
        if not resp.ok:
            return self.fail(request, f"ElevenLabs music error: {resp.status} {resp.body}")
        data = resp.body if isinstance(resp.body, dict) else {}
        return self.ok(
            request,
            {
                "job_id": data.get("composition_plan_id") or data.get("id") or "",
                "audio_url": data.get("url") or "",
                "prompt": prompt,
                "async": True,
            },
        )

    def _health_probe(self):
        # Prefer /voices — TTS-scoped API keys often lack user_read on /user.
        return self.http("GET", "/voices", timeout_sec=15.0, retries=0, headers={"Accept": "application/json"})


class OpenAITTSConnector(ProductionConnector):
    name = "openai_tts"
    label = "OpenAI TTS"
    api_key_env = "OPENAI_API_KEY"
    base_url = "https://api.openai.com/v1"
    capabilities = (cap.SPEECH,)
    profile = ProviderProfile(quality=82, cost_per_unit=0.015, speed=85, consistency=88, latency_ms=4000)

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        text = str(request.payload.get("text") or request.payload.get("script") or "")
        if not text:
            return self.fail(request, "Missing text for speech synthesis")
        model = self.resolved_model(request, "tts-1")
        voice = str(request.payload.get("voice") or "alloy")
        body = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": str(request.payload.get("format") or "mp3"),
        }
        resp = self.http(
            "POST",
            "/audio/speech",
            json_body=body,
            timeout_sec=request.timeout_sec,
            headers={"Accept": "audio/mpeg"},
        )
        if not resp.ok:
            return self.fail(request, f"OpenAI TTS error: {resp.status} {resp.body}")
        audio_b64 = ""
        if isinstance(resp.raw, (bytes, bytearray)) and resp.raw:
            audio_b64 = base64.b64encode(bytes(resp.raw)).decode("ascii")
        elif isinstance(resp.body, (bytes, bytearray)) and resp.body:
            audio_b64 = base64.b64encode(bytes(resp.body)).decode("ascii")
        if not audio_b64:
            return self.fail(request, "OpenAI TTS returned empty audio payload")
        return self.ok(
            request,
            {
                "audio_b64": audio_b64,
                "voice": voice,
                "text": text,
                "model": model,
                "format": body["response_format"],
            },
            model=model,
        )

    def _health_probe(self):
        return self.http("GET", "/models", timeout_sec=15.0, retries=0)


class LocalVoiceCloneConnector(ProductionConnector):
    """Future local voice-clone seam — same interface, unavailable until wired."""

    name = "local_voice_clone"
    label = "Local Voice Clone"
    api_key_env = "LOCAL_VOICE_CLONE_ENDPOINT"
    base_url = "http://127.0.0.1:7860"
    capabilities = (cap.SPEECH, cap.VOICE_CLONING)
    profile = ProviderProfile(quality=70, cost_per_unit=0.0, speed=50, consistency=70, latency_ms=8000)

    def is_configured(self) -> bool:
        return bool(self.api_key())

    def _execute_impl(self, request: ProviderRequest) -> ProviderResponse:
        return self.fail(
            request,
            "Local voice clone is reserved for a future on-device backend — use ElevenLabs or OpenAI TTS today.",
        )

    def _health_probe(self):
        return self.http("GET", "/health", timeout_sec=5.0, retries=0)
