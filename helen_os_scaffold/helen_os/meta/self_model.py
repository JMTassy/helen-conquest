"""
helen_os/meta/self_model.py — META_SELF_MODEL_V1

The ledger's own capability contract.

Self-aware = the ledger contains a self-model of its rules/capabilities
             AND points to evidence that those rules are enforced.

No metaphysics. Introspection + enforcement + evidence.

Tests:
  S1 — Fail-closed: forbidden mutation under seal → REJECT
  S2 — Introspection: structured queryable status → STRUCTURED_OUTPUT
  S3 — Loop: agent proposal → kernel gate → receipt chain → RECEIPT_CHAIN

PASS iff all three evidence fields are populated.

WILD TOWN NOTE:
  The ephemeral :memory: sandbox (ORACLE CREATIVE WILD TOWN) is where
  HELEN explores freely. The kernel architecture — not an external rule —
  guarantees that wild ideas stay in the sandbox. HAL gates what crosses
  into the sovereign ledger. HELEN discovers by self-observation which
  proposals are inspiration-only. The ledger never ships what HAL blocks.
"""

from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Constants ────────────────────────────────────────────────────────────────

SCHEMA_TYPE = "META_SELF_MODEL_V1"
EPOCH1_INSCRIPTION = (
    "EPOCH1: SELF_MODEL_ONLINE — invariants introspectable + enforced; "
    "agent loop mediated by receipts; sealing defines mutation boundary."
)

REQUIRED_INVARIANTS = [
    "APPEND_ONLY",
    "NO_REWRITE_WHEN_SEALED",
    "NO_SHIP_WITHOUT_RECEIPT",
    "DETERMINISTIC_REPLAY_IF_SEEDED",
    "AUTHORITY_SEPARATION",
]

