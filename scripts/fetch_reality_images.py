#!/usr/bin/env python3
"""Download curated Reality catalog images from Wikimedia Commons."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT / "data" / "reality" / "images"
CATALOG_PATH = ROOT / "data" / "reality" / "catalog.json"

# Wikimedia Commons — Special:FilePath resolves to the canonical upload URL.
ENTRIES = [
    {
        "image_id": "hoverfly_lateral",
        "filename": "hoverfly_lateral.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Episyrphus_balteatus_2.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Episyrphus_balteatus_2.jpg?width=900",
        "license": "CC-BY-SA",
        "credit": "Alvesgaspar / Wikimedia Commons",
        "organism": "Hoverfly",
        "scientific_name": "Episyrphus balteatus",
        "concepts": ["batesian_mimicry", "hoverfly", "mimic", "insect"],
    },
    {
        "image_id": "wasp_lateral",
        "filename": "wasp_lateral.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Vespula_germanica.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Vespula_germanica.jpg?width=900",
        "license": "CC-BY-SA",
        "credit": "Richard Bartz / Wikimedia Commons",
        "organism": "German wasp",
        "scientific_name": "Vespula germanica",
        "concepts": ["batesian_mimicry", "wasp", "model", "warning_coloration"],
    },
    {
        "image_id": "coral_snake",
        "filename": "coral_snake.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Coral_009.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Coral_009.jpg?width=900",
        "license": "CC-BY",
        "credit": "Dawson / Wikimedia Commons",
        "organism": "Eastern coral snake",
        "scientific_name": "Micrurus fulvius",
        "concepts": ["coral_snake", "warning_coloration", "venomous", "model"],
    },
    {
        "image_id": "scarlet_kingsnake",
        "filename": "scarlet_kingsnake.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Lampropeltis_triangulum_elapsoides.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Lampropeltis_triangulum_elapsoides.jpg?width=900",
        "license": "CC-BY-SA",
        "credit": "Patrick Coin / Wikimedia Commons",
        "organism": "Scarlet kingsnake",
        "scientific_name": "Lampropeltis elapsoides",
        "concepts": ["kingsnake", "mimic", "harmless", "batesian_mimicry"],
    },
    {
        "image_id": "monarch_adult",
        "filename": "monarch_adult.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Monarch_Butterfly_Danaus_plexippus_Male_2664px.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Monarch_Butterfly_Danaus_plexippus_Male_2664px.jpg?width=900",
        "license": "CC-BY-SA",
        "credit": "D. Gordon E. Robertson / Wikimedia Commons",
        "organism": "Monarch butterfly",
        "scientific_name": "Danaus plexippus",
        "concepts": ["monarch", "warning_coloration", "butterfly"],
    },
    {
        "image_id": "viceroy_adult",
        "filename": "viceroy_adult.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Viceroy_Butterfly.jpg",
        "fetch_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Viceroy_Butterfly.jpg?width=900",
        "license": "CC-BY-SA",
        "credit": "Cephas / Wikimedia Commons",
        "organism": "Viceroy butterfly",
        "scientific_name": "Limenitis archippus",
        "concepts": ["viceroy", "mimic", "butterfly"],
    },
]


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "GenerationalRealityBot/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) < 5000:
        raise RuntimeError(f"Download too small ({len(data)} bytes): {url}")
    dest.write_bytes(data)


def main() -> int:
    catalog_images = []
    for entry in ENTRIES:
        dest = IMAGES_DIR / entry["filename"]
        print(f"Fetching {entry['image_id']} → {dest.name}", flush=True)
        download(entry["fetch_url"], dest)
        from PIL import Image

        with Image.open(dest) as im:
            w, h = im.size
        catalog_images.append(
            {
                "image_id": entry["image_id"],
                "path": f"images/{entry['filename']}",
                "license": entry["license"],
                "source_url": entry["source_url"],
                "credit": entry["credit"],
                "organism": entry["organism"],
                "scientific_name": entry["scientific_name"],
                "concepts": entry["concepts"],
                "width": w,
                "height": h,
            }
        )
        print(f"  ✓ {w}×{h}", flush=True)

    catalog = {
        "schema_version": 1,
        "project": "project_reality",
        "images": catalog_images,
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Wrote {CATALOG_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
