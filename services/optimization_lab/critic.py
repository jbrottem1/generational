"""Module 3 — Self-Critic: detailed post-production critique."""

from __future__ import annotations


def critique_production(candidate: dict, winner: dict, leaderboard: list) -> dict:
    """Identify weak spots and suggest automatic improvements."""
    axes = (winner or {}).get("axes") or {}
    scores = (winner or {}).get("scores") or {}
    issues: list[dict] = []

    if int(scores.get("hook_quality") or 0) < 90:
        issues.append(
            {
                "kind": "weak_hook",
                "severity": "high",
                "message": "Hook quality below excellence bar",
                "suggestion": "Swap to higher-scoring open-loop or shock-statistic hook",
            }
        )
    if int(scores.get("retention") or 0) < 90:
        issues.append(
            {
                "kind": "slow_pacing",
                "severity": "high",
                "message": "Retention score suggests pacing fatigue risk",
                "suggestion": "Accelerate mid-body cuts; add pattern interrupt",
            }
        )
    if int(scores.get("narration") or 0) < 88:
        issues.append(
            {
                "kind": "weak_narration",
                "severity": "medium",
                "message": "Narration energy / clarity can improve",
                "suggestion": "Shift to authoritative_educator or high_energy_host",
            }
        )
    if int(scores.get("visual_quality") or 0) < 90:
        issues.append(
            {
                "kind": "repetitive_visuals",
                "severity": "medium",
                "message": "Visual quality below documentary bar",
                "suggestion": "Prefer science_documentary style + diversify camera moves",
            }
        )
    if int(scores.get("seo") or 0) < 90:
        issues.append(
            {
                "kind": "weak_seo",
                "severity": "medium",
                "message": "Title/tags under-optimized for CTR",
                "suggestion": "Use curiosity title + denser tag set",
            }
        )
    if axes.get("music") == "soft_pulse" and int(scores.get("entertainment") or 0) < 85:
        issues.append(
            {
                "kind": "low_energy",
                "severity": "low",
                "message": "Music mood may feel flat",
                "suggestion": "Try cinematic_rise or urgent_beat",
            }
        )
    if len(axes.get("camera_movement") or []) < 2:
        issues.append(
            {
                "kind": "poor_transitions",
                "severity": "medium",
                "message": "Camera vocabulary too narrow",
                "suggestion": "Use multi-stage compound moves",
            }
        )

    # Relative: if runner-up beats winner on a key dim, note missed opportunity
    if len(leaderboard) >= 2:
        top = leaderboard[0]
        second = leaderboard[1]
        if int(second.get("hook_quality") or 0) > int(top.get("hook_quality") or 0):
            issues.append(
                {
                    "kind": "missed_emotional_opportunity",
                    "severity": "medium",
                    "message": f"Version {second.get('label')} had a stronger hook",
                    "suggestion": "Borrow runner-up hook into winner revision",
                }
            )

    strengths = [
        k for k, v in scores.items() if k != "overall" and int(v or 0) >= 92
    ]
    return {
        "issue_count": len(issues),
        "issues": issues,
        "strengths": strengths,
        "summary": (
            f"{len(issues)} improvement opportunities; "
            f"strengths: {', '.join(strengths[:5]) or 'building'}"
        ),
        "auto_fixable": [i for i in issues if i["severity"] in ("high", "medium")],
    }
