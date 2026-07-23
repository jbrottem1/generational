"""Tests for permanent Generational Media Library."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.generational_os.media_library import (
    STANDARD_CATEGORIES,
    build_library_filename,
    classify_production,
    library_root,
    search_library,
)


def test_library_root_parts():
    path = library_root()
    assert path.name == "Videos"
    assert "AI Start-Up" in path.parts


def test_standard_categories_count():
    assert len(STANDARD_CATEGORIES) >= 45
    assert "Biology" in STANDARD_CATEGORIES
    assert "Paleontology" in STANDARD_CATEGORIES
    assert "Miscellaneous" in STANDARD_CATEGORIES


def test_classify_turtle_biology():
    result = classify_production(
        title="Origin of Turtles",
        demo_id="foundation_v2_turtle_202",
        filename="Biology_001_202_Origin_of_Turtles.mp4",
    )
    assert result["primary"] == "Biology"
    assert "Paleontology" in result["secondary"] or result["primary"] == "Biology"


def test_classify_black_holes_astronomy():
    result = classify_production(title="Black Holes", subject="supermassive black holes")
    assert result["primary"] == "Astronomy"


def test_classify_ai_chips_technology():
    result = classify_production(title="AI Chips", subject="semiconductor neural accelerators")
    primary = result["primary"]
    assert primary in ("Technology", "Artificial Intelligence", "Computer Science")


def test_build_library_filename():
    name = build_library_filename(
        category="Biology",
        series="001",
        episode="202",
        topic="Origin of Turtles",
    )
    assert name == "Biology_001_202_Origin_of_Turtles.mp4"


def test_search_library_empty_query():
    # Should not raise even when index is empty
    results = search_library()
    assert isinstance(results, list)


def test_video_library_index_exists():
    index_path = ROOT / "data" / "generational_os" / "VIDEO_LIBRARY.json"
    assert index_path.is_file()
    data = json.loads(index_path.read_text())
    assert data["schema_version"] == 1
    assert "productions" in data


if __name__ == "__main__":
    test_library_root_parts()
    test_standard_categories_count()
    test_classify_turtle_biology()
    test_classify_black_holes_astronomy()
    test_classify_ai_chips_technology()
    test_build_library_filename()
    test_search_library_empty_query()
    test_video_library_index_exists()
    print("all media_library tests passed")
