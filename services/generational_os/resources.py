"""GenOS resource management — API usage, credits, cost estimates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

RESOURCES_PATH = project_root() / "data" / "generational_os" / "RESOURCES.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if not RESOURCES_PATH.exists():
        return {
            "api_calls": {},
            "productions": [],
            "totals": {},
            "updated_at": "",
        }
    try:
        return json.loads(RESOURCES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"api_calls": {}, "productions": [], "totals": {}, "updated_at": ""}


def _save(data: dict[str, Any]) -> None:
    RESOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    RESOURCES_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def record_api_usage(provider: str, *, units: float = 1.0, kind: str = "call") -> None:
    data = _load()
    api = dict(data.get("api_calls") or {})
    row = dict(api.get(provider) or {"calls": 0, "units": 0.0})
    row["calls"] = int(row.get("calls") or 0) + 1
    row["units"] = float(row.get("units") or 0) + float(units)
    row["kind"] = kind
    row["last_at"] = _now()
    api[provider] = row
    data["api_calls"] = api
    _save(data)


def estimate_production_cost(
    *,
    length_sec: int = 45,
    narrator: str = "professor",
    used_elevenlabs: bool = True,
    used_images: int = 5,
    render_sec: float = 30.0,
) -> dict[str, Any]:
    """Rough operating cost model (USD) for planning — not billing truth."""
    # Heuristic rates
    el_chars = max(80, int(length_sec * 14))
    el_cost = (el_chars / 1000.0) * 0.30 if used_elevenlabs else 0.0
    image_cost = used_images * 0.04
    compute = (render_sec / 60.0) * 0.02
    total = round(el_cost + image_cost + compute, 4)
    return {
        "estimated_usd": total,
        "breakdown": {
            "elevenlabs_usd": round(el_cost, 4),
            "images_usd": round(image_cost, 4),
            "compute_usd": round(compute, 4),
        },
        "assumptions": {
            "length_sec": length_sec,
            "narrator": narrator,
            "el_chars": el_chars,
            "used_images": used_images,
            "render_sec": render_sec,
        },
    }


def record_production_resources(
    production_id: str,
    *,
    length_sec: int = 45,
    render_sec: float | None = None,
    elevenlabs_present: bool = False,
    storage_bytes: int = 0,
    processing_ms: int = 0,
) -> dict[str, Any]:
    cost = estimate_production_cost(
        length_sec=length_sec,
        used_elevenlabs=elevenlabs_present,
        render_sec=float(render_sec or 30),
    )
    row = {
        "production_id": production_id,
        "at": _now(),
        "length_sec": length_sec,
        "render_sec": render_sec,
        "storage_bytes": storage_bytes,
        "processing_ms": processing_ms,
        "elevenlabs": elevenlabs_present,
        "cost": cost,
    }
    data = _load()
    prods = list(data.get("productions") or [])
    prods.append(row)
    data["productions"] = prods[-200:]
    totals = dict(data.get("totals") or {})
    totals["productions"] = int(totals.get("productions") or 0) + 1
    totals["estimated_usd"] = round(float(totals.get("estimated_usd") or 0) + float(cost["estimated_usd"]), 4)
    totals["storage_bytes"] = int(totals.get("storage_bytes") or 0) + int(storage_bytes)
    data["totals"] = totals
    _save(data)
    return row


def snapshot_resources() -> dict[str, Any]:
    """Live + stored resource snapshot for dashboard."""
    data = _load()
    eleven = {"configured": False, "note": "credits not queried live"}
    try:
        import os

        from core.env import load_application_env

        load_application_env(create_if_missing=False)
        key = os.environ.get("ELEVENLABS_API_KEY") or ""
        eleven["configured"] = bool(key)
        eleven["key_present"] = bool(key)
    except Exception:  # noqa: BLE001
        pass

    # Storage — sample key OS roots only (avoid full-tree walks on huge media trees)
    storage = 0
    sample_roots = [
        project_root() / "data" / "generational_os",
        project_root() / "data" / "productions" / "_ops",
        project_root() / "data" / "trend_opportunity",
    ]
    try:
        for root in sample_roots:
            if not root.is_dir():
                continue
            for p in root.rglob("*"):
                if p.is_file():
                    try:
                        storage += p.stat().st_size
                    except OSError:
                        pass
    except OSError:
        storage = 0

    queue_util = {}
    try:
        from services.production_operations.queue import queue_summary

        queue_util = queue_summary()
    except Exception:  # noqa: BLE001
        queue_util = {}

    return {
        "generated_at": _now(),
        "api_usage": data.get("api_calls") or {},
        "elevenlabs": eleven,
        "model_usage": data.get("api_calls") or {},
        "storage_bytes": storage,
        "storage_mb": round(storage / (1024 * 1024), 2),
        "queue_utilization": queue_util,
        "totals": data.get("totals") or {},
        "recent_production_costs": (data.get("productions") or [])[-10:],
        "estimated_cost_per_production_usd": (
            round(
                float((data.get("totals") or {}).get("estimated_usd") or 0)
                / max(1, int((data.get("totals") or {}).get("productions") or 1)),
                4,
            )
        ),
        "path": str(RESOURCES_PATH),
    }
