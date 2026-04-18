"""
tests/test_epoch2_e3_law_ledger.py

E3 — LawLedger: inscription, schema, and "no receipt → no law" enforcement.

Tests:
  E3.1 — inscribe() on passed SigmaResult → Receipt with R-prefix
  E3.2 — inscribe() on FAILED SigmaResult → raises ValueError
  E3.3 — LAW_V1 payload has all required fields
  E3.4 — evidence_hashes are non-empty (receipt IDs from sigma runs)
  E3.5 — LawLedger.list_laws() returns inscribed laws
  E3.6 — law_text is present and non-empty
  E3.7 — inscription_receipt_id is set after inscribe()
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.epoch2.sigma_gate import SigmaGate, SigmaResult
from helen_os.epoch2.law_ledger import LawLedger, LawV1


def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


def make_passed_sigma(km) -> SigmaResult:
    """Return a SigmaResult that passes (closure_success=True)."""
    return SigmaGate.run(
        hypothesis="closure_success == True (law ledger test)",
        metric_fn=lambda m: float(m.closure_success),
        metric_name="closure_success",
        threshold=1.0,
        kernel=km,
        seed_set=[42],
    )


def make_failed_sigma(km) -> SigmaResult:
    """Return a SigmaResult that fails (impossible threshold)."""
    return SigmaGate.run(
        hypothesis="dispute_heat == 0 (always fails)",
        metric_fn=lambda m: 0.0 if m.dispute_heat > 0.0 else 1.0,
        metric_name="zero_dispute_heat",
        threshold=1.0,
        kernel=km,
        seed_set=[42],
    )


# ── E3.1 — inscribe returns Receipt ──────────────────────────────────────────

def test_e3_inscribe_returns_receipt():
    """E3.1 — inscribe() on a passed SigmaResult returns Receipt with R-prefix."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    sigma = make_passed_sigma(km)

    assert sigma.passed, "Fixture sigma result must pass"
    receipt = law_ledger.inscribe(sigma, law_text="Test law: closure is achievable")

    assert receipt.id.startswith("R-"), f"Receipt id should start with R-: {receipt.id}"
    assert len(receipt.cum_hash) == 64
    print(f"✅ E3.1: inscribe() returned receipt {receipt.id}")


# ── E3.2 — inscribe raises on failed sigma ────────────────────────────────────

def test_e3_inscribe_raises_on_failed_sigma():
    """E3.2 — inscribe() on a FAILED SigmaResult raises ValueError."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    failed_sigma = make_failed_sigma(km)

    assert not failed_sigma.passed, "Fixture sigma result must fail"
    with pytest.raises(ValueError, match="Cannot inscribe a failed sigma result"):
        law_ledger.inscribe(failed_sigma, law_text="Should not be inscribed")

    print("✅ E3.2: inscribe() raises ValueError on failed sigma result")


# ── E3.3 — LAW_V1 payload fields ─────────────────────────────────────────────

def test_e3_law_v1_payload_fields():
    """E3.3 — to_ledger_payload() has all required LAW_V1 fields."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    sigma = make_passed_sigma(km)
    law_ledger.inscribe(sigma, law_text="Closure is achievable under standard conditions")

    laws = law_ledger.list_laws()
    assert len(laws) == 1
    payload = laws[0].to_ledger_payload()

    required = [
        "type", "hypothesis", "law_text", "metric",
        "seed_set", "adversarial_gates_passed",
        "evidence_hashes", "inscribed_at", "inscription_receipt_id",
    ]
    for f in required:
        assert f in payload, f"Missing LAW_V1 field: {f!r}"
    assert payload["type"] == "LAW_V1"
    print(f"✅ E3.3: LAW_V1 payload has all required fields")


# ── E3.4 — evidence_hashes non-empty ─────────────────────────────────────────

def test_e3_evidence_hashes_non_empty():
    """E3.4 — evidence_hashes must contain at least one receipt ID."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    sigma = make_passed_sigma(km)
    law_ledger.inscribe(sigma, law_text="Test: evidence hashes")

    laws = law_ledger.list_laws()
    payload = laws[0].to_ledger_payload()

    assert len(payload["evidence_hashes"]) >= 1, "evidence_hashes must not be empty"
    for rid in payload["evidence_hashes"]:
        assert rid.startswith("R-"), f"evidence_hash should be R-prefix: {rid!r}"
    print(f"✅ E3.4: evidence_hashes = {payload['evidence_hashes']}")


# ── E3.5 — list_laws() returns inscribed laws ────────────────────────────────

def test_e3_list_laws():
    """E3.5 — list_laws() returns all inscribed laws."""
    km = make_kernel()
    law_ledger = LawLedger(km)

    sigma1 = SigmaGate.run(
        hypothesis="H1: admissibility",
        metric_fn=lambda m: m.admissibility_rate,
        metric_name="admissibility_rate",
        threshold=0.80,
        kernel=km, seed_set=[42],
    )
    sigma2 = SigmaGate.run(
        hypothesis="H2: closure",
        metric_fn=lambda m: float(m.closure_success),
        metric_name="closure_success",
        threshold=1.0,
        kernel=km, seed_set=[42],
    )

    if sigma1.passed:
        law_ledger.inscribe(sigma1, law_text="Admissibility is high")
    if sigma2.passed:
        law_ledger.inscribe(sigma2, law_text="Closure is achievable")

    laws = law_ledger.list_laws()
    expected = sum(1 for s in [sigma1, sigma2] if s.passed)
    assert len(laws) == expected, f"Expected {expected} laws, got {len(laws)}"
    for law in laws:
        assert isinstance(law, LawV1)
    print(f"✅ E3.5: list_laws() returned {len(laws)} law(s)")


# ── E3.6 — law_text is non-empty ─────────────────────────────────────────────

def test_e3_law_text_non_empty():
    """E3.6 — law_text is present and non-empty in inscribed laws."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    sigma = make_passed_sigma(km)
    law_text = "LAW: Closure is structurally achievable in 20-tick runs."
    law_ledger.inscribe(sigma, law_text=law_text)

    laws = law_ledger.list_laws()
    assert laws[0].law_text == law_text
    assert len(laws[0].law_text) > 10
    print(f"✅ E3.6: law_text = {laws[0].law_text!r}")


# ── E3.7 — inscription_receipt_id is set ─────────────────────────────────────

def test_e3_inscription_receipt_id():
    """E3.7 — inscription_receipt_id is set on the law after inscribe()."""
    km = make_kernel()
    law_ledger = LawLedger(km)
    sigma = make_passed_sigma(km)
    receipt = law_ledger.inscribe(sigma, law_text="Test receipt id")

    laws = law_ledger.list_laws()
    assert laws[0].inscription_receipt_id is not None
    assert laws[0].inscription_receipt_id == receipt.id
    assert laws[0].inscription_receipt_id.startswith("R-")
    print(f"✅ E3.7: inscription_receipt_id = {laws[0].inscription_receipt_id}")
