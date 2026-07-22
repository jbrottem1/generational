"""Factual integrity helpers — quotes, fabricated-history risk flags."""

from __future__ import annotations

import re

# Patterns that look like a direct quotation attributed to a named person.
_QUOTE_PATTERNS = (
    re.compile(r'["“]([^"”]{12,180})["”]\s*[-–—,]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})'),
    re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(?:once\s+)?(?:said|wrote|declared)\s*[,:]?\s*["“]([^"”]{12,180})["”]'),
)

# Modern / frequently misquoted figures — require research overlap; never invent.
SENSITIVE_ATTRIBUTION_NAMES = (
    "einstein",
    "steve jobs",
    "elon musk",
    "jordan peterson",
    "navy seal",
    "tony robbins",
    "andrew huberman",
    "david goggins",
    "james clear",
    "marcus aurelius",  # public domain — still must not fabricate
    "seneca",
    "epictetus",
    "churchill",
    "lincoln",
)

HISTORY_CLAIM_CUES = (
    "in history",
    "historically",
    "during the war",
    "in ancient",
    "once said",
    "famously said",
    "according to legend",  # legend ≠ verified fact
)


def find_quoted_attributions(script: str) -> list[dict]:
    """Return attributed quotation spans found in a script."""
    found = []
    for pattern in _QUOTE_PATTERNS:
        for match in pattern.finditer(script or ""):
            groups = match.groups()
            if len(groups) == 2:
                # Pattern order differs; pick quote vs name by length/heuristics.
                a, b = groups[0].strip(), groups[1].strip()
                if len(a) > len(b):
                    quote, name = a, b
                else:
                    quote, name = b, a
                found.append({"quote": quote, "attribution": name, "span": match.group(0)})
    return found


def quote_integrity_flags(script: str, research: dict | None = None) -> list[str]:
    """Flag unverified quotations and high-risk fabricated-history cues.

    Deterministic heuristics only — never invents "verification". When a direct
    quote appears without research keyword overlap for the attributed name,
    the production is held for human review.
    """
    research = research or {}
    flags: list[str] = []
    lower = (script or "").lower()

    # Research corpus as a weak overlap check for attributed names.
    corpus_parts = [
        " ".join(research.get("important_facts") or []),
        " ".join(research.get("statistics") or []),
        str(research.get("summary", "")),
    ]
    for doc in research.get("documents") or []:
        if isinstance(doc, dict):
            corpus_parts.append(doc.get("title", ""))
            corpus_parts.append(doc.get("summary", ""))
    corpus = " ".join(corpus_parts).lower()

    for item in find_quoted_attributions(script or ""):
        name = item["attribution"].lower()
        if name and name not in corpus:
            flags.append(
                f"Unverified quotation attributed to {item['attribution']} — "
                "verify attribution or paraphrase in original language."
            )

    for name in SENSITIVE_ATTRIBUTION_NAMES:
        if name in lower and ("said" in lower or "wrote" in lower or '"' in (script or "") or "“" in (script or "")):
            if name not in corpus:
                flag = (
                    f"Named figure '{name.title()}' appears with speech attribution "
                    "but no matching research source — do not fabricate quotations."
                )
                if flag not in flags:
                    flags.append(flag)

    for cue in HISTORY_CLAIM_CUES:
        if cue in lower and not corpus.strip():
            flag = f"Historical claim cue '{cue}' with empty research corpus — verify before publish."
            if flag not in flags:
                flags.append(flag)

    return flags
