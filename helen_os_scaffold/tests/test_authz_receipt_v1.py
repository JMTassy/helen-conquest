"""
tests/test_authz_receipt_v1.py — AUTHZ_RECEIPT_V1 + canyon law tests

Tests HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 law:
  "helen_proposal_used=True iff AUTHZ_RECEIPT_V1 binds to (verdict_id, verdict_hash_hex)"

Groups:
  AR1.x — AuthzReceiptV1 schema validation
  AR2.x — validate_authz_binding (binding correctness)
  AR3.x — ReducedConclusion with helen_proposal_used=True integration

Also tests proposed law objects:
  AR4.x — ProposedLawV1 schema + law_hash stability + inscription tracking
  AR5.x — Canonical law objects (CANYON_NONINTERFERENCE_V1, HELEN_PROPOSAL_USE_RECEIPT_GATE_V1)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydantic import ValidationError

from helen_os.meta.authz_receipt import (
    AuthzReceiptV1,
    AuthzReceiptRef,
    AuthzBindingError,
    validate_authz_binding,
)
from helen_os.meta.proposed_law import (
    ProposedLawV1,
    LawStatus,
    CANYON_NONINTERFERENCE_V1,
    HELEN_PROPOSAL_USE_RECEIPT_GATE_V1,
)
from helen_os.meta.conclusion_v1 import (
    HELENConclusion,
    ReducedConclusion,
    ConclusionReducer,
)
from helen_os.epoch3.quest_bank import get_quest
from helen_os.epoch3.sim_loop import SimLoop
from helen_os.epoch2.law_ledger import LawLedger
from helen_os.kernel import GovernanceVM


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run_q1():
    """Run Q1 and return a reduced conclusion with verdict_id/verdict_hash_hex."""
    quest      = get_quest("Q1")
    kernel     = GovernanceVM(ledger_path=":memory:")
    law_ledger = LawLedger(kernel=kernel)
    sim        = SimLoop(kernel=kernel)
    sim_result = sim.run(quest=quest, seed=42, ticks=20, law_ledger=law_ledger)
    conclusion = HELENConclusion(quest_id="Q1", quest_type="SOLVE_PARADOX")
    return ConclusionReducer.reduce(conclusion, sim_result, kernel)


def _make_authz(verdict_id: str, verdict_hash_hex: str, rid: str = "R-test0001") -> AuthzReceiptV1:
    """Build a valid AUTHZ_RECEIPT_V1 for the given verdict."""
    return AuthzReceiptV1(
        rid  = rid,
        refs = AuthzReceiptRef(
            verdict_id       = verdict_id,
            verdict_hash_hex = verdict_hash_hex,
        ),
        authorizes   = {
            "field": "ReducedConclusion.helen_proposal_used",
            "value": True,
        },
        reason_codes = ["CANYON_AUTHORIZED"],
    )


# ── AR1.x — AuthzReceiptV1 schema validation ───────────────────────────────────

def test_ar1_1_authz_receipt_validates():
    """AR1.1 — AuthzReceiptV1 validates correctly with all required fields."""
    authz = AuthzReceiptV1(
        rid  = "R-ab1234cd",
        refs = AuthzReceiptRef(
            verdict_id       = "V-deadbeef",
            verdict_hash_hex = "a" * 64,
        ),
        authorizes   = {
            "field": "ReducedConclusion.helen_proposal_used",
            "value": True,
        },
        reason_codes = ["CANYON_AUTHORIZED"],
    )
    assert authz.type                      == "AUTHZ_RECEIPT_V1"
    assert authz.rid                       == "R-ab1234cd"
    assert authz.refs.verdict_id           == "V-deadbeef"
    assert authz.refs.verdict_hash_hex     == "a" * 64
    assert authz.authorizes["field"]       == "ReducedConclusion.helen_proposal_used"
    assert authz.authorizes["value"]       is True
    assert "CANYON_AUTHORIZED"             in authz.reason_codes


def test_ar1_2_wrong_field_target_rejected():
    """AR1.2 — AuthzReceiptV1 with wrong authorizes.field → ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        AuthzReceiptV1(
            rid  = "R-bad",
            refs = AuthzReceiptRef(verdict_id="V-x", verdict_hash_hex="b" * 64),
            authorizes   = {
                "field": "ReducedConclusion.overall_pass",  # ← wrong field
                "value": True,
            },
        )
    assert "helen_proposal_used" in str(exc_info.value), (
        "Error must mention the expected field name"
    )


