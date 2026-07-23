"""Master concept art lock for DOCTOR_001 / CHAR-0001."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "MASTER_CONCEPT_ART"

REQUIRED = [
    "doctor_001_01_front_view.png",
    "doctor_001_06_hero_portrait.png",
    "doctor_001_16_fullbody_turnaround.png",
    "doctor_001_20_official_character_reference_sheet.png",
    "INDEX.json",
    "MASTER_CONCEPT_BIBLE.md",
]


def test_master_concept_art_package_complete():
    assert ART.is_dir()
    for name in REQUIRED:
        assert (ART / name).is_file(), name
    for i in range(1, 21):
        matches = list(ART.glob(f"doctor_001_{i:02d}_*.png"))
        assert matches, f"missing output #{i}"
    assert (ART / "doctor_001_expressions_sheet.png").is_file()
