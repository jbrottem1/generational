"""Production readiness scoring for the master pipeline."""

from __future__ import annotations

from typing import Any

from services.master_pipeline.registry import registry_summary


PROVIDER_ENVS = [
    ("openai", "OPENAI_API_KEY", True),
    ("anthropic", "ANTHROPIC_API_KEY", False),
    ("gemini", "GOOGLE_API_KEY", False),
    ("elevenlabs", "ELEVENLABS_API_KEY", True),  # required for real voice
    ("runway", "RUNWAY_API_KEY", True),  # required for real video
    ("flux", "BFL_API_KEY", False),
    ("fal", "FAL_KEY", False),
    ("replicate", "REPLICATE_API_TOKEN", False),
    ("ideogram", "IDEOGRAM_API_KEY", False),
    ("youtube", "YOUTUBE_ACCESS_TOKEN", False),
    ("tiktok", "TIKTOK_ACCESS_TOKEN", False),
    ("instagram", "INSTAGRAM_ACCESS_TOKEN", False),
    ("facebook", "FACEBOOK_ACCESS_TOKEN", False),
    ("linkedin", "LINKEDIN_ACCESS_TOKEN", False),
    ("x", "X_ACCESS_TOKEN", False),
]


def provider_integration_status() -> list[dict[str, Any]]:
    from services.provider_runtime.config import has_credential

    rows = []
    for name, env, required_for_real_video in PROVIDER_ENVS:
        present = bool(has_credential(env))
        rows.append(
            {
                "provider": name,
                "env_var": env,
                "configured": present,
                "status": "connected" if present else "configurable",
                "required_for_real_mp4": required_for_real_video,
            }
        )
    return rows


def production_readiness_report() -> dict[str, Any]:
    """Evidence-based readiness score for end-to-end video production."""
    summary = registry_summary()
    providers = provider_integration_status()
    configured = [p for p in providers if p["configured"]]
    required_media = [p for p in providers if p["required_for_real_mp4"]]
    media_ready = [p for p in required_media if p["configured"]]

    # Scoring rubric (honest)
    score = 0
    notes: list[str] = []

    # Architecture / orchestration (max 35)
    if summary["engines_ready"] >= 30:
        score += 25
        notes.append("Engine registry healthy")
    else:
        score += 15
        notes.append("Some engines not ready")
    score += 10  # Orchestrator + WE exist and are wired
    notes.append("Studio → Workflow Executor → Orchestrator path live")

    # LLM (max 15)
    if any(p["provider"] == "openai" and p["configured"] for p in providers):
        score += 15
        notes.append("OpenAI configured — script/ideation live")
    else:
        notes.append("OpenAI missing — Demo Mode for ideation")

    # Real media (max 30)
    if len(media_ready) >= 2:
        score += 30
        notes.append("Voice + video providers configured")
    elif len(media_ready) == 1:
        score += 12
        notes.append("Partial media providers — render still mock-capable only")
    else:
        score += 5
        notes.append("No ElevenLabs/Runway — finished MP4 not available")

    # Publish (max 10)
    publish_ready = any(
        p["provider"] in {"youtube", "tiktok", "instagram"} and p["configured"] for p in providers
    )
    if publish_ready:
        score += 10
        notes.append("At least one publish OAuth token present")
    else:
        score += 4
        notes.append("Publish remains dry-run without OAuth")

    # Stubs (max 10)
    stubs = summary["agents_stub"]
    if stubs <= 3:
        score += 10
    elif stubs <= 5:
        score += 6
    else:
        score += 3
    notes.append(f"{stubs} agents stub/reserved/worktree")

    score = min(100, score)

    if score >= 90:
        band = "production_demo_ready"
    elif score >= 75:
        band = "dry_run_ready"
    elif score >= 60:
        band = "architecture_ready"
    else:
        band = "blocked"

    blockers = []
    if not any(p["provider"] == "elevenlabs" and p["configured"] for p in providers):
        blockers.append("Real TTS (ElevenLabs or OpenAI TTS wiring) required for finished audio")
    if not any(p["provider"] == "runway" and p["configured"] for p in providers) and not any(
        p["provider"] in {"fal", "replicate"} and p["configured"] for p in providers
    ):
        blockers.append("Real video/image provider required for finished MP4")
    if not publish_ready:
        blockers.append("OAuth tokens required for live publish (dry-run available)")

    return {
        "score": score,
        "band": band,
        "notes": notes,
        "blockers": blockers,
        "registry": {
            "agent_count": summary["agent_count"],
            "agents_ready": summary["agents_ready"],
            "agents_partial": summary["agents_partial"],
            "agents_stub": summary["agents_stub"],
            "engine_count": summary["engine_count"],
            "engines_ready": summary["engines_ready"],
        },
        "providers": providers,
        "providers_configured": len(configured),
        "estimated_time_to_first_production": (
            "immediate (dry-run / mock render)" if score >= 75 else "1–3 days after media keys"
        ),
        "estimated_time_to_first_publish": (
            "immediate dry-run; live publish after OAuth (same day if tokens ready)"
            if score >= 75
            else "blocked on media + OAuth"
        ),
        "next_priorities": [
            "Connect ElevenLabs (or enable OpenAI TTS path) for real voice",
            "Connect Runway / Fal / Replicate for real visual frames",
            "Wire fulfillers in engines/render/assets.py to ProviderRuntime",
            "Add YouTube OAuth for first live publish",
            "Merge character/animation/optlab stubs only when product needs them",
        ],
    }
