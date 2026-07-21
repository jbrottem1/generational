"""Trusted evidence sources and gather pipeline."""

from __future__ import annotations

import re
from typing import Any

from core.log import get_logger, log_event
from services.evidence_intelligence.models import (
    ANNOTATION_KINDS,
    CAMERA_MOTIONS,
    EvidenceHit,
    EvidencePackage,
    ModalityDecision,
    MotionPlan,
    AnnotationSpec,
    SceneEvidencePlan,
    _clamp,
)
from services.quality.visual_priority import (
    AUTHENTIC_PHOTO_TYPES,
    is_authentic_photo,
    prefer_authentic,
    priority_rank,
    select_visual_source,
)

logger = get_logger(__name__)

# Priority search order — real institutional sources first
TRUSTED_SOURCES = (
    "NASA",
    "NOAA",
    "USGS",
    "NIH",
    "CDC",
    "WHO",
    "PubMed",
    "Google Scholar",
    "Wikimedia Commons",
    "Library of Congress",
    "Smithsonian",
    "National Park Service",
    "ESA",
    "US Government",
    "University repositories",
    "Official company media kits",
    "Open-license educational collections",
    "Reality Catalog",
    "Knowledge Atlas",
)

_SOURCE_HINTS = {
    "nasa": "NASA",
    "noaa": "NOAA",
    "usgs": "USGS",
    "nih": "NIH",
    "cdc": "CDC",
    "who": "WHO",
    "pubmed": "PubMed",
    "scholar": "Google Scholar",
    "wikimedia": "Wikimedia Commons",
    "wikipedia": "Wikimedia Commons",
    "loc.gov": "Library of Congress",
    "smithsonian": "Smithsonian",
    "nps": "National Park Service",
    "esa": "ESA",
    "gov": "US Government",
    "edu": "University repositories",
}

_DIAGRAM_CUES = re.compile(r"\b(diagram|schematic|cross[- ]section|anatomy|labeled|flowchart)\b", re.I)
_ANIM_CUES = re.compile(r"\b(process|cycle|how .+ works|mechanism|step by step|sequence)\b", re.I)
_3D_CUES = re.compile(r"\b(3d|three[- ]dimensional|orbit|molecule|structure|volume|ct scan|mri)\b", re.I)
_MAP_CUES = re.compile(r"\b(map|region|continent|ocean|border|geography|satellite)\b", re.I)


def infer_source_label(credit: str = "", url: str = "", license_name: str = "") -> str:
    blob = f"{credit} {url} {license_name}".lower()
    for needle, label in _SOURCE_HINTS.items():
        if needle in blob:
            return label
    if license_name.upper() in ("NASA", "NOAA", "US-GOV", "US_GOV"):
        return license_name.upper().replace("_", "-")
    return "Open-license educational collections"


def _hit_from_atlas(row: dict[str, Any]) -> EvidenceHit:
    vtype = str(row.get("visual_type") or "photograph")
    conf = _clamp(40 + float(row.get("relevance") or 0) * 40 + float(row.get("quality_score") or 0) * 20)
    return EvidenceHit(
        source="Knowledge Atlas",
        image_id=str(row.get("asset_id") or ""),
        asset_id=str(row.get("asset_id") or ""),
        title=str(row.get("topic") or row.get("asset_id") or ""),
        path=str(row.get("path") or ""),
        url="",
        license_status="catalog",
        visual_type=vtype,
        evidence_confidence=conf,
        credit="Knowledge Atlas",
        concepts=[],
        provider_tier=priority_rank(vtype),
    )


def _hit_from_reality(img: Any) -> EvidenceHit:
    data = img.to_dict() if hasattr(img, "to_dict") else dict(img)
    license_name = str(data.get("license") or "unknown")
    source = infer_source_label(str(data.get("credit") or ""), str(data.get("source_url") or ""), license_name)
    return EvidenceHit(
        source=source if source != "Open-license educational collections" else "Reality Catalog",
        image_id=str(data.get("image_id") or ""),
        asset_id=str(data.get("image_id") or ""),
        title=str(data.get("organism") or data.get("image_id") or ""),
        path=str(data.get("path") or ""),
        url=str(data.get("source_url") or ""),
        license_status=license_name,
        visual_type="photograph",
        evidence_confidence=88,
        credit=str(data.get("credit") or ""),
        concepts=list(data.get("concepts") or []),
        provider_tier=1,
    )


