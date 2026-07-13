"""Generational Animation — character performance & lip sync foundation."""

from __future__ import annotations

from services.animation.lip_sync import AmplitudeMouthDriver, MouthDriver, build_mouth_timeline
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec, draw_stick_figure

__all__ = [
    "AmplitudeMouthDriver",
    "MouthDriver",
    "StickFigureSpec",
    "build_mouth_timeline",
    "draw_stick_figure",
    "render_lip_sync_performance",
]
