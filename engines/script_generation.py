"""Script Generation Engine — runs immediately after the Psychology Engine.

Every psychology-scored candidate gets multiple stylistically distinct,
platform-aware script variants (Authority Reveal, Story First, Myth Bust,
Countdown Payoff). Each variant is built section-first — primary hook,
pattern interrupt, curiosity hook, context, escalation, evidence, emotional
peak, resolution, call to action — with per-section duration, emotional
intensity, attention score, visual intent, B-roll type, and caption
emphasis. The Hook Engine writes ten styled hook candidates per idea and
ranks them using the candidate's ViralScore psychology dimensions; the
retention model estimates drop-off risk, engagement, retention, rewatch
probability, curiosity strength, and emotional pacing for every variant.

Variants are scored 0-100 (`services/scripts/scorer.py`) and the winner is
attached as the candidate's script, so the downstream Ranking engine can
weigh *script quality* — not just concept psychology — when selecting what
gets produced. When an AI provider is available, the strongest candidates
(by ViralScore) get an extra LLM-written variant that competes against the
heuristic ones on the same deterministic scorecard; in Demo Mode the
heuristic variants carry the whole pipeline.

Generation itself is delegated to the modular `services/scripts` package,
which is equally usable standalone to re-script any approved idea for any
supported platform (YouTube Shorts, TikTok, Instagram Reels, Facebook
Reels, X video, long-form YouTube).
"""

from __future__ import annotations

from core.constants import SCRIPT_VARIANTS_PER_IDEA
from core.log import get_logger, log_event
from engines.base import Engine
from services.provider_runtime.engine_api import runtime_generate_json
from services.scripts import (
    DEFAULT_PLATFORM,
    ScriptVariant,
    build_structured_script,
    finalize_variant,
    generate_variants,
    get_platform_spec,
    rank_variants,
)

logger = get_logger(__name__)

# How many top candidates (by ViralScore) get an extra AI-written variant.
# Bounded so one pipeline run stays a single LLM call regardless of pool size.
MAX_AI_ENHANCED = 8


