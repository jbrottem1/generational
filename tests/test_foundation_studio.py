"""PROJECT FOUNDATION — whiteboard + white studio smoke tests."""

from __future__ import annotations

from PIL import Image

from services.animation.foundation_studio import (
    F_EQUALS_MA_ACTIONS,
    FOUNDATION_DEMOS,
    draw_white_studio,
    get_foundation_demo,
)
from services.animation.fluid_motion import GESTURE_POSES, pose_for
from services.animation.teaching_choreography import PLANS
from services.animation.whiteboard import align_equation_to_write_beat, write_window_from_plan


def test_white_studio_is_pure_white():
    img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    floor_y = draw_white_studio(img)
    assert floor_y > 1000
    # Sample center above floor — must be white
    assert img.getpixel((540, 400)) == (255, 255, 255)


def test_foundation_demos_registered():
    for key in (
        "foundation_f_equals_ma",
        "foundation_force_mass",
        "foundation_newton_everyday",
    ):
        assert key in FOUNDATION_DEMOS
        assert get_foundation_demo(key) is not None
        assert key in PLANS


def test_write_gesture_pose():
    assert "write" in GESTURE_POSES
    pose = pose_for("write")
    assert pose["rhx"] > pose["rx"]  # hand extended toward board


def test_foundation_demo_draws_board():
    img = Image.new("RGB", (1080, 1920), (128, 128, 128))
    drawer = get_foundation_demo("foundation_f_equals_ma")
    assert drawer is not None
    drawer(img, t=5.0, duration=20.0)
    # Board area should be near-white after draw
    px = img.getpixel((900, 300))
    assert px[0] > 240 and px[1] > 240 and px[2] > 240


def test_f_equals_ma_equation_syncs_to_write_beat():
    plan = PLANS["foundation_f_equals_ma"]
    win = write_window_from_plan(plan, label="write_equation")
    assert win["start"] == 0.22
    assert win["end"] == 0.42
    eq = next(a for a in F_EQUALS_MA_ACTIONS if a.kind == "equation")
    assert eq.start >= win["start"] - 0.01
    assert eq.end <= win["end"] + 0.01
    # Mid-write: equation partially visible
    assert eq.start < 0.30 < eq.end


def test_align_equation_helper():
    from services.animation.whiteboard import BoardAction

    actions = [
        BoardAction("equation", "F = m × a", start=0.10, end=0.20, row=2),
        BoardAction("underline", "F = m × a", start=0.20, end=0.25, row=2),
    ]
    synced = align_equation_to_write_beat(actions, 0.22, 0.42)
    assert synced[0].start == 0.22
    assert synced[0].end < synced[1].end
    assert synced[1].end == 0.42
