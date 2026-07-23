"""Shared HTTP client for production provider connectors.

Uses the stdlib so adapters do not require vendor SDKs. Supports timeouts,
JSON bodies, basic retries, and an injectable transport for tests.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class HttpResponse:
    status: int
    body: Any
    headers: dict = field(default_factory=dict)
    raw: bytes = b""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


Transport = Callable[["HttpRequest"], HttpResponse]


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    json_body: "dict | list | None" = None
    data: "bytes | None" = None
    timeout_sec: float = 60.0


_default_transport: "Transport | None" = None


def set_default_transport(transport: "Transport | None") -> None:
    """Override the global HTTP transport (tests / offline mode)."""
    global _default_transport
    _default_transport = transport


def get_default_transport() -> Transport:
    return _default_transport or urllib_transport


def urllib_transport(request: HttpRequest) -> HttpResponse:
    """Stdlib urllib transport — production default."""
    headers = {"Accept": "application/json", **request.headers}
    body = request.data
    if request.json_body is not None:
        body = json.dumps(request.json_body).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(
        request.url,
        data=body,
        headers=headers,
        method=request.method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=request.timeout_sec) as resp:
            raw = resp.read()
            parsed: Any = raw
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "application/json" in content_type or raw[:1] in (b"{", b"["):
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    parsed = raw
            return HttpResponse(
                status=getattr(resp, "status", 200),
                body=parsed,
                headers=dict(resp.headers.items()),
                raw=raw if isinstance(raw, (bytes, bytearray)) else b"",
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read() if hasattr(exc, "read") else b""
        parsed: Any = raw
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            parsed = raw.decode("utf-8", errors="replace") if raw else str(exc)
        return HttpResponse(status=exc.code, body=parsed, headers=dict(exc.headers.items()) if exc.headers else {}, raw=raw)
    except urllib.error.URLError as exc:
        return HttpResponse(status=0, body={"error": str(exc.reason)}, headers={}, raw=b"")


def request_json(
    method: str,
    url: str,
    *,
    headers: "dict | None" = None,
    json_body: "dict | list | None" = None,
    data: "bytes | None" = None,
    timeout_sec: float = 60.0,
    retries: int = 1,
    transport: "Transport | None" = None,
) -> HttpResponse:
    """Perform an HTTP request with optional retries on transient failures."""
    transport = transport or get_default_transport()
    req = HttpRequest(
        method=method,
        url=url,
        headers=headers or {},
        json_body=json_body,
        data=data,
        timeout_sec=timeout_sec,
    )
    last = HttpResponse(status=0, body={"error": "no attempt"})
    for attempt in range(max(1, retries + 1)):
        last = transport(req)
        # Do not retry hard client errors; do retry throttling / server / network.
        if last.ok or last.status in (400, 401, 403, 404, 422):
            return last
        if attempt < retries:
            # Intelligent backoff — slower for rate limits (429) / quota pressure
            factor = 1.5 if last.status == 429 else 0.2
            time.sleep(min(factor * (attempt + 1), 3.0))
    return last
