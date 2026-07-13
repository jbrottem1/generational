"""Voice production connectors — ElevenLabs and OpenAI TTS."""

from __future__ import annotations

import base64

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
        voice_id = str(request.payload.get("voice_id") or "21m00Tcm4TlvDq8ikWAM")
        model = self.resolved_model(request, "eleven_multilingual_v2")
        body = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": float(request.payload.get("stability") or 0.5),
                "similarity_boost": float(request.payload.get("similarity_boost") or 0.75),
            },
        }
        # Prefer timestamped endpoint when requested (word-level alignment).
        with_ts = bool(request.payload.get("with_timestamps"))
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
                    headers={"Accept": "application/json"},
                )
            if not resp.ok and resp.status != 0:
                return self.fail(request, f"ElevenLabs TTS error: {resp.status} {resp.body}")
        audio_b64 = ""
        audio_url = ""
        word_timestamps: list = []
        if isinstance(resp.body, dict):
            audio_b64 = str(resp.body.get("audio_base64") or "")
            audio_url = str(resp.body.get("url") or "")
            alignment = resp.body.get("alignment") or resp.body.get("normalized_alignment") or {}
            chars = alignment.get("characters") or []
            starts = alignment.get("character_start_times_seconds") or []
            ends = alignment.get("character_end_times_seconds") or []
            if chars and starts and ends:
                # Collapse character alignment into rough word spans.
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
        elif isinstance(resp.raw, (bytes, bytearray)) and resp.raw:
            audio_b64 = base64.b64encode(bytes(resp.raw)).decode("ascii")
        elif isinstance(resp.body, (bytes, bytearray)):
            audio_b64 = base64.b64encode(bytes(resp.body)).decode("ascii")
        duration = 0.0
        if word_timestamps:
            duration = float(word_timestamps[-1].get("end") or 0)
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
        return self.http("GET", "/user", timeout_sec=15.0, retries=0, headers={"Accept": "application/json"})


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
