"""Revision engine — stage 7: automatically improve sections the critic flagged.

Applies targeted fixes (hook strengthening, filler removal, claim softening,
sentence splitting, viewer address) and then re-runs the critic's analysis
so every script carries its post-revision critique score.
"""

from __future__ import annotations

import re

from core.log import get_logger, log_event
from engines.base import Engine
from engines.critic import analyze_script, critic_score
from engines.heuristics import ABSOLUTE_CLAIMS, BORING_REPLACEMENTS, sentences

logger = get_logger(__name__)


def _strengthen_hook(hook: str) -> str:
    return f"Nobody talks about this: {hook[0].lower()}{hook[1:]}" if hook else hook


def _remove_filler(text: str) -> str:
    lower_map = dict(BORING_REPLACEMENTS)
    result = text
    for phrase, replacement in lower_map.items():
        result = re.sub(re.escape(phrase), replacement, result, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", result).strip()


def _soften_claims(text: str) -> str:
    result = text
    for claim, softer in ABSOLUTE_CLAIMS.items():
        result = re.sub(rf"\b{re.escape(claim)}\b", softer, result, flags=re.IGNORECASE)
    return result


def _split_long_sentences(text: str) -> str:
    fixed = []
    for sentence in sentences(text):
        if len(sentence.split()) > 28 and " and " in sentence:
            head, tail = sentence.split(" and ", 1)
            tail = tail.rstrip(".!?")
            fixed.append(f"{head.rstrip('.!?')}. And {tail[0].upper()}{tail[1:]}." if tail else head)
        else:
            fixed.append(sentence)
    return " ".join(fixed)


def _add_viewer_address(text: str) -> str:
    return f"{text} Here's what this means for you."


class RevisionEngine(Engine):
    key = "revision"
    label = "Revision"
    icon = "🔧"
    description = "Automatically rewrite the weak sections the critic flagged."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        revised_count = 0

        for idea in selected:
            issues = idea.get("critique", {}).get("issues", [])
            if not issues:
                idea["revised"] = False
                continue

            applied = []
            hook = idea.get("hook", "")
            script = idea.get("script", "")

            for issue in issues:
                if issue.startswith("Weak hook"):
                    new_hook = _strengthen_hook(hook)
                    script = script.replace(hook, new_hook, 1) if hook and hook in script else script
                    hook = new_hook
                    applied.append("Strengthened hook with a curiosity gap.")
                elif issue.startswith("Boring phrasing"):
                    script = _remove_filler(script)
                    applied.append("Removed filler phrasing.")
                elif issue.startswith("Unsupported claim"):
                    script = _soften_claims(script)
                    applied.append("Softened absolute claims.")
                elif issue.startswith("Poor pacing"):
                    script = _split_long_sentences(script)
                    applied.append("Split an overlong sentence.")
                elif issue.startswith("Low retention"):
                    script = _add_viewer_address(script)
                    applied.append("Added direct viewer address.")
                elif issue.startswith("Repetition"):
                    applied.append("Flagged repeated wording for variation.")

            idea["hook"] = hook
            idea["script"] = script
            idea["revised"] = True
            idea["revisions"] = applied
            revised_count += 1

            remaining = analyze_script(hook, script)
            idea["critique"] = {"issues": remaining, "score": critic_score(remaining)}

        log_event(logger, "revision.completed", scripts=len(selected), revised=revised_count)
        return {"selected_ideas": selected}
