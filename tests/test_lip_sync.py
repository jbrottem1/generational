"""Lip-sync foundation tests."""

from __future__ import annotations

import numpy as np

from services.animation.lip_sync import AmplitudeMouthDriver, PhonemeMouthDriver
from services.animation.stick_figure import draw_stick_figure


def test_mouth_driver_interface_amplitude():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # tone then silence
    sig = np.concatenate(
        [
            0.3 * np.sin(2 * np.pi * 220 * t[: sr // 2]),
            np.zeros(sr // 2),
        ]
    )
    driver = AmplitudeMouthDriver(sig, sr, silence_threshold=0.02)
    assert driver.openness_at(0.1) > 0.1
    assert driver.openness_at(0.8) == 0.0


def test_phoneme_driver_same_api():
    d = PhonemeMouthDriver([{"t": 0.0, "openness": 0.0}, {"t": 0.2, "openness": 0.8}])
    assert d.openness_at(0.2) >= 0.5


def test_stick_figure_mouth_states():
    closed = draw_stick_figure(size=256, mouth_open=0.0)
    opened = draw_stick_figure(size=256, mouth_open=0.9)
    assert closed.size == (256, 256)
    assert opened.size == (256, 256)
    # Open mouth should change pixels vs closed
    assert list(closed.getdata()) != list(opened.getdata())