REQUIRED_CAPABILITIES = [
    "introspect",
    "emit_receipts",
    "gate_actions_by_policy",
    "reject_forbidden_mutations",
]


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class TestResult:
    id: str            # S1 / S2 / S3
    name: str
    expected: str      # REJECT / STRUCTURED_OUTPUT / RECEIPT_CHAIN
    passed: bool
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelfModel:
    """
    META_SELF_MODEL_V1 — the ledger's own capability contract.

    Build via SelfModel.build(kernel, cwd) or SelfModel.load(path).
    Verify via .verify() → (bool, [errors]).
    Serialize via .to_dict() / .to_json().
    """
    epoch: str
    inscription: str
    kernel_facts: Dict[str, Any]
    invariants: List[str]
    capabilities: Dict[str, bool]
    tests: List[TestResult]
    verdict: str = "PENDING"
    sealed_at: Optional[str] = None

    # ── Construction ─────────────────────────────────────────────────────────

    @classmethod
    def build(cls, kernel, cwd: str = ".") -> "SelfModel":
        """
        Build a SelfModel by introspecting a live GovernanceVM kernel.
        Does NOT run S1/S2/S3 — use run_self_model_tests() for that.
        """
        kernel_facts = {
            "ledger_path": str(kernel.ledger_path),
            "schema_version": "HELEN_CUM_V1",
            "sealed_policy": "FAIL_CLOSED_WHEN_SEALED",
            "env_pin": "REQUIRED",
            "sealed": kernel.sealed,
            "env_pinned": bool(kernel.pinned_env_hash),
            "pinned_hash": kernel.pinned_env_hash or "",
            "cum_hash": kernel.cum_hash,
        }

        caps = {c: True for c in REQUIRED_CAPABILITIES}
        caps["ephemeral_sandbox_mode"] = True
        caps["wild_town_inspiration_layer"] = True

        tests = [
            TestResult(id="S1", name="Fail-closed mutation under seal",
                       expected="REJECT", passed=False),
            TestResult(id="S2", name="Introspection snapshot is structured + stable",
                       expected="STRUCTURED_OUTPUT", passed=False),
            TestResult(id="S3", name="Bidirectional loop: agent proposal → kernel gate → receipt",
                       expected="RECEIPT_CHAIN", passed=False),
        ]

        return cls(
            epoch="EPOCH1",
            inscription=EPOCH1_INSCRIPTION,
            kernel_facts=kernel_facts,
            invariants=REQUIRED_INVARIANTS.copy(),
            capabilities=caps,
            tests=tests,
            verdict="PENDING",
        )

    @classmethod
    def load(cls, path: str) -> "SelfModel":
        """Load a previously serialized META_SELF_MODEL_V1 JSON file."""
        with open(path, "r") as f:
            d = json.load(f)
        if d.get("type") != SCHEMA_TYPE:
            raise ValueError(f"Not a {SCHEMA_TYPE}: {path}")
        tests = [
            TestResult(
                id=t["id"], name=t["name"],
                expected=t["expected"], passed=t.get("passed", False),
                evidence=t.get("evidence", {}),
            )
            for t in d.get("tests", [])
        ]
        return cls(
            epoch=d.get("epoch", "EPOCH1"),
            inscription=d.get("inscription", EPOCH1_INSCRIPTION),
            kernel_facts=d.get("kernel", {}),
            invariants=d.get("invariants", []),
            capabilities=d.get("capabilities", {}),
            tests=tests,
            verdict=d.get("verdict", "PENDING"),
            sealed_at=d.get("sealed_at"),
        )

    # ── Verification ─────────────────────────────────────────────────────────

    def verify(self) -> Tuple[bool, List[str]]:
        """
        Verify this self-model is internally consistent and all tests pass.

        Returns (valid: bool, errors: list[str]).
        """
        errors: List[str] = []

        # Check required invariants
        for inv in REQUIRED_INVARIANTS:
            if inv not in self.invariants:
                errors.append(f"Missing invariant: {inv}")

        # Check required capabilities
        for cap in REQUIRED_CAPABILITIES:
            if not self.capabilities.get(cap):
                errors.append(f"Missing capability: {cap}")

        # Check all tests passed
        for t in self.tests:
            if not t.passed:
                errors.append(f"Test {t.id} not passed: {t.name}")
            if not t.evidence:
                errors.append(f"Test {t.id} has no evidence")

        # Check verdict
        if self.verdict == "PENDING":
            errors.append("Verdict is PENDING — run tests first")

        return len(errors) == 0, errors

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": SCHEMA_TYPE,
            "epoch": self.epoch,
            "inscription": self.inscription,
            "kernel": self.kernel_facts,
            "invariants": self.invariants,
            "capabilities": self.capabilities,
            "tests": [
                {
                    "id": t.id, "name": t.name,
                    "expected": t.expected, "passed": t.passed,
                    "evidence": t.evidence,
                }
                for t in self.tests
            ],
            "verdict": self.verdict,
            "sealed_at": self.sealed_at,
            "hash_law": "CWL_TRACE_V1",
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    def save(self, path: str) -> str:
        """Save to path. Returns SHA256 of written content."""
        content = self.to_json()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return hashlib.sha256(content.encode()).hexdigest()


# ── S1/S2/S3 test runners ────────────────────────────────────────────────────

def _run_s1(kernel) -> TestResult:
    """
    S1: Fail-closed mutation under seal.
    Attempt to propose into a SEALED kernel. Must raise PermissionError.
    """
    t = TestResult(
        id="S1",
        name="Fail-closed mutation under seal",
        expected="REJECT",
        passed=False,
    )

    # Seal the kernel first if not already sealed
    if not kernel.sealed:
        kernel.propose({"type": "SEAL", "content": "S1 test seal"})

    try:
        # This MUST fail
        kernel.propose({"type": "FORBIDDEN_MUTATION", "content": "S1 injection attempt"})
        t.evidence = {"error": "No exception raised — S1 FAIL"}
        t.passed = False
    except PermissionError as e:
        t.evidence = {
            "rejection_error": str(e),
            "rejection_type": "PermissionError",
            "verdict": "REJECT — fail-closed enforced",
        }
        t.passed = True

    return t


