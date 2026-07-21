"""Generational OS — Autonomous Media Operating System (GenOS)."""

from __future__ import annotations

__all__ = [
    "ExecutionLayer",
    "LAYER_OWNERS",
    "PIPELINE_STAGES",
    "ProductionStage",
    "build_genos_dashboard",
    "build_operating_dashboard",
    "generate_all_reports",
    "run_operating_cycle",
    "simulate_operating_day",
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
    if name in ("run_operating_cycle", "simulate_operating_day", "build_genos_dashboard"):
        from services.generational_os import genos as g

        return getattr(g, name)
    if name == "generate_all_reports":
        from services.generational_os.reports_os import generate_all_reports

        return generate_all_reports
    raise AttributeError(name)
