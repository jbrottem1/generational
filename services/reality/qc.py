"""Reality export QC — license, resolution, readability."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.reality.catalog import ALLOWED_LICENSES, RealityImage, get_image, load_catalog


MIN_SHORT_SIDE = 400
MIN_PANEL_FRACTION = 0.12  # image panel occupies meaningful canvas area


@dataclass
class RealityQCResult:
    passed: bool
    images_used: list[str] = field(default_factory=list)
    licenses_ok: bool = True
    panel_readable: bool = True
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "images_used": self.images_used,
            "licenses_ok": self.licenses_ok,
            "panel_readable": self.panel_readable,
            "hard_fails": self.hard_fails,
            "warnings": self.warnings,
        }


def validate_image(img: RealityImage) -> list[str]:
    fails: list[str] = []
    if not img.path.is_file():
        fails.append(f"missing_image:{img.image_id}")
        return fails
    if img.license not in ALLOWED_LICENSES:
        fails.append(f"license_not_allowed:{img.image_id}:{img.license}")
    short = min(img.width, img.height)
    if short < MIN_SHORT_SIDE:
        fails.append(f"resolution_too_low:{img.image_id}:{short}")
    return fails


def evaluate_reality_export(
    *,
    image_ids: list[str],
    demo_id: str | None = None,
) -> RealityQCResult:
    """Validate reality images referenced by a production."""
    hard: list[str] = []
    warnings: list[str] = []
    used: list[str] = []

    if not image_ids:
        hard.append("no_reality_images")
        return RealityQCResult(
            passed=False,
            licenses_ok=False,
            panel_readable=False,
            hard_fails=hard,
        )

    licenses_ok = True
    readable = True
    for iid in image_ids:
        img = get_image(iid)
        if img is None:
            hard.append(f"unknown_image_id:{iid}")
            licenses_ok = False
            readable = False
            continue
        used.append(iid)
        fails = validate_image(img)
        for f in fails:
            if f.startswith("license"):
                licenses_ok = False
            if f.startswith("resolution") or f.startswith("missing"):
                readable = False
            hard.append(f)

    if demo_id and not demo_id.startswith("foundation_"):
        warnings.append("reality_qc_demo_not_foundation")

    passed = not hard
    return RealityQCResult(
        passed=passed,
        images_used=used,
        licenses_ok=licenses_ok and not any("license" in f for f in hard),
        panel_readable=readable and not any(
            f.startswith("missing") or f.startswith("resolution") for f in hard
        ),
        hard_fails=hard,
        warnings=warnings,
    )


def collect_demo_image_ids(demo_id: str) -> list[str]:
    from services.reality.planner import plan_reality_beats

    ids: list[str] = []
    for panel in plan_reality_beats(demo_id):
        ids.extend(panel.image_ids)
    return list(dict.fromkeys(ids))
