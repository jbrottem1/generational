"""Tests for true-motion compositor helpers and slideshow rejection."""

from __future__ import annotations

from services.media_production.true_motion import is_ken_burns_only


def test_is_ken_burns_only_detects_slideshow():
    assert is_ken_burns_only(["ken_burns", "ken_burns", "slow_zoom_in"]) is True
    assert is_ken_burns_only([]) is True


def test_is_ken_burns_only_allows_real_motion_verbs():
    assert is_ken_burns_only(["cinematic_push_in", "pan_right", "handheld_drift"]) is False
    assert is_ken_burns_only(["true_layered_animation"]) is False