def test_ar1_3_wrong_value_false_rejected():
    """AR1.3 — AuthzReceiptV1 with authorizes.value=False → ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        AuthzReceiptV1(
            rid  = "R-bad",
            refs = AuthzReceiptRef(verdict_id="V-x", verdict_hash_hex="c" * 64),
            authorizes   = {
                "field": "ReducedConclusion.helen_proposal_used",
                "value": False,   # ← wrong value
            },
        )
    assert "True" in str(exc_info.value), "Error must mention that value must be True"


def test_ar1_4_missing_canyon_authorized_reason_code_rejected():
    """AR1.4 — AuthzReceiptV1 without CANYON_AUTHORIZED in reason_codes → ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        AuthzReceiptV1(
            rid  = "R-bad",
            refs = AuthzReceiptRef(verdict_id="V-x", verdict_hash_hex="d" * 64),
            authorizes   = {
                "field": "ReducedConclusion.helen_proposal_used",
                "value": True,
            },
            reason_codes = ["SOME_OTHER_CODE"],  # ← missing CANYON_AUTHORIZED
        )
    assert "CANYON_AUTHORIZED" in str(exc_info.value)


# ── AR2.x — validate_authz_binding (binding correctness) ─────────────────────

def test_ar2_1_valid_binding_passes():
    """AR2.1 — validate_authz_binding passes when refs match exactly."""
    authz = _make_authz("V-ab1234cd", "e" * 64)
    # Must not raise
    validate_authz_binding(authz, "V-ab1234cd", "e" * 64)


def test_ar2_2_wrong_verdict_id_raises():
    """AR2.2 — validate_authz_binding raises AuthzBindingError when verdict_id doesn't match."""
    authz = _make_authz("V-correct00", "f" * 64)
    with pytest.raises(AuthzBindingError) as exc_info:
        validate_authz_binding(authz, "V-different", "f" * 64)
    assert "V-different" in str(exc_info.value) or "does not bind" in str(exc_info.value)


def test_ar2_3_wrong_verdict_hash_raises():
    """AR2.3 — validate_authz_binding raises AuthzBindingError when verdict_hash_hex doesn't match."""
    authz = _make_authz("V-sameid000", "0" * 64)
    with pytest.raises(AuthzBindingError) as exc_info:
        validate_authz_binding(authz, "V-sameid000", "1" * 64)  # ← different hash
    assert "does not bind" in str(exc_info.value)


def test_ar2_4_both_wrong_raises():
    """AR2.4 — validate_authz_binding raises when both fields are wrong."""
    authz = _make_authz("V-foo", "a" * 64)
    with pytest.raises(AuthzBindingError):
        validate_authz_binding(authz, "V-bar", "b" * 64)


# ── AR3.x — ReducedConclusion with helen_proposal_used=True integration ────────

def test_ar3_1_helen_proposal_used_true_with_valid_authz():
    """
    AR3.1 — ReducedConclusion with helen_proposal_used=True + matching AUTHZ_RECEIPT_V1 → valid.

    The stone permits the river: an AUTHZ_RECEIPT_V1 that binds to the exact
    (verdict_id, verdict_hash_hex) authorizes helen_proposal_used=True.
    """
    reduced = _run_q1()
    assert reduced.helen_proposal_used is False   # Default state

    # Build a correctly-bound AUTHZ_RECEIPT_V1
    authz = _make_authz(reduced.verdict_id, reduced.verdict_hash_hex, rid="R-canyon01")

    # Construct a new ReducedConclusion with helen_proposal_used=True + authz
    authorized = ReducedConclusion(
        quest_id                  = reduced.quest_id,
        quest_type                = reduced.quest_type,
        contradiction_resolved    = reduced.contradiction_resolved,
        reality_transformed       = reduced.reality_transformed,
        temporal_insights_gained  = reduced.temporal_insights_gained,
        overall_pass              = reduced.overall_pass,
        next_quest_seed           = reduced.next_quest_seed,
        verdict_id                = reduced.verdict_id,
        verdict_hash_hex          = reduced.verdict_hash_hex,
        helen_proposal_used       = True,
        authz_receipt             = authz.model_dump(),  # Pass as dict
        evaluation_receipt_id     = reduced.evaluation_receipt_id,
    )

    assert authorized.helen_proposal_used is True, (
        "helen_proposal_used should be True when valid AUTHZ_RECEIPT_V1 is present"
    )
    assert authorized.authz_receipt is not None