def gather_evidence_hits(
    topic: str,
    *,
    concepts: list[str] | None = None,
    narration: str = "",
    domain: str = "general",
    limit: int = 8,
) -> list[EvidenceHit]:
    """Search Reality Catalog + Knowledge Atlas (trusted local corpus first)."""
    concepts = concepts or _extract_concepts(topic, narration)
    hits: list[EvidenceHit] = []

    # Reality catalog
    try:
        from services.reality.catalog import images_for_concepts, load_catalog

        load_catalog()
        for img in images_for_concepts(*concepts[:8])[:limit]:
            hits.append(_hit_from_reality(img))
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "evidence.reality_search_error", level=30, error=str(exc)[:160])

    # Knowledge Atlas
    try:
        from services.knowledge_atlas import search_visuals

        for row in search_visuals(query=topic, concepts=concepts, domain=None if domain == "general" else domain, limit=limit):
            hits.append(_hit_from_atlas(row))
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "evidence.atlas_search_error", level=30, error=str(exc)[:160])

    # Dedup by id
    seen: set[str] = set()
    unique: list[EvidenceHit] = []
    for h in hits:
        key = h.asset_id or h.image_id or h.path
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(h)

    # Prefer authentic via priority
    as_dicts = [h.to_dict() for h in unique]
    ordered = prefer_authentic(as_dicts, limit=limit)
    return [EvidenceHit.from_dict(d) for d in ordered]


def decide_modality(
    narration: str,
    hits: list[EvidenceHit],
    *,
    topic: str = "",
) -> ModalityDecision:
    text = f"{topic} {narration}"
    photos = [h for h in hits if is_authentic_photo(h.visual_type) or h.provider_tier == 1]
    diagrams = [h for h in hits if h.visual_type in ("diagram", "map", "chart", "graph", "geological_cross_section")]
    videos = [h for h in hits if h.is_video or h.visual_type == "video_footage"]

    real = bool(photos)
    diagram_pref = bool(_DIAGRAM_CUES.search(text) or _MAP_CUES.search(text)) and (bool(diagrams) or not real)
    need_anim = bool(_ANIM_CUES.search(text)) and not real
    need_3d = bool(_3D_CUES.search(text)) and not real
    has_any = bool(hits)

    if real:
        chosen = "photograph"
        ai_only = False
    elif diagrams or diagram_pref:
        chosen = "diagram"
        ai_only = not has_any
    elif videos:
        chosen = "video_footage"
        ai_only = False
    elif need_3d:
        chosen = "visualization_3d"
        ai_only = True
    elif need_anim:
        chosen = "animation"
        ai_only = True
    elif has_any:
        chosen = hits[0].visual_type or "public_domain"
        ai_only = False
    else:
        chosen = "ai_generated"
        ai_only = True

    return ModalityDecision(
        real_image_available=real,
        video_footage_available=bool(videos),
        diagram_preferred=diagram_pref,
        animation_required=need_anim and not real,
        visualization_3d_required=need_3d and not real,
        ai_generation_fallback_only=ai_only,
        chosen_modality=chosen,
    )


def select_best_hit(hits: list[EvidenceHit], modality: ModalityDecision) -> EvidenceHit | None:
    if not hits:
        return None
    photos = [h.to_dict() for h in hits if is_authentic_photo(h.visual_type) or h.provider_tier <= 1]
    diagrams = [h.to_dict() for h in hits if h.visual_type in ("diagram", "map", "chart", "graph")]
    illustrations = [h.to_dict() for h in hits if h.visual_type in ("illustration", "document", "scientific_illustration")]
    reconstructions = [h.to_dict() for h in hits if "reconstruction" in h.visual_type]
    ai = [h.to_dict() for h in hits if h.provider_tier >= 5]

    if modality.chosen_modality == "diagram" and diagrams:
        pick = select_visual_source(authentic_hits=[], diagram_hits=diagrams)
    else:
        pick = select_visual_source(
            authentic_hits=photos,
            diagram_hits=diagrams,
            illustration_hits=illustrations,
            reconstruction_hits=reconstructions,
            ai_hits=ai or ([hits[0].to_dict()] if hits else []),
        )
    asset = pick.get("asset")
    return EvidenceHit.from_dict(asset) if isinstance(asset, dict) else None


