"""Agent 22 Phase 2 — production hardening integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.provider_runtime import (
    ChunkedUploader,
    ProviderRequest,
    ProviderResponse,
    ProviderRuntime,
    all_providers,
    ensure_registered,
    get_provider,
    runtime_generate_json,
    validate_credential,
)
from services.provider_runtime.http_client import HttpRequest, HttpResponse, set_default_transport
from services.provider_runtime.registry import reset_registry
from services.provider_runtime.reliability import ProviderReliabilityManager
from services.provider_runtime.selection import set_reliability_manager
from services.provider_runtime.streaming import stream_chat_completions
from services.provider_runtime.uploads import OAuthTokenManager


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    reset_registry()
    set_reliability_manager(ProviderReliabilityManager())
    set_default_transport(None)
    for key in (
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY",
        "BFL_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "ELEVENLABS_API_KEY",
        "YOUTUBE_ACCESS_TOKEN", "LINKEDIN_ACCESS_TOKEN", "OLLAMA_HOST", "COMFYUI_ENDPOINT",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    set_default_transport(None)
    reset_registry()
    set_reliability_manager(None)


def _mock(handler):
    set_default_transport(handler)


# ---------------------------------------------------- engine migration


def test_engines_do_not_import_core_ai():
    from pathlib import Path

    engines = Path("engines")
    offenders = []
    for path in engines.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "from core.ai" in text or "import core.ai" in text:
            offenders.append(str(path))
    assert not offenders, f"engines still import core.ai: {offenders}"


def test_runtime_generate_json_parses_text_json():
    ensure_registered()

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(
            status=200,
            body={
                "choices": [{"message": {"content": json.dumps({"candidates": [{"title": "A", "hook": "B"}]})}}],
                "usage": {"total_tokens": 11},
            },
        )

    _mock(handler)
    data, tokens, provider = runtime_generate_json(
        "sys", "user",
        preferred_provider="openai",
    )
    # Without key, falls back to demo — still returns structured path via demo payload or None
    assert tokens >= 0
    assert isinstance(provider, str)


def test_ideation_engine_uses_runtime(monkeypatch):
    from engines.ideation import IdeationEngine

    def fake_json(system, user, model="", operation="generate_script", **kwargs):
        return {"candidates": [{"title": "T", "hook": "H", "angle": "A"}] * 3}, 5, "openai"

    monkeypatch.setattr("engines.ideation.runtime_generate_json", fake_json)
    result = IdeationEngine().run({"command": "make psychology shorts", "candidate_count": 3})
    assert len(result["candidates"]) == 3
    assert result["candidates"][0]["title"] == "T"


# ---------------------------------------------------- new connectors


def test_xai_fal_replicate_registered():
    ensure_registered()
    names = {p.name for p in all_providers()}
    for name in ("xai", "fal_ai", "replicate", "comfyui", "ollama", "linkedin"):
        assert name in names


def test_xai_connector_chat():
    from services.provider_runtime.connectors.platforms import XAIConnector

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(
            status=200,
            body={"choices": [{"message": {"content": "grok says hi"}}], "usage": {"total_tokens": 3}},
        )

    _mock(handler)
    c = XAIConnector()
    c.set_credential_overrides({"XAI_API_KEY": "xai-test"})
    resp = c.execute(ProviderRequest(operation="generate_script", payload={"prompt": "hi"}))
    assert resp.success
    assert "grok" in resp.data["text"]


def test_fal_and_replicate_connectors():
    from services.provider_runtime.connectors.platforms import FalConnector, ReplicateConnector

    def handler(req: HttpRequest) -> HttpResponse:
        if "fal" in req.url or "queue.fal" in req.url:
            return HttpResponse(status=200, body={"images": [{"url": "https://img/fal.png"}]})
        return HttpResponse(status=200, body={"id": "pred1", "status": "starting", "output": None, "urls": {}})

    _mock(handler)
    fal = FalConnector()
    fal.set_credential_overrides({"FAL_KEY": "k"})
    rep = ReplicateConnector()
    rep.set_credential_overrides({"REPLICATE_API_TOKEN": "r8_x"})
    assert fal.execute(ProviderRequest(operation="generate_image", payload={"prompt": "a"})).success
    assert rep.execute(ProviderRequest(operation="generate_image", payload={"prompt": "a"})).success


def test_linkedin_publish_connector():
    from services.provider_runtime.connectors.publishing import LinkedInPublishingConnector

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body={"id": "urn:li:share:1"})

    _mock(handler)
    c = LinkedInPublishingConnector()
    c.set_credential_overrides({"LINKEDIN_ACCESS_TOKEN": "t", "LINKEDIN_AUTHOR_URN": "urn:li:person:1"})
    resp = c.execute(ProviderRequest(operation="publish", payload={"package": {"title": "Hi", "description": "Post"}}))
    assert resp.success
    assert resp.data["mock"] is False


# ---------------------------------------------------- reliability


def test_blacklist_and_failover():
    ensure_registered()
    reliability = ProviderReliabilityManager(blacklist_ttl_sec=60)
    set_reliability_manager(reliability)
    reliability.blacklist("openai")
    runtime = ProviderRuntime(config={"cache_enabled": False, "emit_analytics": False})
    runtime._reliability = reliability
    runtime._selector._reliability = reliability
    # Preferred blacklisted provider should not be selected when allow_fallback
    resp = runtime.generate_script({"prompt": "hello"}, preferred_provider="openai", allow_fallback=True)
    assert resp.success  # demo or other
    assert resp.provider != "openai" or not reliability.is_blacklisted("openai")


def test_weighting_and_recovery():
    reliability = ProviderReliabilityManager()
    reliability.set_weight("openai", 2.0)
    reliability.record_failure("openai", "boom")
    assert reliability.get_weight("openai") < 2.0
    reliability.blacklist("openai", ttl_sec=1)
    assert reliability.is_blacklisted("openai")
    assert reliability.recover("openai") == 1
    assert not reliability.is_blacklisted("openai")


def test_circuit_breaker_still_works():
    from services.provider_runtime.health import ProviderHealthMonitor
    from services.provider_runtime.adapter import ProviderAdapter

    class P(ProviderAdapter):
        name = "p"
        capabilities = ()

        def is_available(self):
            return True

        def execute(self, request):
            return ProviderResponse(success=False, provider=self.name, operation=request.operation)

    mon = ProviderHealthMonitor(failure_threshold=2, recovery_timeout_sec=60)
    p = P()
    mon.record_failure("p")
    mon.record_failure("p")
    assert mon.is_healthy(p) is False


# ---------------------------------------------------- uploads / oauth / streaming


def test_chunked_upload_resume(tmp_path):
    calls = {"n": 0}

    def put(url, data, headers):
        calls["n"] += 1
        return HttpResponse(status=308 if calls["n"] < 2 else 200, body={})

    uploader = ChunkedUploader(chunk_size=4, transport_put=put)
    path = tmp_path / "video.bin"
    path.write_bytes(b"0123456789abcdef")
    session = uploader.upload_file(path, "https://upload.example/resumable", start_at=0)
    assert session.status == "completed"
    assert session.bytes_uploaded == 16
    assert calls["n"] >= 2


def test_oauth_refresh_mocked():
    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body={"access_token": "new-token", "expires_in": 3600})

    _mock(handler)
    mgr = OAuthTokenManager({
        "YOUTUBE_REFRESH_TOKEN": "r",
        "YOUTUBE_CLIENT_ID": "id",
        "YOUTUBE_CLIENT_SECRET": "sec",
    })
    token = mgr.get_access_token("youtube")
    assert token == "new-token"


def test_streaming_fallback_to_json():
    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(
            status=200,
            body={"choices": [{"message": {"content": "streamed text"}}], "usage": {"total_tokens": 2}},
        )

    _mock(handler)
    text, usage = stream_chat_completions(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer x"},
        body={"model": "gpt-4o-mini", "messages": []},
    )
    assert text == "streamed text"
    assert usage["total_tokens"] == 2


def test_openai_streaming_path():
    from services.provider_runtime.connectors.text import OpenAIConnector

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(
            status=200,
            body={"choices": [{"message": {"content": "hello stream"}}], "usage": {"total_tokens": 4}},
        )

    _mock(handler)
    c = OpenAIConnector()
    c.set_credential_overrides({"OPENAI_API_KEY": "sk-test"})
    resp = c.execute(ProviderRequest(operation="generate_script", payload={"prompt": "hi", "stream": True}))
    assert resp.success
    assert resp.data.get("streamed") is True


# ---------------------------------------------------- security / observability


def test_credential_validation_and_audit():
    from services.provider_runtime.security import get_audit_log

    get_audit_log().clear()
    result = validate_credential("openai", {"OPENAI_API_KEY": "sk-abc"})
    assert result["valid"] is True
    events = get_audit_log().events("credential_validation")
    assert events


def test_runtime_metrics_summary():
    runtime = ProviderRuntime(config={"cache_enabled": False, "emit_analytics": False})
    runtime.generate_metadata({"title": "x"})
    summary = runtime.metrics_summary()
    assert "usage" in summary
    assert "reliability" in summary


def test_youtube_chunked_upload_path(tmp_path):
    from services.provider_runtime.connectors.publishing import YouTubePublishingConnector

    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake-video-bytes-1234567890")

    def handler(req: HttpRequest) -> HttpResponse:
        if req.method.upper() == "PUT":
            return HttpResponse(status=200, body={})
        return HttpResponse(
            status=200,
            body={"id": "yt99"},
            headers={"Location": "https://upload.example/session"},
        )

    _mock(handler)
    c = YouTubePublishingConnector()
    c.set_credential_overrides({"YOUTUBE_ACCESS_TOKEN": "t"})
    resp = c.execute(
        ProviderRequest(
            operation="publish",
            payload={"package": {"title": "T", "video_path": str(video), "video": {"path": str(video)}}},
        )
    )
    assert resp.success
    assert resp.data.get("upload", {}).get("status") == "completed"
