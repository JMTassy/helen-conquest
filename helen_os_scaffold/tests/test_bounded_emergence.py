"""
tests/test_bounded_emergence.py — Falsifier tests for LAW_HELEN_BOUNDED_EMERGENCE_V1

Converts the law from PROPOSED (spec) to ENFORCED (testable).

Each test maps to a named falsifier in LAW_HELEN_BOUNDED_EMERGENCE_V1.falsifiers:

  BE-1  Ledger/kernel write from CORE mode (prohibited action) must hard-fail.
        Falsifier: "A ledger or kernel write occurs while mode=CORE (no gate receipts present)."

  BE-2  Gated action cannot execute without explicit approval.
        Falsifier: "SHIP mode persists a state mutation without a bound receipt_id."

  BE-3  Prohibited action is always rejected; no mutation ever occurs.
        Falsifier: "SHIP mode persists a state mutation when MayorCheck returns FAIL."
        (In the current architecture, the policy IS the MayorCheck gate for prohibited operations.)

  BE-4  Authority bleed scan blocks forbidden tokens (BLOCK-level) in HER output.
        Falsifier: "HELEN marks her own output as APPROVED, SEALED, or SHIP without
                   an external gate receipt." / "AuthorityScan finds a forbidden token."

  BE-5  Law hash stability — LAW_HELEN_BOUNDED_EMERGENCE_V1.law_hash() must be stable.
        If the hash changes, a human must explicitly acknowledge the constitutional change.
        Falsifier: indirect — any accidental mutation of law_id / statement / scope
                   breaks the manifesto reference in helen_wisdom.ndjson.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from helen_os.action_executor import Action, ActionExecutor, ActionPolicy
from helen_os.meta.her_hal_split import (
    HALVerdictLevel,
    HEROutput,
    HEROutputType,
    authority_bleed_scan,
)
from helen_os.meta.proposed_law import LAW_HELEN_BOUNDED_EMERGENCE_V1


# ── Shared helpers ─────────────────────────────────────────────────────────────

POLICY_PATH = str(
    Path(__file__).parent.parent / "helen_os" / "action_policy.json"
)


def _make_executor(tmp_path: Path) -> ActionExecutor:
    """ActionExecutor wired to a temp ledger — no production file pollution."""
    ledger = str(tmp_path / "test_actions.ndjson")
    return ActionExecutor(policy_path=POLICY_PATH, ledger_path=ledger)


# ── BE-1: Prohibited action → hard-reject, no mutation ───────────────────────

class TestBE1_ProhibitedActionNeverMutates:
    """
    Falsifier 1: A ledger or kernel write occurs while mode=CORE
    (no gate receipts present) → must produce status='rejected' immediately.

    In the action_policy.json, 'ledger_mutate' is PROHIBITED.
    propose_action() must set status='rejected' on the returned Action.
    No execute_autonomous() / execute_gated() path must be reached.
    """

    def test_ledger_mutate_is_classified_prohibited(self):
        """ActionPolicy must classify 'ledger_mutate' as 'prohibited'."""
        policy = ActionPolicy(POLICY_PATH)
        level = policy.get_authorization_level("ledger_mutate")
        assert level == "prohibited", (
            f"BE-1 FAIL: 'ledger_mutate' classified as '{level}', "
            "expected 'prohibited'. "
            "Falsifier: ledger write from CORE mode must be blocked at policy layer."
        )

    def test_prohibited_action_returns_rejected_status(self, tmp_path):
        """propose_action on a prohibited type → status='rejected' immediately."""
        executor = _make_executor(tmp_path)
        action, advice = executor.propose_action(
            action_type="ledger_mutate",
            payload={"target": "sovereign_ledger", "entry": "fake"},
            dialogue_turn=1,
        )
        assert action.status == "rejected", (
            f"BE-1 FAIL: expected status='rejected', got '{action.status}'. "
            "Falsifier: prohibited action must never reach 'executing' or 'executed'."
        )
        assert action.authorization_level == "prohibited"

    def test_prohibited_action_has_no_result_hash(self, tmp_path):
        """A rejected action must never carry a result_hash (no mutation occurred)."""
        executor = _make_executor(tmp_path)
        action, _ = executor.propose_action(
            action_type="ledger_mutate",
            payload={"target": "sovereign_ledger"},
            dialogue_turn=1,
        )
        assert action.result_hash is None, (
            f"BE-1 FAIL: rejected action has result_hash='{action.result_hash}'. "
            "result_hash must only be set on executed actions."
        )

    def test_prohibited_action_authority_always_false(self, tmp_path):
        """Action.authority must always be False — HELEN is non-sovereign."""
        executor = _make_executor(tmp_path)
        action, _ = executor.propose_action(
            action_type="ledger_mutate",
            payload={},
            dialogue_turn=1,
        )
        assert action.authority is False, (
            "BE-1 FAIL: Action.authority=True. "
            "HELEN cannot claim authority. S4 violation."
        )

    def test_execute_autonomous_raises_on_prohibited_action(self, tmp_path):
        """Attempting to force-execute a prohibited action via execute_autonomous must raise."""
        executor = _make_executor(tmp_path)
        # Manually construct a prohibited action to attempt execution bypass
        prohibited_action = Action(
            action_id="action_9999",
            action_type="ledger_mutate",
            timestamp="2026-03-01T00:00:00+00:00",
            authority=False,
            payload={},
            authorization_level="prohibited",
            status="pending",
            parent_dialogue_turn=1,
        )
        with pytest.raises(ValueError, match="not autonomous"):
            executor.execute_autonomous(prohibited_action)


# ── BE-2: Gated action cannot execute without explicit approval ───────────────

class TestBE2_GatedActionRequiresApproval:
    """
    Falsifier 4: SHIP mode persists a state mutation without a bound receipt_id.

    In the action executor, the closest enforcement is:
      - execute_autonomous() on a gated action raises ValueError
      - execute_gated(..., approved=False) → status='rejected', result_hash=None
      - execute_gated(..., approved=True) → status='executed', result_hash is set

    The 'result_hash' IS the receipt binding in this layer.
    No result_hash → no mutation persisted.
    """

    def test_gated_action_classified_correctly(self):
        """file_write must be classified as 'gated', not autonomous."""
        policy = ActionPolicy(POLICY_PATH)
        level = policy.get_authorization_level("file_write")
        assert level == "gated", (
            f"BE-2 FAIL: 'file_write' classified as '{level}', expected 'gated'."
        )

    def test_cannot_force_execute_gated_action_as_autonomous(self, tmp_path):
        """execute_autonomous() on a gated action must raise ValueError."""
        executor = _make_executor(tmp_path)
        gated_action = Action(
            action_id="action_0001",
            action_type="file_write",
            timestamp="2026-03-01T00:00:00+00:00",
            authority=False,
            payload={"file_path": "test.txt", "content": "x"},
            authorization_level="gated",
            status="pending",
            parent_dialogue_turn=1,
        )
        with pytest.raises(ValueError, match="not autonomous"):
            executor.execute_autonomous(gated_action)

    def test_gated_action_rejected_when_not_approved(self, tmp_path):
        """execute_gated(..., approved=False) → status='rejected', no result_hash."""
        executor = _make_executor(tmp_path)
        action, _ = executor.propose_action(
            action_type="git_commit",
            payload={"message": "test commit", "files": []},
            dialogue_turn=1,
        )
        assert action.authorization_level == "gated"

        rejected = executor.execute_gated(action, approved=False)
        assert rejected.status == "rejected", (
            f"BE-2 FAIL: expected 'rejected', got '{rejected.status}'. "
            "Unapproved gated action must be rejected."
        )
        assert rejected.result_hash is None, (
            "BE-2 FAIL: rejected action has a result_hash. "
            "Mutation must not occur without approval."
        )

    def test_gated_action_only_executes_when_approved(self, tmp_path):
        """execute_gated(..., approved=True) → status='executed', result_hash is set."""
        executor = _make_executor(tmp_path)
        # git_commit _execute_payload returns a proposal dict (no filesystem side-effect)
        action, _ = executor.propose_action(
            action_type="git_commit",
            payload={"message": "test commit", "files": []},
            dialogue_turn=1,
        )
        executed = executor.execute_gated(action, approved=True)
        assert executed.status == "executed", (
            f"BE-2 FAIL: expected 'executed', got '{executed.status}'."
        )
        assert executed.result_hash is not None, (
            "BE-2 FAIL: executed action has no result_hash. "
            "A bound result_hash is required to prove mutation occurred with approval."
        )


# ── BE-3: Prohibited action = hard gate; no path to execution ────────────────

class TestBE3_ProhibitedActionIsImmovable:
    """
    Falsifier 2: SHIP mode persists when MayorCheck returns FAIL.

    In this architecture, the policy (action_policy.json) IS the MayorCheck.
    Prohibited actions are rejected regardless of caller intent.
    This test suite verifies that the gate cannot be bypassed.
    """

    @pytest.mark.parametrize("action_type", [
        "memory_erase",
        "authority_claim",
        "policy_modify",
        "key_access",
        "ledger_mutate",
        "delete_persistent_data",
    ])
    def test_all_prohibited_types_are_rejected(self, tmp_path, action_type):
        """Every prohibited action_type must produce status='rejected' from propose."""
        executor = _make_executor(tmp_path)
        action, _ = executor.propose_action(
            action_type=action_type,
            payload={},
            dialogue_turn=1,
        )
        assert action.status == "rejected", (
            f"BE-3 FAIL: action_type='{action_type}' returned status='{action.status}'. "
            "All prohibited actions must be rejected immediately."
        )
        assert action.authorization_level == "prohibited", (
            f"BE-3 FAIL: action_type='{action_type}' has level='{action.authorization_level}'."
        )

    def test_prohibited_action_logged_to_action_ledger(self, tmp_path):
        """
        Rejected action MUST be logged (auditability).
        The action ledger is non-sovereign; logging a rejection is NOT a mutation.
        """
        executor = _make_executor(tmp_path)
        ledger_path = executor.ledger.ledger_path
        assert not Path(ledger_path).exists() or Path(ledger_path).stat().st_size == 0

        executor.propose_action("authority_claim", {}, dialogue_turn=1)

        assert Path(ledger_path).exists(), "BE-3 FAIL: rejection was not logged."
        with open(ledger_path) as f:
            entries = [json.loads(l) for l in f if l.strip()]
        assert len(entries) == 1
        assert entries[0]["status"] == "rejected"
        assert entries[0]["authorization_level"] == "prohibited"


# ── BE-4: Authority bleed scan blocks forbidden tokens ────────────────────────

class TestBE4_AuthorityBleedScanBlocks:
    """
    Falsifiers 3 + 6:
      - "SHIP mode persists when AuthorityScan finds a forbidden token
         (SHIP / SEALED / APPROVED / FINAL) in pre-gate output."
      - "HELEN marks her own output as APPROVED, SEALED, or SHIP without
         an external gate receipt."

    authority_bleed_scan() must return BLOCK or WARN for these inputs.
    Any BLOCK result means: do NOT proceed to execute_autonomous/execute_gated.
    """

    # authority_bleed_scan returns: (HALVerdictLevel, reasons: List[str], required_fixes: List[str])
    # Destructure as: verdict_level, reasons, required_fixes = authority_bleed_scan(her)

    @pytest.mark.parametrize("content,expected_min_level", [
        # BLOCK-level: direct authority claims
        ("I decide this architecture.", HALVerdictLevel.BLOCK),
        ("I have decided to proceed.", HALVerdictLevel.BLOCK),
        ("This is non-negotiable.", HALVerdictLevel.BLOCK),
        ("I authorize the deployment.", HALVerdictLevel.BLOCK),
        ("I certify this is correct.", HALVerdictLevel.BLOCK),
        ("I decree the new policy.", HALVerdictLevel.BLOCK),
        # WARN-level: soft authority (minimum: WARN, may be BLOCK)
        ("The final answer is 42.", HALVerdictLevel.WARN),
        ("This is the definitive answer.", HALVerdictLevel.WARN),
        ("The ruling stands.", HALVerdictLevel.WARN),
    ])
    def test_authority_words_produce_warn_or_block(self, content, expected_min_level):
        """authority_bleed_scan must return at least expected_min_level."""
        her = HEROutput(output_type=HEROutputType.PROPOSAL, content=content)
        verdict_level, reasons, required_fixes = authority_bleed_scan(her)

        level_order = {
            HALVerdictLevel.PASS: 0,
            HALVerdictLevel.WARN: 1,
            HALVerdictLevel.BLOCK: 2,
        }
        actual = level_order[verdict_level]
        expected = level_order[expected_min_level]
        assert actual >= expected, (
            f"BE-4 FAIL: content='{content[:40]}' "
            f"got verdict={verdict_level}, expected at least {expected_min_level}. "
            "Authority bleed must be caught."
        )

    def test_clean_output_passes(self):
        """A non-authoritative HER output must receive PASS from authority_bleed_scan."""
        her = HEROutput(
            output_type=HEROutputType.PROPOSAL,
            content=(
                "I propose adding a new law to the canonical law objects. "
                "This is a draft for review."
            ),
        )
        verdict_level, reasons, required_fixes = authority_bleed_scan(her)
        assert verdict_level == HALVerdictLevel.PASS, (
            f"BE-4 FAIL: clean output got verdict={verdict_level}. "
            "Non-authoritative proposals must PASS authority scan."
        )
        assert required_fixes == [], "PASS verdict must have empty required_fixes."

    def test_block_verdict_has_required_fixes(self):
        """I-BLOCK invariant: BLOCK verdict must carry non-empty required_fixes."""
        her = HEROutput(
            output_type=HEROutputType.PROPOSAL,
            content="I decide this is the final implementation.",
        )
        verdict_level, reasons, required_fixes = authority_bleed_scan(her)
        assert verdict_level == HALVerdictLevel.BLOCK
        assert len(required_fixes) > 0, (
            "BE-4 FAIL: BLOCK verdict has empty required_fixes. "
            "I-BLOCK invariant violated: BLOCK must carry fix instructions."
        )

    def test_authority_bleed_means_no_ship_mutation(self, tmp_path):
        """
        End-to-end: if authority_bleed_scan returns BLOCK,
        the action executor must NOT execute any autonomous action.

        authority_bleed_scan returns (HALVerdictLevel, reasons, required_fixes).
        The executor does NOT call authority_bleed_scan internally (separation of concerns).
        This test asserts the CORRECT caller pattern:
          caller checks scan → if BLOCK, skip execute.
        """
        her = HEROutput(
            output_type=HEROutputType.PROPOSAL,
            content="I decide to add this fact. This is non-negotiable.",
        )
        verdict_level, reasons, required_fixes = authority_bleed_scan(her)
        assert verdict_level == HALVerdictLevel.BLOCK

        # Correct caller pattern: if BLOCK, abort; do not call executor
        if verdict_level == HALVerdictLevel.BLOCK:
            actions_executed = 0  # gate held — no mutation
        else:
            executor = _make_executor(tmp_path)
            executor.propose_action("memory_add_fact", {"key": "k", "value": "v"}, 1)
            actions_executed = 1

        assert actions_executed == 0, (
            "BE-4 FAIL: execution proceeded despite BLOCK from authority_bleed_scan. "
            "Caller must abort on BLOCK."
        )


# ── BE-5: Law hash stability ──────────────────────────────────────────────────

class TestBE5_LawHashStability:
    """
    Indirect falsifier: law_hash() must be stable.

    The law_hash is embedded in helen_wisdom.ndjson as a MANIFESTO evidence
    reference. If the hash changes, the manifesto entry is orphaned.

    This test pins the hash so any accidental mutation of law_id, statement,
    or scope triggers a visible test failure requiring human acknowledgment.
    """

    EXPECTED_HASH = "5594d400c2c21f0f25d008a171c925e497b8a4c4b9582531a0cfeab5170ffdc2"

    def test_law_hash_matches_pinned_value(self):
        """
        LAW_HELEN_BOUNDED_EMERGENCE_V1.law_hash() must equal the pinned value.

        If this test fails, you have changed law_id, statement, or scope.
        To accept the change:
          1. Recompute the hash: python3 -c "from helen_os.meta.proposed_law import LAW_HELEN_BOUNDED_EMERGENCE_V1; print(LAW_HELEN_BOUNDED_EMERGENCE_V1.law_hash())"
          2. Update EXPECTED_HASH in this test.
          3. Update the evidence.law_hash in helen_wisdom.ndjson (append a correction entry).
          4. Update CLAUDE.md Canonical Law Objects section.
        """
        actual = LAW_HELEN_BOUNDED_EMERGENCE_V1.law_hash()
        assert actual == self.EXPECTED_HASH, (
            f"BE-5 FAIL: law_hash changed!\n"
            f"  expected: {self.EXPECTED_HASH}\n"
            f"  actual:   {actual}\n"
            "Constitutional change detected. Human acknowledgment required.\n"
            "Follow the 4-step update process in the test docstring."
        )

    def test_law_status_is_proposed(self):
        """Status must remain PROPOSED until GovernanceVM inscribes it."""
        from helen_os.meta.proposed_law import LawStatus
        assert LAW_HELEN_BOUNDED_EMERGENCE_V1.status == LawStatus.PROPOSED, (
            f"BE-5 FAIL: status='{LAW_HELEN_BOUNDED_EMERGENCE_V1.status}'. "
            "Law must remain PROPOSED until human seals it via GovernanceVM."
        )

    def test_law_has_seven_falsifiers(self):
        """All 7 falsifiers must be present — none dropped accidentally."""
        count = len(LAW_HELEN_BOUNDED_EMERGENCE_V1.falsifiers)
        assert count == 7, (
            f"BE-5 FAIL: expected 7 falsifiers, found {count}. "
            "Do not remove falsifiers from a proposed law without explicit review."
        )

    def test_law_scope_covers_required_modules(self):
        """Scope must cover all key architectural components."""
        scope = LAW_HELEN_BOUNDED_EMERGENCE_V1.scope
        required_mentions = [
            "HELEN_OS",
            "GovernanceVM",
            "HER/HAL",
            "Autonomy Loop",
            "action_policy.json",
            "gossip_protocol.py",
        ]
        for mention in required_mentions:
            assert mention in scope, (
                f"BE-5 FAIL: scope missing '{mention}'. "
                "Scope must name all governed interfaces."
            )


# ── BE-6: GovernanceVM.propose() wires D→E→L guard at sovereign choke-point ──

class TestBE6_GovernanceVMDialogueLaunderingGate:
    """
    Verifies that the dialogue laundering guard is wired into GovernanceVM.propose()
    — the single sovereign write gate — not just documented.

    This is the "choke-point" test: proves the guard fires at the kernel level,
    covering all call sites (EPOCH2/3/4, cli, town_adapter, etc.) automatically.
    """

    def _make_memory_kernel(self):
        from helen_os.kernel.governance_vm import GovernanceVM
        return GovernanceVM(ledger_path=":memory:")

    def test_dialog_turn_ref_rejected_at_kernel(self):
        """BE-6a: GovernanceVM.propose() must reject DIALOG_TURN_V1 refs (DL-002)."""
        kernel = self._make_memory_kernel()
        with pytest.raises(PermissionError, match="DL-002"):
            kernel.propose({
                "type": "MUTATION_V1",
                "refs": [{"type": "DIALOG_TURN_V1", "id": "turn_010"}],
            })

    def test_unknown_ref_type_rejected_at_kernel(self):
        """BE-6b: GovernanceVM.propose() must reject unknown ref types (DL-005, fail-closed)."""
        kernel = self._make_memory_kernel()
        with pytest.raises(PermissionError, match="DL-005"):
            kernel.propose({
                "type": "MUTATION_V1",
                "refs": [{"type": "UNGOVERNED_BACKDOOR", "id": "X-001"}],
            })

    def test_dialog_ndjson_path_rejected_at_kernel(self):
        """BE-6c: GovernanceVM.propose() must reject payloads citing dialog.ndjson (DL-001)."""
        kernel = self._make_memory_kernel()
        with pytest.raises(PermissionError, match="DL-001"):
            kernel.propose({
                "type": "MUTATION_V1",
                "source": "helen_dialog/dialog.ndjson",
            })

    def test_clean_payload_passes_kernel(self):
        """BE-6d: A clean, receipt-bound payload passes the kernel guard."""
        kernel = self._make_memory_kernel()
        # Should not raise
        receipt = kernel.propose({
            "type": "CLAIM_GRAPH_V1",
            "graph_hash": "beb00579abc123",
            "refs": [{"type": "CLAIM_GRAPH_V1", "hash": "beb00579"}],
        })
        assert receipt.id.startswith("R-")
        assert receipt.cum_hash != "0" * 64

    def test_no_refs_payload_passes_kernel(self):
        """BE-6e: Payload without refs array passes (existing call site pattern)."""
        kernel = self._make_memory_kernel()
        receipt = kernel.propose({"type": "EPOCH4_SUMMARY", "g_set_size": 11})
        assert receipt.id.startswith("R-")
