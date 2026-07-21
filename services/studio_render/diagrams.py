"""Module 7 — Diagram Animator: prefer animated educational graphics."""

from __future__ import annotations

DOMAIN_KEYWORDS = {
    "biology": ("cell", "dna", "organism", "evolution", "species", "gene"),
    "physics": ("force", "energy", "mass", "gravity", "velocity", "quantum"),
    "chemistry": ("atom", "molecule", "reaction", "bond", "element"),
    "astronomy": ("planet", "star", "orbit", "galaxy", "nasa", "space"),
    "engineering": ("circuit", "bridge", "engine", "structure", "load"),
    "math": ("equation", "graph", "function", "derivative", "proof"),
    "technology": ("chip", "algorithm", "network", "ai", "software", "robot"),
}


def _domain(text: str) -> str | None:
    t = text.lower()
    for domain, keys in DOMAIN_KEYWORDS.items():
        if any(k in t for k in keys):
            return domain
    return None


def build_diagrams(candidate: dict) -> list[dict]:
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    if not scenes:
        scenes = list((candidate.get("evidence_package") or {}).get("scenes") or [])
    diagrams: list[dict] = []

    title_blob = str(candidate.get("title") or candidate.get("topic") or "")
    for i, scene in enumerate(scenes or [{"scene_id": "s1", "narration": title_blob}]):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        text = str(scene.get("narration") or "")
        domain = _domain(text) or _domain(title_blob)
        if not domain and not any(
            w in text.lower() for w in ("process", "steps", "timeline", "map", "cross section", "flow")
        ):
            continue

        kind = "process"
        if any(w in text.lower() for w in ("timeline", "history", "years")):
            kind = "timeline"
        elif any(w in text.lower() for w in ("map", "region", "earth", "continent")):
            kind = "map"
        elif any(w in text.lower() for w in ("cross section", "inside", "layer")):
            kind = "cross_section"
        elif any(w in text.lower() for w in ("evol", "tree", "ancestor")):
            kind = "evolution_tree"
        elif any(w in text.lower() for w in ("flow", "pipeline", "steps")):
            kind = "flowchart"
        elif domain == "math":
            kind = "graph"
        elif domain:
            kind = f"{domain}_diagram"

        diagrams.append(
            {
                "scene_id": sid,
                "domain": domain or "general",
                "kind": kind,
                "animated": True,
                "prefer_over_static": True,
                "duration_sec": 2.5,
                "easing": "ease_in_out",
                "reason": f"Educational graphic for {domain or kind} — animate instead of static",
            }
        )
    return diagrams
