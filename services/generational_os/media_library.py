"""Permanent Generational Media Library — ~/Desktop/AI Start-Up/Videos/."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

# LOCKED default — user Mac local library root
LIBRARY_ROOT_PARTS = ("Desktop", "AI Start-Up", "Videos")

# Standard category folders (auto-created on demand)
STANDARD_CATEGORIES: tuple[str, ...] = (
    "Biology",
    "Chemistry",
    "Physics",
    "Mathematics",
    "Astronomy",
    "Earth Science",
    "Geology",
    "Paleontology",
    "Zoology",
    "Botany",
    "Medicine",
    "Genetics",
    "Microbiology",
    "Neuroscience",
    "Psychology",
    "Engineering",
    "Technology",
    "Artificial Intelligence",
    "Robotics",
    "Computer Science",
    "Business",
    "Economics",
    "Finance",
    "Marketing",
    "Entrepreneurship",
    "History",
    "Geography",
    "Government",
    "Law",
    "Philosophy",
    "Religion",
    "Military",
    "Infrastructure",
    "Transportation",
    "Aviation",
    "Motorized Vehicles",
    "Space",
    "Ocean",
    "Animals",
    "Plants",
    "Environment",
    "Climate",
    "Energy",
    "Manufacturing",
    "Industrial Processes",
    "Miscellaneous",
)

# Primary classification rules (first match wins)
_CLASSIFICATION_RULES: list[tuple[str, str]] = [
    (r"turtle|mimicry|evolution|cell|immune|dna|ecology|pesticide|organism|species", "Biology"),
    (r"paleont|fossil|dinosaur|eunotosaurus|proganochelys", "Paleontology"),
    (r"zoolog|mammal|reptile|amphibian|invertebrate", "Zoology"),
    (r"botany|plant|photosynth|flora", "Botany"),
    (r"genetic|crispr|gene|heredity|genome", "Genetics"),
    (r"microbi|bacteria|virus|pathogen", "Microbiology"),
    (r"neuro|brain|synapse|cortex", "Neuroscience"),
    (r"psych|bias|cognitive|behavior|mental", "Psychology"),
    (r"black.hole|galaxy|star|planet|cosmos|jwst|astro", "Astronomy"),
    (r"space|rocket|orbit|nasa|mars", "Space"),
    (r"ocean|marine|sea|aquatic|coral", "Ocean"),
    (r"climate|warming|carbon|emission|greenhouse", "Climate"),
    (r"environment|pollution|conservation|ecosystem", "Environment"),
    (r"energy|solar|wind|nuclear|battery|renewable", "Energy"),
    (r"newton|force|gravity|momentum|f=.?ma|physics", "Physics"),
    (r"quantum|mechanics|relativity", "Physics"),
    (r"chemistry|molecule|atom|reaction|organic.chem", "Chemistry"),
    (r"math|algebra|calculus|equation|geometry", "Mathematics"),
    (r"geolog|earthquake|volcano|mineral|plate.tect", "Geology"),
    (r"earth.science|weather|atmosphere|hydrolog", "Earth Science"),
    (r"medicine|health|clinical|drug|pharma|hospital", "Medicine"),
    (r"ai.chip|machine.learning|llm|gpt|neural|deep.learn", "Artificial Intelligence"),
    (r"robot|automation|drone", "Robotics"),
    (r"computer|software|program|coding|algorithm", "Computer Science"),
    (r"tech|semiconductor|chip|hardware", "Technology"),
    (r"engineer|mechanical|electrical|civil", "Engineering"),
    (r"manufactur|factory|assembly.line", "Manufacturing"),
    (r"industrial|process.plant|refinery", "Industrial Processes"),
    (r"business|startup|company|management", "Business"),
    (r"econom|gdp|inflation|macro", "Economics"),
    (r"finance|invest|stock|market|bank", "Finance"),
    (r"market|brand|advertis|consumer", "Marketing"),
    (r"entrepreneur|founder|venture", "Entrepreneurship"),
    (r"history|ancient|war|empire|century", "History"),
    (r"geograph|map|continent|country", "Geography"),
    (r"government|politic|democracy|election", "Government"),
    (r"law|legal|court|constitution", "Law"),
    (r"philosoph|ethic|logic|metaphys", "Philosophy"),
    (r"religion|faith|theology", "Religion"),
    (r"military|army|defense|weapon", "Military"),
    (r"infrastructure|bridge|road|utility", "Infrastructure"),
    (r"transport|rail|transit|logistics", "Transportation"),
    (r"aviation|aircraft|flight|airplane", "Aviation"),
    (r"vehicle|automotive|car|motor|engine", "Motorized Vehicles"),
    (r"animal|wildlife|pet|fauna", "Animals"),
    (r"plant|tree|forest|crop", "Plants"),
]

_LIBRARY_INDEX = project_root() / "data" / "generational_os" / "VIDEO_LIBRARY.json"


def library_root(*, create: bool = False) -> Path:
    """~/Desktop/AI Start-Up/Videos/"""
    path = Path.home().joinpath(*LIBRARY_ROOT_PARTS)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        for cat in STANDARD_CATEGORIES:
            (path / cat).mkdir(exist_ok=True)
    return path


def library_index_path() -> Path:
    return _LIBRARY_INDEX


def _sanitize_token(text: str, *, max_len: int = 48) -> str:
    text = re.sub(r"[^\w\s-]", "", str(text or "").strip())
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "Untitled")[:max_len]


def build_library_filename(
    *,
    category: str,
    series: str,
    episode: str,
    topic: str,
    ext: str = ".mp4",
) -> str:
    """<Category>_<Series>_<Episode>_<Topic>.mp4"""
    cat = _sanitize_token(category, max_len=32)
    ser = _sanitize_token(series, max_len=24) or "000"
    ep = _sanitize_token(episode, max_len=16) or "001"
    top = _sanitize_token(topic, max_len=56)
    return f"{cat}_{ser}_{ep}_{top}{ext}"


def classify_production(
    *,
    subject: str = "",
    title: str = "",
    series: str = "",
    filename: str = "",
    domain: str = "",
    demo_id: str = "",
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Return primary category, secondary categories, and folder name."""
    blob = " ".join(
        [subject, title, series, filename, demo_id, " ".join(keywords or [])]
    ).lower()

    if domain:
        primary = _resolve_category_name(domain)
        if primary:
            secondaries = _secondary_matches(blob, exclude=primary)
            return {"primary": primary, "secondary": secondaries, "folder": primary}

    primary = "Miscellaneous"
    for pattern, folder in _CLASSIFICATION_RULES:
        if re.search(pattern, blob, re.I):
            primary = folder
            break

    secondaries = _secondary_matches(blob, exclude=primary)
    return {"primary": primary, "secondary": secondaries, "folder": primary}


