"""Generational OS V2.5 — Autonomous Media Operating System."""

from __future__ import annotations

__all__ = [
    "ExecutionLayer",
    "LAYER_OWNERS",
    "PIPELINE_STAGES",
    "ProductionStage",
    "build_operating_dashboard",
    "write_dashboard",
]


def __getattr__(name: str):
    if name in ("ExecutionLayer", "LAYER_OWNERS"):
        from services.generational_os.layers import LAYER_OWNERS, ExecutionLayer

        return {"ExecutionLayer": ExecutionLayer, "LAYER_OWNERS": LAYER_OWNERS}[name]
    if name in ("PIPELINE_STAGES", "ProductionStage"):
        from services.generational_os.pipeline import PIPELINE_STAGES, ProductionStage

        return {"PIPELINE_STAGES": PIPELINE_STAGES, "ProductionStage": ProductionStage}[name]
    if name in ("build_operating_dashboard", "write_dashboard"):
        from services.generational_os.dashboard import build_operating_dashboard, write_dashboard

        return {"build_operating_dashboard": build_operating_dashboard, "write_dashboard": write_dashboard}[name]
    raise AttributeError(name)