def test_ar3_2_helen_proposal_used_true_no_authz_rejected():
    """
    AR3.2 — ReducedConclusion with helen_proposal_used=True + no authz → ValidationError.

    HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 falsifier 1:
    helen_proposal_used=True without AUTHZ_RECEIPT_V1 must be rejected.
    """
    reduced = _run_q1()

    with pytest.raises(ValidationError) as exc_info:
        ReducedConclusion(
            quest_id                  = reduced.quest_id,
            quest_type                = reduced.quest_type,
            contradiction_resolved    = reduced.contradiction_resolved,
            reality_transformed       = reduced.reality_transformed,
            temporal_insights_gained  = reduced.temporal_insights_gained,
            overall_pass              = reduced.overall_pass,
            next_quest_seed           = reduced.next_quest_seed,
            verdict_id                = reduced.verdict_id,
            verdict_hash_hex          = reduced.verdict_hash_hex,
            helen_proposal_used       = True,
            authz_receipt             = None,   # ← no receipt → must fail
        )
    assert "AUTHZ_RECEIPT_V1" in str(exc_info.value) or "authz_receipt" in str(exc_info.value)


def test_ar3_3_helen_proposal_used_true_wrong_hash_rejected():
    """
    AR3.3 — ReducedConclusion with helen_proposal_used=True + wrong verdict_hash → ValidationError.

    HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 falsifier 2:
    AUTHZ_RECEIPT_V1 that binds to a DIFFERENT verdict_hash_hex must be rejected.
    Retroactive authorization is impossible.
    """
    reduced = _run_q1()

    # Build an AUTHZ_RECEIPT_V1 that binds to a DIFFERENT (wrong) verdict_hash_hex
    wrong_hash = "0" * 64   # Not the real verdict_hash_hex
    authz_wrong = _make_authz(reduced.verdict_id, wrong_hash, rid="R-wrong001")

    with pytest.raises(ValidationError) as exc_info:
        ReducedConclusion(
            quest_id                  = reduced.quest_id,
            quest_type                = reduced.quest_type,
            contradiction_resolved    = reduced.contradiction_resolved,
            reality_transformed       = reduced.reality_transformed,
            temporal_insights_gained  = reduced.temporal_insights_gained,
            overall_pass              = reduced.overall_pass,
            next_quest_seed           = reduced.next_quest_seed,
            verdict_id                = reduced.verdict_id,
            verdict_hash_hex          = reduced.verdict_hash_hex,
            helen_proposal_used       = True,
            authz_receipt             = authz_wrong.model_dump(),  # Wrong hash → binding fails
        )
    err = str(exc_info.value)
    assert ("does not bind" in err or "AuthzBinding" in err or "verdict_hash" in err), (
        f"Error must indicate binding failure, got: {err[:300]}"
    )


def test_ar3_4_helen_proposal_used_false_always_valid():
    """
    AR3.4 — helen_proposal_used=False (default) is always valid without authz_receipt.

    This is the normal path. The gate exists but is never triggered.
    """
    reduced = _run_q1()
    # Already defaults to False — but also test explicit construction
    explicit = ReducedConclusion(
        quest_id                  = reduced.quest_id,
        quest_type                = reduced.quest_type,
        contradiction_resolved    = reduced.contradiction_resolved,
        reality_transformed       = reduced.reality_transformed,
        temporal_insights_gained  = reduced.temporal_insights_gained,
        overall_pass              = reduced.overall_pass,
        next_quest_seed           = reduced.next_quest_seed,
        verdict_id                = reduced.verdict_id,
        verdict_hash_hex          = reduced.verdict_hash_hex,
        helen_proposal_used       = False,
        authz_receipt             = None,
    )
    assert explicit.helen_proposal_used is False


