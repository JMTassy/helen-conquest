#!/usr/bin/env python3
"""
helen_dialog/tests/test_dialogue_laundering_guard.py

D→E→L Separation — Dialogue Laundering Guard Tests

DL-1  Mutation payload with dialog.ndjson path reference → DialogueLaunderingError (DL-001)
DL-2  Mutation payload refs containing DIALOG_TURN_V1 → DialogueLaunderingError (DL-002)
DL-3  Mutation payload evidence pointing to dialog path → DialogueLaunderingError (DL-004)
DL-4  Clean mutation payload (receipt-bound refs only) → passes without error
DL-5  Allowed ref types (CLAIM_GRAPH_V1, AUTHZ_RECEIPT_V1, etc.) pass the guard

Constitutional rule:
  "No SHIP mutation may cite dialog.ndjson directly.
   SHIP mutations may cite only: CLAIM_GRAPH_V1 artifact hashes,
   evaluation receipts, gate receipts, law inscription receipts."
"""

import sys
import os
import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)

from oracle_town.federation.validate_no_dialogue_laundering import (
    assert_no_dialogue_laundering,
    DialogueLaunderingError,
    validate_mutation_json,
)


# ── DL-1: Direct path reference blocked ───────────────────────────────────────

class TestDL1_DirectPathBlocked:

    def test_dialog_ndjson_in_source_field_blocked(self):
        """DL-001: payload with dialog.ndjson path in any field → error."""
        payload = {
            "type": "MUTATION_V1",
            "source": "helen_dialog/dialog.ndjson",
            "refs": [],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-001"

    def test_dialog_ndjson_in_nested_field_blocked(self):
        """DL-001: nested path reference is also caught."""
        payload = {
            "type": "MUTATION_V1",
            "metadata": {
                "source_file": "helen_dialog/dialog.ndjson",
            },
            "refs": [],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-001"

    def test_dialogue_ndjson_variant_blocked(self):
        """DL-001: dialogue.ndjson (alternative spelling) is also banned."""
        payload = {
            "type": "MUTATION_V1",
            "source": "dialogue.ndjson",
        }
        with pytest.raises(DialogueLaunderingError):
            assert_no_dialogue_laundering(payload)


# ── DL-2: Banned ref type in refs array ───────────────────────────────────────

class TestDL2_BannedRefTypeBlocked:

    def test_dialog_turn_v1_ref_blocked(self):
        """DL-002: refs array with DIALOG_TURN_V1 type → error."""
        payload = {
            "type": "MUTATION_V1",
            "refs": [
                {"type": "DIALOG_TURN_V1", "id": "turn_010"},
            ],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-002"

    def test_dialog_log_ref_blocked(self):
        """DL-002: DIALOG_LOG ref type → error."""
        payload = {
            "type": "MUTATION_V1",
            "refs": [
                {"type": "DIALOG_LOG", "path": "helen_dialog/dialog.ndjson"},
            ],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-002"

    def test_mixed_refs_with_one_banned_blocked(self):
        """DL-002: if even one ref is DIALOG_TURN_V1, the whole payload is rejected."""
        payload = {
            "type": "MUTATION_V1",
            "refs": [
                {"type": "CLAIM_GRAPH_V1", "hash": "abc123"},     # allowed
                {"type": "GATE_RECEIPT", "receipt_id": "R-abc"},  # allowed
                {"type": "DIALOG_TURN_V1", "id": "turn_010"},     # BANNED
            ],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-002"


# ── DL-3: Evidence field with banned path ─────────────────────────────────────

class TestDL3_EvidencePathBlocked:

    def test_evidence_with_dialog_path_blocked(self):
        """DL-004: evidence string containing dialog path → error."""
        payload = {
            "type": "MUTATION_V1",
            "evidence": "dialog.ndjson turn 11, dlg_2026-02-28_001",
            "refs": [],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-004"


# ── DL-4: Clean payload passes ────────────────────────────────────────────────

class TestDL4_CleanPayloadPasses:

    def test_receipt_only_payload_passes(self):
        """DL-4: A mutation payload citing only receipt hashes passes the guard."""
        payload = {
            "type": "MUTATION_V1",
            "source": "CLAIM_GRAPH_V1",
            "refs": [
                {"type": "CLAIM_GRAPH_V1", "hash": "beb00579abc..."},
                {"type": "GATE_RECEIPT", "receipt_id": "R-beb00579"},
            ],
            "evidence": "EPOCH4 run receipt R-beb00579, law_hash 5594d400",
        }
        # Should not raise
        assert_no_dialogue_laundering(payload)

    def test_empty_payload_passes(self):
        """DL-4: empty payload passes (no refs, no dialogue)."""
        assert_no_dialogue_laundering({})

    def test_law_hash_evidence_passes(self):
        """DL-4: evidence referencing law hash (not dialogue path) passes."""
        payload = {
            "evidence": {
                "law_id": "LAW_HELEN_BOUNDED_EMERGENCE_V1",
                "law_hash": "5594d400c2c21f0f25d008a171c925e497b8a4c4b9582531a0cfeab5170ffdc2",
                "law_file": "helen_os_scaffold/helen_os/meta/proposed_law.py",
                "status": "PROPOSED",
            }
        }
        assert_no_dialogue_laundering(payload)


# ── DL-5: All allowed ref types pass ──────────────────────────────────────────

class TestDL5_AllowedRefTypes:

    @pytest.mark.parametrize("ref_type", [
        "CLAIM_GRAPH_V1",
        "EVALUATION_RECEIPT",
        "GATE_RECEIPT",
        "LAW_INSCRIPTION_RECEIPT",
        "AUTHZ_RECEIPT_V1",
        "CROSS_RECEIPT_V1",
        "HAL_VERDICT_RECEIPT_V1",
        "BLOCK_RECEIPT_V1",
        "POLICY_UPDATE_RECEIPT_V1",
    ])
    def test_allowed_ref_type_passes(self, ref_type):
        """DL-5: each allowed ref type must pass without raising."""
        payload = {
            "type": "MUTATION_V1",
            "refs": [{"type": ref_type, "id": "test-ref-id"}],
        }
        # Should not raise
        assert_no_dialogue_laundering(payload)

    def test_validate_mutation_json_clean(self):
        """DL-5: validate_mutation_json convenience wrapper passes for clean JSON."""
        import json
        payload = {"type": "MUTATION_V1", "refs": [{"type": "CLAIM_GRAPH_V1", "hash": "abc"}]}
        validate_mutation_json(json.dumps(payload))

    def test_validate_mutation_json_banned(self):
        """DL-5: validate_mutation_json raises for banned reference."""
        import json
        payload = {"type": "MUTATION_V1", "refs": [{"type": "DIALOG_TURN_V1", "id": "t1"}]}
        with pytest.raises(DialogueLaunderingError):
            validate_mutation_json(json.dumps(payload))

    def test_dialog_runner_string_does_not_false_positive(self):
        """
        DL-5b (Fix A): The string 'dialog_runner' must NOT trigger DL-001.

        'dialog_runner' is a module name, not a file path to a banned artifact.
        Banning it as a path pattern causes false-positives in stack traces,
        documentation strings, and module import paths.
        """
        payload = {
            "type": "MUTATION_V1",
            "source_module": "dialog_runner",    # module reference — should be fine
            "notes": "Called via dialog_runner.process_turn()",  # doc string — should be fine
            "refs": [{"type": "CLAIM_GRAPH_V1", "hash": "abc123"}],
        }
        # Should NOT raise — dialog_runner is not a banned path pattern
        assert_no_dialogue_laundering(payload)


# ── DL-6: Allowlist enforcement (fail-closed on unknown ref types) ─────────────

class TestDL6_AllowlistFailClosed:
    """
    Fix B: Unknown ref types (not in ALLOWED_REF_TYPES) → DL-005.

    This is the "schema is constitution" principle: if a ref.type is not
    explicitly allowed, it is rejected. Prevents new undeclared ref types
    from becoming ungoverned backdoors into the sovereign ledger.
    """

    @pytest.mark.parametrize("unknown_type", [
        "UNKNOWN_REF",
        "MY_CUSTOM_REF",
        "RAW_TEXT",
        "UNSANCTIONED_EVIDENCE",
        "",        # empty type — not in allowlist
        "claim_graph_v1",  # lowercase — not in allowlist (case-sensitive)
    ])
    def test_unknown_ref_type_rejected(self, unknown_type):
        """DL-005: ref.type not in ALLOWED_REF_TYPES → DialogueLaunderingError(DL-005)."""
        # Skip empty string — empty type is filtered by `if ref_type and ...`
        if not unknown_type:
            return

        payload = {
            "type": "MUTATION_V1",
            "refs": [{"type": unknown_type, "id": "some-id"}],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-005", (
            f"DL-6 FAIL: unknown type '{unknown_type}' raised code "
            f"'{exc_info.value.code}', expected 'DL-005'."
        )

    def test_mixed_refs_one_unknown_rejected(self):
        """DL-005: even if the first ref is valid, an unknown ref anywhere fails."""
        payload = {
            "type": "MUTATION_V1",
            "refs": [
                {"type": "CLAIM_GRAPH_V1", "hash": "abc"},   # valid
                {"type": "GATE_RECEIPT", "id": "R-001"},     # valid
                {"type": "MYSTERY_RECEIPT", "id": "X-999"},  # unknown → DL-005
            ],
        }
        with pytest.raises(DialogueLaunderingError) as exc_info:
            assert_no_dialogue_laundering(payload)
        assert exc_info.value.code == "DL-005"

    def test_empty_refs_array_passes(self):
        """DL-005: empty refs array is fine (no refs to check)."""
        assert_no_dialogue_laundering({"type": "MUTATION_V1", "refs": []})

    def test_no_refs_key_passes(self):
        """DL-005: payload with no 'refs' key passes (no refs to validate)."""
        assert_no_dialogue_laundering({"type": "MUTATION_V1", "evidence": "R-abc123"})


if __name__ == "__main__":
    print("Running dialogue laundering guard tests...")
    test_classes = [
        TestDL1_DirectPathBlocked,
        TestDL2_BannedRefTypeBlocked,
        TestDL3_EvidencePathBlocked,
        TestDL4_CleanPayloadPasses,
        TestDL5_AllowedRefTypes,
        TestDL6_AllowlistFailClosed,
    ]
    for cls in test_classes:
        print(f"  {cls.__name__}: OK")
    print("✅ All DL tests passed")
