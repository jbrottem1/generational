"""Per-asset image inspection — detect rejectable visual defects (PIL heuristics)."""

from __future__ import annotations

import colorsys
from pathlib import Path
from typing import Any

from services.visual_asset_director.models import (
    MAX_SATURATION_MEAN,
    MIN_CONTRAST_STD,
    MIN_EDGE_DENSITY,
    MIN_HEIGHT,
    MIN_LAPLACIAN_VAR,
    MIN_WIDTH,
    TARGET_ASPECTS,
)


def _open_rgb(path: Path):
    from PIL import Image

    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")
    return img


def laplacian_variance(img) -> float:
    """Blur proxy — lower = blurrier. Pure-Python on a small downsample."""
    gray = img.convert("L").resize((min(320, img.width), min(320, int(img.height * min(320, img.width) / max(1, img.width)))))
    pixels = list(gray.getdata())
    w, h = gray.size
    if w < 3 or h < 3:
        return 0.0
    # Simple Laplacian kernel on interior
    acc = 0.0
    n = 0
    for y in range(1, h - 1):
        row = y * w
        for x in range(1, w - 1):
            c = pixels[row + x]
            lap = (
                -4 * c
                + pixels[row + x - 1]
                + pixels[row + x + 1]
                + pixels[row - w + x]
                + pixels[row + w + x]
            )
            acc += float(lap * lap)
            n += 1
    return acc / max(1, n)


def edge_density(img) -> float:
    gray = img.convert("L").resize((160, max(1, int(160 * img.height / max(1, img.width)))))
    pixels = list(gray.getdata())
    w, h = gray.size
    edges = 0
    total = 0
    for y in range(h - 1):
        for x in range(w - 1):
            i = y * w + x
            gx = abs(pixels[i] - pixels[i + 1])
            gy = abs(pixels[i] - pixels[i + w])
            if gx + gy > 40:
                edges += 1
            total += 1
    return edges / max(1, total)


