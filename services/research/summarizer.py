"""Research summarizer — synthesize documents into structured briefs."""

from __future__ import annotations

from engines.heuristics import clamp, stable_jitter
from services.research.models import ResearchDocument, ResearchIntent, ResearchSummary


def summarize(
    documents: list[ResearchDocument],
    intent: ResearchIntent,
) -> ResearchSummary:
    """Build a structured research summary from scored documents."""
    if not documents:
        return _fallback_summary(intent)

    top = documents[:8]
    subject = intent.subject.title()
    niche = intent.niche

    facts = []
    stats = []
    for doc in top:
        if doc.summary:
            facts.append(doc.summary.split(".")[0].strip() + ".")
        if doc.citation_count > 0:
            stats.append(f"{doc.title}: cited {doc.citation_count} times ({doc.provider}).")
        elif doc.evidence_strength >= 0.7:
            stats.append(f"High-evidence source on {subject}: {doc.source}.")

    trend = clamp(
        int(sum(d.popularity for d in top) / len(top) * 100) if top else 60,
        5,
        98,
    )
    competition = 35 + stable_jitter(niche, 30)
    opportunity = clamp(int(0.7 * trend + 0.3 * (100 - competition)), 5, 98)

    context_text = (
        f"{subject} in the {niche} niche has {len(documents)} vetted sources. "
        f"Top authority: {top[0].source} ({top[0].provider}). "
        f"Content type: {intent.content_type}."
    )

    executive = (
        f"Research on '{subject}' ({niche}) draws from {len(documents)} sources "
        f"across {len({d.provider for d in documents})} providers. "
        f"Audience: {intent.audience}. Intent: {intent.search_intent}. "
        f"Trend strength: {trend}/100. Lead with a data-backed curiosity gap."
    )

    return ResearchSummary(
        executive_summary=executive,
        important_facts=facts[:6] or [f"Limited published data on {subject} — angle carefully."],
        statistics=stats[:4] or [f"Trend score for '{subject}': {trend}/100."],
        contrarian_ideas=[
            f"Popular belief about {subject} may oversimplify the underlying mechanism.",
            f"Experts in {niche.lower()} disagree on the #1 driver of {subject}.",
        ],
        common_myths=[
            f"Everything you've heard about {subject} oversimplifies the science.",
            f"The mainstream take on {subject} ignores recent findings.",
        ],
        questions=[
            f"Why does {subject} happen?",
            f"What does the latest research say about {subject}?",
            f"How does {subject} affect everyday life?",
        ],
        emerging_trends=[
            f"Short-form {niche.lower()} content on {subject} is rising.",
            f"Data-driven explainers outperform opinion takes for {subject}.",
        ],
        key_takeaways=[
            f"Use verified facts from {top[0].provider if top else 'research'} in the hook.",
            f"Target {intent.audience} with {intent.content_type} framing.",
            "Cite at least one source URL in the script for credibility.",
        ],
        topic_context=context_text,
        trend_strength=trend,
        opportunity_score=opportunity,
    )


def _fallback_summary(intent: ResearchIntent) -> ResearchSummary:
    """Demo/heuristic summary when no documents survive scoring."""
    subject = intent.subject
    trend = clamp(58 + stable_jitter(subject, 38), 5, 98)
    competition = 35 + stable_jitter(intent.niche, 30)
    opportunity = clamp(int(0.7 * trend + 0.3 * (100 - competition)), 5, 98)

    context_text = (
        f"{subject.title()} sits in the {intent.niche} niche. "
        f"Short, punchy explainers consistently outperform generic takes."
    )
    executive = (
        f"Audience: {intent.audience}. Intent: {intent.search_intent}. "
        f"Trend strength for '{subject}' scores {trend}/100. "
        f"Recommended: lead with a curiosity-gap hook backed by one concrete fact."
    )
    return ResearchSummary(
        executive_summary=executive,
        important_facts=[f"Research providers returned no high-confidence sources for '{subject}'."],
        statistics=[f"Estimated trend strength: {trend}/100."],
        contrarian_ideas=[f"The common take on {subject} may be incomplete."],
        common_myths=[f"Popular myths about {subject} persist despite new data."],
        questions=[f"What is the latest on {subject}?"],
        emerging_trends=[f"{intent.niche} shorts on {subject} remain in demand."],
        key_takeaways=["Use heuristic research — enable providers for data-backed content."],
        topic_context=context_text,
        trend_strength=trend,
        opportunity_score=opportunity,
    )
