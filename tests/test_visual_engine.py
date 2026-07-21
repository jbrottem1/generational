"""Educational visual engine — layout, annotations, tray exclusivity, QC."""

from __future__ import annotations

from PIL import Image

from services.animation.annotation_engine import SemanticAnnotation, draw_semantic_annotations, resolve_target
from services.animation.foundation_v2 import board_rect_v2, compose_v2_teaching_frame
from services.animation.layout_engine import (
    claim_evidence_tray,
    layout_keyword_board,
    visibility_envelope,
)
from services.animation.turtle_demos import (
    TURTLE_202_KEYWORDS,
    TURTLE_202_POINTERS,
    TURTLE_SHELL_WINDOW,
    TURTLE_TIMELINE_WINDOW,
    draw_turtle_202,
)
from services.animation.whiteboard import BoardAction
from services.quality.visual_layout_qc import evaluate_demo_visual_qc
from services.reality.planner import TURTLE_202_PANELS


def test_visibility_envelope_fades_out():
    assert visibility_envelope(0.10, 0.20, 0.40) == 0.0
    assert visibility_envelope(0.30, 0.20, 0.40) == 1.0
    assert 0.0 < visibility_envelope(0.42, 0.20, 0.40, fade_out=0.05) < 1.0
    assert visibility_envelope(0.50, 0.20, 0.40, fade_out=0.05) == 0.0


def test_keyword_layout_clears_expired_rows():
    actions = [
        BoardAction("write", "Origin of Turtles", start=0.06, end=0.18, row=0, size=56),
        BoardAction("write", "Gradual shell", start=0.40, end=0.54, row=0, size=52),
    ]
    board = board_rect_v2(1080, 1920)
    early = layout_keyword_board(actions, board, 0.12)
    late = layout_keyword_board(actions, board, 0.45)
    assert early.occupied_rows.get(0) == "Origin of Turtles"
    assert late.occupied_rows.get(0) == "Gradual shell"
    assert "Origin of Turtles" not in late.occupied_rows.values()


def test_keyword_layout_no_overlap_same_row_reuse():
    actions = [
        BoardAction("write", "Origin of Turtles", start=0.06, end=0.50, row=0, size=56),
        BoardAction("write", "Gradual shell", start=0.40, end=0.54, row=0, size=52),
    ]
    board = board_rect_v2(1080, 1920)
    layout = layout_keyword_board(actions, board, 0.45)
    writes = [b for b in layout.boxes if b.kind == "write"]
    assert len(writes) == 1
    assert writes[0].meta.get("full_text") == "Gradual shell"


def test_tray_claim_is_exclusive():
    panels = [(0.10, 0.26), (0.54, 0.76)]
    # During panel window, panel wins even if shell window overlaps historically
    claim = claim_evidence_tray(
        0.20,
        panel_windows=panels,
        timeline_window=TURTLE_TIMELINE_WINDOW,
        shell_window=TURTLE_SHELL_WINDOW,
    )
    assert claim.mode == "panel"
    claim2 = claim_evidence_tray(
        0.30,
        panel_windows=panels,
        timeline_window=TURTLE_TIMELINE_WINDOW,
        shell_window=TURTLE_SHELL_WINDOW,
    )
    assert claim2.mode == "timeline"
    claim3 = claim_evidence_tray(
        0.42,
        panel_windows=panels,
        timeline_window=TURTLE_TIMELINE_WINDOW,
        shell_window=TURTLE_SHELL_WINDOW,
    )
    assert claim3.mode == "shell"


def test_semantic_annotation_requires_visible_target():
    canvas = Image.new("RGB", (1080, 1920), (220, 230, 240))
    board = board_rect_v2(1080, 1920)
    layout = layout_keyword_board(TURTLE_202_KEYWORDS, board, 0.45)
    records = draw_semantic_annotations(
        canvas,
        [
            SemanticAnnotation(
                kind="circle",
                start=0.46,
                end=0.54,
                target="keyword:Gradual shell",
                narration_cue="shell",
            )
        ],
        0.48,
        board_layout=layout,
        board_rect=board,
        allow_fallback_coords=False,
    )
    assert records and records[0]["drawn"] is True
    assert records[0]["resolved_kind"] == "keyword"


def test_semantic_annotation_skips_invisible_target():
    canvas = Image.new("RGB", (1080, 1920), (220, 230, 240))
    board = board_rect_v2(1080, 1920)
    layout = layout_keyword_board(TURTLE_202_KEYWORDS, board, 0.12)
    records = draw_semantic_annotations(
        canvas,
        [
            SemanticAnnotation(
                kind="point",
                start=0.10,
                end=0.16,
                target="keyword:Gradual shell",
                narration_cue="not yet visible",
            )
        ],
        0.12,
        board_layout=layout,
        board_rect=board,
        allow_fallback_coords=False,
    )
    assert records and records[0]["drawn"] is False


