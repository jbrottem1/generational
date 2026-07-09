"""Hook visualizer — the strongest first-3-second visual sequence.

The scroll-stop battle is won or lost in five frames. This module plans a
frame-by-frame opening sequence (0.0s → 3.0s) engineered around the three
strongest interrupt patterns — abrupt motion, incomplete information, and
direct address — and explains in plain English why the sequence should stop
a scrolling thumb.
"""

from __future__ import annotations

HOOK_FRAME_COUNT = 5
HOOK_WINDOW_SEC = 3.0

# Frame-level grammar for the opening sequence. Data, not code.
HOOK_FRAME_GRAMMAR = [
    {
        "role": "interrupt",
        "visual": "Frame opens mid-action — {subject} already moving, no fade-in, no title card",
        "camera": "crash zoom settling from 120% to 100%",
        "technique": "abrupt-motion pattern interrupt",
    },
    {
        "role": "anchor",
        "visual": "Hard cut to an extreme close-up of the most unusual detail of {subject}",
        "camera": "locked-off macro, shallow depth of field",
        "technique": "novel detail anchor",
    },
    {
        "role": "gap",
        "visual": "Partial reveal — {subject} half-obscured while the hook line lands",
        "camera": "slow push-in past a foreground occlusion",
        "technique": "curiosity gap (incomplete information)",
    },
    {
        "role": "address",
        "visual": "Direct-to-viewer framing with the hook's key words stamped on screen",
        "camera": "snap to centered eye-level medium close-up",
        "technique": "direct address + synced text overlay",
    },
    {
        "role": "promise",
        "visual": "Tease of the payoff — a 0.4s glimpse of the final reveal, cut before it completes",
        "camera": "whip pan into the first story beat",
        "technique": "open loop into the body of the video",
    },
]


def build_hook_sequence(idea: dict, *, subject: str = "") -> dict:
    """Plan the five-frame opening sequence plus its scroll-stop rationale."""
    subject = subject or idea.get("title") or "the subject"
    hook_line = idea.get("hook", "")
    hook_words = hook_line.split()
    overlay = " ".join(hook_words[:4]).upper() if hook_words else "WAIT FOR THIS"

    frame_length = round(HOOK_WINDOW_SEC / HOOK_FRAME_COUNT, 2)
    frames = []
    for index, grammar in enumerate(HOOK_FRAME_GRAMMAR, start=1):
        start = round((index - 1) * frame_length, 2)
        frames.append(
            {
                "frame": index,
                "time_sec": start,
                "length_sec": frame_length,
                "role": grammar["role"],
                "visual": grammar["visual"].format(subject=subject),
                "camera": grammar["camera"],
                "text_overlay": overlay if grammar["role"] in ("address", "gap") else "",
                "technique": grammar["technique"],
            }
        )

    rationale = (
        f"The sequence opens mid-action with zero dead frames, because the feed decides within "
        f"one swipe-length whether \"{subject}\" earns a pause. Frame 1 uses abrupt motion — the "
        "strongest involuntary attention trigger. Frame 2 anchors on an unusual concrete detail the "
        "brain can't immediately classify. Frame 3 opens a curiosity gap by showing the subject only "
        "partially while the hook line lands. Frame 4 switches to direct address with synced text, "
        "converting passive watching into a personal exchange. Frame 5 flashes the payoff and cuts "
        "away before it completes, opening a loop only watching the full video can close."
    )

    return {
        "window_sec": HOOK_WINDOW_SEC,
        "frame_count": HOOK_FRAME_COUNT,
        "frames": frames,
        "scroll_stop_rationale": rationale,
    }
