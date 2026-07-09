"""Minimal internal HTTP API for production readiness and run control.

Endpoints:
  GET  /health
  GET  /ready
  GET  /readiness
  GET  /providers/health
  GET  /runs/{id}
  POST /runs
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

_RUN_ID_RE = re.compile(r"^/runs/([A-Za-z0-9_.\-]+)$")


def _json_bytes(payload: Any, status: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(payload, default=str).encode("utf-8")
    return status, body, "application/json"


def _handle_get(path: str) -> tuple[int, bytes, str]:
    if path == "/health":
        from core.constants import APP_VERSION

        return _json_bytes({"status": "ok", "version": APP_VERSION})

    if path == "/ready":
        from services.readiness import build_readiness_report

        report = build_readiness_report()
        ready = report.get("overall", 0) >= 90 and not any(
            "Continuous learning" in b for b in report.get("blockers", [])
        )
        return _json_bytes(
            {
                "ready": ready,
                "overall": report.get("overall"),
                "blockers": report.get("blockers", []),
            },
            200 if ready else 503,
        )

    if path == "/readiness":
        from services.readiness import build_readiness_report

        return _json_bytes(build_readiness_report())

    if path == "/providers/health":
        from services.provider_runtime import get_provider_runtime

        runtime = get_provider_runtime()
        health = runtime.health_report() if hasattr(runtime, "health_report") else {}
        return _json_bytes({"health": health, "catalog": runtime.catalog() if hasattr(runtime, "catalog") else []})

    match = _RUN_ID_RE.match(path)
    if match:
        run_id = match.group(1)
        try:
            from services.workflow_executor import get_workflow_executor

            executor = get_workflow_executor()
            run = executor.load_run(run_id)
            if run is None:
                return _json_bytes({"error": "run not found", "run_id": run_id}, 404)
            return _json_bytes(executor.get_status(run_id))
        except Exception as exc:  # noqa: BLE001
            return _json_bytes({"error": str(exc), "run_id": run_id}, 500)

    return _json_bytes({"error": "not found", "path": path}, 404)


def _handle_post(path: str, body: dict) -> tuple[int, bytes, str]:
    if path != "/runs":
        return _json_bytes({"error": "not found", "path": path}, 404)

    command = str(body.get("command") or "").strip()
    if not command:
        return _json_bytes({"error": "command is required"}, 400)

    options = dict(body.get("options") or {})
    publish_mode = str(body.get("publish_mode") or options.pop("publish_mode", "dry_run"))
    count = int(body.get("count", options.pop("count", 1)))
    model = str(body.get("model", options.pop("model", "demo")))
    threshold = int(body.get("threshold", options.pop("threshold", 0)))
    use_executor = bool(body.get("workflow_executor", False))

    try:
        if use_executor:
            from services.workflow_executor import WorkflowConfig, get_workflow_executor

            cfg = WorkflowConfig(
                publish_mode=publish_mode,
                count=count,
                model=model,
            )
            run = get_workflow_executor().execute(
                command,
                cfg,
                context_extra={"threshold": threshold},
            )
            payload = run.to_dict() if hasattr(run, "to_dict") else {"run_id": getattr(run, "run_id", "")}
            return _json_bytes({"ok": True, "via": "workflow_executor", "run": payload})

        from services.orchestrator import get_orchestrator

        result = get_orchestrator().run_full_pipeline(
            command,
            count=count,
            model=model,
            threshold=threshold,
            publish_mode=publish_mode,
        )
        return _json_bytes({"ok": True, "via": "orchestrator", "result": result.to_dict()})
    except Exception as exc:  # noqa: BLE001
        return _json_bytes({"ok": False, "error": str(exc)}, 500)


def create_handler() -> type:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _normalize_path(self) -> str:
            path = urlparse(self.path).path or "/"
            if path != "/" and path.endswith("/"):
                path = path[:-1]
            return path or "/"

        def do_GET(self) -> None:  # noqa: N802
            path = self._normalize_path()
            if path == "/":
                path = "/health"
            status, body, ctype = _handle_get(path)
            self._send(status, body, ctype)

        def do_POST(self) -> None:  # noqa: N802
            path = self._normalize_path()
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._send(*_json_bytes({"error": "invalid JSON"}, 400))
                return
            if not isinstance(payload, dict):
                self._send(*_json_bytes({"error": "JSON object required"}, 400))
                return
            status, body, ctype = _handle_post(path, payload)
            self._send(status, body, ctype)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    """Start the internal API (blocking)."""
    from services.analytics.integration import enable_continuous_learning

    enable_continuous_learning()
    handler = create_handler()
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Generational internal API on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
