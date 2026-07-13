"""Analytics collector — one structured record per published content unit.

Turns a finished ContentPackage (or idea dict) plus its publishing jobs
into ANALYTICS_RECORD_FIELDS records: platform metrics fetched through the
`AnalyticsProvider` interface, and attribution fields fingerprinting every
upstream decision (hook, psychology strategy, script / thumbnail / voice /
render versions, posting time) so the Learning Engine can credit outcomes
back to the choices that produced them.

Pure logic over dicts — no engine imports, no orchestrator imports.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from providers.analytics import get_analytics_provider
from services.analytics.models import (
    ANALYTICS_ENGINE_VERSION,
    ANALYTICS_RECORD_VERSION,
    MetricsStatus,
    empty_metrics,
    performance_score,
)

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint(payload) -> str:
    """Stable 10-hex fingerprint of any JSON-safe payload ("" when empty)."""
    if not payload:
        return ""
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:10]


# ------------------------------------------------------------ attribution


def _psychology_strategy(item: dict) -> list:
    """The psychological triggers/strategies this content leaned on."""
    psychology = item.get("psychology") or {}
    for key in ("triggers", "dominant_triggers", "strategies", "strategy"):
        value = psychology.get(key)
        if isinstance(value, list) and value:
            return [str(v) for v in value[:5]]
        if isinstance(value, str) and value:
            return [value]
    behavioral = item.get("behavioral_intelligence") or {}
    recommendations = behavioral.get("recommendations") or []
    if recommendations:
        return [str(r) for r in recommendations[:3]]
    score = int(item.get("psychology_score", 0) or 0)
    if score >= 70:
        return ["high_impact_psychology"]
    if score >= 40:
        return ["moderate_psychology"]
    return ["baseline_psychology"]


def _video_length_sec(item: dict) -> float:
    render = item.get("render_package") or {}
    for key in ("duration_sec", "estimated_duration_sec"):
        if render.get(key):
            return float(render[key])
    timeline = render.get("timeline") or {}
    if timeline.get("total_duration_sec"):
        return float(timeline["total_duration_sec"])
    audio = item.get("audio_package") or {}
    narration = audio.get("narration_plan") or {}
    if narration.get("total_duration_sec"):
        return float(narration["total_duration_sec"])
    return 0.0


def _title_of(item: dict) -> str:
    seo = item.get("seo_package") or {}
    return str(
        seo.get("recommended_title")
        or seo.get("title")
        or item.get("title", "")
    )


def _thumbnail_source(item: dict) -> "list | dict":
    seo = item.get("seo_package") or {}
    return (
        seo.get("thumbnail_recommendations")
        or item.get("thumbnail_plan")
        or item.get("thumbnail_concepts")
        or []
    )


def _voice_source(item: dict) -> dict:
    audio = item.get("audio_package") or item.get("voice_assets") or {}
    return {
        "voice_style": audio.get("voice_style", {}),
        "pacing": audio.get("pacing", {}),
    }


def build_attribution(item: dict, context: dict) -> dict:
    """The upstream-decision fields for one item, tolerant of both
    canonical ContentPackage dicts and raw idea dicts."""
    script_payload = item.get("script_package") or {
        "script": item.get("script", ""),
        "structured_script": item.get("structured_script", {}),
    }
    render = item.get("render_package") or {}
    extras_scores = item.get("scores") or {}
    return {
        "project_id": str(item.get("project_id", "")),
        "brand_id": str(item.get("brand_id", "") or context.get("brand_id", "")),
        "channel_id": str(item.get("channel_id", "") or context.get("channel_id", "")),
        "topic": str(item.get("topic", "") or context.get("subject", "") or context.get("command", "")[:80]),
        "niche": str(item.get("niche", "") or context.get("niche", "")),
        "title": _title_of(item),
        "hook": str(item.get("hook", "")),
        "keywords": list(item.get("keywords", []) or []),
        "psychology_strategy": _psychology_strategy(item),
        "psychology_score": int(item.get("psychology_score", 0) or 0),
        "virality_score": int(item.get("virality_score", 0) or extras_scores.get("virality", 0) or 0),
        "attention_score": int(item.get("attention_score", 0) or 0),
        "quality_score": int(item.get("quality_score", 0) or extras_scores.get("publish", 0) or 0),
        "script_version": fingerprint(script_payload),
        "thumbnail_version": fingerprint(_thumbnail_source(item)),
        "voice_version": fingerprint(_voice_source(item)),
        "render_version": str(render.get("render_package_version", "") or fingerprint(render)),
        "video_length_sec": _video_length_sec(item),
        "experiment_id": str((item.get("experiment") or {}).get("experiment_id", "")),
        "variant_id": str((item.get("experiment") or {}).get("variant_id", "")),
    }


# --------------------------------------------------------------- records


def _publish_jobs(item: dict) -> list:
    return list((item.get("publishing_package") or {}).get("jobs", []) or [])


def build_record(item: dict, job: dict, context: dict) -> dict:
    """One ANALYTICS_RECORD_FIELDS record for one item x platform job."""
    platform = str(job.get("platform", "") or "unknown")
    attribution = build_attribution(item, context)
    published = job.get("status") == "published"
    content_id = str(job.get("post_id") or job.get("analytics_ref") or attribution["project_id"])

    if published:
        provider = get_analytics_provider(platform)
        metrics = provider.fetch_metrics(content_id, platform)
        metrics_status = MetricsStatus.COLLECTED
        metrics_source = provider.name
    else:
        metrics = empty_metrics()
        metrics_status = MetricsStatus.PENDING
        metrics_source = ""

    record = {
        "record_id": f"ar_{uuid.uuid4().hex[:12]}",
        "record_version": ANALYTICS_RECORD_VERSION,
        "analytics_ref": str(job.get("analytics_ref", "")),
        "platform": platform,
        "post_id": str(job.get("post_id", "")),
        "post_url": str(job.get("post_url", "")),
        "posting_time": str(job.get("scheduled_time", "")),
        "published_at": str(job.get("published_at", "")),
        "metrics": metrics,
        "metrics_status": metrics_status,
        "metrics_source": metrics_source,
        "collected_at": _now_iso(),
    }
    record.update(attribution)
    return record


def collect_item_records(item: dict, context: dict) -> list:
    """Every analytics record for one item (one per publish job)."""
    return [build_record(item, job, context) for job in _publish_jobs(item)]


def build_analytics_package(records: list) -> dict:
    """The ContentPackage `analytics_package` slot value for one item."""
    if not records:
        return {
            "engine_version": ANALYTICS_ENGINE_VERSION,
            "status": "skipped",
            "records": [],
            "metrics": empty_metrics(),
            "performance_score": 0,
            "collected_at": _now_iso(),
        }

    collected = [r for r in records if r["metrics_status"] == MetricsStatus.COLLECTED]
    aggregate = empty_metrics()
    for record in collected:
        for metric, value in record["metrics"].items():
            if metric in aggregate:
                aggregate[metric] += value
    # Rates average across platforms instead of summing.
    for rate in ("audience_retention", "ctr", "average_view_duration_sec", "rpm", "cpm"):
        if collected:
            aggregate[rate] = round(aggregate[rate] / len(collected), 2)

    return {
        "engine_version": ANALYTICS_ENGINE_VERSION,
        "status": "collected" if collected else "pending",
        "records": records,
        "metrics": aggregate,
        "performance_score": performance_score(aggregate) if collected else 0,
        "collected_at": _now_iso(),
    }


def collect_analytics(items: list, context: dict) -> "tuple[list, list]":
    """(all_records, per_item_packages) — writes each item's
    `analytics_package` slot in place (Agent 9's write zone)."""
    all_records, packages = [], []
    for item in items:
        records = collect_item_records(item, context)
        package = build_analytics_package(records)
        item["analytics_package"] = package
        all_records.extend(records)
        packages.append(package)
    log_event(
        logger, "analytics.collected",
        items=len(items), records=len(all_records),
        collected=sum(1 for r in all_records if r["metrics_status"] == MetricsStatus.COLLECTED),
    )
    return all_records, packages


def build_record_from_job(job: dict, attempt: dict) -> dict:
    """One analytics record straight from a PublishingJob + attempt — the
    path used when scheduled jobs execute OUTSIDE a pipeline run (the
    PublishListener seam). Attribution is partial: the job's platform
    publish package carries title/keywords/routing but not the upstream
    intelligence fields, which stay empty rather than guessed."""
    package = job.get("package") or {}
    platform = str(job.get("platform", "") or package.get("platform", "") or "unknown")
    content_id = str(attempt.get("post_id") or job.get("analytics_ref") or job.get("job_id", ""))

    provider = get_analytics_provider(platform)
    metrics = provider.fetch_metrics(content_id, platform)

    record = {
        "record_id": f"ar_{uuid.uuid4().hex[:12]}",
        "record_version": ANALYTICS_RECORD_VERSION,
        "analytics_ref": str(job.get("analytics_ref", "")),
        "project_id": str(job.get("project_id", "") or package.get("project_id", "")),
        "brand_id": str(job.get("brand_id", "")),
        "channel_id": str(job.get("channel_id", "")),
        "platform": platform,
        "post_id": str(attempt.get("post_id", "")),
        "post_url": str(attempt.get("post_url", "")),
        "topic": "",
        "niche": "",
        "title": str(package.get("title", "")),
        "hook": "",
        "keywords": list(package.get("keywords", []) or []),
        "psychology_strategy": [],
        "psychology_score": 0,
        "virality_score": 0,
        "attention_score": 0,
        "quality_score": 0,
        "script_version": "",
        "thumbnail_version": fingerprint(package.get("thumbnail") or {}),
        "voice_version": "",
        "render_version": "",
        "video_length_sec": float((package.get("video") or {}).get("duration_sec", 0) or 0),
        "posting_time": str(job.get("scheduled_time", "")),
        "published_at": str(attempt.get("published_at", "")),
        "experiment_id": "",
        "variant_id": "",
        "metrics": metrics,
        "metrics_status": MetricsStatus.COLLECTED,
        "metrics_source": provider.name,
        "collected_at": _now_iso(),
    }
    return record


def attach_experiment(item: dict, experiment_id: str, variant_id: str) -> dict:
    """Tag an item so its analytics records carry the experiment linkage."""
    item["experiment"] = {"experiment_id": experiment_id, "variant_id": variant_id}
    return item
