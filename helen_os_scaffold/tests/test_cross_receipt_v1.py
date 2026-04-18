"""
tests/test_cross_receipt_v1.py — CROSS_RECEIPT_V1 tests (CR1–CR5)

CR1 — Schema construction + hard invariants
CR2 — Allowlist validation (validate_cross_receipt_allowlist)
CR3 — validate_receipt_linkage integration (L-CROSS + L-NOSELF + L-BUNDLE)
CR4 — Canonical properties + bundle_hash helper
CR5 — verify_all.py checks (non-sovereign audit tool)
"""

import hashlib
import json
import sys
import os

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.meta.cross_receipt_v1 import (
    CrossReceiptV1,
    CrossReceiptBundleRef,
    CrossReceiptBindingError,
    validate_cross_receipt_allowlist,
    cross_receipt_bundle_hash,
)
from helen_os.meta.authz_receipt import AuthzReceiptV1, AuthzReceiptRef
from helen_os.town.validate import (
    validate_receipt_linkage,
    ReceiptLinkageReport,
    ReceiptLinkageError,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _h(seed: str) -> str:
    """Deterministic 64-char SHA256 hex for test data."""
    return hashlib.sha256(seed.encode()).hexdigest()


def _valid_cr(
    rid="CR-test01",
    source="TOWN_A",
    target="TOWN_B",
    tip_seed="ledger_tip",
    bundle_seed="bundle_artifact",
    status="PENDING",
) -> CrossReceiptV1:
    return CrossReceiptV1(
        rid             = rid,
        source_town_id  = source,
        target_town_id  = target,
        ledger_tip_hash = _h(tip_seed),
        bundle_hash     = _h(bundle_seed),
        status          = status,
    )


# ════════════════════════════════════════════════════════════════════════════════
# CR1 — Schema construction + hard invariants
# ════════════════════════════════════════════════════════════════════════════════

class TestCR1_SchemaConstruction:
    """CR1.1–CR1.6: Valid construction + each hard invariant enforced."""

    def test_cr1_1_valid_construction(self):
        """CR1.1: Valid CROSS_RECEIPT_V1 constructs without error."""
        cr = _valid_cr()
        assert cr.type            == "CROSS_RECEIPT_V1"
        assert cr.rid             == "CR-test01"
        assert cr.source_town_id  == "TOWN_A"
        assert cr.target_town_id  == "TOWN_B"
        assert cr.status          == "PENDING"
        assert len(cr.ledger_tip_hash) == 64
        assert len(cr.bundle_hash)     == 64

    def test_cr1_2_self_federation_rejected(self):
        """CR1.2: source_town_id == target_town_id raises ValidationError (CR-SELF)."""
        with pytest.raises(ValidationError) as exc_info:
            CrossReceiptV1(
                rid             = "CR-self01",
                source_town_id  = "TOWN_X",
                target_town_id  = "TOWN_X",
                ledger_tip_hash = _h("tip"),
                bundle_hash     = _h("bundle"),
            )
        assert "Self-federation" in str(exc_info.value) or "CR-SELF" in str(exc_info.value)

    def test_cr1_3_bad_rid_prefix_rejected(self):
        """CR1.3: rid not starting with 'CR-' raises ValidationError."""
        with pytest.raises(ValidationError):
            CrossReceiptV1(
                rid             = "R-not-cr",
                source_town_id  = "TOWN_A",
                target_town_id  = "TOWN_B",
                ledger_tip_hash = _h("tip"),
                bundle_hash     = _h("bundle"),
            )

    def test_cr1_4_bad_ledger_tip_hash_rejected(self):
        """CR1.4: ledger_tip_hash < 64 hex chars raises ValidationError."""
        with pytest.raises(ValidationError):
            CrossReceiptV1(
                rid             = "CR-bad01",
                source_town_id  = "TOWN_A",
                target_town_id  = "TOWN_B",
                ledger_tip_hash = "abc123",  # too short
                bundle_hash     = _h("bundle"),
            )

    def test_cr1_5_bad_bundle_hash_rejected(self):
        """CR1.5: bundle_hash with non-hex chars raises ValidationError."""
        with pytest.raises(ValidationError):
            CrossReceiptV1(
                rid             = "CR-bad02",
                source_town_id  = "TOWN_A",
                target_town_id  = "TOWN_B",
                ledger_tip_hash = _h("tip"),
                bundle_hash     = "g" * 64,  # 'g' is not hex
            )

    def test_cr1_6_invalid_status_rejected(self):
        """CR1.6: status outside allowed enum raises ValidationError."""
        with pytest.raises(ValidationError):
            CrossReceiptV1(
                rid             = "CR-bad03",
                source_town_id  = "TOWN_A",
                target_town_id  = "TOWN_B",
                ledger_tip_hash = _h("tip"),
                bundle_hash     = _h("bundle"),
                status          = "UNKNOWN_STATUS",  # not in enum
            )


# ════════════════════════════════════════════════════════════════════════════════
# CR2 — Allowlist validation
# ════════════════════════════════════════════════════════════════════════════════

class TestCR2_AllowlistValidation:
    """CR2.1–CR2.5: validate_cross_receipt_allowlist behaviour."""

    def setup_method(self):
        self.cr = _valid_cr(source="TOWN_A", target="TOWN_B")

    def test_cr2_1_source_in_allowlist_passes(self):
        """CR2.1: source_town_id in allowlist → no exception."""
        validate_cross_receipt_allowlist(self.cr, ["TOWN_A", "TOWN_C"])

    def test_cr2_2_source_not_in_allowlist_fails(self):
        """CR2.2: source_town_id absent from allowlist → CrossReceiptBindingError."""
        with pytest.raises(CrossReceiptBindingError):
            validate_cross_receipt_allowlist(self.cr, ["TOWN_C", "TOWN_D"])

    def test_cr2_3_empty_allowlist_fails(self):
        """CR2.3: empty allowlist → CrossReceiptBindingError (no towns permitted)."""
        with pytest.raises(CrossReceiptBindingError):
            validate_cross_receipt_allowlist(self.cr, [])

    def test_cr2_4_single_element_allowlist_passes(self):
        """CR2.4: allowlist with exactly source_town_id → passes."""
        validate_cross_receipt_allowlist(self.cr, ["TOWN_A"])

    def test_cr2_5_error_message_contains_town_id(self):
        """CR2.5: error message names the source_town_id for auditability."""
        with pytest.raises(CrossReceiptBindingError) as exc_info:
            validate_cross_receipt_allowlist(self.cr, ["TOWN_Z"])
        assert "TOWN_A" in str(exc_info.value)


# ════════════════════════════════════════════════════════════════════════════════
# CR3 — validate_receipt_linkage integration
# ════════════════════════════════════════════════════════════════════════════════

class TestCR3_ReceiptLinkage:
    """CR3.1–CR3.6: validate_receipt_linkage with CROSS_RECEIPT_V1."""

    def _authz(self, vh: str, vid: str) -> AuthzReceiptV1:
        return AuthzReceiptV1(
            rid          = "R-cr3-01",
            refs         = AuthzReceiptRef(verdict_id=vid, verdict_hash_hex=vh),
            authorizes   = {"field": "ReducedConclusion.helen_proposal_used", "value": True},
            reason_codes = ["CANYON_AUTHORIZED"],
        )

    def test_cr3_1_all_checks_pass(self):
        """CR3.1: Valid cross_receipt + allowlist → report.all_pass=True."""
        cr = _valid_cr()
        report = validate_receipt_linkage(
            cross_receipt = cr,
            allowlist     = ["TOWN_A"],
        )
        assert report.all_pass, report.summary()
        assert report.checks["L-CROSS"]["pass"]
        assert report.checks["L-NOSELF"]["pass"]

    def test_cr3_2_wrong_allowlist_fails_l_cross(self):
        """CR3.2: source_town_id not in allowlist → L-CROSS fails."""
        cr = _valid_cr()
        report = validate_receipt_linkage(
            cross_receipt = cr,
            allowlist     = ["TOWN_Z"],
        )
        assert not report.all_pass
        assert not report.checks["L-CROSS"]["pass"]

    def test_cr3_3_no_cross_receipt_skips_l_cross(self):
        """CR3.3: No cross_receipt → L-CROSS + L-NOSELF are not-applicable (pass)."""
        vh  = _h("cr3_verdict")
        vid = f"V-{vh[:8]}"
        authz = self._authz(vh, vid)

        report = validate_receipt_linkage(
            authz_receipt    = authz,
            verdict_id       = vid,
            verdict_hash_hex = vh,
        )
        assert report.all_pass, report.summary()
        assert report.checks["L-CROSS"]["pass"]

    def test_cr3_4_bundle_ref_mismatch_fails_l_bundle(self):
        """CR3.4: bundle_ref.verdict_hash_hex != reduced_conclusion.verdict_hash_hex → L-BUNDLE fails."""
        vh_real  = _h("cr3_verdict_real")
        vh_wrong = _h("cr3_verdict_wrong")
        vid = f"V-{vh_real[:8]}"

        cr = CrossReceiptV1(
            rid             = "CR-cr3-04",
            source_town_id  = "TOWN_A",
            target_town_id  = "TOWN_B",
            ledger_tip_hash = _h("cr3_tip"),
            bundle_hash     = _h("cr3_bundle"),
            bundle_ref      = CrossReceiptBundleRef(verdict_hash_hex=vh_wrong),
        )

        # Duck-typed ReducedConclusion with the REAL verdict_hash_hex
        class FakeRC:
            verdict_hash_hex = vh_real

        report = validate_receipt_linkage(
            cross_receipt      = cr,
            allowlist          = ["TOWN_A"],
            reduced_conclusion = FakeRC(),
        )
        assert not report.all_pass
        assert not report.checks["L-BUNDLE"]["pass"]

    def test_cr3_5_bundle_ref_match_passes_l_bundle(self):
        """CR3.5: bundle_ref.verdict_hash_hex == reduced_conclusion.verdict_hash_hex → L-BUNDLE passes."""
        vh  = _h("cr3_verdict_match")
        vid = f"V-{vh[:8]}"

        cr = CrossReceiptV1(
            rid             = "CR-cr3-05",
            source_town_id  = "TOWN_A",
            target_town_id  = "TOWN_B",
            ledger_tip_hash = _h("cr3_tip2"),
            bundle_hash     = _h("cr3_bundle2"),
            bundle_ref      = CrossReceiptBundleRef(verdict_hash_hex=vh),
        )

        class FakeRC:
            verdict_hash_hex = vh

        report = validate_receipt_linkage(
            cross_receipt      = cr,
            allowlist          = ["TOWN_A"],
            reduced_conclusion = FakeRC(),
        )
        assert report.all_pass, report.summary()
        assert report.checks["L-BUNDLE"]["pass"]

    def test_cr3_6_raise_on_failure(self):
        """CR3.6: raise_on_failure=True raises ReceiptLinkageError on first fail."""
        cr = _valid_cr()
        with pytest.raises(ReceiptLinkageError):
            validate_receipt_linkage(
                cross_receipt   = cr,
                allowlist       = [],      # empty → L-CROSS fails
                raise_on_failure = True,
            )


# ════════════════════════════════════════════════════════════════════════════════
# CR4 — Canonical properties + bundle_hash helper
# ════════════════════════════════════════════════════════════════════════════════

class TestCR4_CanonicalProperties:
    """CR4.1–CR4.6: Determinism, state transitions, hash helper."""

    def test_cr4_1_pending_status_on_construction(self):
        """CR4.1: Default status is PENDING."""
        cr = _valid_cr()
        assert cr.status == "PENDING"

    def test_cr4_2_accepted_returns_accepted_copy(self):
        """CR4.2: cr.accepted() returns new receipt with status=ACCEPTED."""
        cr       = _valid_cr()
        accepted = cr.accepted(notes="passed allowlist check")
        assert accepted.status == "ACCEPTED"
        assert cr.status == "PENDING"     # original unchanged
        assert accepted.notes == "passed allowlist check"

    def test_cr4_3_rejected_returns_rejected_copy(self):
        """CR4.3: cr.rejected(reason) returns new receipt with status=REJECTED."""
        cr       = _valid_cr()
        rejected = cr.rejected("source not in allowlist")
        assert rejected.status == "REJECTED"
        assert cr.status == "PENDING"

    def test_cr4_4_cross_receipt_bundle_hash_deterministic(self):
        """CR4.4: cross_receipt_bundle_hash is deterministic — same payload → same hash."""
        payload = {"artifact": "FED_EVAL_V1", "quest_id": "Q1", "gates": {"pass": True}}
        h1 = cross_receipt_bundle_hash(payload)
        h2 = cross_receipt_bundle_hash(payload)
        assert h1 == h2
        assert len(h1) == 64
        assert all(c in "0123456789abcdef" for c in h1)

    def test_cr4_5_cross_receipt_bundle_hash_sensitive_to_content(self):
        """CR4.5: Different payload → different bundle_hash (not trivially equal)."""
        p1 = {"quest_id": "Q1"}
        p2 = {"quest_id": "Q2"}
        assert cross_receipt_bundle_hash(p1) != cross_receipt_bundle_hash(p2)

    def test_cr4_6_to_ledger_payload_contains_required_fields(self):
        """CR4.6: to_ledger_payload() returns dict with required fields for GovernanceVM."""
        cr = _valid_cr()
        payload = cr.to_ledger_payload()
        assert payload["type"]            == "CROSS_RECEIPT_V1"
        assert payload["rid"]             == cr.rid
        assert payload["source_town_id"]  == cr.source_town_id
        assert payload["target_town_id"]  == cr.target_town_id
        assert payload["ledger_tip_hash"] == cr.ledger_tip_hash
        assert payload["bundle_hash"]     == cr.bundle_hash
        assert payload["status"]          == "PENDING"


# ════════════════════════════════════════════════════════════════════════════════
# CR5 — verify_all.py integration (non-sovereign audit)
# ════════════════════════════════════════════════════════════════════════════════

class TestCR5_VerifyAll:
    """CR5.1–CR5.4: verify_all.py check functions work correctly."""

    def test_cr5_1_v2_cross_roundtrip_passes(self):
        """CR5.1: verify_all check_v2_cross_roundtrip() → PASS."""
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "verify_all",
            pathlib.Path(__file__).parent.parent / "verify_all.py"
        )
        va = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(va)

        status, note = va.check_v2_cross_roundtrip()
        assert status == "PASS", f"Expected PASS, got {status!r}: {note}"

    def test_cr5_2_v5_allowlist_passes(self):
        """CR5.2: verify_all check_v5_cross_allowlist() → PASS."""
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "verify_all",
            pathlib.Path(__file__).parent.parent / "verify_all.py"
        )
        va = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(va)

        status, note = va.check_v5_cross_allowlist()
        assert status == "PASS", f"Expected PASS, got {status!r}: {note}"

    def test_cr5_3_v6_linkage_passes(self):
        """CR5.3: verify_all check_v6_receipt_linkage() → PASS."""
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "verify_all",
            pathlib.Path(__file__).parent.parent / "verify_all.py"
        )
        va = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(va)

        status, note = va.check_v6_receipt_linkage()
        assert status == "PASS", f"Expected PASS, got {status!r}: {note}"

    def test_cr5_4_v8_json_schemas_pass(self):
        """CR5.4: verify_all check_v8_json_schemas() → PASS (all schemas valid JSON + $schema + $id)."""
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "verify_all",
            pathlib.Path(__file__).parent.parent / "verify_all.py"
        )
        va = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(va)

        status, note = va.check_v8_json_schemas()
        assert status in ("PASS", "SKIP"), f"Expected PASS/SKIP, got {status!r}: {note}"
        if status == "PASS":
            # Must cover both new schemas
            assert "authz_receipt_v1.schema.json" in note
            assert "cross_receipt_v1.schema.json" in note