class ScriptGenerationEngine(Engine):
    key = "script_generation"
    label = "Script Generation"
    icon = "✍️"
    description = (
        "Generate multiple scored, platform-aware script variants for every "
        "psychology-approved candidate; the best variant becomes the script."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        if not candidates:
            return {}

        platform = context.get("target_platform", DEFAULT_PLATFORM)
        spec = get_platform_spec(platform)
        variant_count = context.get("script_variant_count", SCRIPT_VARIANTS_PER_IDEA)
        subject = context.get("subject", "")
        niche = context.get("niche", "")
        research = context.get("research", {})
        locale = context.get("script_locale")  # language/region/dialect target

        variants_by_candidate = []
        for candidate in candidates:
            variants = generate_variants(
                candidate,
                platform=spec.key,
                subject=subject,
                niche=niche,
                research=research,
                variant_count=variant_count,
                locale=locale,
            )
            variants_by_candidate.append(variants)

        enhanced_count = self._add_ai_variants(context, candidates, variants_by_candidate, spec)

        for candidate, variants in zip(candidates, variants_by_candidate):
            ranked = rank_variants(variants)
            self._attach(context, candidate, ranked, spec)

        best_scores = [c["script_score"] for c in candidates]
        summary = {
            "platform": spec.key,
            "platform_label": spec.label,
            "variants_per_idea": len(variants_by_candidate[0]) if variants_by_candidate else 0,
            "scripted": len(candidates),
            "ai_enhanced": enhanced_count,
            "average_best_score": round(sum(best_scores) / len(best_scores), 1) if best_scores else 0,
        }
        log_event(
            logger,
            "script_generation.completed",
            candidates=len(candidates),
            platform=spec.key,
            ai_enhanced=enhanced_count,
            avg_best_score=summary["average_best_score"],
        )
        return {"candidates": candidates, "script_generation_summary": summary}

    def _attach(self, context: dict, candidate: dict, ranked: list, spec) -> None:
        """Attach the ranked variants and promote the winner to the script slot."""
        best = ranked[0]
        candidate["script_variants"] = [variant.to_dict() for variant in ranked]
        candidate["script"] = best.full_script
        candidate["cta"] = best.call_to_action
        candidate["script_score"] = best.score
        candidate["script_style"] = best.style_label
        candidate["script_platform"] = spec.key
        candidate["script_sections"] = best.sections
        candidate["alternate_hooks"] = best.alternate_hooks
        candidate["hook_style"] = best.hook_style
        candidate["script_retention"] = best.retention_model
        # The canonical handoff for Visual Intelligence and other consumers:
        # title, ranked hooks, annotated sections, scene breakdown, emotion
        # and attention timelines, voice/caption direction, retention model,
        # CTA, platform format, and locale in one dict.
        candidate["structured_script"] = build_structured_script(candidate, best, spec)
        candidate["estimated_runtime_sec"] = best.estimated_runtime_sec
        candidate["retention_checkpoints"] = best.retention_checkpoints
        candidate["emotional_progression"] = best.emotional_progression
        candidate["broll_suggestions"] = best.broll_suggestions
        candidate["visual_prompts"] = best.visual_prompts
        candidate["sound_effects"] = best.sound_effects
        candidate["music_style"] = best.music_style
        candidate["suggested_seo_keywords"] = best.seo_keywords
        refs = context.get("research_references")
        if refs:
            candidate["references"] = refs

    def _add_ai_variants(self, context, candidates, variants_by_candidate, spec) -> int:
        """One batched LLM call writes an extra variant for the top candidates."""
        order = sorted(
            range(len(candidates)),
            key=lambda i: candidates[i].get("psychology_score", 0),
            reverse=True,
        )
        top = order[: min(context.get("video_count", MAX_AI_ENHANCED), MAX_AI_ENHANCED)]
        if not top:
            return 0

        concept_lines = "\n".join(
            f'{n}. title: "{candidates[i].get("title", "")}" hook: "{candidates[i].get("hook", "")}" '
            f'angle: "{candidates[i].get("angle", "")}"'
            for n, i in enumerate(top, 1)
        )
        facts = context.get("research", {}).get("important_facts", [])
        system = (
            "You are an elite viral video scriptwriter and storytelling architect. "
            "Respond with valid minified JSON only."
        )
        user = (
            f"Platform: {spec.label} ({spec.min_runtime_sec}-{spec.max_runtime_sec}s, tone: {spec.tone})\n"
            f"Niche: {context.get('niche', '')}\nSubject: {context.get('subject', '')}\n"
            f"Research facts: {facts}\n\n"
            f"Write one complete voiceover script for each concept, in order:\n{concept_lines}\n\n"
            f"Target roughly {spec.target_words} spoken words each. Every script needs: an "
            f"attention hook (first {spec.hook_window_sec}s), a pattern interrupt, an open "
            "curiosity loop, a fact-grounded core story, and a call to action "
            f"({spec.cta_style}).\n"
            'Respond with JSON: {"scripts": [{"hook": "...", "pattern_interrupt": "...", '
            '"curiosity_loop": "...", "core_story": "...", "call_to_action": "..."}]}'
        )
        data, tokens, provider_name = runtime_generate_json(
            system, user, model=context.get("model", ""), operation="generate_script",
        )
        if data is None:
            if provider_name and provider_name != "demo":
                context["error"] = "AI script generation call failed; used heuristic variants."
            return 0
        context["tokens_used"] = context.get("tokens_used", 0) + tokens
        context["provider_used"] = provider_name

        scripts = data.get("scripts", [])
        if len(scripts) < len(top):
            return 0

        enhanced = 0
        for n, i in enumerate(top):
            script_data = scripts[n]
            if not script_data.get("core_story"):
                continue
            base = variants_by_candidate[i][0]
            variant = ScriptVariant(
                variant_id="ai_enhanced",
                style="ai_enhanced",
                style_label="AI Enhanced",
                platform=spec.key,
                hook=script_data.get("hook", candidates[i].get("hook", "")),
                hook_style="ai",
                alternate_hooks=base.alternate_hooks,
                pattern_interrupt=script_data.get("pattern_interrupt", ""),
                curiosity_loop=script_data.get("curiosity_loop", ""),
                core_story=script_data["core_story"],
                emotional_progression=base.emotional_progression,
                call_to_action=script_data.get("call_to_action", base.call_to_action),
                seo_keywords=base.seo_keywords,
                broll_suggestions=base.broll_suggestions,
                visual_prompts=base.visual_prompts,
                sound_effects=base.sound_effects,
                music_style=base.music_style,
                locale=base.locale,
                source="ai",
            )
            # finalize rebuilds the section architecture from the flat AI
            # fields, so AI variants carry the same structure as heuristic ones.
            finalize_variant(variant, spec.words_per_minute, candidates[i].get("psychology"))
            variants_by_candidate[i].append(variant)
            enhanced += 1
        return enhanced
