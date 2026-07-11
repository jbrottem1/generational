"""Live Agent / Engine registry for the Generational Media OS.

Read-only introspection over registered engines + the Agent 1–23 roster.
Does not redesign engines — surfaces readiness for the master pipeline.
"""

from __future__ import annotations

from typing import Any

# Canonical agent roster (Agent 1 maintained). Branch notes are informational.
AGENT_ROSTER: list[dict[str, Any]] = [
    {"agent": 1, "name": "Master Architecture & Orchestrator", "purpose": "Kernel, stages, packaging, hooks", "status": "complete", "branch": "mainline", "engine_keys": ["orchestrator"], "inputs": ["user_prompt"], "outputs": ["PipelineResult", "ContentPackage"], "dependencies": []},
    {"agent": 2, "name": "Psychology & Behavioral Intelligence", "purpose": "Virality, attention, threat scoring", "status": "complete", "branch": "mainline", "engine_keys": ["psychology", "attention_graph", "threat_detection"], "inputs": ["candidates"], "outputs": ["psychology_score", "attention_graph"], "dependencies": ["research", "ideation"]},
    {"agent": 3, "name": "Script Generation", "purpose": "Multi-variant scripts, critic, revision", "status": "complete", "branch": "mainline", "engine_keys": ["script_generation", "script", "critic", "revision"], "inputs": ["candidates"], "outputs": ["script_package"], "dependencies": ["psychology"]},
    {"agent": 4, "name": "Visual Intelligence", "purpose": "Storyboard / shot / visual plan", "status": "complete", "branch": "mainline", "engine_keys": ["visual_intelligence"], "inputs": ["script_package"], "outputs": ["visual_package"], "dependencies": ["script_generation"]},
    {"agent": 5, "name": "Voice & Audio", "purpose": "Audio production plan (TTS planned)", "status": "partial", "branch": "mainline", "engine_keys": ["voice_audio", "voice"], "inputs": ["visual_package"], "outputs": ["audio_package"], "dependencies": ["visual_intelligence"]},
    {"agent": 6, "name": "Render Engine", "purpose": "Assemble render package (mock without live media)", "status": "partial", "branch": "mainline", "engine_keys": ["render", "image", "video"], "inputs": ["visual_package", "audio_package"], "outputs": ["render_package"], "dependencies": ["voice_audio", "quality"]},
    {"agent": 7, "name": "Publishing & Distribution", "purpose": "Schedule + publish (dry-run without OAuth)", "status": "partial", "branch": "mainline", "engine_keys": ["publishing", "scheduler", "publishing_queue"], "inputs": ["publishing_packages"], "outputs": ["publishing_package"], "dependencies": ["render", "seo_optimization"]},
    {"agent": 8, "name": "Global Content Optimization", "purpose": "SEO titles, keywords, publish handoff", "status": "complete", "branch": "mainline", "engine_keys": ["seo_optimization", "seo"], "inputs": ["packages"], "outputs": ["seo_package", "publishing_packages"], "dependencies": ["quality"]},
    {"agent": 9, "name": "Production Pipeline", "purpose": "Scene→timeline→seed render packages", "status": "complete", "branch": "mainline", "engine_keys": ["scene_planning", "narration", "visual_planning", "asset_manager", "subtitle", "timeline", "render_package", "publishing_queue"], "inputs": ["approved_ideas"], "outputs": ["production_packages"], "dependencies": ["quality"]},
    {"agent": 10, "name": "Analytics & Continuous Learning", "purpose": "Post-publish metrics + learning loop", "status": "complete", "branch": "mainline", "engine_keys": ["analytics", "learning"], "inputs": ["publish_jobs"], "outputs": ["analytics_package", "learning_metadata"], "dependencies": ["publishing"]},
    {"agent": 11, "name": "Market / Trend Intelligence", "purpose": "Forecast + market roadmap", "status": "complete", "branch": "mainline", "engine_keys": ["trend_discovery", "opportunity_ranking", "trend_forecasting", "market_intelligence"], "inputs": ["command"], "outputs": ["trend_opportunities", "forecasts"], "dependencies": []},
    {"agent": 12, "name": "Creative Studio", "purpose": "Storyboards, shot lists, style, asset reqs", "status": "complete", "branch": "mainline", "engine_keys": ["creative_studio"], "inputs": ["unified_packages"], "outputs": ["creative_package"], "dependencies": ["quality"]},
    {"agent": 13, "name": "Optimization Laboratory", "purpose": "A/B variants before publish", "status": "stub", "branch": "feature/optimization-laboratory", "engine_keys": ["optimization_lab"], "inputs": ["packages"], "outputs": ["optimization_package"], "dependencies": ["quality"]},
    {"agent": 14, "name": "Universal Asset Generation", "purpose": "Provider-driven asset generation", "status": "partial", "branch": "mainline", "engine_keys": ["asset_generation"], "inputs": ["creative_package"], "outputs": ["asset_package"], "dependencies": ["ai_director", "creative_studio"]},
    {"agent": 15, "name": "Character / Universe / IP", "purpose": "Persistent cast & canon", "status": "stub", "branch": "feature/character-universe", "engine_keys": ["character_universe"], "inputs": ["director_package"], "outputs": ["character_universe_package"], "dependencies": []},
    {"agent": 16, "name": "Animation Director (Animation Studio)", "purpose": "Motion direction, storyboard, camera, env FX, animation QC", "status": "active", "branch": "feature/animation-engine", "engine_keys": ["animation"], "inputs": ["asset_package", "storyboard_package"], "outputs": ["animation_package"], "dependencies": ["quality"]},
    {"agent": 17, "name": "Post-Production", "purpose": "Edit, mix, captions, QC exports", "status": "partial", "branch": "mainline", "engine_keys": ["post_production"], "inputs": ["render_package"], "outputs": ["post_production_package"], "dependencies": ["render"]},
    {"agent": 18, "name": "AI Director", "purpose": "Executive creative strategy before assets", "status": "complete", "branch": "mainline", "engine_keys": ["ai_director"], "inputs": ["unified_packages"], "outputs": ["director_package"], "dependencies": ["quality"]},
    {"agent": 19, "name": "Provider Integration & Runtime", "purpose": "Sole AI/media/publish gateway", "status": "complete", "branch": "mainline", "engine_keys": [], "inputs": ["ProviderRequest"], "outputs": ["ProviderResponse"], "dependencies": []},
    {"agent": 20, "name": "Studio UI", "purpose": "Prompt → pipeline UI", "status": "complete", "branch": "mainline", "engine_keys": [], "inputs": ["settings", "command"], "outputs": ["ProjectRun"], "dependencies": ["workflow_executor"]},
    {"agent": 21, "name": "Workflow Executor", "purpose": "Durable runs, checkpoints, retries", "status": "complete", "branch": "mainline", "engine_keys": [], "inputs": ["prompt"], "outputs": ["ProjectRun"], "dependencies": ["orchestrator"]},
    {"agent": 22, "name": "Autonomous Executive", "purpose": "Planned autonomy layer", "status": "reserved", "branch": "planned", "engine_keys": [], "inputs": [], "outputs": [], "dependencies": ["orchestrator"]},
    {"agent": 23, "name": "Autonomous Production Executor", "purpose": "Long-form autonomous executor", "status": "worktree", "branch": "feature/autonomous-production-executor", "engine_keys": [], "inputs": ["ProductionJob"], "outputs": ["WorkflowResult"], "dependencies": ["workflow_executor"]},
]


