"""EpisodePlaybook — persistent JSON store of design patterns, weaknesses,
and measurable successes under data/episode_design/.

Separate from analytics/executive memory — this is the long-term
institutional memory of what episode designs work and why.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DATA_DIR = Path("data/episode_design")
_PLAYBOOK_FILE = "episode_playbook.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_playbook(data_dir: Path) -> dict:
    path = data_dir / _PLAYBOOK_FILE
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"patterns": [], "meta": {}}
    return {"patterns": [], "meta": {}}


def _save_playbook(data_dir: Path, playbook: dict) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / _PLAYBOOK_FILE
    playbook["meta"]["last_updated"] = _now_iso()
    path.write_text(json.dumps(playbook, indent=2, ensure_ascii=False), encoding="utf-8")


class EpisodePlaybook:
    """Persistent store for Generational Episode Design patterns.

    Patterns are keyed by pattern_id. Each entry records:
    - What the pattern is (name, description, niche)
    - Its strengths and documented weaknesses
    - Successes (project_ids + metrics)
    - Improvement notes over time
    - Usage statistics
    """

    def __init__(self, data_dir: "Path | str | None" = None) -> None:
        if data_dir is None:
            data_dir = _DEFAULT_DATA_DIR
        self._dir = Path(data_dir)
        self._playbook = _load_playbook(self._dir)

    # ---------------------------------------------------------------- read

    def all_patterns(self) -> list:
        return list(self._playbook.get("patterns", []))

    def get_pattern(self, pattern_id: str) -> "dict | None":
        for p in self._playbook.get("patterns", []):
            if p.get("pattern_id") == pattern_id:
                return dict(p)
        return None

    def patterns_for_niche(self, niche: str) -> list:
        return [
            p for p in self._playbook.get("patterns", [])
            if p.get("niche", "").lower() == niche.lower()
        ]

    # ---------------------------------------------------------------- write

    def record_pattern(
        self,
        pattern_name: str,
        niche: str,
        description: str,
        strengths: "list[str] | None" = None,
        weaknesses: "list[str] | None" = None,
        improvement_notes: str = "",
        pattern_id: "str | None" = None,
    ) -> str:
        """Add or update a design pattern. Returns pattern_id."""
        existing_id = pattern_id or self._find_by_name(pattern_name)
        if existing_id:
            self._update_pattern(
                existing_id,
                description=description,
                strengths=strengths or [],
                weaknesses=weaknesses or [],
                improvement_notes=improvement_notes,
            )
            return existing_id

        pid = pattern_id or f"pat_{uuid.uuid4().hex[:8]}"
        entry = {
            "pattern_id": pid,
            "pattern_name": pattern_name,
            "description": description,
            "niche": niche,
            "strengths": strengths or [],
            "weaknesses": weaknesses or [],
            "successes": [],
            "improvement_notes": improvement_notes,
            "times_used": 0,
            "average_retention_score": 0,
            "last_updated": _now_iso(),
        }
        self._playbook.setdefault("patterns", []).append(entry)
        _save_playbook(self._dir, self._playbook)
        return pid

    def record_success(
        self,
        pattern_id: str,
        project_id: str,
        retention_score: int,
        metrics: "dict | None" = None,
    ) -> bool:
        """Record a successful use of a pattern."""
        for p in self._playbook.get("patterns", []):
            if p.get("pattern_id") == pattern_id:
                p.setdefault("successes", []).append({
                    "project_id": project_id,
                    "retention_score": retention_score,
                    "metrics": metrics or {},
                    "recorded_at": _now_iso(),
                })
                p["times_used"] = p.get("times_used", 0) + 1
                scores = [s["retention_score"] for s in p["successes"] if "retention_score" in s]
                if scores:
                    p["average_retention_score"] = int(round(sum(scores) / len(scores)))
                p["last_updated"] = _now_iso()
                _save_playbook(self._dir, self._playbook)
                return True
        return False

    def record_weakness(self, pattern_id: str, weakness: str) -> bool:
        """Add a documented weakness to a pattern."""
        for p in self._playbook.get("patterns", []):
            if p.get("pattern_id") == pattern_id:
                weaknesses = p.setdefault("weaknesses", [])
                if weakness not in weaknesses:
                    weaknesses.append(weakness)
                p["last_updated"] = _now_iso()
                _save_playbook(self._dir, self._playbook)
                return True
        return False

    def summary(self) -> dict:
        patterns = self._playbook.get("patterns", [])
        scores = [p["average_retention_score"] for p in patterns if p.get("average_retention_score")]
        return {
            "pattern_count": len(patterns),
            "total_successes": sum(len(p.get("successes", [])) for p in patterns),
            "niches_covered": sorted({p.get("niche", "") for p in patterns if p.get("niche")}),
            "average_retention_score": int(round(sum(scores) / len(scores))) if scores else 0,
            "last_updated": self._playbook.get("meta", {}).get("last_updated", ""),
        }

    # ---------------------------------------------------------------- helpers

    def _find_by_name(self, name: str) -> "str | None":
        for p in self._playbook.get("patterns", []):
            if p.get("pattern_name", "").lower() == name.lower():
                return p["pattern_id"]
        return None

    def _update_pattern(self, pattern_id: str, **updates) -> None:
        for p in self._playbook.get("patterns", []):
            if p.get("pattern_id") == pattern_id:
                for k, v in updates.items():
                    if v:
                        p[k] = v
                p["last_updated"] = _now_iso()
                _save_playbook(self._dir, self._playbook)
                return


def get_playbook(data_dir: "Path | str | None" = None) -> EpisodePlaybook:
    """Return a playbook instance (not a singleton — caller controls scope)."""
    return EpisodePlaybook(data_dir=data_dir)
