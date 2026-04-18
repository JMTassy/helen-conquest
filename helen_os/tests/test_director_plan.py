"""
Tests for HELEN render director layer.

D1: same artifact + template → same governed plan (deterministic)
D2: authority=False always — cannot be set True
D3: plan bound to source receipt hash
D4: plan_hash is sha256: prefixed
D5: tone → template mapping is deterministic
D6: all 10 templates produce valid plans
D7: pipeline returns plan as third element
D8: different artifacts → different plans
"""
import pytest

from helen_os.render.models import ExecutionArtifactV1
from helen_os.render.director import (
    DirectorPlanV1, direct, direct_governed, govern, from_template,
    _tone_to_style, TEMPLATES,
)
from helen_os.render.contracts import canonical_json, sha256_hex
from helen_os.render.video import VideoRenderProfileV1, compile_video_spec, PROFILE_MEDITATION
from helen_os.render.pipeline import run_video_render

RECEIPT_HASH = "sha256:" + "a" * 64
PREV_HASH    = "sha256:" + "0" * 64


def _artifact(**kw) -> ExecutionArtifactV1:
    defaults = dict(
        artifact_id="art_001", run_id="run_001",
        receipt_hash=RECEIPT_HASH,
        content="We closed the seam. No receipt, no claim.",
        tone="calm", persona="helen",
    )
    defaults.update(kw)
    return ExecutionArtifactV1(**defaults)


# ── D1: determinism ────────────────────────────────────────────────────────────

def test_director_plan_is_deterministic():
    a  = _artifact()
    p1 = direct_governed(a, "meditation")
    p2 = direct_governed(a, "meditation")
    assert p1.plan_hash == p2.plan_hash, "D1: same inputs must produce same plan"
    assert p1.plan_id   == p2.plan_id


def test_spec_with_plan_is_deterministic():
    a    = _artifact()
    plan = direct_governed(a, "meditation")
    s1   = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    s2   = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    assert canonical_json(s1) == canonical_json(s2), "D1: spec must be byte-stable"


# ── D2: authority ─────────────────────────────────────────────────────────────

def test_director_plan_authority_is_false():
    plan = direct_governed(_artifact(), "meditation")
    assert plan.authority is False, "D2: authority must be False"


def test_director_plan_authority_cannot_be_true():
    a   = _artifact()
    raw = direct(a.artifact_id, a.content)
    with pytest.raises((ValueError, TypeError)):
        DirectorPlanV1(
            plan=raw,
            source_artifact_id=a.artifact_id,
            source_receipt_hash=a.receipt_hash,
            plan_hash="sha256:" + "b" * 64,
            authority=True,
        )


# ── D3: receipt binding ────────────────────────────────────────────────────────

def test_plan_bound_to_source_receipt_hash():
    a    = _artifact()
    plan = direct_governed(a, "meditation")
    assert plan.source_receipt_hash == a.receipt_hash, "D3: plan must carry source receipt hash"
    assert plan.source_artifact_id  == a.artifact_id


def test_plan_hash_in_spec():
    a    = _artifact()
    plan = direct_governed(a, "meditation")
    spec = compile_video_spec(a, PROFILE_MEDITATION, plan=plan)
    assert spec["plan_hash"]           == plan.plan_hash
    assert spec["source_receipt_hash"] == a.receipt_hash


# ── D4: plan_hash integrity ────────────────────────────────────────────────────

def test_plan_hash_is_sha256_prefixed():
    plan = direct_governed(_artifact(), "witness")
    assert plan.plan_hash.startswith("sha256:"), "D4: plan_hash must be sha256: prefixed"


# ── D5: tone → template mapping ───────────────────────────────────────────────

@pytest.mark.parametrize("tone,expected", [
    ("calm",       "meditation"),
    ("reflective", "witness"),
    ("precise",    "clarity"),
    ("serious",    "manifesto"),
    ("warm",       "meditation"),
])
def test_tone_to_style_mapping(tone, expected):
    assert _tone_to_style(tone) == expected, f"D5: tone {tone} must map to {expected}"


def test_unknown_tone_defaults_to_meditation():
    assert _tone_to_style("unknown_tone") == "meditation"


# ── D6: all templates produce valid plans ─────────────────────────────────────

@pytest.mark.parametrize("template", list(TEMPLATES.keys()))
def test_all_templates_produce_valid_governed_plans(template):
    a    = _artifact()
    plan = direct_governed(a, template)
    assert len(plan.shots) > 0,           f"{template}: must have at least one shot"
    assert len(plan.emotion_curve) > 0,   f"{template}: must have emotion curve"
    assert plan.total_duration() > 0,     f"{template}: total duration must be > 0"
    assert plan.authority is False
    assert plan.plan_hash.startswith("sha256:")


@pytest.mark.parametrize("template", list(TEMPLATES.keys()))
def test_all_templates_voice_profile_set(template):
    plan = direct_governed(_artifact(), template)
    assert plan.voice_profile, f"{template}: voice_profile must be non-empty"


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
    plan = direct_governed(a, "witness")
    media, receipt, returned_plan = run_video_render(
        a, PROFILE_MEDITATION,
        previous_hash=PREV_HASH, renderer_name="stub",
        plan=plan,
    )
    assert returned_plan.plan_id == plan.plan_id


# ── D8: different artifacts → different plans ──────────────────────────────────

def test_different_artifacts_produce_different_plans():
    a1 = _artifact(artifact_id="art_001", content="first text here")
    a2 = _artifact(artifact_id="art_002", content="second text here")
    p1 = direct_governed(a1, "meditation")
    p2 = direct_governed(a2, "meditation")
    assert p1.plan_hash != p2.plan_hash
    assert p1.plan_id   != p2.plan_id


def test_different_templates_produce_different_plans():
    a  = _artifact()
    p1 = direct_governed(a, "meditation")
    p2 = direct_governed(a, "manifesto")
    assert p1.plan_hash != p2.plan_hash
    assert p1.voice_profile != p2.voice_profile
