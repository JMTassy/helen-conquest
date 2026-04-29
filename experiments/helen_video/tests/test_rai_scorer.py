"""VIDEO_RAI_SCORE_V1 — functional and component tests."""
import hashlib
import pytest

from helen_video.admissibility_gate import PIPELINE_SALT
from helen_video.rai_scorer import (
    DEFAULT_ACCEPT_THRESHOLD,
    novelty_score,
    receipt_binding_score,
    reducer_admission_score,
    sovereignty_leakage,
    symbolic_drift,
    rai_score,
    score_candidate,
)


def _pipeline_hash(content_hash: str) -> str:
    return hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()


def _good_receipt(content_hash: str = "abc") -> dict:
    return {
        "content_hash": content_hash,
        "pipeline_hash": _pipeline_hash(content_hash),
        "visual_coherence": 0.85,
        "temporal_alignment": 0.75,
    }


def _candidate(with_receipt: bool = True, content_hash: str = "abc") -> dict:
    c = {"candidate_id": "cid1", "prompt": "test", "model": "helen-core", "status": "CANDIDATE"}
    if with_receipt:
        c["receipt"] = _good_receipt(content_hash)
    return c


# ── component tests ────────────────────────────────────────────────────────────

def test_novelty_no_prior():
    assert novelty_score({}) == 1.0


def test_novelty_new_hash():
    c = _candidate(content_hash="new_hash")
    assert novelty_score(c, prior_hashes={"old_hash"}) == 1.0


def test_novelty_duplicate_hash():
    c = _candidate(content_hash="abc")
    # novelty_score reads receipt.content_hash if "receipt" in candidate
    assert novelty_score(c, prior_hashes={"abc"}) == 0.0


def test_binding_score_none_receipt():
    assert receipt_binding_score(None) == 0.0


def test_binding_score_valid():
    assert receipt_binding_score(_good_receipt()) == 1.0


def test_binding_score_forged():
    r = {**_good_receipt(), "pipeline_hash": "fake"}
    assert receipt_binding_score(r) == 0.0


def test_reducer_scores():
    assert reducer_admission_score("ACCEPT") == 1.0
    assert reducer_admission_score("PENDING") == 0.5
    assert reducer_admission_score("REJECT") == 0.0
    assert reducer_admission_score("UNKNOWN") == 0.0


def test_sovereignty_clean_candidate():
    c = _candidate()
    assert sovereignty_leakage(c) == 0.0


def test_sovereignty_leaks_on_delivery_key():
    c = {**_candidate(), "deliver": True}
    assert sovereignty_leakage(c) > 0.0


def test_symbolic_drift_no_receipt():
    assert symbolic_drift({}) == 1.0


def test_symbolic_drift_forged_receipt():
    c = {"receipt": {**_good_receipt(), "pipeline_hash": "fake"}}
    assert symbolic_drift(c) == 1.0


def test_symbolic_drift_bound_receipt():
    c = {"receipt": _good_receipt()}
    assert symbolic_drift(c) == 0.0


# ── functional ─────────────────────────────────────────────────────────────────

def test_rai_score_zero_without_binding():
    assert rai_score(1.0, 0.0, 1.0, 0.0, 0.0) == 0.0


def test_rai_score_zero_without_admission():
    assert rai_score(1.0, 1.0, 0.0, 0.0, 0.0) == 0.0


def test_rai_score_collapses_with_leakage():
    low = rai_score(1.0, 1.0, 1.0, 100.0, 0.0)
    high = rai_score(1.0, 1.0, 1.0, 0.0, 0.0)
    assert low < high


def test_rai_score_collapses_with_drift():
    low = rai_score(1.0, 1.0, 1.0, 0.0, 100.0)
    high = rai_score(1.0, 1.0, 1.0, 0.0, 0.0)
    assert low < high


# ── score_candidate integration ────────────────────────────────────────────────

def test_score_candidate_accept():
    verdict = score_candidate(_candidate(), _good_receipt())
    assert verdict.decision == "ACCEPT"
    assert verdict.score > DEFAULT_ACCEPT_THRESHOLD
    assert verdict.components["B_receipt"] == 1.0
    assert verdict.components["A_reducer"] == 1.0


def test_score_candidate_reject_no_receipt():
    verdict = score_candidate(_candidate(with_receipt=False), None)
    assert verdict.decision == "REJECT"
    assert verdict.score == 0.0


def test_score_candidate_reject_on_leakage():
    c = {**_candidate(), "deliver": True}
    verdict = score_candidate(c, _good_receipt())
    assert verdict.components["L_sovereignty"] > 0.0


def test_score_candidate_includes_all_components():
    verdict = score_candidate(_candidate(), _good_receipt())
    required = {"P_novel", "B_receipt", "A_reducer", "L_sovereignty", "D_symbolic", "eps"}
    assert required <= set(verdict.components.keys())