def test_turtle_compositor_draws_without_crash():
    canvas = Image.new("RGB", (1080, 1920), (0, 0, 0))
    draw_turtle_202(canvas, t=10.0, duration=25.0)
    # Content zone should not be pure black after draw
    assert canvas.getpixel((700, 200)) != (0, 0, 0)


def test_turtle_visual_qc_passes_readability_gate():
    result = evaluate_demo_visual_qc("foundation_v2_turtle_202")
    assert result.readability >= 95.0, result.to_dict()
    assert result.passed, result.to_dict()
    assert not any(r.startswith("overlapping_text") for r in result.hard_fails)
    assert not any(r.startswith("annotations_missing_semantic_targets") for r in result.hard_fails)


def test_resolve_keyword_target():
    board = board_rect_v2(1080, 1920)
    layout = layout_keyword_board(TURTLE_202_KEYWORDS, board, 0.48)
    target = resolve_target(
        "keyword:Gradual shell",
        canvas_size=(1080, 1920),
        board_layout=layout,
        board_rect=board,
    )
    assert target is not None
    assert target.kind == "keyword"
    assert target.rect[2] > target.rect[0]


def test_turtle_panels_do_not_overlap_timeline_shell():
    """Exclusive schedule: panel windows must not intersect timeline/shell."""
    for panel in TURTLE_202_PANELS:
        # No overlap with timeline
        assert panel.end <= TURTLE_TIMELINE_WINDOW[0] or panel.start >= TURTLE_TIMELINE_WINDOW[1] or (
            panel.end <= TURTLE_SHELL_WINDOW[0] and panel.start >= TURTLE_TIMELINE_WINDOW[1]
        ) or panel.start >= TURTLE_SHELL_WINDOW[1] or panel.end <= TURTLE_TIMELINE_WINDOW[0]
        # Stronger: no intersection with either exclusive window
        def intersects(a0, a1, b0, b1):
            return a0 < b1 and b0 < a1

        assert not intersects(panel.start, panel.end, *TURTLE_TIMELINE_WINDOW)
        assert not intersects(panel.start, panel.end, *TURTLE_SHELL_WINDOW)


def test_annotation_requires_teaching_purpose():
    canvas = Image.new("RGB", (1080, 1920), (220, 230, 240))
    board = board_rect_v2(1080, 1920)
    layout = layout_keyword_board(TURTLE_202_KEYWORDS, board, 0.45)
    records = draw_semantic_annotations(
        canvas,
        [
            SemanticAnnotation(
                kind="circle",
                start=0.46,
                end=0.54,
                target="keyword:Gradual shell",
                narration_cue="",  # missing purpose
            )
        ],
        0.48,
        board_layout=layout,
        board_rect=board,
        require_teaching_purpose=True,
    )
    assert records and records[0]["drawn"] is False
    assert records[0]["reason"] == "missing_teaching_purpose"


def test_visual_priority_photos_beat_ai():
    from services.quality.visual_priority import prefer_authentic, priority_rank, select_visual_source

    assert priority_rank("photograph") < priority_rank("ai_image")
    ranked = prefer_authentic(
        [
            {"asset_id": "ai1", "visual_type": "ai_image", "relevance": 0.99},
            {"asset_id": "photo1", "visual_type": "photograph", "relevance": 0.50},
        ]
    )
    assert ranked[0]["asset_id"] == "photo1"
    pick = select_visual_source(
        authentic_hits=[{"asset_id": "p", "visual_type": "photograph"}],
        ai_hits=[{"asset_id": "a", "visual_type": "ai_image"}],
    )
    assert pick["tier"] == 1
    assert pick["ai_fallback"] is False


def test_authentic_media_policy_hard_fails_unused_photos():
    from services.quality.visual_education_qc import validate_authentic_media_policy

    hard, _ = validate_authentic_media_policy(
        image_ids=[],
        available_photo_count=3,
        ai_used=True,
    )
    assert any("real_photos_available_but_unused" in h for h in hard)
    assert any("ai_imagery_used_when_real_photos_available" in h for h in hard)


def test_seasons_visual_qc_requires_reality_photos():
    from services.reality.catalog import load_catalog
    from services.reality.qc import collect_demo_image_ids

    load_catalog.cache_clear()
    ids = collect_demo_image_ids("foundation_v2_seasons_001")
    assert "earth_apollo17" in ids
    assert "season_spring" in ids
    result = evaluate_demo_visual_qc("foundation_v2_seasons_001")
    assert result.passed, result.to_dict()
    assert not any("annotations_missing_teaching_purpose" in r for r in result.hard_fails)
    assert not any("no_reality_images" in r for r in result.hard_fails)


def test_seasons_compositor_draws_real_photos():
    from services.animation.seasons_demos import draw_seasons_001

    canvas = Image.new("RGB", (1080, 1920), (0, 0, 0))
    draw_seasons_001(canvas, t=18.0, duration=50.0)  # spring/summer window
    # Tray region should not remain pure black
    assert canvas.getpixel((700, 1200)) != (0, 0, 0)
