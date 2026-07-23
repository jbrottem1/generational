"""Tests for Foundation Visual System V2."""

from __future__ import annotations

from PIL import Image

from services.animation.foundation_v2 import (
    clamp_keyword,
    draw_foundation_v2_studio,
    is_foundation_v2_demo,
    keyword_word_count,
    render_keyword_board,
)
from services.animation.whiteboard import BoardAction


def test_is_foundation_v2_demo():
    assert is_foundation_v2_demo("foundation_v2_turtle_202")
    assert not is_foundation_v2_demo("foundation_batesian_101")


def test_keyword_clamp_max_eight_words():
    text = "one two three four five six seven eight nine ten"
    assert keyword_word_count(clamp_keyword(text)) <= 8


def test_v2_studio_draws_baby_blue():
    canvas = Image.new("RGB", (1080, 1920), (0, 0, 0))
    floor_y = draw_foundation_v2_studio(canvas)
    assert 1500 < floor_y < 1600
    px = canvas.getpixel((100, 100))
    assert px[2] > px[0]  # blue tint


def test_keyword_board_renders():
    canvas = Image.new("RGB", (1080, 1920), (200, 220, 240))
    actions = [BoardAction("write", "Gradual shell", start=0.0, end=1.0, row=0, size=48)]
    render_keyword_board(canvas, actions, 0.5)
    assert canvas.getpixel((400, 200)) != (200, 220, 240)
