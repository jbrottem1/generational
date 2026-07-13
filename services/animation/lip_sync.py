"""Lip-sync mouth drivers — amplitude now, phoneme-ready later.

Architecture rule: performers consume ``MouthDriver.openness_at(t)`` only.
Swap AmplitudeMouthDriver → PhonemeMouthDriver without changing the performer.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from services.media_production.ffmpeg_assembler import find_ffmpeg


class MouthDriver(ABC):
    """Abstract mouth aperture driver. openness in [0, 1]."""

    @abstractmethod
    def openness_at(self, t_sec: float) -> float:
        raise NotImplementedError

    def timeline(self, duration_sec: float, fps: float = 24.0) -> list[dict[str, Any]]:
        n = max(1, int(duration_sec * fps))
        rows = []
        for i in range(n):
            t = i / fps
            rows.append({"t": round(t, 4), "openness": round(self.openness_at(t), 4)})
        return rows


class AmplitudeMouthDriver(MouthDriver):
    """Open/closed mouth from audio energy. Closed in silence.

    Educator / foundation presets tighten follow (lower silence floor, less
    envelope smoothing). Reversible via ``profile=\"default\"`` or explicit kwargs.
    """

    PROFILES: dict[str, dict[str, float]] = {
        "default": {
            "silence_threshold": 0.018,
            "attack": 0.03,
            "release": 0.07,
            "smooth": 0.28,
            "curve": 0.65,
            "floor": 0.12,
        },
        # Snappier syllable edges for white-studio professor narration
        "educator": {
            "silence_threshold": 0.014,
            "attack": 0.02,
            "release": 0.055,
            "smooth": 0.18,
            "curve": 0.58,
            "floor": 0.10,
        },
        "foundation": {
            "silence_threshold": 0.012,
            "attack": 0.018,
            "release": 0.05,
            "smooth": 0.15,
            "curve": 0.55,
            "floor": 0.10,
        },
    }

    def __init__(
        self,
        samples: np.ndarray,
        sample_rate: int,
        *,
        silence_threshold: float | None = None,
        attack: float | None = None,
        release: float | None = None,
        smooth: float | None = None,
        profile: str = "default",
        curve: float | None = None,
        floor: float | None = None,
    ) -> None:
        preset = dict(self.PROFILES.get(profile) or self.PROFILES["default"])
        self.samples = samples.astype(np.float64)
        self.sr = int(sample_rate)
        self.silence_threshold = float(
            silence_threshold if silence_threshold is not None else preset["silence_threshold"]
        )
        self.attack = float(attack if attack is not None else preset["attack"])
        self.release = float(release if release is not None else preset["release"])
        self.smooth = float(smooth if smooth is not None else preset["smooth"])
        self.curve = float(curve if curve is not None else preset["curve"])
        self.floor = float(floor if floor is not None else preset["floor"])
        self.profile = profile
        self._env = self._build_envelope()

    @classmethod
    def from_audio_file(cls, path: str | Path, **kwargs: Any) -> "AmplitudeMouthDriver":
        samples, sr = load_mono_wav(path)
        return cls(samples, sr, **kwargs)

    def _build_envelope(self) -> np.ndarray:
        # Frame at ~100 Hz for smooth mouth
        hop = max(1, self.sr // 100)
        win = max(hop * 2, self.sr // 50)
        if len(self.samples) < win:
            return np.zeros(1)
        energies = []
        for i in range(0, len(self.samples) - win, hop):
            chunk = self.samples[i : i + win]
            energies.append(float(np.sqrt(np.mean(chunk * chunk) + 1e-12)))
        env = np.array(energies, dtype=np.float64)
        if env.max() > 0:
            env = env / env.max()
        # Smooth
        k = max(1, int(self.smooth * 10))
        kernel = np.ones(k) / k
        env = np.convolve(env, kernel, mode="same")
        return env

    def openness_at(self, t_sec: float) -> float:
        if len(self._env) == 0:
            return 0.0
        idx = int(t_sec * 100)
        idx = max(0, min(len(self._env) - 1, idx))
        e = float(self._env[idx])
        if e < self.silence_threshold:
            return 0.0
        # Map energy to mouth aperture with profile curve
        open_amt = (e - self.silence_threshold) / max(1e-6, 1.0 - self.silence_threshold)
        open_amt = max(0.0, min(1.0, open_amt))
        # Prefer mid openings for natural speech rhythm
        return float(self.floor + (1.0 - self.floor) * (open_amt ** self.curve))


class PhonemeMouthDriver(MouthDriver):
    """Future phoneme/viseme driver — same interface, not yet wired to a phoneme backend."""

    def __init__(self, cues: list[dict[str, Any]] | None = None) -> None:
        # cues: [{t, phoneme, openness}] — reserved for upgrade
        self.cues = list(cues or [])

    def openness_at(self, t_sec: float) -> float:
        if not self.cues:
            return 0.0
        # Nearest cue
        best = min(self.cues, key=lambda c: abs(float(c.get("t") or 0) - t_sec))
        return float(best.get("openness") or 0.0)


def load_mono_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Load audio as mono float64 via ffmpeg → wav."""
    path = Path(path)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg required for lip-sync amplitude analysis")
    with tempfile.TemporaryDirectory(prefix="lipsync_") as tmp:
        wav = Path(tmp) / "a.wav"
        cmd = [
            ffmpeg, "-y", "-i", str(path),
            "-ac", "1", "-ar", "16000",
            str(wav),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        if proc.returncode != 0 or not wav.exists():
            raise RuntimeError((proc.stderr or "wav convert failed")[-400:])
        import wave

        with wave.open(str(wav), "rb") as w:
            sr = w.getframerate()
            n = w.getnframes()
            raw = w.readframes(n)
            width = w.getsampwidth()
        if width == 2:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
        elif width == 1:
            samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128.0
        else:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
        return samples, sr


def build_mouth_timeline(
    audio_path: str | Path,
    *,
    duration_sec: float | None = None,
    fps: float = 24.0,
    driver: MouthDriver | None = None,
    profile: str = "default",
) -> dict[str, Any]:
    """Build a mouth timeline package (amplitude now; phoneme-swappable)."""
    driver = driver or AmplitudeMouthDriver.from_audio_file(audio_path, profile=profile)
    if duration_sec is None:
        samples, sr = load_mono_wav(audio_path)
        duration_sec = len(samples) / float(sr)
    rows = driver.timeline(float(duration_sec), fps=fps)
    speaking = sum(1 for r in rows if r["openness"] > 0.12)
    return {
        "driver": type(driver).__name__,
        "upgrade_path": "Replace AmplitudeMouthDriver with PhonemeMouthDriver — same openness_at() API",
        "fps": fps,
        "duration_sec": duration_sec,
        "frames": rows,
        "speaking_frame_ratio": round(speaking / max(1, len(rows)), 3),
        "closed_in_silence": True,
    }


def save_timeline(timeline: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return path
