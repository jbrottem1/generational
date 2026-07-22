"""Photographic educational fallback — real photos when AI image gen fails.

Approved fallback visuals only: licensed Wikimedia Commons photographs (or
entries already in the Project Reality catalog). Never returns mock:// URIs,
runtime:// placeholders, or solid-color lavfi gradients.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from core.log import get_logger
from services.media_production.persistence import write_bytes

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
_STOP = frozenset(
    {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
        "this", "that", "from", "into", "over", "under", "cinematic", "photorealistic",
        "realistic", "image", "photo", "still", "scene", "vertical", "short",
        "youtube", "background", "camera", "shot", "close", "wide", "detail",
        "educational", "documentary", "style", "highly", "engaging", "about",
        "why", "how", "what", "have", "has", "are", "is", "be", "as", "at",
    }
)

# Prefer stable Commons FilePath URLs for common educational topics.
_CURATED: dict[str, dict[str, str]] = {
    "octopus": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Common octopus",
    },
    "octopuses": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Common octopus",
    },
    "heart": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_hearts_diagram.png?width=1200",
        "credit": "Wikimedia Commons",
        "license": "public_domain",
        "label": "Octopus circulatory diagram",
    },
    "hearts": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Octopus anatomy context",
    },
    "blood": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Octopus underwater",
    },
    "gill": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Octopus gills context",
    },
    "underwater": {
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Octopus_vulgaris_2.jpg?width=1200",
        "credit": "Albert Kok / Wikimedia Commons",
        "license": "CC-BY-SA",
        "label": "Underwater octopus",
    },
}


def _keywords(prompt: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z]{3,}", (prompt or "").lower())
    out: list[str] = []
    for w in words:
        if w in _STOP or w in out:
            continue
        out.append(w)
        if len(out) >= limit:
            break
    return out


def _catalog_hit(keywords: list[str]) -> dict[str, Any] | None:
    try:
        from services.reality.catalog import images_for_concepts, load_catalog
    except Exception:  # noqa: BLE001
        return None
    hits = images_for_concepts(*keywords)
    if not hits:
        # loose organism/name match
        catalog = load_catalog()
        for img in catalog.values():
            blob = " ".join(
                [img.organism, img.scientific_name, " ".join(img.concepts)]
            ).lower()
            if any(k in blob for k in keywords):
                hits.append(img)
                break
    if not hits:
        return None
    img = hits[0]
    if not img.path.exists() or img.path.stat().st_size < 1024:
        return None
    return {
        "path": str(img.path),
        "provider": "reality_catalog",
        "placeholder": False,
        "approved_fallback_visual": True,
        "status": "approved_fallback",
        "credit": img.credit,
        "license": img.license,
        "source_url": img.source_url,
        "label": img.organism or img.image_id,
        "width": img.width or 0,
        "height": img.height or 0,
    }


def _download(url: str, *, name: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "GenerationalVisualPipeline/2.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").lower()
    if not data or len(data) < 1024:
        return ""
    ext = "jpg"
    if "png" in ctype or url.lower().endswith(".png"):
        ext = "png"
    elif "webp" in ctype:
        ext = "webp"
    return write_bytes(data, kind="images", name=name, ext=ext)


def _curated_hit(keywords: list[str], *, name: str) -> dict[str, Any] | None:
    for key in keywords:
        entry = _CURATED.get(key)
        if not entry:
            continue
        try:
            local = _download(entry["fetch_url"], name=f"{name}_{key}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("photographic_fallback.curated_failed | key=%s err=%s", key, exc)
            continue
        if not local:
            continue
        return {
            "path": local,
            "provider": "wikimedia_curated",
            "placeholder": False,
            "approved_fallback_visual": True,
            "status": "approved_fallback",
            "credit": entry.get("credit", ""),
            "license": entry.get("license", ""),
            "source_url": entry.get("fetch_url", ""),
            "label": entry.get("label", key),
        }
    return None


def _commons_search(query: str, *, name: str) -> dict[str, Any] | None:
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1200,
            "format": "json",
        }
    )
    req = urllib.request.Request(api, headers={"User-Agent": "GenerationalVisualPipeline/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("photographic_fallback.commons_search_failed | q=%s err=%s", query, exc)
        return None
    pages = ((payload.get("query") or {}).get("pages") or {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = str(info.get("mime") or "")
        if not mime.startswith("image/"):
            continue
        url = str(info.get("thumburl") or info.get("url") or "")
        if not url:
            continue
        try:
            local = _download(url, name=name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("photographic_fallback.download_failed | url=%s err=%s", url[:120], exc)
            continue
        if not local:
            continue
        meta = info.get("extmetadata") or {}
        credit = str((meta.get("Artist") or {}).get("value") or "Wikimedia Commons")
        # Strip simple HTML from credit
        credit = re.sub(r"<[^>]+>", "", credit)[:160]
        license_name = str((meta.get("LicenseShortName") or {}).get("value") or "unknown")
        return {
            "path": local,
            "provider": "wikimedia_commons",
            "placeholder": False,
            "approved_fallback_visual": True,
            "status": "approved_fallback",
            "credit": credit,
            "license": license_name,
            "source_url": url,
            "label": str(page.get("title") or query),
            "width": int(info.get("thumbwidth") or info.get("width") or 0),
            "height": int(info.get("thumbheight") or info.get("height") or 0),
        }
    return None


def fetch_photographic_fallback(
    prompt: str,
    *,
    name: str = "scene",
    keywords: "list[str] | None" = None,
) -> dict[str, Any]:
    """Return a real on-disk photograph for the prompt, or a failed placeholder."""
    keys = list(keywords or []) or _keywords(prompt)
    if not keys and prompt:
        keys = ["science", "nature"]

    for finder in (
        lambda: _catalog_hit(keys),
        lambda: _curated_hit(keys, name=name),
        lambda: _commons_search(" ".join(keys[:4]), name=name),
        lambda: _commons_search(keys[0], name=name) if keys else None,
    ):
        try:
            hit = finder()
        except Exception as exc:  # noqa: BLE001
            logger.warning("photographic_fallback.finder_error | %s", exc)
            hit = None
        if hit and hit.get("path"):
            path = Path(str(hit["path"]))
            if not path.is_absolute():
                path = ROOT / path
            if path.exists() and path.stat().st_size >= 1024:
                hit["prompt"] = prompt
                hit["keywords"] = keys
                hit["file_size"] = path.stat().st_size
                return hit

    return {
        "path": "",
        "provider": "photographic_fallback",
        "placeholder": True,
        "approved_fallback_visual": False,
        "status": "failed",
        "error": f"No photographic fallback found for keywords={keys!r}",
        "prompt": prompt,
        "keywords": keys,
    }
