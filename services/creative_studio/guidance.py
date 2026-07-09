"""Learning loop — upstream intelligence shapes future creative packages.

Reads what Analytics/Learning (Agent 9), Trend Discovery (Agents 1/11),
the Optimization Laboratory (Agent 13), and Behavioral Intelligence
(Agent 2) already put on the shared context, and derives creative
guidance (CREATIVE_GUIDANCE_FIELDS) the Director folds into the next
blueprint. Read-only over context keys — never an engine call
(Architecture Directive #1).
"""

from __future__ import annotations

# Learning recommendation targets whose guidance the studio adopts.
_RELEVANT_TARGETS = ("visual_intelligence", "creative_studio", "script_generation")

# Keyword → pacing hint mapping mined from recommendation texts.
_PACING_SIGNALS = (
    ("shorter", "rapid"),
    ("faster", "rapid"),
    ("quick cut", "rapid"),
    ("slower", "measured"),
    ("longer", "measured"),
    ("breathing room", "slow"),
)


def derive_creative_guidance(context: dict) -> dict:
    """One guidance dict from everything upstream intelligence provided.

    Missing sources are simply skipped — with an empty context the
    guidance is empty and the Director designs from defaults.
    """
    sources: "list[str]" = []
    notes: "list[str]" = []
    pacing_hint = ""
    style_hint = ""
    hook_emphasis = ""
    retention_focus = ""

    # Learning Engine (Agent 9) — confidence-scored recommendations.
    recommendations = context.get("learning_recommendations") or []
    if recommendations:
        sources.append("learning_recommendations")
        relevant = [
            rec for rec in recommendations
            if str(rec.get("target_engine", "")) in _RELEVANT_TARGETS
        ]
        for rec in relevant[:5]:
            text = str(rec.get("recommendation", rec.get("insight", ""))).strip()
            if text:
                notes.append(f"learning: {text}")
            lowered = text.lower()
            for signal, tempo in _PACING_SIGNALS:
                if signal in lowered and not pacing_hint:
                    pacing_hint = tempo

    # Trend intelligence (Agent 11) — the top recommendation's format cues.
    trend_recs = context.get("opportunity_recommendations") or []
    if trend_recs:
        sources.append("opportunity_recommendations")
        top = trend_recs[0]
        if top.get("thumbnail_direction"):
            notes.append(f"trend: thumbnail — {top['thumbnail_direction']}")
        if top.get("hook_direction"):
            hook_emphasis = str(top["hook_direction"])
        if top.get("recommended_format"):
            style_hint = str(top["recommended_format"])

    # Optimization Laboratory (Agent 13) — experiment outcomes.
    optimization = context.get("optimization_report") or context.get("optimization_summary") or {}
    if optimization:
        sources.append("optimization_report")
        winner = optimization.get("winning_variant") or optimization.get("top_recommendation")
        if winner:
            notes.append(f"optimization: favor proven variant {winner}")

    # Behavioral Intelligence (Agent 2) — retention weak points.
    behavioral = context.get("psychology_report") or {}
    if behavioral:
        sources.append("psychology_report")
    attention = context.get("attention_report") or {}
    if attention:
        sources.append("attention_report")
        retention_focus = "protect the mid-video attention dip — escalate at the midpoint"

    return {
        "sources": sources,
        "pacing_hint": pacing_hint,
        "style_hint": style_hint,
        "hook_emphasis": hook_emphasis,
        "retention_focus": retention_focus,
        "notes": notes,
    }


def apply_guidance_to_item(item: dict, guidance: dict) -> dict:
    """A guided copy of the item the Director designs from.

    Only fills creative preferences the item does not already state —
    explicit requests always beat learned guidance. The original item is
    never mutated.
    """
    guided = dict(item)
    if guidance.get("pacing_hint") and not guided.get("pacing"):
        guided["pacing"] = guidance["pacing_hint"]
    if guidance.get("style_hint") and not guided.get("visual_style"):
        # Only adopt the hint when it names a real registered style.
        from services.creative_studio.styles import get_style

        if get_style(str(guidance["style_hint"])):
            guided["visual_style"] = str(guidance["style_hint"])
    return guided
