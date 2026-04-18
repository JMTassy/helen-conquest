"""
Tests for HELEN render director layer.

D1: same artifact + style → same plan (deterministic)
D2: authority=False always — cannot be set True
D3: plan bound to source receipt hash
D4: plan_hash = sha256(canonical plan body)
D5: tone → style mapping is deterministic
D6: all 4 styles produce valid plans with shots and sound
D7: pipeline returns plan as third element
D8: different artifacts → different plans
"""
import pytest

from helen_os.render.models import ExecutionArtifactV1
from helen_os.render.director import DirectorPlanV1, direct, _tone_to_style
from helen_os.render.contracts import canonical_json, sha256_hex
from helen_os.render.video import VideoRenderProfileV1, compile_video_spec, PROFILE_MEDITATION
from helen_os.render.pipeline import run_video_render

RECEIPT_HASH = "sha256:" + "a" * 64
PREV_HASH    = "sha256:" + "0" * 64


def _artifact(**kw) -> ExecutionArtifactV1:
    defaults = dict(
        artifact_id="art_001", run_id="run_001",
        receipt_hash=RECEIPT_HASH,
        content="We closed the seam.",
        tone="calm", persona="helen",
    )
    defaults.update(kw)
    return ExecutionArtifactV1(**defaults)


# ── D1: determinism ────────────────────────────────────────────────────────────

def test_director_plan_is_deterministic():
    a = _artifact()
    p1 = direct(a, "meditation")
    p2 = direct(a, "meditation")
    assert p1.plan_hash == p2.plan_hash, "D1: same inputs must produce same plan"
    assert p1.plan_id   == p2.plan_id


def test_spec_with_plan_is_deterministic():
    a    = _artifact()
    plan = direct(a, "meditation")
    s1   = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    s2   = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    assert canonical_json(s1) == canonical_json(s2), "D1: spec must be byte-stable"


# ── D2: authority ─────────────────────────────────────────────────────────────

def test_director_plan_authority_is_false():
    plan = direct(_artifact(), "meditation")
    assert plan.authority is False, "D2: authority must be False"


def test_director_plan_authority_cannot_be_true():
    with pytest.raises((ValueError, TypeError)):
        DirectorPlanV1(
            plan_id="x", source_artifact_id="a", source_receipt_hash=RECEIPT_HASH,
            style="meditation", tempo="slow_build",
            emotion_curve=["calm"], shots=[], sound=None, voice=None,
            plan_hash="sha256:" + "b" * 64,
            authority=True,
        )


# ── D3: receipt binding ────────────────────────────────────────────────────────

def test_plan_bound_to_source_receipt_hash():
    a    = _artifact()
    plan = direct(a, "meditation")
    assert plan.source_receipt_hash == a.receipt_hash, "D3: plan must carry source receipt hash"
    assert plan.source_artifact_id  == a.artifact_id


def test_plan_hash_in_spec():
    a    = _artifact()
    plan = direct(a, "meditation")
    spec = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    assert spec["plan_hash"] == plan.plan_hash
    assert spec["source_receipt_hash"] == a.receipt_hash


# ── D4: plan_hash integrity ────────────────────────────────────────────────────

def test_plan_hash_is_sha256_prefixed():
    plan = direct(_artifact(), "oracle")
    assert plan.plan_hash.startswith("sha256:"), "D4: plan_hash must be sha256: prefixed"


# ── D5: tone → style mapping ───────────────────────────────────────────────────

@pytest.mark.parametrize("tone,expected", [
    ("calm",       "meditation"),
    ("reflective", "witness"),
    ("precise",    "oracle"),
    ("serious",    "declaration"),
    ("warm",       "meditation"),
])
def test_tone_to_style_mapping(tone, expected):
    assert _tone_to_style(tone) == expected, f"D5: tone {tone} must map to {expected}"


def test_unknown_tone_defaults_to_meditation():
    assert _tone_to_style("unknown_tone") == "meditation"


# ── D6: all styles produce valid plans ────────────────────────────────────────

@pytest.mark.parametrize("style", ["meditation", "oracle", "witness", "declaration"])
def test_all_styles_produce_valid_plans(style):
    plan = direct(_artifact(), style)
    assert plan.style == style
    assert len(plan.shots) > 0,         f"{style}: must have at least one shot"
    assert len(plan.emotion_curve) > 0, f"{style}: must have emotion curve"
    assert plan.sound is not None,      f"{style}: must have sound design"
    assert plan.voice is not None,      f"{style}: must have voice directive"
    assert plan.total_duration() > 0,   f"{style}: total duration must be > 0"


@pytest.mark.parametrize("style", ["meditation", "oracle", "witness", "declaration"])
def test_all_styles_have_voice_state(style):
    plan = direct(_artifact(), style)
    assert plan.voice.state, f"{style}: voice.state must be non-empty"
    assert plan.voice.delivery_notes is not None


# ── D7: pipeline returns plan ─────────────────────────────────────────────────

def test_pipeline_returns_director_plan():
    media, receipt, plan = run_video_render(
        _artifact(), PROFILE_MEDITATION,
        previous_hash=PREV_HASH, renderer_name="stub",
    )
    assert isinstance(plan, DirectorPlanV1)
    assert plan.authority is False
    assert receipt.source_receipt_hash == RECEIPT_HASH


def test_pipeline_with_explicit_plan():
    a    = _artifact()
    plan = direct(a, "oracle")
    media, receipt, returned_plan = run_video_render(
        a, PROFILE_MEDITATION,
        previous_hash=PREV_HASH, renderer_name="stub",
        plan=plan,
    )
    assert returned_plan.style == "oracle"


# ── D8: different artifacts → different plans ──────────────────────────────────

def test_different_artifacts_produce_different_plans():
    a1 = _artifact(artifact_id="art_001", content="first")
    a2 = _artifact(artifact_id="art_002", content="second")
    p1 = direct(a1, "meditation")
    p2 = direct(a2, "meditation")
    assert p1.plan_hash != p2.plan_hash
    assert p1.plan_id   != p2.plan_id


def test_different_styles_produce_different_plans():
    a  = _artifact()
    p1 = direct(a, "meditation")
    p2 = direct(a, "oracle")
    assert p1.plan_hash    != p2.plan_hash
    assert p1.style        != p2.style
    assert p1.emotion_curve != p2.emotion_curve