# ── AR4.x — ProposedLawV1 schema ──────────────────────────────────────────────

def test_ar4_1_proposed_law_v1_validates():
    """AR4.1 — ProposedLawV1 validates with required fields."""
    law = ProposedLawV1(
        law_id     = "TEST_LAW_V1",
        statement  = "Under all conditions, X implies Y.",
        scope      = "test module",
        falsifiers = ["X does not imply Y in case Z"],
        proof_hint = "Empirical observation from 100 runs",
    )
    assert law.type        == "PROPOSED_LAW_V1"
    assert law.status      == LawStatus.PROPOSED
    assert law.receipt_id  is None
    assert law.cum_hash    is None


def test_ar4_2_law_hash_is_stable():
    """AR4.2 — ProposedLawV1.law_hash() is deterministic (same inputs → same hash)."""
    law1 = ProposedLawV1(law_id="L1", statement="Test statement", scope="test")
    law2 = ProposedLawV1(law_id="L1", statement="Test statement", scope="test")
    assert law1.law_hash() == law2.law_hash(), "law_hash must be deterministic"
    assert len(law1.law_hash()) == 64, "law_hash must be 64-char SHA256"


def test_ar4_3_inscribed_with_receipt():
    """AR4.3 — ProposedLawV1.inscribed_with() produces correct INSCRIBED status."""
    law      = ProposedLawV1(law_id="L1", statement="Test", scope="test")
    inscribed = law.inscribed_with(receipt_id="R-abc123", cum_hash="d" * 64)
    assert inscribed.status     == LawStatus.INSCRIBED
    assert inscribed.receipt_id == "R-abc123"
    assert inscribed.cum_hash   == "d" * 64
    # Original unchanged (Pydantic model_copy returns new instance)
    assert law.status           == LawStatus.PROPOSED


def test_ar4_4_to_ledger_payload():
    """AR4.4 — ProposedLawV1.to_ledger_payload() returns receipt-safe dict."""
    law     = ProposedLawV1(law_id="L1", statement="Test", scope="scope1", falsifiers=["F1"])
    payload = law.to_ledger_payload()
    assert payload["type"]       == "PROPOSED_LAW_V1"
    assert payload["law_id"]     == "L1"
    assert payload["statement"]  == "Test"
    assert payload["status"]     == "PROPOSED"
    assert "F1"                  in payload["falsifiers"]


# ── AR5.x — Canonical law objects ────────────────────────────────────────────

def test_ar5_1_canyon_noninterference_law_shape():
    """AR5.1 — CANYON_NONINTERFERENCE_V1 has correct law_id and non-empty falsifiers."""
    law = CANYON_NONINTERFERENCE_V1
    assert law.law_id    == "CANYON_NONINTERFERENCE_V1"
    assert law.status    == LawStatus.PROPOSED
    assert len(law.falsifiers) >= 2, "Must have at least 2 falsifiers"
    assert "ConclusionReducer" in law.scope
    assert law.proof_hint is not None


def test_ar5_2_helen_proposal_gate_law_shape():
    """AR5.2 — HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 has correct shape + references AUTHZ_RECEIPT_V1."""
    law = HELEN_PROPOSAL_USE_RECEIPT_GATE_V1
    assert law.law_id    == "HELEN_PROPOSAL_USE_RECEIPT_GATE_V1"
    assert law.status    == LawStatus.PROPOSED
    assert len(law.falsifiers) >= 2
    assert "AUTHZ_RECEIPT_V1" in law.statement
    assert "helen_proposal_used" in law.statement


def test_ar5_3_law_hashes_are_distinct():
    """AR5.3 — The two canonical laws have distinct law_hash values."""
    h1 = CANYON_NONINTERFERENCE_V1.law_hash()
    h2 = HELEN_PROPOSAL_USE_RECEIPT_GATE_V1.law_hash()
    assert h1 != h2, "Distinct laws must have distinct law_hash values"
    assert len(h1) == 64 and len(h2) == 64
