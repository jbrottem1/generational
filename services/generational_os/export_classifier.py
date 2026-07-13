"""Domain-classified Desktop export — delegates to permanent media library."""

from __future__ import annotations

from pathlib import Path

from services.generational_os.media_library import (
    LIBRARY_ROOT_PARTS,
    STANDARD_CATEGORIES,
    build_library_filename,
    category_dir,
    classify_production,
    library_root,
    versioned_export_path,
)

# Backward-compatible aliases (V2.5 → Media Library)
EXPORT_ROOT_PARTS = LIBRARY_ROOT_PARTS
DOMAIN_FOLDERS = STANDARD_CATEGORIES

_LEGACY_EXPORT_PARTS = (
    "Desktop",
    "AI Start-Up",
    "videos",
    "Test run 2 generational",
)


def export_root(*, create: bool = False) -> Path:
    return library_root(create=create)


def legacy_export_root() -> Path:
    return Path.home().joinpath(*_LEGACY_EXPORT_PARTS)


def classify_domain(
    *,
    subject: str = "",
    series: str = "",
    filename: str = "",
    domain: str = "",
    demo_id: str = "",
    title: str = "",
    keywords: list[str] | None = None,
) -> str:
    """Return primary category folder for automatic filing."""
    result = classify_production(
        subject=subject,
        title=title,
        series=series,
        filename=filename,
        domain=domain,
        demo_id=demo_id,
        keywords=keywords,
    )
    return result["primary"]


def classified_export_dir(
    *,
    subject: str = "",
    series: str = "",
    filename: str = "",
    domain: str = "",
    demo_id: str = "",
    title: str = "",
    create: bool = True,
) -> Path:
    folder = classify_domain(
        subject=subject,
        series=series,
        filename=filename,
        domain=domain,
        demo_id=demo_id,
        title=title,
    )
    return category_dir(folder, create=create)


def unique_path(directory: Path, filename: str, *, file_hash: str = "") -> Path:
    path, _ = versioned_export_path(directory, filename, file_hash=file_hash)
    return path


__all__ = [
    "EXPORT_ROOT_PARTS",
    "DOMAIN_FOLDERS",
    "export_root",
    "legacy_export_root",
    "classify_domain",
    "classified_export_dir",
    "unique_path",
    "build_library_filename",
]
