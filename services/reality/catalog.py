"""Licensed scientific image catalog for PROJECT REALITY."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "reality" / "catalog.json"
IMAGES_ROOT = ROOT / "data" / "reality"

ALLOWED_LICENSES = frozenset({"public_domain", "CC0", "CC-BY", "CC-BY-SA"})


@dataclass(frozen=True)
class RealityImage:
    image_id: str
    path: Path
    license: str
    source_url: str
    credit: str
    organism: str
    scientific_name: str
    concepts: tuple[str, ...]
    width: int
    height: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "path": str(self.path),
            "license": self.license,
            "source_url": self.source_url,
            "credit": self.credit,
            "organism": self.organism,
            "scientific_name": self.scientific_name,
            "concepts": list(self.concepts),
            "width": self.width,
            "height": self.height,
        }


def _parse_entry(raw: dict[str, Any]) -> RealityImage:
    rel = str(raw["path"])
    path = IMAGES_ROOT / rel if not rel.startswith("/") else Path(rel)
    return RealityImage(
        image_id=str(raw["image_id"]),
        path=path,
        license=str(raw["license"]),
        source_url=str(raw.get("source_url") or ""),
        credit=str(raw.get("credit") or ""),
        organism=str(raw.get("organism") or ""),
        scientific_name=str(raw.get("scientific_name") or ""),
        concepts=tuple(str(c) for c in (raw.get("concepts") or [])),
        width=int(raw.get("width") or 0),
        height=int(raw.get("height") or 0),
    )


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, RealityImage]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    out: dict[str, RealityImage] = {}
    for raw in data.get("images") or []:
        img = _parse_entry(raw)
        out[img.image_id] = img
    return out


def get_image(image_id: str) -> RealityImage | None:
    return load_catalog().get(image_id)


def images_for_concepts(*concepts: str) -> list[RealityImage]:
    wanted = {c.lower() for c in concepts}
    hits: list[RealityImage] = []
    for img in load_catalog().values():
        if wanted & {c.lower() for c in img.concepts}:
            hits.append(img)
    return hits
