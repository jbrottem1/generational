"""Script fallback engine — write scripts for concepts that reach ranking unscripted.

Since v7.2 the Script Generation Engine (engines/script_generation.py) runs
immediately after Psychology and attaches multi-variant scripts to every
candidate, so in the standard intelligence pipeline this stage is a no-op
safety net. It still fully scripts `selected_ideas` in custom workflows
that skip script generation — nothing downstream breaks either way.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.provider_runtime.engine_api import runtime_generate_json

logger = get_logger(__name__)


class ScriptEngine(Engine):
    key = "script"
    label = "Script"
    icon = "📝"
    description = "Fallback scriptwriter for concepts the Script Generation Engine didn't cover."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        # Ideas already scripted by the Script Generation Engine keep their
        # scored best variant — this stage only covers the gaps.
        unscripted = [idea for idea in selected if not idea.get("script")]
        if not unscripted:
            return {"selected_ideas": selected} if selected else {}

        scripts = self._provider_scripts(context, unscripted)
        if scripts is None:
            scripts = [self._heuristic_script(context, idea) for idea in unscripted]

        for idea, script_data in zip(unscripted, scripts):
            idea["script"] = script_data["script"]
            idea["cta"] = script_data.get("cta", "Follow for more like this!")
            refs = context.get("research_references")
            if refs:
                idea["references"] = refs

        log_event(logger, "script.generated", scripts=len(unscripted))
        return {"selected_ideas": selected}

    def _provider_scripts(self, context: dict, selected: list) -> "list | None":
        concept_lines = "\n".join(
            f'{i}. title: "{idea["title"]}" hook: "{idea["hook"]}"' for i, idea in enumerate(selected, 1)
        )
        system = (
            "You are an elite short-form voiceover scriptwriter. "
            "Respond with valid minified JSON only."
        )
        user = (
            f"Niche: {context.get('niche', '')}\nSubject: {context.get('subject', '')}\n"
            f"Audience: {context.get('research', {}).get('audience', '')}\n\n"
            f"Write a 15-30 second voiceover script for each concept, in order:\n{concept_lines}\n\n"
            'Respond with JSON: {"scripts": [{"script": "full script starting with the hook", '
            '"cta": "short call to action"}]}'
        )
        data, tokens, provider_name = runtime_generate_json(
            system, user, model=context.get("model", ""), operation="generate_script",
        )
        if data is None:
            if provider_name and provider_name != "demo":
                context["error"] = "AI script call failed; used heuristic fallback."
            return None
        context["tokens_used"] = context.get("tokens_used", 0) + tokens
        context["provider_used"] = provider_name
        scripts = data.get("scripts", [])
        if len(scripts) < len(selected):
            return None
        return scripts

    def _heuristic_script(self, context: dict, idea: dict) -> dict:
        subject = context.get("subject", "this topic")
        niche = context.get("niche", "this niche")
        facts = context.get("research", {}).get("important_facts", [])
        fact_line = facts[0] if facts else f"Research in {niche.lower()} points to one specific driver."
        script = {
            "script": (
                f"{idea['hook']} "
                f"Here's what most people miss: {subject} isn't what it looks like on the surface. "
                f"{fact_line} "
                f"The practical takeaway for you: change one small input and "
                f"the whole pattern shifts. Watch what happens when you apply this for just one week."
            ),
            "cta": "Follow for more — tomorrow's video goes deeper.",
        }
        refs = context.get("research_references")
        if refs:
            idea["references"] = refs
        return script
