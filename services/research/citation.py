"""Citation analysis — map scripts to research sources and flag unsupported claims."""

from __future__ import annotations

from engines.analysis import analyze_script
from core.heuristics import ABSOLUTE_CLAIMS, AUTHORITY_WORDS, clamp, count_hits, has_digit
from services.research.models import ResearchDocument


def _match_sources(script: str, documents: list[ResearchDocument], limit: int = 5) -> list[dict]:
    lower = script.lower()
    matched = []
    for doc in documents:
        score = 0
        for tag in doc.topic_tags or doc.keywords:
            if tag and tag.lower() in lower:
                score += 1
        if doc.title.lower()[:20] in lower:
            score += 2
        if score > 0:
            matched.append((score, doc))
    matched.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
    return [
        {
            "title": doc.title,
            "source_name": doc.source,
            "url": doc.url,
            "provider": doc.provider,
            "credibility_score": doc.credibility_score,
            "confidence_score": doc.confidence,
        }
        for _, doc in matched[:limit]
    ]


def _unsupported_claims(script: str) -> list[str]:
    claims = []
    lower = script.lower()
    for phrase in ABSOLUTE_CLAIMS:
        if phrase in lower and not (has_digit(script) or count_hits(script, AUTHORITY_WORDS)):
            claims.append(f"Absolute claim without cited evidence: '{phrase.strip()}'.")
    issues = analyze_script("", script)
    for issue in issues:
        if "Unsupported claim" in issue and issue not in claims:
            claims.append(issue)
    return claims


def analyze_citations(
    hook: str,
    script: str,
    research: dict,
    documents: list[ResearchDocument] | None = None,
) -> dict:
    """Build citation package for one script."""
    documents = documents or []
    if not documents and research.get("documents"):
        documents = [ResearchDocument.from_dict(d) for d in research["documents"]]

    supporting = _match_sources(f"{hook} {script}", documents)
    unsupported = _unsupported_claims(script)
    has_sources = bool(supporting)
    base_confidence = research.get("research_confidence", 0.4)

    claim_confidence = clamp(
        int(
            100
            * (
                0.45 * base_confidence
                + 0.35 * (sum(s["credibility_score"] for s in supporting) / max(len(supporting), 1) if supporting else 0.2)
                + 0.20 * (1 - min(len(unsupported), 3) / 3)
            )
        ),
        10,
        98,
    )

    notes = []
    if supporting:
        notes.append(f"Script aligns with {len(supporting)} research source(s).")
    else:
        notes.append("No direct source overlap detected — claims rely on general research brief.")
    if unsupported:
        notes.append(f"{len(unsupported)} unsupported claim warning(s) detected.")
    if research.get("fallback"):
        notes.append("Research ran in demo/fallback mode — verify facts before publishing.")

    citation_list = [
        {"title": s["title"], "url": s["url"], "source_name": s["source_name"], "provider": s["provider"]}
        for s in supporting
    ]
    if not citation_list and research.get("research_brief", {}).get("results"):
        for result in research["research_brief"]["results"][:3]:
            citation_list.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "source_name": result.get("source_name", ""),
                    "provider": result.get("provider", ""),
                }
            )

    return {
        "supporting_sources": supporting,
        "claim_confidence": claim_confidence,
        "unsupported_claims": unsupported,
        "fact_check_notes": notes,
        "citation_list": citation_list,
        "citation_count": len(citation_list),
        "has_sources": has_sources,
    }