# Master production stage order (must match Orchestrator — no bypass).
MASTER_PIPELINE_STAGES: list[dict[str, Any]] = [
    {"stage": "executive_intake", "label": "Executive Intelligence", "orch_stage": "trend", "required": True},
    {"stage": "topic_research", "label": "Topic Research", "orch_stage": "research", "required": True},
    {"stage": "creative_planning", "label": "Creative Planning", "orch_stage": "psychology", "required": True},
    {"stage": "script_generation", "label": "Script Generation", "orch_stage": "script", "required": True},
    {"stage": "storyboard", "label": "Storyboard Generation", "orch_stage": "attention", "required": True},
    {"stage": "scene_planning", "label": "Scene Planning", "orch_stage": "visual", "required": True},
    {"stage": "visual_intelligence", "label": "Visual Intelligence", "orch_stage": "audio", "required": True},
    {"stage": "refinement_quality", "label": "Quality Gate", "orch_stage": "quality", "required": True},
    {"stage": "production", "label": "Asset / Production Packaging", "orch_stage": "production", "required": True},
    {"stage": "packaging", "label": "Content Packaging", "orch_stage": "packaging", "required": True},
    {"stage": "ai_director", "label": "AI Director", "orch_stage": "ai_director", "required": True},
    {"stage": "creative_studio", "label": "Creative Studio", "orch_stage": "creative", "required": True},
    {"stage": "character_ip", "label": "Character/IP", "orch_stage": "character_universe", "required": False},
    {"stage": "asset_generation", "label": "Asset Generation", "orch_stage": "asset_generation", "required": True},
    {"stage": "animation", "label": "Animation", "orch_stage": "animation", "required": False},
    {"stage": "voice", "label": "Voice Generation", "orch_stage": "audio", "required": True},
    {"stage": "music_sfx", "label": "Music / Sound Effects", "orch_stage": "audio", "required": True},
    {"stage": "render", "label": "Render", "orch_stage": "render", "required": True},
    {"stage": "post_production", "label": "Post Production", "orch_stage": "post_production", "required": True},
    {"stage": "captions_thumb_meta", "label": "Captions / Thumbnail / Metadata", "orch_stage": "seo", "required": True},
    {"stage": "optimization", "label": "Optimization Lab", "orch_stage": "optimization", "required": False},
    {"stage": "qa_publish", "label": "QA + Publishing", "orch_stage": "publish", "required": True},
    {"stage": "analytics", "label": "Analytics", "orch_stage": "analytics", "required": True},
    {"stage": "learning", "label": "Learning Engine", "orch_stage": "learning", "required": True},
    {"stage": "executive_review", "label": "Executive Review", "orch_stage": "learning", "required": True},
]


