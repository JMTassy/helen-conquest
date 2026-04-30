"""Tests for complexity_extractor — clutter + overcomplexity metrics."""
import pytest
from helen_video.complexity_extractor import extract, check, MAX_SAFE_OVERLAYS, MAX_SAFE_DEPTH


# ── fixtures ──────────────────────────────────────────────────────────────────

SIMPLE_SCALE = "[0:v]scale=720:1280[out]"

SINGLE_OVERLAY = """
[0:v]scale=720:405[vid];
[vid]pad=720:1280:0:437:color=#080810[padded];
[padded][1:v]overlay=0:0[vout]
"""

HUD_OVERLAY = """
[0:v]scale=720:405,fps=24,eq=brightness=0.02[vid];
[vid]pad=720:1280:0:437:color=#080810[padded];
[padded][1:v]overlay=0:0[vout]
"""

ABYME_BROKEN = """
[0:v][1:v]overlay=0:0[tmp];
[tmp][1:v]overlay=80:272[bg1];
[bg1][2:v]overlay=0:0[vout]
"""

ABYME_FIXED = """
[1:v]scale=560:315,fps=24,split=2[sc_a][sc_b];
[sc_b]gblur=sigma=7[sc_glow];
[0:v][sc_glow]overlay=80:272[bg1];
[bg1][sc_a]overlay=80:277[bg2];
[bg2][2:v]overlay=0:0[vout]
"""

DEEP_PIPELINE = """
[0:v]scale=720:405[s1];
[s1]eq=brightness=0.02[s2];
[s2]colorbalance=rs=0.06[s3];
[s3][1:v]overlay=0:0[s4];
[s4][2:v]overlay=0:100[s5];
[s5][3:v]overlay=0:200[vout]
"""


# ── clutter metric ────────────────────────────────────────────────────────────

def test_simple_scale_no_clutter():
    m = extract(SIMPLE_SCALE)
    assert m.overlay_count == 0
    assert m.clutter == 0.0


def test_single_overlay_low_clutter():
    m = extract(SINGLE_OVERLAY)
    assert m.overlay_count == 1
    assert m.clutter < 1.0 / MAX_SAFE_OVERLAYS + 0.01


def test_hud_overlay_safe():
    m = extract(HUD_OVERLAY)
    assert m.overlay_count == 1
    assert not m.flag


def test_abyme_fixed_at_boundary():
    m = extract(ABYME_FIXED)
    assert m.overlay_count == MAX_SAFE_OVERLAYS


def test_deep_pipeline_flags_overcomplexity():
    m = extract(DEEP_PIPELINE)
    assert m.overlay_count >= MAX_SAFE_OVERLAYS
    assert m.flag


# ── overcomplexity score ──────────────────────────────────────────────────────

def test_overcomplexity_zero_for_simple():
    m = extract(SIMPLE_SCALE)
    assert m.overcomplexity == 0.0


def test_overcomplexity_increases_with_overlays():
    m1 = extract(SINGLE_OVERLAY)
    m2 = extract(DEEP_PIPELINE)
    assert m2.overcomplexity > m1.overcomplexity


def test_overcomplexity_bounded():
    m = extract(DEEP_PIPELINE)
    assert 0.0 <= m.overcomplexity <= 1.0


# ── operator-veto flag ────────────────────────────────────────────────────────

def test_check_returns_true_for_safe_graph():
    assert check(HUD_OVERLAY) is True


def test_check_returns_false_for_deep_stacked():
    assert check(DEEP_PIPELINE) is False


def test_abyme_broken_flag():
    m = extract(ABYME_BROKEN)
    assert m.overlay_count == MAX_SAFE_OVERLAYS


# ── stream and depth counting ─────────────────────────────────────────────────

def test_stream_count_simple():
    m = extract(SIMPLE_SCALE)
    assert m.stream_count >= 1


def test_split_increments_stream_count():
    fc = "[0:v]scale=720:1280,split=2[a][b];[a]eq=brightness=0.1[a2];[b][a2]overlay=0:0[out]"
    m  = extract(fc)
    assert m.stream_count >= 4


def test_depth_single_node():
    m = extract(SIMPLE_SCALE)
    assert m.depth >= 1


def test_depth_chain():
    m1 = extract(SINGLE_OVERLAY)
    m2 = extract(DEEP_PIPELINE)
    assert m2.depth > m1.depth


# ── edge cases ────────────────────────────────────────────────────────────────

def test_empty_string():
    m = extract("")
    assert m.overlay_count == 0
    assert m.clutter == 0.0
    assert not m.flag


def test_whitespace_only():
    m = extract("   \n\t  ")
    assert m.overlay_count == 0


def test_metrics_frozen():
    m = extract(SIMPLE_SCALE)
    with pytest.raises((AttributeError, TypeError)):
        m.overlay_count = 99  # type: ignore[misc]
