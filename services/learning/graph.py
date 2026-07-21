"""Knowledge graph — topics, styles, psychology, retention patterns.

Persists to data/analytics/knowledge_graph.json and expands with every
production / analytics insight.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger, log_event

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DIR = str(ROOT / "data" / "analytics")
_GRAPH_FILE = "knowledge_graph.json"

NODE_TYPES = (
    "topic",
    "creator",
    "channel",
    "audience_segment",
    "keyword",
    "search_trend",
    "video_style",
    "psychology_technique",
    "visual_style",
    "voice_style",
    "thumbnail_style",
    "retention_pattern",
    "platform",
    "engine",
)

_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(directory: str | None = None) -> Path:
    d = Path(directory or _DEFAULT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / _GRAPH_FILE


def _empty() -> dict:
    return {"nodes": {}, "edges": [], "updated_at": _now(), "version": "1.0"}


def _load(directory: str | None = None) -> dict:
    path = _path(directory)
    if not path.is_file():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _empty()
        data.setdefault("nodes", {})
        data.setdefault("edges", [])
        return data
    except Exception:
        return _empty()


def _save(graph: dict, directory: str | None = None) -> None:
    graph["updated_at"] = _now()
    _path(directory).write_text(json.dumps(graph, indent=2, default=str), encoding="utf-8")


def _node_id(kind: str, value: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{kind}:{value}")[:80]
    return safe.lower()


class KnowledgeGraph:
    def __init__(self, directory: str | None = None) -> None:
        self.directory = directory

    def upsert_node(self, kind: str, value: str, *, meta: dict | None = None) -> str:
        if not value:
            return ""
        nid = _node_id(kind, str(value))
        with _lock:
            g = _load(self.directory)
            node = g["nodes"].get(nid) or {
                "id": nid,
                "type": kind,
                "value": str(value),
                "weight": 0,
                "meta": {},
                "created_at": _now(),
            }
            node["weight"] = int(node.get("weight") or 0) + 1
            if meta:
                node["meta"] = {**(node.get("meta") or {}), **meta}
            node["updated_at"] = _now()
            g["nodes"][nid] = node
            _save(g, self.directory)
        return nid

    def link(
        self,
        source_id: str,
        target_id: str,
        *,
        relation: str = "related_to",
        weight: float = 1.0,
        meta: dict | None = None,
    ) -> None:
        if not source_id or not target_id:
            return
        with _lock:
            g = _load(self.directory)
            edges = g.get("edges") or []
            for edge in edges:
                if (
                    edge.get("source") == source_id
                    and edge.get("target") == target_id
                    and edge.get("relation") == relation
                ):
                    edge["weight"] = float(edge.get("weight") or 0) + float(weight)
                    if meta:
                        edge["meta"] = {**(edge.get("meta") or {}), **meta}
                    edge["updated_at"] = _now()
                    _save(g, self.directory)
                    return
            edges.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "relation": relation,
                    "weight": float(weight),
                    "meta": meta or {},
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            )
            g["edges"] = edges
            _save(g, self.directory)

    def expand_from_production(self, record: dict) -> dict[str, Any]:
        topic = self.upsert_node("topic", record.get("topic") or "", meta={"qa": record.get("qa_score")})
        platform = self.upsert_node("platform", record.get("platform") or "")
        if topic and platform:
            self.link(topic, platform, relation="published_on", weight=1.0)
        # Style / score nodes
        if record.get("visual_score"):
            vs = self.upsert_node(
                "visual_style",
                f"visual_score_{int(record['visual_score']) // 10 * 10}",
                meta={"score": record.get("visual_score")},
            )
            if topic and vs:
                self.link(topic, vs, relation="used_visual", weight=float(record.get("visual_score") or 0) / 100)
        if record.get("psychology_score"):
            ps = self.upsert_node(
                "psychology_technique",
                f"psych_{int(record['psychology_score']) // 10 * 10}",
            )
            if topic and ps:
                self.link(topic, ps, relation="used_psychology", weight=1.0)
        if record.get("animation_score"):
            an = self.upsert_node(
                "retention_pattern",
                f"cine_{int(record['animation_score']) // 10 * 10}",
            )
            if topic and an:
                self.link(topic, an, relation="used_camera", weight=1.0)
        log_event(logger, "learning.graph_expanded", topic=record.get("topic"))
        return {"topic": topic, "platform": platform}

    def expand_from_insight(self, insight: dict) -> None:
        dim = str(insight.get("dimension") or "")
        value = str(insight.get("value") or "")
        type_map = {
            "hook": "psychology_technique",
            "psychology_strategy": "psychology_technique",
            "thumbnail_version": "thumbnail_style",
            "voice_version": "voice_style",
            "topic": "topic",
            "niche": "audience_segment",
            "keyword": "keyword",
            "platform": "platform",
            "title": "search_trend",
        }
        kind = type_map.get(dim, "video_style")
        nid = self.upsert_node(
            kind,
            value,
            meta={
                "lift": insight.get("lift"),
                "confidence": insight.get("confidence"),
                "samples": insight.get("samples"),
            },
        )
        engine = self.upsert_node("engine", dim)
        if nid and engine:
            self.link(
                engine,
                nid,
                relation="performs_with_lift",
                weight=float(insight.get("lift") or 0),
                meta={"confidence": insight.get("confidence")},
            )

    def snapshot(self) -> dict[str, Any]:
        with _lock:
            g = _load(self.directory)
        return {
            "node_count": len(g.get("nodes") or {}),
            "edge_count": len(g.get("edges") or []),
            "updated_at": g.get("updated_at"),
            "types": _count_types(g.get("nodes") or {}),
        }

    def to_dict(self) -> dict:
        with _lock:
            return _load(self.directory)


def _count_types(nodes: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for node in nodes.values():
        t = str(node.get("type") or "unknown")
        out[t] = out.get(t, 0) + 1
    return out


_GRAPH: KnowledgeGraph | None = None


def get_knowledge_graph(directory: str | None = None) -> KnowledgeGraph:
    global _GRAPH
    if directory is not None:
        return KnowledgeGraph(directory)
    if _GRAPH is None:
        _GRAPH = KnowledgeGraph()
    return _GRAPH
