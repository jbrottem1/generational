"""Tests for PROJECT REALITY image integration."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from services.reality.catalog import load_catalog
from services.reality.panel import RealityPanel, draw_reality_panel
from services.reality.qc import collect_demo_image_ids, evaluate_reality_export


def test_catalog_loads_all_batesian_images():
    catalog = load_catalog()
    assert len(catalog) >= 6
    for iid in (
        "hoverfly_lateral",
        "wasp_lateral",
        "coral_snake",
        "scarlet_kingsnake",
        "monarch_adult",
        "viceroy_adult",
    ):
        img = catalog[iid]
        assert img.path.is_file(), f"missing file for {iid}"
        assert img.license in {"CC-BY", "CC-BY-SA", "CC0", "public_domain"}


def test_reality_qc_passes_for_batesian_demos():
    for demo_id in (
        "foundation_batesian_101",
        "foundation_coral_102",
        "foundation_bluffing_103",
    ):
        ids = collect_demo_image_ids(demo_id)
        result = evaluate_reality_export(image_ids=ids, demo_id=demo_id)
        assert result.passed, result.hard_fails
        assert result.licenses_ok
        assert result.panel_readable


def test_draw_split_compare_panel():
    canvas = Image.new("RGB", (1080, 1920), (255, 255, 255))
    panel = RealityPanel(
        layout="split_compare",
        start=0.0,
        end=1.0,
        image_ids=["wasp_lateral", "hoverfly_lateral"],
        labels=["Wasp", "Hoverfly"],
    )
    draw_reality_panel(canvas, panel, 0.5)
    # Spot-check that panel region is not pure white
    px = canvas.getpixel((800, 1200))
    assert px != (255, 255, 255)