def _ensure_engines_loaded() -> None:
    import engines  # noqa: F401 — registers all engines


def live_engine_registry() -> list[dict[str, Any]]:
    """Machine-readable engine inventory from the live registry."""
    _ensure_engines_loaded()
    from engines.registry import describe_all

    return describe_all()


def live_agent_registry() -> list[dict[str, Any]]:
    """Agent roster enriched with live engine readiness."""
    _ensure_engines_loaded()
    from engines.registry import get_engine

    rows = []
    for agent in AGENT_ROSTER:
        engine_states = []
        for key in agent.get("engine_keys") or []:
            eng = get_engine(key)
            if eng is None:
                engine_states.append({"key": key, "registered": False, "ready": False})
            else:
                engine_states.append(
                    {
                        "key": key,
                        "registered": True,
                        "ready": bool(eng.is_ready()),
                        "version": getattr(eng, "version", ""),
                        "label": getattr(eng, "label", key),
                    }
                )
        ready_flags = [e["ready"] for e in engine_states if e.get("registered")]
        if agent["status"] in {"reserved", "worktree"}:
            readiness = agent["status"]
        elif not engine_states and agent["status"] == "complete":
            readiness = "service_complete"
        elif ready_flags and all(ready_flags):
            readiness = "ready"
        elif any(ready_flags):
            readiness = "partial"
        elif engine_states and not any(e.get("registered") for e in engine_states):
            readiness = "missing"
        else:
            readiness = "not_ready" if engine_states else agent["status"]

        rows.append(
            {
                **agent,
                "readiness": readiness,
                "engines": engine_states,
            }
        )
    return rows


def master_pipeline_map() -> list[dict[str, Any]]:
    """Documented master stages mapped onto Orchestrator stage names."""
    return list(MASTER_PIPELINE_STAGES)


def registry_summary() -> dict[str, Any]:
    agents = live_agent_registry()
    engines = live_engine_registry()
    ready_engines = sum(1 for e in engines if e.get("ready"))
    return {
        "agent_count": len(agents),
        "agents_ready": sum(1 for a in agents if a.get("readiness") in {"ready", "service_complete", "complete"}),
        "agents_partial": sum(1 for a in agents if a.get("readiness") == "partial" or a.get("status") == "partial"),
        "agents_stub": sum(1 for a in agents if a.get("status") in {"stub", "reserved", "worktree"}),
        "engine_count": len(engines),
        "engines_ready": ready_engines,
        "master_stages": len(MASTER_PIPELINE_STAGES),
        "agents": agents,
        "engines": engines,
        "pipeline": master_pipeline_map(),
    }