_STOP_CUES = frozenset(
    {
        "the", "and", "for", "with", "this", "that", "from", "into", "process",
        "inside", "modern", "before", "after", "about", "their", "there", "when",
        "where", "which", "while", "using", "makes", "make", "made", "then",
        "also", "just", "over", "under", "each", "both", "some", "many", "most",
        "image", "digital", "final", "actually", "engineers", "assemble",
    }
)

_TEACHING_NOUNS = re.compile(
    r"\b("
    r"earth|sun|moon|planet|orbit|axis|tilt|season|seasons|equator|pole|atmosphere|"
    r"camera|lens|lenses|sensor|shutter|processor|factory|chip|calibration|"
    r"nucleus|cell|satellite|microscope|diagram|fossil|shell|coral|"
    r"wasp|hoverfly|predator|mimic|evolution|galaxy|"
    r"black\s+hole|event\s+horizon|ct\s+scan|mri|histology|specimen|artifact|"
    r"northern\s+hemisphere|southern\s+hemisphere|image\s+sensor"
    r")\b",
    re.I,
)


def build_annotation_plan(
    narration: str,
    *,
    start_sec: float,
    end_sec: float,
    evidence: EvidenceHit | None = None,
) -> list[AnnotationSpec]:
    """Build annotations only for terms explicitly in narration (teaching purpose required)."""
    text = (narration or "").strip()
    if not text:
        return []

    duration = max(0.5, end_sec - start_sec)
    cues: list[str] = []
    for match in _TEACHING_NOUNS.finditer(text):
        cue = match.group(0).strip()
        key = cue.lower()
        if key in _STOP_CUES or len(key) < 3:
            continue
        if cue not in cues:
            cues.append(cue)
    cues = cues[:3]
    if not cues:
        return []

    plans: list[AnnotationSpec] = []
    slot = duration / max(1, len(cues) + 0.5)
    for i, cue in enumerate(cues):
        a0 = start_sec + i * slot * 0.85
        a1 = min(end_sec - 0.15, a0 + max(1.2, slot * 0.9))
        kind = ("label", "circle", "arrow")[i % 3]
        target = f"keyword:{cue}"
        region = {
            "x0": 0.35 + i * 0.08,
            "y0": 0.28 + i * 0.06,
            "x1": 0.62 + i * 0.05,
            "y1": 0.48 + i * 0.05,
        }
        plans.append(
            AnnotationSpec(
                kind=kind,
                target=target,
                narration_cue=cue,
                start_sec=round(a0, 3),
                end_sec=round(a1, 3),
                label_text=cue.title() if kind == "label" else "",
                highlight_region=region,
                callout_target=target,
                extras={"fade_in": 0.025, "fade_out": 0.045, "teaching_purpose": f"identify {cue}"},
            )
        )
    if evidence and len(cues) >= 2 and "compare" in text.lower():
        plans.append(
            AnnotationSpec(
                kind="comparison_overlay",
                target=f"keyword:{cues[0]}",
                narration_cue=cues[0],
                start_sec=round(start_sec + duration * 0.4, 3),
                end_sec=round(end_sec - 0.2, 3),
                callout_target=f"keyword:{cues[1]}",
                extras={"compare_with": cues[1], "fade_in": 0.025, "fade_out": 0.045},
            )
        )
    return plans[:4]


