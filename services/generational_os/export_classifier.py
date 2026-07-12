"""Domain-classified Desktop export — Generational/Videos/{Category}/."""

from __future__ import annotations

import re
from pathlib import Path

# V2.5 canonical export root
EXPORT_ROOT_PARTS = (
    "Desktop",
    "AI Start-up",
    "Generational",
    "Videos",
)

DOMAIN_FOLDERS: tuple[str, ...] = (
    "Biology",
    "Physics",
    "Chemistry",
    "Mathematics",
    "Earth Science",
    "Astronomy",
    "Medicine",
    "Technology",
    "Engineering",
    "Psychology",
    "History",
    "Business",
    "Artificial Intelligence",
    "Miscellaneous",
)

# Map keywords / prefixes → folder
_DOMAIN_RULES: list[tuple[str, str]] = [
    (r"^biology[_\s]", "Biology"),
    (r"^bio[_\s]", "Biology"),
    (r"turtle|mimicry|evolution|cell|immune|dna|ecology", "Biology"),
    (r"^physics[_\s]|newton|force|gravity|momentum", "Physics"),
    (r"^chemistry[_\s]|molecule|atom|reaction", "Chemistry"),
    (r"^math[_\s]|equation|algebra|calculus", "Mathematics"),
    (r"earth|geology|climate|weather|plate", "Earth Science"),
    (r"astro|planet|star|galaxy|cosmos|jwst", "Astronomy"),
    (r"medicine|health|brain|neuro|immune", "Medicine"),
    (r"tech|software|computer|robot|ai[_\s]", "Technology"),
    (r"engineer|mechanical|electrical", "Engineering"),
    (r"psych|bias|cognitive|behavior", "Psychology"),
    (r"history|ancient|war|empire", "History"),
    (r"business|econom|market|startup", "Business"),
    (r"artificial.intelligence|machine.learning|llm|gpt|neural", "Artificial Intelligence"),
]

_LEGACY_EXPORT_PARTS = (
    "Desktop",
    "AI Start-up",
    "videos",
    "Test run 2 generational",
)


def export_root(*, create: bool = False) -> Path:
    path = Path.home().joinpath(*EXPORT_ROOT_PARTS)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        for domain in DOMAIN_FOLDERS:
            (path / domain).mkdir(exist_ok=True)
    return path


def legacy_export_root() -> Path:
    return Path.home().joinpath(*_LEGACY_EXPORT_PARTS)


def classify_domain(
    *,
    subject: str = "",
    series: str = "",
    filename: str = "",
    domain: str = "",
    demo_id: str = "",
) -> str:
    """Return one of DOMAIN_FOLDERS for automatic filing."""
    if domain:
        for folder in DOMAIN_FOLDERS:
            if folder.lower() == domain.strip().lower():
                return folder
        if domain.strip().lower() in ("ai", "ml"):
            return "Artificial Intelligence"

    blob = " ".join([subject, series, filename, demo_id]).lower()
    for pattern, folder in _DOMAIN_RULES:
        if re.search(pattern, blob, re.I):
            return folder
    return "Miscellaneous"


def classified_export_dir(
    *,
    subject: str = "",
    series: str = "",
    filename: str = "",
    domain: str = "",
    demo_id: str = "",
    create: bool = True,
) -> Path:
    folder = classify_domain(
        subject=subject,
        series=series,
        filename=filename,
        domain=domain,
        demo_id=demo_id,
    )
    root = export_root(create=create)
    dest = root / folder
    if create:
        dest.mkdir(parents=True, exist_ok=True)
    return dest


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, ext = Path(filename).stem, Path(filename).suffix
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate
        version += 1
