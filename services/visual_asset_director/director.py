"""Visual Asset Director — select / validate / prepare assets for cinematic + render."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from services.visual_asset_director.composition import score_composition
from services.visual_asset_director.continuity import continuity_report
from services.visual_asset_director.inspect import inspect_asset
from services.visual_asset_director.models import MIN_OVERALL_TO_APPROVE
from services.visual_asset_director.scorecard import build_scorecard
from services.visual_asset_director.styles import resolve_style_profile, style_compatibility


def _scene_id(scene: dict[str, Any], idx: int) -> str:
    return str(scene.get("scene_id") or scene.get("id") or scene.get("beat") or f"scene_{idx:02d}")


def _collect_candidates_for_scene(
    scene: dict[str, Any],
    *,
    idx: int,
    asset_pool: list[dict[str, Any]],
    fallback_dirs: list[Path],
) -> list[dict[str, Any]]:
    """Gather candidate asset paths for one scene (does not invent media)."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(path: str, meta: dict[str, Any] | None = None, source: str = "") -> None:
        p = str(path or "").strip()
        if not p or p in seen:
            return
        seen.add(p)
        out.append({"path": p, "meta": dict(meta or {}), "source": source})

    for key in ("image", "image_path", "asset_path", "still_path", "uri", "file", "approved_asset_path"):
        if scene.get(key):
            add(str(scene[key]), {"from": key}, "scene_field")
    for key in ("candidates", "asset_candidates", "media_candidates", "images"):
        for item in scene.get(key) or []:
            if isinstance(item, str):
                add(item, {}, "scene_list")
            elif isinstance(item, dict):
                add(
                    str(item.get("path") or item.get("uri") or item.get("image") or ""),
                    item,
                    "scene_list",
                )

    # Map pool slots by index / keyword overlap
    purpose = str(scene.get("purpose") or scene.get("narration") or scene.get("title") or "")
    for asset in asset_pool:
        uri = str(asset.get("uri") or asset.get("path") or asset.get("local_path") or "")
        if not uri:
            continue
        hay = f"{asset.get('topic')} {' '.join(map(str, asset.get('keywords') or []))} {asset.get('collection')}".lower()
        toks = {t for t in purpose.lower().split() if len(t) > 3}
        if toks and any(t in hay for t in toks):
            add(uri, asset, "asset_intelligence")
        elif idx < len(asset_pool) and asset is asset_pool[idx]:
            add(uri, asset, "asset_intelligence_slot")

    # Fallback directory plates (e.g. Assets/scenes/00_hook.png)
    for d in fallback_dirs:
        if not d.exists():
            continue
        files = sorted(
            [p for p in d.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")],
            key=lambda p: p.name,
        )
        if idx < len(files):
            add(str(files[idx]), {"filename": files[idx].name}, "scene_dir")
        # Also offer neighbors as alternates
        for p in files:
            add(str(p), {"filename": p.name}, "scene_dir_pool")

    return out


def evaluate_candidate(
    path: str,
    *,
    scene: dict[str, Any] | None = None,
    style_profile: dict[str, Any] | None = None,
    target_aspect: str = "9:16",
    meta: dict[str, Any] | None = None,
    continuity_hint: float = 70.0,
    character_hint: float = 70.0,
    environment_hint: float = 70.0,
) -> dict[str, Any]:
    """Evaluate one candidate image for a scene."""
    insp = inspect_asset(path, target_aspect=target_aspect, meta=meta)
    comp = score_composition(insp, scene=scene)
    card = build_scorecard(
        insp,
        comp,
        continuity_hint=continuity_hint,
        character_hint=character_hint,
        environment_hint=environment_hint,
        style_profile=style_profile,
        meta=meta,
    )
    style_fit = style_compatibility(meta or {}, style_profile or {})
    reasons = list(insp.get("reject_reasons") or [])
    overall = float(card.get("overall_professional_quality") or 0)
    if overall < MIN_OVERALL_TO_APPROVE and "low_educational_clarity" not in reasons and float(card.get("educational_clarity") or 100) < 50:
        reasons.append("low_educational_clarity")
    if style_fit < 40 and "style_drift" not in reasons:
        reasons.append("style_drift")
    approved = len(reasons) == 0 and overall >= MIN_OVERALL_TO_APPROVE
    return {
        "path": path,
        "approved": approved,
        "reject_reasons": sorted(set(reasons)),
        "warnings": list(insp.get("warnings") or []),
        "inspection": insp,
        "composition": comp,
        "scorecard": card,
        "style_compatibility": style_fit,
        "overall": overall,
    }


def select_best_for_scene(
    candidates: list[dict[str, Any]],
    *,
    scene: dict[str, Any],
    style_profile: dict[str, Any],
    target_aspect: str = "9:16",
    used_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Pick strongest candidate; reject poor ones; avoid repeats when alternatives exist."""
    used_paths = used_paths or set()
    evaluations = []
    for c in candidates:
        ev = evaluate_candidate(
            c["path"],
            scene=scene,
            style_profile=style_profile,
            target_aspect=target_aspect,
            meta=c.get("meta"),
        )
        ev["source"] = c.get("source")
        # Soft penalty for repeat
        if c["path"] in used_paths:
            ev["overall"] = max(0.0, float(ev["overall"]) - 12)
            ev.setdefault("warnings", []).append("repeated_asset_soft_penalty")
        evaluations.append(ev)

    evaluations.sort(key=lambda e: (-float(e.get("overall") or 0), len(e.get("reject_reasons") or [])))
    approved = [e for e in evaluations if e.get("approved") and e["path"] not in used_paths]
    rejected = [e for e in evaluations if not e.get("approved")]

    selected = approved[0] if approved else None
    # Never silently re-approve a used path — prefer unused provisional (even if soft-failing)
    unused = [e for e in evaluations if e["path"] not in used_paths]
    provisional = None
    if not selected:
        provisional = unused[0] if unused else (evaluations[0] if evaluations else None)
        if provisional and provisional["path"] in used_paths:
            provisional = dict(provisional)
            provisional.setdefault("warnings", []).append("repeated_asset")
            provisional["reject_reasons"] = sorted(
                set(list(provisional.get("reject_reasons") or []) + ["repeated_asset"])
            )

    return {
        "scene_id": _scene_id(scene, 0),
        "selected": selected,
        "provisional": provisional,
        "approved_alternates": approved[1:4],
        "rejected": [
            {
                "path": e["path"],
                "reject_reasons": e.get("reject_reasons"),
                "overall": e.get("overall"),
                "warnings": e.get("warnings"),
            }
            for e in rejected
        ],
        "evaluations": evaluations,
    }


def direct_visual_assets(
    candidate: dict[str, Any] | None = None,
    *,
    scenes: list[dict[str, Any]] | None = None,
    asset_paths: list[str] | None = None,
    asset_pool: list[dict[str, Any]] | None = None,
    world_package: dict[str, Any] | None = None,
    cinematic_package: dict[str, Any] | None = None,
    style: str | None = None,
    niche: str = "",
    topic: str = "",
    platform: str = "youtube_shorts",
    target_aspect: str = "9:16",
    fallback_scene_dirs: list[str | Path] | None = None,
    character_refs: list[dict[str, Any]] | None = None,
    production_id: str = "",
) -> dict[str, Any]:
    """
    Main entry: evaluate candidates per scene, approve/reject, continuity, VISUAL package.

    Composes World Builder / Scene Builder / Asset Intelligence / Cinematic — does not replace them.
    """
    cand = dict(candidate or {})
    vp = dict(cand.get("visual_package") or {})
    scene_list = list(scenes or vp.get("scenes") or cand.get("scenes") or [])
    topic = topic or str(cand.get("topic") or cand.get("title") or "")
    niche = niche or str(cand.get("category") or cand.get("niche") or "")
    world_package = world_package or cand.get("world_package") or {}
    cinematic_package = cinematic_package or cand.get("cinematic_direction_package") or cand.get("cinematography_package") or {}

    pool = list(asset_pool or [])
    if not pool and cand.get("asset_intelligence"):
        pool = list((cand["asset_intelligence"].get("selected_media") or []))
    if not pool and cand.get("visual_assets"):
        pool = list(cand["visual_assets"])
    for p in asset_paths or []:
        pool.append({"uri": p, "path": p, "topic": topic})

    world_type = str(
        world_package.get("world_type")
        or (world_package.get("world") or {}).get("world_type")
        or ""
    )
    style_profile = resolve_style_profile(style, niche=niche, topic=topic, world_type=world_type)

    if platform in ("youtube_shorts", "tiktok", "instagram_reels") and target_aspect == "9:16":
        pass
    elif cand.get("aspect_ratio"):
        target_aspect = str(cand.get("aspect_ratio"))

    chars = list(character_refs or cand.get("character_references") or [])
    if not chars and "professor" in f"{topic} {niche} {cand}".lower():
        chars = [{"name": "Professor", "role": "educator", "continuity_lock": True}]

    dirs = [Path(d) for d in (fallback_scene_dirs or [])]
    # Auto-detect common local scene folders from candidate packages
    for key in ("scene_dir", "assets_dir", "project_assets"):
        if cand.get(key):
            dirs.append(Path(str(cand[key])))

    if not scene_list and dirs:
        # Synthesize scenes from directory file count
        for d in dirs:
            if d.exists():
                files = sorted(p for p in d.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
                scene_list = [{"scene_id": f"scene_{i:02d}", "purpose": f.stem, "image": str(f)} for i, f in enumerate(files)]
                break

    used: set[str] = set()
    scene_results: list[dict[str, Any]] = []
    approved_assets: list[dict[str, Any]] = []
    rejected_assets: list[dict[str, Any]] = []

    for idx, scene in enumerate(scene_list):
        cands = _collect_candidates_for_scene(scene, idx=idx, asset_pool=pool, fallback_dirs=dirs)
        if not cands and scene.get("image"):
            cands = [{"path": str(scene["image"]), "meta": {}, "source": "scene"}]
        pick = select_best_for_scene(
            cands,
            scene=scene,
            style_profile=style_profile,
            target_aspect=target_aspect,
            used_paths=used,
        )
        sid = _scene_id(scene, idx)
        pick["scene_id"] = sid
        pick["scene"] = {"scene_id": sid, "purpose": scene.get("purpose") or scene.get("beat"), "notes": scene.get("notes")}

        selected = pick.get("selected")
        provisional = pick.get("provisional")
        chosen = selected or provisional
        row: dict[str, Any] = {
            "scene_id": sid,
            "scene": scene,
            "approved": bool(selected),
            "selected_path": selected["path"] if selected else None,
            "provisional_path": None if selected else (provisional or {}).get("path"),
            "scorecard": (chosen or {}).get("scorecard"),
            "composition": (chosen or {}).get("composition"),
            "inspection": (chosen or {}).get("inspection"),
            "reject_reasons": [] if selected else list((provisional or {}).get("reject_reasons") or ["no_approvable_candidate"]),
            "rejected": pick.get("rejected") or [],
            "style_compatibility": (chosen or {}).get("style_compatibility") or 0,
            "cinematic_ready": bool(selected),
        }
        if selected:
            used.add(selected["path"])
            approved_assets.append(
                {
                    "scene_id": sid,
                    "path": selected["path"],
                    "scorecard": selected.get("scorecard"),
                    "composition": selected.get("composition"),
                    "source": selected.get("source"),
                }
            )
            # Prepare for cinematic / renderer (soft fields only)
            scene["approved_asset_path"] = selected["path"]
            scene["visual_asset_scorecard"] = selected.get("scorecard")
            scene["visual_asset_approved"] = True
            scene["cinematic_ready"] = True
            scene["style_profile"] = style_profile.get("style_key")
        else:
            scene["visual_asset_approved"] = False
            scene["cinematic_ready"] = False
            scene["visual_asset_reject_reasons"] = row["reject_reasons"]
            if provisional and provisional.get("path"):
                # Soft fallback for continuity — marked not approved / not cinematic-ready
                scene["provisional_asset_path"] = provisional["path"]
                scene["visual_asset_scorecard"] = provisional.get("scorecard")
                used.add(str(provisional["path"]))
            for r in pick.get("rejected") or []:
                rejected_assets.append({"scene_id": sid, **r})
            if not pick.get("rejected"):
                rejected_assets.append(
                    {
                        "scene_id": sid,
                        "path": None,
                        "reject_reasons": ["no_candidate_assets"],
                        "overall": 0,
                    }
                )

        scene_results.append(row)
        scene_list[idx] = scene

    cont = continuity_report(
        scene_results,
        world_package=world_package,
        style_profile=style_profile,
        character_refs=chars,
    )
    # Re-score continuity onto scorecards
    for row in scene_results:
        if row.get("scorecard"):
            row["scorecard"]["continuity"] = cont.get("continuity_score")
            row["scorecard"]["character_consistency"] = cont.get("character_consistency")
            row["scorecard"]["environment_consistency"] = cont.get("environment_consistency")

    # Thumbnail candidate = highest thumbnail_appeal among approved
    thumb = None
    best_thumb = -1.0
    for a in approved_assets:
        tap = float((a.get("scorecard") or {}).get("thumbnail_appeal") or 0)
        if tap > best_thumb:
            best_thumb = tap
            thumb = {
                "path": a["path"],
                "scene_id": a["scene_id"],
                "thumbnail_appeal": tap,
                "scorecard": a.get("scorecard"),
            }

    env_refs = []
    for env in world_package.get("environment_packages") or world_package.get("environments") or []:
        if isinstance(env, dict):
            env_refs.append(
                {
                    "environment_id": env.get("environment_id") or env.get("zone_id"),
                    "name": env.get("name") or env.get("zone_name"),
                    "world_id": world_package.get("world_id"),
                }
            )

    overall_scores = [
        float((r.get("scorecard") or {}).get("overall_professional_quality") or 0)
        for r in scene_results
        if r.get("scorecard")
    ]
    package = {
        "package_type": "VISUAL_PACKAGE",
        "package_version": "1.0.0",
        "production_id": production_id or cand.get("production_id") or "",
        "topic": topic,
        "niche": niche,
        "platform": platform,
        "style_profile": style_profile,
        "approved_assets": approved_assets,
        "rejected_assets": rejected_assets,
        "rejection_reasons_summary": _reason_summary(rejected_assets),
        "visual_scores": {
            "per_scene": {
                r["scene_id"]: r.get("scorecard") for r in scene_results if r.get("scorecard")
            },
            "mean_overall_professional_quality": round(
                sum(overall_scores) / len(overall_scores), 1
            )
            if overall_scores
            else 0.0,
            "mean_approved_professional_quality": round(
                sum(
                    float((a.get("scorecard") or {}).get("overall_professional_quality") or 0)
                    for a in approved_assets
                )
                / max(1, len(approved_assets)),
                1,
            )
            if approved_assets
            else 0.0,
            "approved_count": len(approved_assets),
            "rejected_count": len(rejected_assets),
            "approval_rate": round(len(approved_assets) / max(1, len(scene_list)), 3),
            "cinematic_ready_count": sum(1 for r in scene_results if r.get("cinematic_ready")),
        },
        "continuity_report": cont,
        "thumbnail_candidate": thumb,
        "character_references": chars,
        "environment_references": env_refs,
        "asset_manifest": [
            {
                "scene_id": r["scene_id"],
                "path": r.get("selected_path") or r.get("provisional_path"),
                "approved": r.get("approved"),
                "provisional": bool(r.get("provisional_path") and not r.get("approved")),
                "cinematic_ready": r.get("cinematic_ready"),
                "overall": (r.get("scorecard") or {}).get("overall_professional_quality"),
                "reject_reasons": r.get("reject_reasons") or [],
            }
            for r in scene_results
        ],
        "scene_direction": scene_results,
        "cinematic_hints": {
            "note": "Does not replace AI Cinematic Director — prepares approved stills only",
            "preferred_motion": style_profile.get("motion"),
            "preferred_lighting": style_profile.get("lighting"),
            "has_cinematic_package": bool(cinematic_package),
        },
        "composes": [
            "world_builder",
            "scene_builder",
            "asset_intelligence",
            "cinematic_director",
            "audience_intelligence",
            "creative_performance_lab",
        ],
        "does_not_replace": [
            "scene_builder",
            "cinematic_director",
            "renderer",
            "world_builder",
        ],
        "fingerprint": hashlib.sha256(
            "|".join(str(a.get("path")) for a in approved_assets).encode()
        ).hexdigest()[:16],
    }
    package["validation"] = validate_visual_package(package)
    return package


def _reason_summary(rejected: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rejected:
        for reason in r.get("reject_reasons") or []:
            counts[str(reason)] = counts.get(str(reason), 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def validate_visual_package(package: dict[str, Any]) -> dict[str, Any]:
    fails: list[str] = []
    warnings: list[str] = []
    if not package.get("style_profile"):
        fails.append("missing_style_profile")
    if not package.get("asset_manifest"):
        warnings.append("empty_manifest")
    approved = package.get("approved_assets") or []
    if not approved:
        fails.append("no_approved_assets")
    cont = package.get("continuity_report") or {}
    if float(cont.get("continuity_score") or 0) < 40:
        fails.append("continuity_collapse")
    if float((package.get("visual_scores") or {}).get("mean_overall_professional_quality") or 0) < 40:
        warnings.append("low_mean_professional_quality")
    # Style drift flag
    if any(i.get("reason") == "style_drift" for i in cont.get("continuity_issues") or []):
        fails.append("style_drift")
    return {
        "ok": not fails,
        "passed": not fails,
        "hard_fails": fails,
        "warnings": warnings,
    }
