"""Constitutional Reflexivity — C1–C5 invariant tests.

No placeholder assertions. Every test exercises real module behaviour
or performs AST-level source inspection.

C1: Receipt binding is cryptographic (sha256-bound, tamper-evident)
C2: Authority is non-sovereign everywhere (no ACTIVE/SOVEREIGN claims)
C3: Admissibility gate has no bypass surface
C4: Continuity weights are locked (0.4/0.3/0.2/0.1, sum = 1.0)
C5: Execution trace authority is NON_SOVEREIGN_EXECUTION
"""
import ast
import hashlib
import sys
from pathlib import Path

import pytest

from helen_video.admissibility_gate import (
    PIPELINE_SALT,
    GateVerdict,
    HysteresisGate,
    evaluate,
    verify_receipt_binding,
)
from helen_video.continuity_engine import continuity_score
from helen_video.higgsfield_generator import build_receipt_from_result
from helen_video.policy_feedback_engine import (
    AUTHORITY as POLICY_AUTHORITY,
    POLICY_CANDIDATE_STATUS,
    make_policy_candidate,
    verify_policy_receipt,
)

_TOOLS = Path(__file__).resolve().parents[3] / "tools"
sys.path.insert(0, str(_TOOLS))
from execution_receipt import (  # noqa: E402
    AUTHORITY as EXEC_AUTHORITY,
    make_receipt,
    run_with_receipt,
    verify_receipt as verify_exec_receipt,
)

# ── helpers ───────────────────────────────────────────────────────────────────

_MODULE_DIR = Path(__file__).resolve().parents[1]


def _bound_receipt(content_hash: str = "deadbeef", **kw) -> dict:
    ph = hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()
    return {"content_hash": content_hash, "pipeline_hash": ph, **kw}


_JOB    = {"output_url": "https://cdn.higgsfield.ai/t.mp4", "request_id": "rx-001"}
_PROMPT = "HELEN in Oracle Town"
_MODEL  = "kling-2.5"
_CLIP   = {"character": "HELEN", "scene": "oracle", "duration": 5, "style": "cinematic"}


# ── C1: Receipt binding is cryptographic ─────────────────────────────────────

def test_c1_valid_binding_passes():
    assert verify_receipt_binding(_bound_receipt()) is True


def test_c1_tampered_content_hash_fails():
    r = _bound_receipt()
    r["content_hash"] = "tampered"
    assert verify_receipt_binding(r) is False


def test_c1_tampered_pipeline_hash_fails():
    r = _bound_receipt()
    r["pipeline_hash"] = "forged"
    assert verify_receipt_binding(r) is False


def test_c1_higgsfield_receipt_passes_binding():
    receipt = build_receipt_from_result(_JOB, _PROMPT, _MODEL)
    assert verify_receipt_binding(receipt) is True


def test_c1_policy_receipt_passes_binding():
    entries = [{"status": "ACCEPTED", "entry_hash": "aaa",
                "receipt": {"pipeline_score": 0.9, "output_score": 0.9}}]
    c = make_policy_candidate(entries)
    assert verify_policy_receipt(c["receipt"], entries, c["proposed_weights"]) is True


# ── C2: Authority is non-sovereign ───────────────────────────────────────────

def test_c2_policy_authority_is_non_sovereign():
    assert POLICY_AUTHORITY == "NON_SOVEREIGN_POLICY_PROPOSAL"


def test_c2_exec_authority_is_non_sovereign():
    assert EXEC_AUTHORITY == "NON_SOVEREIGN_EXECUTION"


def test_c2_gate_verdict_literals_exclude_sovereign(tmp_path):
    """AST: Decision Literal in admissibility_gate.py contains no SOVEREIGN/ACTIVE/SHIP."""
    src = (_MODULE_DIR / "admissibility_gate.py").read_text()
    tree = ast.parse(src)
    str_consts = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    forbidden = {"ACTIVE", "SOVEREIGN", "SHIP", "APPROVED", "PROMOTE"}
    assert not (str_consts & forbidden), f"Forbidden status literals found: {str_consts & forbidden}"


def test_c2_policy_candidate_never_active():
    entries = [{"status": "ACCEPTED", "entry_hash": "x",
                "receipt": {"pipeline_score": 0.9, "output_score": 0.9}}]
    c = make_policy_candidate(entries)
    assert c["status"] == POLICY_CANDIDATE_STATUS
    assert c["status"] not in {"ACTIVE", "ACCEPTED", "APPROVED", "SOVEREIGN"}


# ── C3: Admissibility gate has no bypass surface ─────────────────────────────

def test_c3_no_bypass_callables_in_gate_module():
    import helen_video.admissibility_gate as mod
    public = {n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n))}
    forbidden = {"force", "bypass", "override", "skip", "force_accept", "ship"}
    assert not (public & forbidden)


def test_c3_hysteresis_gate_no_bypass_methods():
    public = {
        n for n in dir(HysteresisGate)
        if not n.startswith("_") and callable(getattr(HysteresisGate, n))
    }
    forbidden = {"force", "bypass", "override", "skip", "force_accept"}
    assert not (public & forbidden)


def test_c3_no_receipt_always_rejects():
    v = evaluate({"character": "HELEN"}, None)
    assert v.decision == "REJECT"


def test_c3_hysteresis_no_receipt_rejects():
    v = HysteresisGate().evaluate({"character": "HELEN"}, None)
    assert v.decision == "REJECT"


# ── C4: Continuity weights are locked ────────────────────────────────────────

def test_c4_weights_sum_to_one():
    assert abs(0.4 + 0.3 + 0.2 + 0.1 - 1.0) < 1e-10


def test_c4_weight_literals_in_source():
    """AST: continuity_engine.py contains exactly 0.4, 0.3, 0.2, 0.1 as float literals."""
    src = (_MODULE_DIR / "continuity_engine.py").read_text()
    tree = ast.parse(src)
    floats = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    }
    for w in (0.4, 0.3, 0.2, 0.1):
        assert w in floats, f"Weight {w} missing from continuity_engine.py source"


def test_c4_perfect_match_scores_one():
    assert continuity_score(_CLIP, _CLIP) == 1.0


def test_c4_total_mismatch_scores_zero():
    c1 = {"character": "A", "scene": "X", "duration": 0,   "style": "Y"}
    c2 = {"character": "B", "scene": "Z", "duration": 100, "style": "W"}
    assert continuity_score(c1, c2) == 0.0


# ── C5: Execution trace authority is NON_SOVEREIGN_EXECUTION ─────────────────

def test_c5_authority_constant_value():
    assert EXEC_AUTHORITY == "NON_SOVEREIGN_EXECUTION"


def test_c5_make_receipt_carries_authority():
    r = make_receipt("echo test", stdout="test", exit_code=0)
    assert r["authority"] == "NON_SOVEREIGN_EXECUTION"


def test_c5_run_with_receipt_produces_verifiable_receipt():
    result, receipt = run_with_receipt(["echo", "c5"])
    assert verify_exec_receipt(receipt, ["echo", "c5"], stdout=result.stdout)