def _resolve_category_name(name: str) -> str | None:
    n = name.strip()
    for cat in STANDARD_CATEGORIES:
        if cat.lower() == n.lower():
            return cat
    # Allow dynamic new categories (Title Case)
    if n and n not in STANDARD_CATEGORIES:
        return _title_category(n)
    return None


def _title_category(name: str) -> str:
    return " ".join(w.capitalize() for w in re.split(r"[\s_/]+", name.strip()) if w)


def _secondary_matches(blob: str, *, exclude: str) -> list[str]:
    found: list[str] = []
    for pattern, folder in _CLASSIFICATION_RULES:
        if folder == exclude or folder in found:
            continue
        if re.search(pattern, blob, re.I):
            found.append(folder)
    return found[:4]


def category_dir(category: str, *, create: bool = True) -> Path:
    folder = _resolve_category_name(category) or _title_category(category)
    root = library_root(create=create)
    dest = root / folder
    if create:
        dest.mkdir(parents=True, exist_ok=True)
    return dest


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_index() -> dict[str, Any]:
    if not _LIBRARY_INDEX.is_file():
        return {"schema_version": 1, "library_root": str(library_root()), "productions": []}
    return json.loads(_LIBRARY_INDEX.read_text(encoding="utf-8"))


def _save_index(index: dict[str, Any]) -> None:
    _LIBRARY_INDEX.parent.mkdir(parents=True, exist_ok=True)
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index["library_root"] = str(library_root())
    _LIBRARY_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    # Mirror index at library root when on local Mac
    root = library_root()
    if root.parent.exists():
        try:
            (root / "VIDEO_LIBRARY.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
        except OSError:
            pass


def find_duplicate(file_hash: str, *, project_id: str = "") -> dict[str, Any] | None:
    index = _load_index()
    for entry in index.get("productions") or []:
        if entry.get("file_hash") == file_hash and entry.get("project_id") != project_id:
            return entry
    return None


def search_library(
    *,
    query: str = "",
    category: str = "",
    series: str = "",
    character: str = "",
    platform: str = "",
    date_from: str = "",
) -> list[dict[str, Any]]:
    """Instant search across VIDEO_LIBRARY.json."""
    index = _load_index()
    rows = list(index.get("productions") or [])
    q = query.lower().strip()

    def _match(entry: dict[str, Any]) -> bool:
        if category and entry.get("category", "").lower() != category.lower():
            return False
        if series and series.lower() not in str(entry.get("series") or "").lower():
            return False
        if character and character.lower() not in str(entry.get("character") or "").lower():
            return False
        if platform and entry.get("platform", "").lower() != platform.lower():
            return False
        if date_from and str(entry.get("created_at") or "") < date_from:
            return False
        if not q:
            return True
        hay = " ".join(
            [
                str(entry.get("title") or ""),
                str(entry.get("topic") or ""),
                str(entry.get("category") or ""),
                str(entry.get("series") or ""),
                " ".join(entry.get("keywords") or []),
                " ".join(entry.get("scientific_sources") or []),
            ]
        ).lower()
        return q in hay or any(q in kw.lower() for kw in entry.get("keywords") or [])

    return [e for e in rows if _match(e)]


def register_library_entry(entry: dict[str, Any]) -> None:
    index = _load_index()
    productions = index.setdefault("productions", [])
    pid = entry.get("project_id")
    productions[:] = [p for p in productions if p.get("project_id") != pid]
    productions.append(entry)
    productions.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    _save_index(index)


def versioned_export_path(directory: Path, filename: str, *, file_hash: str = "") -> tuple[Path, bool]:
    """Return export path; bool=True if new version suffix applied."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate, False
    if file_hash:
        try:
            if file_sha256(candidate) == file_hash:
                return candidate, False  # identical — reuse
        except OSError:
            pass
    stem, ext = Path(filename).stem, Path(filename).suffix
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate, True
        if file_hash:
            try:
                if file_sha256(candidate) == file_hash:
                    return candidate, False
            except OSError:
                pass
        version += 1


def companion_dir_for(mp4_path: Path) -> Path:
    return mp4_path.parent / mp4_path.stem


def write_companion_files(
    companion_dir: Path,
    *,
    script_md: str = "",
    sources: list[str] | None = None,
    captions_srt: str = "",
    metadata: dict[str, Any] | None = None,
    production_report_md: str = "",
    render_manifest: dict[str, Any] | None = None,
    thumbnail_placeholder: bool = True,
) -> dict[str, str]:
    """Create companion folder alongside MP4."""
    companion_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    script_path = companion_dir / "script.md"
    script_path.write_text(script_md or "# Script\n\n(TBD)\n", encoding="utf-8")
    paths["script"] = str(script_path)

    sources_path = companion_dir / "sources.json"
    sources_path.write_text(json.dumps({"sources": sources or []}, indent=2), encoding="utf-8")
    paths["sources"] = str(sources_path)

    captions_path = companion_dir / "captions.srt"
    captions_path.write_text(captions_srt or "", encoding="utf-8")
    paths["captions"] = str(captions_path)

    meta_path = companion_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata or {}, indent=2), encoding="utf-8")
    paths["metadata"] = str(meta_path)

    report_path = companion_dir / "production_report.md"
    report_path.write_text(production_report_md or "# Production Report\n\n(TBD)\n", encoding="utf-8")
    paths["production_report"] = str(report_path)

    render_path = companion_dir / "render_manifest.json"
    render_path.write_text(json.dumps(render_manifest or {}, indent=2), encoding="utf-8")
    paths["render_manifest"] = str(render_path)

    thumb_path = companion_dir / "thumbnail.png"
    if thumbnail_placeholder and not thumb_path.exists():
        # Minimal 1x1 PNG placeholder — replaced in post-production
        thumb_path.write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                "1f15c4890000000a49444154789c6300010000050001000d0a2db400000000"
                "49454e44ae426082"
            )
        )
    paths["thumbnail"] = str(thumb_path)
    return paths