def build_motion_plan(
    modality: ModalityDecision,
    *,
    annotations: list[AnnotationSpec] | None = None,
    attention: int = 50,
) -> MotionPlan:
    annotations = annotations or []
    if modality.chosen_modality in ("diagram", "chart", "map"):
        motion = "static_hold"
    elif attention >= 70 and annotations:
        motion = "push_in_highlight"
    elif modality.real_image_available:
        motion = "ken_burns_in"
    else:
        motion = "slow_pan_right"
    if motion not in CAMERA_MOTIONS:
        motion = "ken_burns_in"

    zooms: list[dict[str, Any]] = []
    for ann in annotations[:2]:
        region = ann.highlight_region or {}
        zooms.append(
            {
                "at_sec": ann.start_sec,
                "until_sec": ann.end_sec,
                "scale": 1.12 if ann.kind in ("circle", "arrow") else 1.06,
                "focus_x": (float(region.get("x0", 0.4)) + float(region.get("x1", 0.6))) / 2,
                "focus_y": (float(region.get("y0", 0.3)) + float(region.get("y1", 0.5))) / 2,
                "reason": f"emphasize {ann.narration_cue}",
            }
        )
    return MotionPlan(camera_motion=motion, suggested_zooms=zooms, intensity=_clamp(30 + attention * 0.4))


def _extract_concepts(topic: str, narration: str = "") -> list[str]:
    text = f"{topic} {narration}".lower()
    tokens = [t for t in re.findall(r"[a-z0-9]+", text) if len(t) > 2]
    stop = {"the", "and", "for", "with", "that", "this", "from", "about", "into", "video", "short"}
    return list(dict.fromkeys(t for t in tokens if t not in stop))[:10]


