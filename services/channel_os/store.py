"""Persist Channel Profiles + production index for Multi-Channel Media OS."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from core.storage.json_collection import JsonCollectionStore, slugify
from services.channel_os.profiles import normalize_profile
from services.channels import get_channel_manager

ROOT = project_root() / "data" / "channel_os"
PROFILES_DIR = ROOT / "profiles"
DB_PATH = ROOT / "CHANNEL_LIBRARY.db"
INDEX_JSON = ROOT / "CHANNEL_PROFILES.json"
PRODUCTIONS_JSON = ROOT / "CHANNEL_PRODUCTIONS.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_productions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                production_id TEXT,
                topic TEXT,
                category TEXT,
                created_at TEXT,
                success INTEGER,
                creative_score REAL,
                project_root TEXT,
                report_path TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ch_prod_channel ON channel_productions(channel_id)"
        )
        conn.commit()
    return ROOT


def _profile_store() -> JsonCollectionStore:
    ensure_store()
    return JsonCollectionStore(str(PROFILES_DIR))


def save_profile(profile: dict[str, Any], *, sync_legacy: bool = True) -> dict[str, Any]:
    """Save a Channel Profile and optionally sync to legacy ChannelManager."""
    ensure_store()
    profile = normalize_profile(profile)
    # Never persist plaintext credentials in channel JSON (use env / secrets manager)
    creds = profile.get("credentials")
    if isinstance(creds, dict) and any(str(v).strip() for v in creds.values() if v is not None):
        profile["credentials"] = {}
        profile["credentials_note"] = "stripped — set secrets via environment / secret manager, not profile JSON"
    else:
        profile["credentials"] = {}
    # Key files by brand_name for JsonCollectionStore
    profile["name"] = profile.get("brand_name") or profile["name"]
    _profile_store().save(profile)

    if sync_legacy:
        mgr = get_channel_manager()
        legacy_name = profile["name"]
        existing = mgr.get_channel(legacy_name)
        # build_channel only accepts a narrow kwargs set — create then enrich via update
        create_kwargs = {
            "brand_voice": profile.get("brand_voice") or profile.get("tone") or "",
            "platforms": profile.get("platforms") or [],
            "posting_schedule": profile.get("upload_schedule") or {},
            "credentials": profile.get("credentials") or {},
        }
        if existing:
            mgr.update_channel(legacy_name, niche=profile.get("niche") or "", **create_kwargs)
        else:
            mgr.create_channel(legacy_name, profile.get("niche") or "", **create_kwargs)
        mgr.update_channel(
            legacy_name,
            status=profile.get("status") or "active",
            metrics=profile.get("metrics") or {},
            channel_profile={
                k: profile.get(k)
                for k in (
                    "channel_id",
                    "description",
                    "target_audience",
                    "topic_categories",
                    "narrator_profile",
                    "voice_profile",
                    "visual_style",
                    "world_preferences",
                    "thumbnail_style",
                    "hashtag_strategy",
                    "seo_rules",
                    "monetization_status",
                    "publishing_status",
                )
            },
        )

    _refresh_profiles_index()
    return profile


def get_profile(channel_id_or_name: str) -> dict[str, Any] | None:
    ensure_store()
    store = _profile_store()
    direct = store.load(channel_id_or_name)
    if direct:
        return normalize_profile(direct)
    needle = channel_id_or_name.strip().lower().replace(" ", "_")
    for row in store.list_all():
        p = normalize_profile(row)
        if p.get("channel_id") == needle or slugify(p.get("brand_name") or "") == slugify(channel_id_or_name):
            return p
    return None


def list_profiles(*, status: str | None = "active") -> list[dict[str, Any]]:
    ensure_store()
    rows = [normalize_profile(r) for r in _profile_store().list_all()]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    rows.sort(key=lambda r: r.get("brand_name") or "")
    return rows


def record_channel_production(
    *,
    channel_id: str,
    production_id: str,
    topic: str,
    category: str,
    success: bool,
    creative_score: float | None,
    project_root: str,
    report_path: str = "",
) -> dict[str, Any]:
    ensure_store()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO channel_productions
            (channel_id, production_id, topic, category, created_at, success, creative_score, project_root, report_path)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                channel_id,
                production_id,
                topic,
                category,
                _now(),
                1 if success else 0,
                creative_score,
                project_root,
                report_path,
            ),
        )
        conn.commit()

    profile = get_profile(channel_id)
    if profile:
        metrics = dict(profile.get("metrics") or {})
        metrics["videos_published"] = int(metrics.get("videos_published") or 0) + (1 if success else 0)
        # rolling creative average
        prior_n = int(metrics.get("videos_published") or 1)
        prior_avg = metrics.get("average_creative_score")
        if creative_score is not None:
            if prior_avg is None:
                metrics["average_creative_score"] = round(float(creative_score), 1)
            else:
                # approximate after increment
                metrics["average_creative_score"] = round(
                    ((float(prior_avg) * max(0, prior_n - 1)) + float(creative_score)) / max(1, prior_n),
                    1,
                )
        profile["metrics"] = metrics
        hist = list(profile.get("analytics_history") or [])
        hist.append(
            {
                "at": _now(),
                "production_id": production_id,
                "topic": topic,
                "creative_score": creative_score,
                "success": success,
            }
        )
        profile["analytics_history"] = hist[-50:]
        save_profile(profile, sync_legacy=True)

    _refresh_productions_index()
    return {"channel_id": channel_id, "production_id": production_id, "project_root": project_root}


def list_channel_productions(*, channel_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
    ensure_store()
    sql = "SELECT * FROM channel_productions WHERE 1=1"
    params: list[Any] = []
    if channel_id:
        sql += " AND channel_id=?"
        params.append(channel_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _refresh_profiles_index() -> None:
    rows = list_profiles(status=None)
    INDEX_JSON.write_text(
        json.dumps({"updated_at": _now(), "count": len(rows), "profiles": rows}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _refresh_productions_index() -> None:
    rows = list_channel_productions(limit=200)
    PRODUCTIONS_JSON.write_text(
        json.dumps({"updated_at": _now(), "count": len(rows), "productions": rows}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
