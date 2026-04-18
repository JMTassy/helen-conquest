"""
tests/test_conclusion_v1.py — HELEN_CONCLUSION_V1 + ConclusionReducer

Tests:
  CN1.1  HELENConclusion validates required fields correctly
  CN1.2  shipability is always "NONSHIPABLE" (enforced by validator, cannot override)
  CN1.3  to_receipt_payload() returns all required keys including notes + shipability
  CN2.1  Reducer: same sim_result + two different HELENConclusions → identical gates
         (proves gates derive from phase evidence, not from HELEN's proposal)
  CN2.2  next_quest_seed is deterministic (same inputs → same 64-char hex seed)
  CN2.3  helen_proposal_used is always False in ReducedConclusion (structural invariant)
  CN2.4  ReducedConclusion contains all three gate booleans + correct overall_pass
  CN3.1  PARADOX quest (Q1) → contradiction_resolved derives from delta_closure + paradox_injected
  CN3.2  REALITY quest (Q2) → reality_transformed derives from base closure + shadow ran
  CN3.3  TEMPORAL quest (Q3) → temporal_insights_gained requires sigma_passed + laws >= 1
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.meta.conclusion_v1 import (
    HELENConclusion,
    ProposedLaw,
    ReducedConclusion,
    ConclusionReducer,
)
from helen_os.epoch3.quest_bank import get_quest
from helen_os.epoch3.sim_loop import SimLoop
from helen_os.epoch2.law_ledger import LawLedger
from helen_os.kernel import GovernanceVM


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_conclusion(
    quest_id:   str = "Q1",
    quest_type: str = "SOLVE_PARADOX",
    notes:      str = "Test conclusion — NONSHIPABLE",
    receipts:   list = None,
) -> HELENConclusion:
    """Build a standard HELENConclusion for testing."""
    return HELENConclusion(
        quest_id              = quest_id,
        quest_type            = quest_type,
        proposed_laws         = [
            ProposedLaw(
                law_id     = "LAW-TEST-001",
                statement  = "Test law statement derived from sim evidence",
                proof_hint = "Empirical — phase A + B + C",
            )
        ],
        proposed_metrics      = {"mean_shift": 0.12},
        proposed_sigma_deltas = {"sigma_mean_shift": 0.12},
        receipt_pointers      = receipts or ["R-abc123", "R-def456"],
        notes                 = notes,
    )


def _run_quest(quest_id: str, seed: int = 42, ticks: int = 20):
    """
    Run a quest and return (sim_result, kernel).

    Uses an ephemeral :memory: kernel — non-sovereign, no ledger side-effects.
    A LawLedger is always provided so Phase C can inscribe laws (required for Q3).
    """
    quest      = get_quest(quest_id)
    kernel     = GovernanceVM(ledger_path=":memory:")
    law_ledger = LawLedger(kernel=kernel)
    sim        = SimLoop(kernel=kernel)
    result     = sim.run(quest=quest, seed=seed, ticks=ticks, law_ledger=law_ledger)
    return result, kernel


# ── CN1.x — HELENConclusion schema validation ─────────────────────────────────

def test_cn1_1_helen_conclusion_validates():
    """CN1.1 — HELENConclusion validates required fields correctly."""
    conclusion = _make_conclusion()

    assert conclusion.type       == "HELEN_CONCLUSION_V1"
    assert conclusion.quest_id   == "Q1"
    assert conclusion.quest_type == "SOLVE_PARADOX"
    assert len(conclusion.proposed_laws) == 1
    assert conclusion.proposed_laws[0].law_id == "LAW-TEST-001"
    assert conclusion.proposed_laws[0].proof_hint == "Empirical — phase A + B + C"
    assert conclusion.receipt_pointers == ["R-abc123", "R-def456"]
    assert conclusion.proposed_metrics == {"mean_shift": 0.12}


def test_cn1_2_shipability_always_nonshipable():
    """
    CN1.2 — shipability is always NONSHIPABLE.

    The field_validator forces "NONSHIPABLE" regardless of what value is passed.
    HELEN_CONCLUSION_V1 can NEVER be SHIPABLE or REVIEW.
    """
    # Default
    c1 = _make_conclusion()
    assert c1.shipability == "NONSHIPABLE"

    # Even passing SHIPABLE explicitly → overridden to NONSHIPABLE
    c2 = HELENConclusion(
        quest_id    = "Q1",
        quest_type  = "SOLVE_PARADOX",
        shipability = "SHIPABLE",   # ← must be overridden
    )
    assert c2.shipability == "NONSHIPABLE", (
        f"Expected 'NONSHIPABLE', got {c2.shipability!r}. "
        "HELEN_CONCLUSION_V1 shipability is structural, cannot be overridden."
    )

    # Even passing REVIEW → overridden to NONSHIPABLE
    c3 = HELENConclusion(
        quest_id    = "Q1",
        quest_type  = "SOLVE_PARADOX",
        shipability = "REVIEW",
    )
    assert c3.shipability == "NONSHIPABLE"


def test_cn1_3_to_receipt_payload():
    """CN1.3 — to_receipt_payload() returns all required keys correctly."""
    conclusion = _make_conclusion(notes="Test note — NONSHIPABLE")
    payload    = conclusion.to_receipt_payload()

    required_keys = {
        "type", "quest_id", "quest_type",
        "proposed_law_ids", "proposed_metrics", "proposed_sigma_deltas",
        "receipt_pointers", "notes", "shipability",
    }
    missing = required_keys - set(payload.keys())
    assert not missing, f"Missing keys in receipt payload: {missing}"

    assert payload["type"]        == "HELEN_CONCLUSION_V1"
    assert payload["shipability"] == "NONSHIPABLE"
    assert payload["notes"]       == "Test note — NONSHIPABLE"
    assert "LAW-TEST-001" in payload["proposed_law_ids"]
    assert payload["quest_id"]    == "Q1"
    assert payload["receipt_pointers"] == ["R-abc123", "R-def456"]


# ── CN2.x — ConclusionReducer invariants ──────────────────────────────────────

def test_cn2_1_reducer_gates_from_evidence_not_proposal():
    """
    CN2.1 — Same sim_result + two different HELENConclusions → identical gates.

    This proves the core invariant: gates derive from phase evidence (sim_result),
    not from anything HELEN proposed.

    Even if conclusion_A proposes completely different laws and metrics than
    conclusion_B, the gate values (contradiction_resolved, reality_transformed,
    temporal_insights_gained) must be identical because they come from the SAME
    sim_result phase evidence.
    """
    sim_result, _ = _run_quest("Q1")

    # Two conclusions with VERY different proposed values
    conclusion_a = HELENConclusion(
        quest_id      = "Q1",
        quest_type    = "SOLVE_PARADOX",
        notes         = "Conclusion A — proposes high confidence laws",
        proposed_laws = [ProposedLaw(law_id="LAW-A", statement="HELEN Law A")],
        proposed_metrics = {"mean_shift": 0.99, "confidence": 1.0},
    )
    conclusion_b = HELENConclusion(
        quest_id      = "Q1",
        quest_type    = "SOLVE_PARADOX",
        notes         = "Conclusion B — proposes zero confidence",
        proposed_laws = [ProposedLaw(law_id="LAW-B", statement="HELEN Law B")],
        proposed_metrics = {"mean_shift": 0.01, "confidence": 0.0},
    )

    # Use separate ephemeral kernels (different receipt IDs — but gates should match)
    reduced_a = ConclusionReducer.reduce(conclusion_a, sim_result, GovernanceVM(ledger_path=":memory:"))
    reduced_b = ConclusionReducer.reduce(conclusion_b, sim_result, GovernanceVM(ledger_path=":memory:"))

    # Gates MUST be identical — they come from sim_result, not from HELEN's proposal
    assert reduced_a.contradiction_resolved == reduced_b.contradiction_resolved, (
        "contradiction_resolved must be identical: it derives from sim evidence, not proposals"
    )
    assert reduced_a.reality_transformed == reduced_b.reality_transformed, (
        "reality_transformed must be identical: it derives from sim evidence, not proposals"
    )
    assert reduced_a.temporal_insights_gained == reduced_b.temporal_insights_gained, (
        "temporal_insights_gained must be identical: it derives from sim evidence, not proposals"
    )
    assert reduced_a.overall_pass == reduced_b.overall_pass


def test_cn2_2_next_quest_seed_is_deterministic():
    """
    CN2.2 — next_quest_seed is deterministic.

    Same (conclusion, sim_result) with different kernels → same 64-char seed.
    No wall clock. No external entropy.
    Seed derived only from: quest_id + receipt_pointers + gates + metrics.
    """
    sim_result, _ = _run_quest("Q1")
    conclusion    = _make_conclusion("Q1", "SOLVE_PARADOX")

    # Two completely independent ephemeral kernels
    reduced_x = ConclusionReducer.reduce(conclusion, sim_result, GovernanceVM(ledger_path=":memory:"))
    reduced_y = ConclusionReducer.reduce(conclusion, sim_result, GovernanceVM(ledger_path=":memory:"))

    assert reduced_x.next_quest_seed == reduced_y.next_quest_seed, (
        f"Seed not deterministic:\n"
        f"  x: {reduced_x.next_quest_seed}\n"
        f"  y: {reduced_y.next_quest_seed}\n"
        "Seed must depend only on (quest_id, receipt_pointers, gates, metrics)."
    )
    assert len(reduced_x.next_quest_seed) == 64, (
        f"next_quest_seed must be 64-char SHA256 hex, got {len(reduced_x.next_quest_seed)}"
    )
    # Seed must be non-trivial hex
    assert all(c in "0123456789abcdef" for c in reduced_x.next_quest_seed)


def test_cn2_3_helen_proposal_never_used():
    """
    CN2.3 — helen_proposal_used is always False in ReducedConclusion.

    This is the structural invariant of the reducer: HELEN never sets gates.
    """
    sim_result, kernel = _run_quest("Q1")
    conclusion         = _make_conclusion()
    reduced            = ConclusionReducer.reduce(conclusion, sim_result, kernel)

    assert reduced.helen_proposal_used is False, (
        "helen_proposal_used MUST be False — HELEN cannot set gates. "
        "Gates are always recomputed from phase evidence."
    )

    # Also verify that attempting to construct ReducedConclusion with helen_proposal_used=True fails
    import pytest
    with pytest.raises(Exception):
        ReducedConclusion(
            quest_id                  = "Q1",
            quest_type                = "SOLVE_PARADOX",
            contradiction_resolved    = True,
            reality_transformed       = True,
            temporal_insights_gained  = True,
            overall_pass              = True,
            next_quest_seed           = "a" * 64,
            helen_proposal_used       = True,   # ← must be rejected
        )


def test_cn2_4_reduced_conclusion_has_all_gates():
    """
    CN2.4 — ReducedConclusion contains all three gate booleans + correct overall_pass.

    overall_pass = contradiction_resolved AND reality_transformed AND temporal_insights_gained
    """
    sim_result, kernel = _run_quest("Q1")
    conclusion         = _make_conclusion()
    reduced            = ConclusionReducer.reduce(conclusion, sim_result, kernel)

    assert isinstance(reduced.contradiction_resolved,   bool), "contradiction_resolved must be bool"
    assert isinstance(reduced.reality_transformed,      bool), "reality_transformed must be bool"
    assert isinstance(reduced.temporal_insights_gained, bool), "temporal_insights_gained must be bool"
    assert isinstance(reduced.overall_pass,             bool), "overall_pass must be bool"

    # overall_pass is the conjunction of all three gates
    expected_overall = (
        reduced.contradiction_resolved
        and reduced.reality_transformed
        and reduced.temporal_insights_gained
    )
    assert reduced.overall_pass == expected_overall, (
        f"overall_pass={reduced.overall_pass!r} should be "
        f"contradiction({reduced.contradiction_resolved!r}) AND "
        f"reality({reduced.reality_transformed!r}) AND "
        f"temporal({reduced.temporal_insights_gained!r}) = {expected_overall!r}"
    )


# ── CN3.x — Quest-type-specific gate derivation ───────────────────────────────

def test_cn3_1_paradox_quest_gates():
    """
    CN3.1 — SOLVE_PARADOX: contradiction_resolved derives from delta_closure + paradox_injected.

    For Q1:
      - base world W closes (closure_success=True)
      - Phase B injects paradox (closure_success=False in shadow)
      - delta_closure > 0.5 (base closed, shadow didn't)
      → contradiction_resolved=True
    """
    sim_result, kernel = _run_quest("Q1")
    conclusion = HELENConclusion(
        quest_id      = "Q1",
        quest_type    = "SOLVE_PARADOX",
        proposed_laws = [],
        notes         = "Q1 conclusion — NONSHIPABLE",
    )
    reduced = ConclusionReducer.reduce(conclusion, sim_result, kernel)

    # Verify the phase evidence that drives the gate
    assert sim_result.phase_b.paradox_injected, (
        "Q1 Phase B must inject paradox (INJECT_PARADOX op)"
    )
    assert sim_result.phase_c.delta_closure_success > 0.5, (
        f"Q1 delta_closure_success={sim_result.phase_c.delta_closure_success} must be > 0.5"
    )

    # The gate must reflect the evidence
    assert reduced.contradiction_resolved, (
        "Q1 contradiction_resolved must be True when paradox injected + delta_closure > 0.5"
    )

    # evidence_gates must contain the derivation record
    ev = reduced.evidence_gates.get("contradiction_resolved_from", {})
    assert "paradox_injected"      in ev, "evidence_gates must record paradox_injected"
    assert "delta_closure_success" in ev, "evidence_gates must record delta_closure_success"
    assert ev["paradox_injected"]  is True


def test_cn3_2_reality_quest_gates():
    """
    CN3.2 — ALTER_REALITY: reality_transformed derives from base closure + shadow ran.

    For Q2:
      - base world W closes (admissibility_rate >= 0.80)
      - Phase B runs shadow world W' with different seed (SET_SEED op)
      - shadow_ran=True (shadow_metrics_list is non-empty)
      → reality_transformed=True
    """
    sim_result, kernel = _run_quest("Q2")
    conclusion = HELENConclusion(
        quest_id      = "Q2",
        quest_type    = "ALTER_REALITY",
        proposed_laws = [],
        notes         = "Q2 conclusion — NONSHIPABLE",
    )
    reduced = ConclusionReducer.reduce(conclusion, sim_result, kernel)

    # Verify the phase evidence
    shadow_ran = len(sim_result.phase_b.shadow_metrics_list) > 0
    assert shadow_ran, "Q2 Phase B must run shadow world (SET_SEED op)"

    # The gate must reflect the evidence
    assert reduced.reality_transformed, (
        "Q2 reality_transformed must be True when base closed + shadow ran"
    )

    # evidence_gates must contain the derivation record
    ev = reduced.evidence_gates.get("reality_transformed_from", {})
    assert "shadow_ran" in ev, "evidence_gates must record shadow_ran"
    assert ev["shadow_ran"] is True


def test_cn3_3_temporal_quest_gates():
    """
    CN3.3 — EXPLORE_TEMPORAL: temporal_insights_gained requires sigma_passed + laws >= 1.

    For Q3:
      - sigma gate passes (sovereignty_drift == 0 across horizons)
      - At least 1 LAW_V1 is inscribed by Phase C
      → temporal_insights_gained=True
    """
    sim_result, kernel = _run_quest("Q3")
    conclusion = HELENConclusion(
        quest_id      = "Q3",
        quest_type    = "EXPLORE_TEMPORAL",
        proposed_laws = [],
        notes         = "Q3 conclusion — NONSHIPABLE",
    )
    reduced = ConclusionReducer.reduce(conclusion, sim_result, kernel)

    # Verify the phase evidence
    assert sim_result.phase_c.sigma_passed, (
        "Q3 sigma gate must pass (sovereignty_drift == 0)"
    )
    assert sim_result.phase_c.laws_inscribed_count >= 1, (
        f"Q3 must inscribe >= 1 law, got {sim_result.phase_c.laws_inscribed_count}"
    )

    # The gate must reflect the evidence
    assert reduced.temporal_insights_gained, (
        "Q3 temporal_insights_gained must be True when sigma_passed + laws >= 1"
    )

    # evidence_gates must contain the derivation record
    ev = reduced.evidence_gates.get("temporal_insights_gained_from", {})
    assert "sigma_passed"         in ev, "evidence_gates must record sigma_passed"
    assert "laws_inscribed_count" in ev, "evidence_gates must record laws_inscribed_count"
    assert ev["sigma_passed"]          is True
    assert ev["laws_inscribed_count"]  >= 1


# ── CN4.x — Canyon Non-Interference (CANYON_NONINTERFERENCE_V1) ───────────────

def test_cn4_1_same_eadm_same_verdict_hash():
    """
    CN4.1 — CANYON_NONINTERFERENCE_V1: same E_adm (sim_result) → same verdict_hash_hex.

    Two different HELENConclusion proposals run against the same sim_result
    must produce the SAME verdict_hash_hex (and verdict_id).

    This is the ledger-append invariant: same admissible evidence → same
    sovereign mutation. Narrative variation cannot affect the ledger.
    """
    sim_result, _ = _run_quest("Q1")

    conclusion_alpha = HELENConclusion(
        quest_id      = "Q1",
        quest_type    = "SOLVE_PARADOX",
        notes         = "Alpha proposal — high confidence",
        proposed_laws = [ProposedLaw(law_id="LAW-ALPHA", statement="Alpha law")],
        proposed_metrics = {"confidence": 0.99, "mean_shift": 0.95},
    )
    conclusion_beta = HELENConclusion(
        quest_id      = "Q1",
        quest_type    = "SOLVE_PARADOX",
        notes         = "Beta proposal — entirely different narrative",
        proposed_laws = [ProposedLaw(law_id="LAW-BETA", statement="Beta law"),
                         ProposedLaw(law_id="LAW-BETA-2", statement="Another beta law")],
        proposed_metrics = {"confidence": 0.01, "mean_shift": 0.0},
    )

    # Use separate ephemeral kernels (different receipt IDs — verdict_hash must still match)
    reduced_alpha = ConclusionReducer.reduce(conclusion_alpha, sim_result, GovernanceVM(ledger_path=":memory:"))
    reduced_beta  = ConclusionReducer.reduce(conclusion_beta,  sim_result, GovernanceVM(ledger_path=":memory:"))

    # CANYON_NONINTERFERENCE_V1 falsifier 1: same E_adm → same verdict_hash_hex
    assert reduced_alpha.verdict_hash_hex == reduced_beta.verdict_hash_hex, (
        "verdict_hash_hex must be identical for same E_adm (sim_result). "
        "Canyon non-interference: narrative cannot change the ledger transition.\n"
        f"  alpha: {reduced_alpha.verdict_hash_hex}\n"
        f"  beta:  {reduced_beta.verdict_hash_hex}"
    )
    assert reduced_alpha.verdict_id == reduced_beta.verdict_id, (
        "verdict_id must be identical for same E_adm"
    )
    assert len(reduced_alpha.verdict_hash_hex) == 64, "verdict_hash_hex must be 64-char SHA256"
    assert reduced_alpha.verdict_id.startswith("V-"), "verdict_id must start with 'V-'"


def test_cn4_2_same_inputs_same_verdict_hash_across_runs():
    """
    CN4.2 — CANYON_NONINTERFERENCE_V1: deterministic verdict under replay.

    Same (conclusion, sim_result) run twice produces same verdict_hash_hex.
    This is CANYON_NONINTERFERENCE_V1 falsifier 2: deterministic replay.
    """
    sim_result, _ = _run_quest("Q1")
    conclusion    = _make_conclusion("Q1", "SOLVE_PARADOX")

    # Two independent runs with different kernels
    reduced_run1 = ConclusionReducer.reduce(conclusion, sim_result, GovernanceVM(ledger_path=":memory:"))
    reduced_run2 = ConclusionReducer.reduce(conclusion, sim_result, GovernanceVM(ledger_path=":memory:"))

    assert reduced_run1.verdict_hash_hex == reduced_run2.verdict_hash_hex, (
        "verdict_hash_hex must be deterministic under replay with same inputs.\n"
        f"  run1: {reduced_run1.verdict_hash_hex}\n"
        f"  run2: {reduced_run2.verdict_hash_hex}"
    )
    assert reduced_run1.next_quest_seed == reduced_run2.next_quest_seed, (
        "next_quest_seed must also be deterministic under replay"
    )


def test_cn4_3_different_eadm_different_verdict_allowed():
    """
    CN4.3 — CANYON_NONINTERFERENCE_V1 falsifier 3 (negative): different E_adm is allowed
    to produce different verdict_hash_hex.

    The law only constrains SAME E_adm → SAME verdict. It explicitly PERMITS
    different E_adm (different sim_results) to produce different verdicts.
    This test proves the system is not over-constrained (i.e., it can distinguish).
    """
    sim_q1, _ = _run_quest("Q1")   # SOLVE_PARADOX
    sim_q2, _ = _run_quest("Q2")   # ALTER_REALITY

    conclusion_q1 = HELENConclusion(quest_id="Q1", quest_type="SOLVE_PARADOX")
    conclusion_q2 = HELENConclusion(quest_id="Q2", quest_type="ALTER_REALITY")

    reduced_q1 = ConclusionReducer.reduce(conclusion_q1, sim_q1, GovernanceVM(ledger_path=":memory:"))
    reduced_q2 = ConclusionReducer.reduce(conclusion_q2, sim_q2, GovernanceVM(ledger_path=":memory:"))

    # Different E_adm → different verdict (permitted — system discriminates)
    assert reduced_q1.verdict_hash_hex != reduced_q2.verdict_hash_hex, (
        "Different sim_results should produce different verdict_hash_hex. "
        "If they were equal, the system would be unable to distinguish quest outcomes."
    )
    assert reduced_q1.quest_type != reduced_q2.quest_type, "Sanity check: different quest types"
