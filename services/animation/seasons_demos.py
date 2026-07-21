"""Foundation V2 — Four Seasons educational Short demo.

Authentic photographs (NASA Earth + seasonal landscapes) are mandatory.
Orbit diagram is a Tier-2 scientific diagram that supplements photos —
never replaces them. Semantic pointers require teaching purpose + targets.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from services.animation.foundation_v2 import (
    PointerAction,
    evidence_tray_v2,
)
from services.animation.layout_engine import visibility_envelope
from services.animation.whiteboard import BoardAction, _font
from services.reality.panel import draw_panels
from services.reality.planner import SEASONS_001_PANELS


# Keyword-only board — short phrases, never full narration
SEASONS_KEYWORDS: list[BoardAction] = [
    BoardAction("write", "NOT distance", start=0.00, end=0.12, row=0, size=52, color=(200, 50, 40)),
    BoardAction("underline", "NOT distance", start=0.06, end=0.12, row=0, size=52, color=(200, 50, 40)),
    BoardAction("write", "Axial tilt", start=0.12, end=0.28, row=0, size=56, color=(20, 40, 90)),
    BoardAction("write", "23.5°", start=0.20, end=0.32, row=1, size=58, color=(20, 40, 90)),
    BoardAction("circle", "23.5°", start=0.24, end=0.32, row=1, size=58),
    BoardAction("write", "More sunlight", start=0.32, end=0.48, row=0, size=48, color=(40, 120, 60)),
    BoardAction("write", "Spring · Summer", start=0.34, end=0.48, row=1, size=40, color=(60, 140, 80)),
    BoardAction("write", "Less sunlight", start=0.48, end=0.66, row=0, size=48, color=(80, 100, 160)),
    BoardAction("write", "Autumn · Winter", start=0.50, end=0.66, row=1, size=40, color=(120, 80, 50)),
    BoardAction("write", "Four seasons", start=0.72, end=0.88, row=0, size=54, color=(20, 40, 90)),
    BoardAction("write", "Tilt shapes life", start=0.84, end=0.98, row=1, size=44, color=(20, 40, 80)),
]

# Every pointer answers: what exactly am I emphasizing?
SEASONS_POINTERS: list[PointerAction] = [
    PointerAction("tap", start=0.04, end=0.10, target="keyword:NOT distance", narration_cue="myth bust: seasons are not caused by distance"),
    PointerAction("point", start=0.12, end=0.20, target="panel:earth", narration_cue="real Earth photograph from NASA Apollo 17"),
    PointerAction("circle", start=0.24, end=0.30, target="keyword:23.5°", narration_cue="Earth's axial tilt angle"),
    PointerAction("point", start=0.34, end=0.40, target="panel:spring", narration_cue="spring landscape — increasing sunlight"),
    PointerAction("point", start=0.41, end=0.46, target="panel:summer", narration_cue="summer landscape — more direct rays"),
    PointerAction("point", start=0.50, end=0.56, target="panel:autumn", narration_cue="autumn foliage — decreasing sunlight"),
    PointerAction("underline", start=0.57, end=0.64, target="panel:winter", narration_cue="winter snow — shorter days"),
    PointerAction("point", start=0.72, end=0.82, target="panel:earth", narration_cue="zoom out to Earth — one tilted planet"),
    PointerAction("circle", start=0.86, end=0.94, target="keyword:Tilt shapes life", narration_cue="final takeaway: tilt creates seasons"),
]

# Exclusive tray windows — photos never stack with diagram
ORBIT_WINDOW = (0.22, 0.32)  # scientific diagram between Earth photo and seasons
ORBIT_ZOOM_WINDOW = (0.0, 0.0)  # unused — Earth photo used for zoom-out instead
SPRING_SUMMER_WINDOW = (0.32, 0.48)
AUTUMN_WINTER_WINDOW = (0.48, 0.66)


def _draw_sun(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, alpha: float) -> None:
    if alpha <= 0.05:
        return
    col = (255, 210, 60)
    for i in range(8):
        ang = math.radians(i * 45 + 10)
        x1 = cx + int(r * 1.2 * math.cos(ang))
        y1 = cy + int(r * 1.2 * math.sin(ang))
        x2 = cx + int(r * 1.7 * math.cos(ang))
        y2 = cy + int(r * 1.7 * math.sin(ang))
        d.line((x1, y1, x2, y2), fill=col, width=3)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 220, 80), outline=(230, 160, 40), width=2)


def _draw_earth_tilt(
    d: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    r: int,
    *,
    tilt_deg: float = 23.5,
    alpha: float = 1.0,
) -> None:
    if alpha <= 0.05:
        return
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(50, 120, 200), outline=(30, 80, 150), width=3)
    d.ellipse((cx - r // 2, cy - r // 3, cx + r // 4, cy + r // 3), fill=(60, 150, 70))
    rad = math.radians(tilt_deg)
    dx = int(r * 1.35 * math.sin(rad))
    dy = int(-r * 1.35 * math.cos(rad))
    d.line((cx - dx, cy + dy, cx + dx, cy - dy), fill=(200, 50, 40), width=4)
    d.ellipse((cx + dx - 5, cy - dy - 5, cx + dx + 5, cy - dy + 5), fill=(200, 50, 40))
    d.text((cx - r, cy + r + 8), "23.5° tilt", fill=(200, 50, 40), font=_font(18))


def draw_orbit_tilt_diagram(canvas: Image.Image, p: float, *, window: tuple[float, float] = ORBIT_WINDOW) -> None:
    """Tier-2 scientific diagram — axial tilt on orbit (supplements NASA photo)."""
    start, end = window
    if end <= start:
        return
    alpha = visibility_envelope(p, start, end, fade_in=0.03, fade_out=0.04)
    if alpha <= 0.05:
        return
    d = ImageDraw.Draw(canvas)
    tray = evidence_tray_v2(*canvas.size)
    x0, y0, x1, y1 = tray
    d.rounded_rectangle(tray, radius=14, fill=(248, 252, 255), outline=(60, 90, 120), width=2)

    sun_x = x0 + 70
    sun_y = (y0 + y1) // 2
    _draw_sun(d, sun_x, sun_y, 26, alpha)

    orbit_cx = (x0 + x1) // 2 + 30
    orbit_cy = (y0 + y1) // 2
    orbit_rx = (x1 - x0) // 2 - 90
    orbit_ry = (y1 - y0) // 2 - 36
    d.ellipse(
        (orbit_cx - orbit_rx, orbit_cy - orbit_ry, orbit_cx + orbit_rx, orbit_cy + orbit_ry),
        outline=(100, 140, 180),
        width=2,
    )
    local = (p - start) / max(end - start, 1e-6)
    angle = local * math.pi * 1.5 - math.pi / 2
    ex = orbit_cx + int(orbit_rx * math.cos(angle))
    ey = orbit_cy + int(orbit_ry * math.sin(angle))
    _draw_earth_tilt(d, ex, ey, 34, tilt_deg=23.5, alpha=alpha)
    d.text((x0 + 16, y0 + 10), "Axial tilt (diagram)", fill=(20, 40, 90), font=_font(22))
    d.text((x0 + 16, y1 - 34), "Supplements NASA Earth photo", fill=(80, 100, 120), font=_font(16))


def _panel_drawer(canvas: Image.Image, panels, p: float) -> None:
    from services.animation.foundation_v2 import evidence_tray_v2 as tray_fn

    draw_panels(canvas, panels, p, layout_rect_fn=tray_fn)


def draw_seasons_001(canvas: Image.Image, t: float, duration: float) -> None:
    """Real photographs first; orbit diagram only in exclusive tray window."""
    p = t / max(duration, 0.1)

    from services.animation.foundation_v2 import (
        board_rect_v2,
        draw_foundation_v2_studio,
        render_keyword_board,
        render_pointer_actions,
    )
    from services.animation.layout_engine import claim_evidence_tray

    draw_foundation_v2_studio(canvas)
    board_rect = board_rect_v2(*canvas.size)
    layout = render_keyword_board(canvas, SEASONS_KEYWORDS, p)

    panel_windows = [(float(pn.start), float(pn.end)) for pn in SEASONS_001_PANELS]
    claim = claim_evidence_tray(
        p,
        panel_windows=panel_windows,
        timeline_window=(0.0, 0.0),
        shell_window=ORBIT_WINDOW,
    )

    panel_slots: dict[str, tuple[int, int, int, int]] = {}
    tray = evidence_tray_v2(*canvas.size)

    if claim.mode == "panel":
        _panel_drawer(canvas, SEASONS_001_PANELS, p)
        for i, pn in enumerate(SEASONS_001_PANELS):
            if visibility_envelope(p, float(pn.start), float(pn.end)) > 0.05:
                panel_slots[str(i)] = tray
                for img_id in pn.image_ids:
                    panel_slots[img_id] = tray
                    if "earth" in img_id:
                        panel_slots["earth"] = tray
                    if "spring" in img_id:
                        panel_slots["spring"] = tray
                    if "summer" in img_id:
                        panel_slots["summer"] = tray
                    if "autumn" in img_id:
                        panel_slots["autumn"] = tray
                    if "winter" in img_id:
                        panel_slots["winter"] = tray
    elif claim.mode == "shell":
        draw_orbit_tilt_diagram(canvas, p, window=ORBIT_WINDOW)
        panel_slots["earth"] = tray

    render_pointer_actions(
        canvas,
        SEASONS_POINTERS,
        p,
        board_layout=layout,
        board_rect=board_rect,
        panel_slots=panel_slots,
        allow_fallback_coords=False,
    )


SEASONS_DEMOS = {
    "foundation_v2_seasons_001": draw_seasons_001,
}


def get_seasons_demo(demo_id: str):
    return SEASONS_DEMOS.get(demo_id)