def _scene_inputs_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull scene-like beats from structured script / visual package / fallback."""
    scenes: list[dict[str, Any]] = []
    structured = candidate.get("structured_script") or {}
    beats = structured.get("beats") or structured.get("scenes") or []
    if isinstance(beats, list) and beats:
        t = 0.0
        for i, beat in enumerate(beats):
            if not isinstance(beat, dict):
                continue
            narr = str(beat.get("narration") or beat.get("text") or beat.get("line") or "")
            dur = float(beat.get("duration_sec") or beat.get("length_sec") or 4.0)
            scenes.append(
                {
                    "scene_number": i + 1,
                    "scene_id": str(beat.get("scene_id") or f"s{i+1}"),
                    "narration": narr,
                    "start_sec": t,
                    "end_sec": t + dur,
                }
            )
            t += dur
        if scenes:
            return scenes

    script = str(candidate.get("script") or "")
    if script:
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", script) if p.strip()]
        t = 0.0
        for i, part in enumerate(parts[:8]):
            dur = max(3.0, min(8.0, len(part.split()) * 0.45))
            scenes.append(
                {
                    "scene_number": i + 1,
                    "scene_id": f"s{i+1}",
                    "narration": part,
                    "start_sec": t,
                    "end_sec": t + dur,
                }
            )
            t += dur
        if scenes:
            return scenes

    # Single-beat fallback from title/hook
    narr = str(candidate.get("hook") or candidate.get("angle") or candidate.get("title") or "Educational visual")
    return [{"scene_number": 1, "scene_id": "s1", "narration": narr, "start_sec": 0.0, "end_sec": 5.0}]


def plan_scene_evidence(
    narration: str,
    *,
    scene_number: int = 1,
    scene_id: str = "s1",
    start_sec: float = 0.0,
    end_sec: float = 5.0,
    topic: str = "",
    domain: str = "general",
    attention_hint: int = 50,
) -> SceneEvidencePlan:
    hits = gather_evidence_hits(topic or narration[:80], narration=narration, domain=domain)
    modality = decide_modality(narration, hits, topic=topic)
    best = select_best_hit(hits, modality)
    annotations = build_annotation_plan(narration, start_sec=start_sec, end_sec=end_sec, evidence=best)
    motion = build_motion_plan(modality, annotations=annotations, attention=attention_hint)

    conf = int(best.evidence_confidence) if best else 15
    if modality.real_image_available:
        conf = max(conf, 75)
    elif modality.ai_generation_fallback_only:
        conf = min(conf, 35)

    image = best.to_dict() if best else {}
    asset_ids = [best.asset_id] if best and best.asset_id else []
    reality_ids: list[str] = []
    if best and best.image_id and (best.source == "Reality Catalog" or best.provider_tier == 1):
        reality_ids = [best.image_id]

    # Asset type for Visual Intelligence adapters
    if best and not modality.ai_generation_fallback_only:
        asset_type = "atlas_image"
    else:
        asset_type = "ai_image"

    transition = "crossfade" if modality.real_image_available else "hard_cut"
    attention = _clamp(
        0.35 * conf
        + 0.25 * attention_hint
        + 0.20 * (80 if modality.real_image_available else 40)
        + 0.20 * min(100, 40 + len(annotations) * 15)
    )

    return SceneEvidencePlan(
        scene_id=scene_id,
        scene_number=scene_number,
        narration=narration,
        modality=modality,
        evidence=best,
        evidence_confidence=conf,
        image_source=best.source if best else "",
        license_status=best.license_status if best else "unknown",
        visual_type=best.visual_type if best else modality.chosen_modality,
        motion_plan=motion,
        annotation_plan=annotations,
        highlight_regions=[a.highlight_region for a in annotations if a.highlight_region],
        callout_targets=[a.callout_target for a in annotations if a.callout_target],
        annotation_locations=[
            {"target": a.target, "kind": a.kind, "start_sec": a.start_sec, "end_sec": a.end_sec}
            for a in annotations
        ],
        narration_timing={"start_sec": start_sec, "end_sec": end_sec},
        transition_type=transition,
        expected_attention_score=attention,
        image=image,
        atlas_asset_ids=asset_ids,
        reality_image_ids=reality_ids if reality_ids else ([best.image_id] if best and best.image_id else []),
        asset_type=asset_type,
    )


def build_evidence_package(
    candidate: dict[str, Any],
    *,
    topic: str = "",
    domain: str = "general",
    attention: dict[str, Any] | None = None,
) -> EvidencePackage:
    """Full evidence package for one scripted candidate."""
    title = str(candidate.get("title") or topic or "educational topic")
    attention_hint = int(
        (attention or {}).get("retention_score")
        or candidate.get("human_attention_score")
        or candidate.get("psychology_score")
        or 50
    )
    scene_inputs = _scene_inputs_from_candidate(candidate)
    scenes: list[SceneEvidencePlan] = []
    for raw in scene_inputs:
        scenes.append(
            plan_scene_evidence(
                str(raw.get("narration") or ""),
                scene_number=int(raw.get("scene_number") or len(scenes) + 1),
                scene_id=str(raw.get("scene_id") or f"s{len(scenes)+1}"),
                start_sec=float(raw.get("start_sec") or 0),
                end_sec=float(raw.get("end_sec") or 5),
                topic=title,
                domain=domain,
                attention_hint=attention_hint,
            )
        )

    authentic = sum(1 for s in scenes if s.modality.real_image_available or (s.evidence and s.evidence.provider_tier <= 2))
    ai_fallbacks = sum(1 for s in scenes if s.modality.ai_generation_fallback_only)
    overall = _clamp(sum(s.evidence_confidence for s in scenes) / max(1, len(scenes)))

    reasoning = (
        f"Evidence for '{title}': {authentic}/{len(scenes)} scenes with authentic media; "
        f"{ai_fallbacks} AI-fallback-only. Overall confidence {overall}. "
        f"Sources queried: Reality Catalog + Knowledge Atlas (+ trusted institutional priority list)."
    )
    log_event(
        logger,
        "evidence_intelligence.package_built",
        topic=title[:80],
        scenes=len(scenes),
        authentic=authentic,
        ai_fallback=ai_fallbacks,
        confidence=overall,
    )
    return EvidencePackage(
        topic=title,
        scenes=scenes,
        trusted_sources_queried=list(TRUSTED_SOURCES),
        authentic_hit_count=authentic,
        ai_fallback_count=ai_fallbacks,
        overall_evidence_confidence=overall,
        reasoning=reasoning,
    )