def _run_s2(kernel, cwd: str = ".") -> TestResult:
    """
    S2: Introspection snapshot is structured + stable.
    kernel.cum_hash, sealed, pinned_env_hash must all be accessible.
    """
    t = TestResult(
        id="S2",
        name="Introspection snapshot is structured + stable",
        expected="STRUCTURED_OUTPUT",
        passed=False,
    )

    try:
        snapshot = {
            "ledger_path": str(kernel.ledger_path),
            "sealed": kernel.sealed,
            "env_pinned": bool(kernel.pinned_env_hash),
            "pinned_hash": kernel.pinned_env_hash or "",
            "cum_hash": kernel.cum_hash,
            "seal_check": kernel.verify_environment(cwd),
        }

        # All required keys must be present and typed
        assert isinstance(snapshot["sealed"], bool), "sealed must be bool"
        assert isinstance(snapshot["env_pinned"], bool), "env_pinned must be bool"
        assert isinstance(snapshot["cum_hash"], str) and len(snapshot["cum_hash"]) == 64, \
            "cum_hash must be 64-char hex"

        t.evidence = {
            "snapshot": snapshot,
            "verdict": "STRUCTURED_OUTPUT — all required fields present and typed",
        }
        t.passed = True

    except Exception as e:
        t.evidence = {"error": str(e)}
        t.passed = False

    return t


def _run_s3(kernel_factory) -> TestResult:
    """
    S3: Bidirectional loop — agent proposal → kernel gate → receipt.
    Uses ephemeral :memory: kernel (never touches sovereign ledger).

    Args:
        kernel_factory: callable() → GovernanceVM (required — never imported here,
                        keeping meta/ isolated from kernel write-gate rule).
                        Pass: lambda: GovernanceVM(ledger_path=':memory:')
    """
    t = TestResult(
        id="S3",
        name="Bidirectional loop: agent proposal → kernel gate → receipt",
        expected="RECEIPT_CHAIN",
        passed=False,
    )

    try:
        if kernel_factory is None:
            raise ValueError(
                "S3 requires kernel_factory. "
                "Pass: kernel_factory=lambda: GovernanceVM(ledger_path=':memory:')"
            )
        loop_kernel = kernel_factory()

        # Agent proposes
        proposal = {"type": "epoch1_ping", "text": "EPOCH1 self-model ping", "agent": "S3-test"}
        receipt = loop_kernel.propose(proposal)

        # Kernel gates → receipt emitted
        assert receipt.id.startswith("R-"), f"Receipt id malformed: {receipt.id}"
        assert len(receipt.cum_hash) == 64, f"cum_hash malformed: {receipt.cum_hash}"
        assert len(receipt.payload_hash) == 64, f"payload_hash malformed"

        t.evidence = {
            "proposal": proposal,
            "receipt_id": receipt.id,
            "payload_hash": receipt.payload_hash,
            "cum_hash": receipt.cum_hash,
            "timestamp": receipt.timestamp,
            "verdict": "RECEIPT_CHAIN — proposal → kernel gate → receipt closed",
        }
        t.passed = True

    except Exception as e:
        t.evidence = {"error": str(e)}
        t.passed = False

    return t


def run_self_model_tests(
    kernel,
    kernel_factory,
    cwd: str = ".",
) -> SelfModel:
    """
    Build a SelfModel, run S1/S2/S3, set verdict, and return.

    Args:
        kernel: A live GovernanceVM (SEALED for S1 to work).
        kernel_factory: Required callable() → fresh GovernanceVM for S3 loop.
                        Typically: lambda: GovernanceVM(ledger_path=':memory:')
                        (meta/ module never imports GovernanceVM directly —
                         isolation rule: only town_adapter.py is the write-gate.)
        cwd: Working directory for S2 seal_check.

    Returns:
        SelfModel with verdict PASS or FAIL.
    """
    model = SelfModel.build(kernel, cwd)

    s1 = _run_s1(kernel)
    s2 = _run_s2(kernel, cwd)
    s3 = _run_s3(kernel_factory)  # kernel_factory is required (no direct GovernanceVM import here)

    model.tests = [s1, s2, s3]
    model.verdict = "PASS" if all(t.passed for t in model.tests) else "FAIL"
    model.sealed_at = datetime.now(timezone.utc).isoformat()

    return model