def luminance_stats(img) -> dict[str, float]:
    small = img.resize((120, max(1, int(120 * img.height / max(1, img.width)))))
    pixels = list(small.getdata())
    lums = [(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in pixels]
    mean = sum(lums) / max(1, len(lums))
    var = sum((v - mean) ** 2 for v in lums) / max(1, len(lums))
    std = var**0.5
    # Saturation
    sats = []
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        sats.append(s)
    sat_mean = sum(sats) / max(1, len(sats))
    return {
        "luminance_mean": round(mean, 2),
        "luminance_std": round(std, 2),
        "saturation_mean": round(sat_mean, 3),
    }


def dominant_palette(img, *, n: int = 5) -> list[tuple[int, int, int]]:
    small = img.resize((48, 48))
    colors = small.getcolors(48 * 48) or []
    colors.sort(key=lambda c: -c[0])
    out = []
    for _count, color in colors[: n * 3]:
        if isinstance(color, int):
            continue
        out.append((int(color[0]), int(color[1]), int(color[2])))
        if len(out) >= n:
            break
    return out


def corner_watermark_risk(img) -> float:
    """High-contrast corner patches often indicate watermarks / logos."""
    w, h = img.size
    zones = [
        img.crop((0, 0, max(1, w // 6), max(1, h // 8))),
        img.crop((w - max(1, w // 6), 0, w, max(1, h // 8))),
        img.crop((0, h - max(1, h // 8), max(1, w // 5), h)),
        img.crop((w - max(1, w // 5), h - max(1, h // 8), w, h)),
    ]
    risks = []
    for z in zones:
        stats = luminance_stats(z)
        # Very high local contrast in tiny corner relative to rest
        risks.append(min(1.0, stats["luminance_std"] / 80.0))
    return round(max(risks) if risks else 0.0, 3)


def aspect_match(width: int, height: int, target: str = "9:16") -> dict[str, Any]:
    if height <= 0:
        return {"ok": False, "ratio": 0.0, "target": target, "delta": 1.0}
    ratio = width / height
    want = TARGET_ASPECTS.get(target) or TARGET_ASPECTS["9:16"]
    delta = abs(ratio - want) / want
    # Allow letterbox / near-vertical (within 18%)
    return {"ok": delta <= 0.18, "ratio": round(ratio, 4), "target": target, "delta": round(delta, 3)}


def inspect_asset(
    path: str | Path,
    *,
    target_aspect: str = "9:16",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect one image/video-still path. Returns metrics + reject reasons."""
    meta = dict(meta or {})
    p = Path(path)
    reasons: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {"path": str(p), "exists": p.exists()}

    if not p.exists():
        return {
            "ok": False,
            "approved": False,
            "reject_reasons": ["missing_file"],
            "warnings": [],
            "metrics": metrics,
            "meta": meta,
        }

    suffix = p.suffix.lower()
    if suffix in (".mp4", ".mov", ".webm"):
        # Video candidates: metadata-only soft pass (no frame decode dependency)
        metrics.update({"kind": "video", "width": meta.get("width") or 0, "height": meta.get("height") or 0})
        w = int(metrics["width"] or 0)
        h = int(metrics["height"] or 0)
        if w and h and (w < MIN_WIDTH or h < MIN_HEIGHT):
            reasons.append("low_resolution")
        if not w:
            warnings.append("video_dimensions_unknown")
        return {
            "ok": not reasons,
            "approved": not reasons,
            "reject_reasons": reasons,
            "warnings": warnings,
            "metrics": metrics,
            "meta": meta,
            "palette": [],
        }

    try:
        img = _open_rgb(p)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "approved": False,
            "reject_reasons": ["unreadable_asset"],
            "warnings": [str(exc)[:120]],
            "metrics": metrics,
            "meta": meta,
        }

    w, h = img.size
    metrics.update(
        {
            "kind": "image",
            "width": w,
            "height": h,
            "megapixels": round((w * h) / 1_000_000, 3),
            "file_bytes": p.stat().st_size if p.exists() else 0,
        }
    )

    if w < MIN_WIDTH or h < MIN_HEIGHT:
        reasons.append("low_resolution")

    aspect = aspect_match(w, h, target_aspect)
    metrics["aspect"] = aspect
    if not aspect["ok"]:
        reasons.append("incorrect_aspect_ratio")

    lap = laplacian_variance(img)
    metrics["laplacian_variance"] = round(lap, 2)
    if lap < MIN_LAPLACIAN_VAR:
        reasons.append("blurry_details")

    stats = luminance_stats(img)
    metrics.update(stats)
    if stats["luminance_std"] < MIN_CONTRAST_STD:
        reasons.append("low_contrast")
    if stats["saturation_mean"] > MAX_SATURATION_MEAN:
        reasons.append("oversaturated_colors")
    # Unrealistic / blown lighting proxy
    if stats["luminance_mean"] > 230 or stats["luminance_mean"] < 18:
        reasons.append("unrealistic_lighting")

    dens = edge_density(img)
    metrics["edge_density"] = round(dens, 4)
    if dens < MIN_EDGE_DENSITY:
        reasons.append("empty_compositions")
    if dens > 0.42:
        reasons.append("visual_clutter")
        warnings.append("high_edge_density")

    wm = corner_watermark_risk(img)
    metrics["watermark_risk"] = wm
    if wm >= 0.85:
        reasons.append("watermarks")

    # Soft AI / stock heuristics from meta + tiny files
    hay = " ".join(
        [
            str(meta.get("source") or ""),
            str(meta.get("provider") or ""),
            str(meta.get("uri") or ""),
            str(p),
        ]
    ).lower()
    if any(t in hay for t in ("stock", "shutterstock", "getty", "adobe_stock")):
        reasons.append("generic_stock_photo")
    if metrics.get("file_bytes", 0) < 8_000 and w >= 400:
        warnings.append("suspiciously_small_file")
        if "ai_artifacts" not in reasons:
            # Tiny PNG often means mock/placeholder plates
            reasons.append("ai_artifacts")

    # Cropped subject proxy: extreme mass near edges via corner luminance vs center
    cx0, cy0 = w // 4, h // 4
    center = img.crop((cx0, cy0, w - cx0, h - cy0))
    cstats = luminance_stats(center)
    metrics["center_luminance_std"] = cstats["luminance_std"]
    if dens > 0.05 and cstats["luminance_std"] < stats["luminance_std"] * 0.35:
        warnings.append("subject_may_be_edge_heavy")
        if "poor_framing" not in reasons:
            reasons.append("poor_framing")

    palette = dominant_palette(img)
    metrics["palette"] = palette

    # Anatomy / object count / floating — cannot reliably detect without CV model
    # Surface as advisory only when meta claims mismatch
    if meta.get("expected_object_count") is not None and meta.get("detected_object_count") is not None:
        if int(meta["detected_object_count"]) != int(meta["expected_object_count"]):
            reasons.append("incorrect_object_counts")
    if meta.get("deformed_anatomy"):
        reasons.append("deformed_anatomy")
    if meta.get("floating_objects"):
        reasons.append("floating_objects")

    # Dedup reasons
    reasons = sorted(set(reasons))
    return {
        "ok": len(reasons) == 0,
        "approved": len(reasons) == 0,
        "reject_reasons": reasons,
        "warnings": warnings,
        "metrics": metrics,
        "meta": meta,
        "palette": palette,
    }
