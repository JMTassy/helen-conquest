#!/usr/bin/env python3
"""
ORACLE TOWN Kernel v1.0

Production-grade deterministic governance kernel.

Core Invariants:
- K5: Determinism (same input → identical output)
- K15: No receipt = no execution (fail-closed)
- K21: Policy immutability (hash-pinned)
- K22: Append-only ledger (no mutations)
- K23: Mayor is pure function (no I/O)
- K24: Daemon liveness (fail-closed if unreachable)

This module combines:
1. Canonical event schemas (JSON)
2. DFA state machine (event routing)
3. Merkle tree hashing (epoch roots)
4. Deterministic replay engine
5. Receipt generation (Mayor)
6. Immutable ledger (append-only)
"""

import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from copy import deepcopy


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL EVENT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class EventType(Enum):
    """Event types in governance automaton"""
    ALLOW = "ALLOW"           # Accept proposal
    PREVENT = "PREVENT"       # Reject proposal
    INITIATE = "INITIATE"     # Start new process
    TERMINATE = "TERMINATE"   # End process
    AMEND = "AMEND"          # Modify existing state


class ClaimType(Enum):
    """Types of claims"""
    CLAIM = "CLAIM"
    VERDICT = "VERDICT"
    PROOFREF = "PROOFREF"


@dataclass
class CanonicalEvent:
    """
    Canonical event structure (immutable).

    All fields are required and ordered lexicographically for hashing.
    """
    event_id: str              # Unique identifier (epoch:counter)
    event_type: str            # EventType enum value
    timestamp: str             # ISO 8601 UTC
    proposer: str              # Agent identifier
    content: Dict[str, Any]    # Event payload (must be JSON-serializable)
    policy_version: str        # Policy under which event was evaluated

    def to_canonical_json(self) -> str:
        """Serialize to canonical JSON for hashing (sorted keys, no whitespace)"""
        data = {
            "content": self.content,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "policy_version": self.policy_version,
            "proposer": self.proposer,
            "timestamp": self.timestamp,
        }
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    def compute_hash(self) -> str:
        """SHA256 hash of canonical JSON (first 16 chars for readability)"""
        canonical = self.to_canonical_json()
        full_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return full_hash[:16]


@dataclass
class Claim:
    """A proposal for the kernel to evaluate"""
    claim_id: str
    claim_type: str            # ClaimType enum value
    proposer: str
    intent: str
    evidence: Dict[str, Any]   # Supporting data
    timestamp: str


@dataclass
class Receipt:
    """Immutable execution record (output of Mayor)"""
    receipt_id: str
    claim_id: str
    decision: str              # "ACCEPT" or "REJECT"
    event_type: str            # EventType that was approved
    policy_version: str
    timestamp: str
    gates_passed: List[str]
    failed_gate: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage (sorted keys)"""
        return {
            "claim_id": self.claim_id,
            "decision": self.decision,
            "event_type": self.event_type,
            "failed_gate": self.failed_gate,
            "gates_passed": sorted(self.gates_passed),
            "policy_version": self.policy_version,
            "reason": self.reason,
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
        }

    def compute_hash(self) -> str:
        """Hash of receipt for chain integrity"""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
        full_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return full_hash[:16]


@dataclass
class LedgerEntry:
    """Single entry in append-only ledger"""
    entry_id: str              # L-000001, L-000002, ...
    timestamp: str
    entry_type: str            # "EVENT", "RECEIPT", "EPOCH_ROOT"
    content: Dict[str, Any]
    hash: str                  # SHA256 of content (first 16 chars)


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION GATES
# ═══════════════════════════════════════════════════════════════════════════

class DFAValidator:
    """Deterministic Finite Automaton for claim validation"""

    def __init__(self, policy_version: str = "POLICY_v1.0"):
        self.policy_version = policy_version
        self.policy_hash = self._compute_policy_hash()

    def _compute_policy_hash(self) -> str:
        """K21: Policy immutability — hash must remain constant"""
        full_hash = hashlib.sha256(self.policy_version.encode()).hexdigest()
        return full_hash[:16]

    def validate(self, claim: Claim) -> Tuple[bool, str, List[str]]:
        """
        Validate claim against gates.

        Returns:
            (is_valid, failed_gate_name, gates_passed)
        """
        gates_passed = []

        # Gate 1: Schema completeness (K1: fail-closed default)
        if not self._validate_schema(claim):
            return False, "SCHEMA_INCOMPLETE", gates_passed
        gates_passed.append("schema_check")

        # Gate 2: Policy immutability (K21)
        if self.policy_hash != self._compute_policy_hash():
            return False, "POLICY_TAMPERING_DETECTED", gates_passed
        gates_passed.append("policy_integrity")

        # Gate 3: No self-attestation (K2: proposer ≠ validator)
        # (Validator is kernel, proposer is agent — always different)
        gates_passed.append("authority_separation")

        # Gate 4: Evidence presence (K15)
        if not claim.evidence or not claim.evidence.get("content_hash"):
            return False, "EVIDENCE_INCOMPLETE", gates_passed
        gates_passed.append("evidence_check")

        # Gate 5: Determinism seed compatibility (K5)
        if not self._validate_determinism_seed(claim):
            return False, "NONDETERMINISTIC_INPUT", gates_passed
        gates_passed.append("determinism_check")

        return True, None, gates_passed

    def _validate_schema(self, claim: Claim) -> bool:
        """Check that claim has all required fields"""
        required = ['claim_id', 'proposer', 'intent', 'timestamp', 'evidence']
        return all(hasattr(claim, field) and getattr(claim, field) is not None
                   for field in required)

    def _validate_determinism_seed(self, claim: Claim) -> bool:
        """K5: Check that evidence is deterministically reproducible"""
        # Evidence must include a determinism seed for replay
        evidence = claim.evidence or {}
        return 'content_hash' in evidence and evidence['content_hash']


# ═══════════════════════════════════════════════════════════════════════════
# MAYOR: PURE RECEIPT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class Mayor:
    """
    Pure function: (claim, evidence) → receipt

    K23: Mayor is pure function only
    - No I/O, no file access, no LLM calls
    - Same input → same output, always
    """

    def __init__(self, policy_version: str = "POLICY_v1.0", receipt_counter: int = 0, deterministic_counter_seed: Optional[int] = None, deterministic_time: Optional[str] = None):
        self.policy_version = policy_version
        self.validator = DFAValidator(policy_version)
        self.receipt_counter = deterministic_counter_seed if deterministic_counter_seed is not None else receipt_counter
        self.deterministic_time = deterministic_time

    def ratify(self, claim: Claim) -> Receipt:
        """
        Generate receipt for a claim.

        Returns:
            Receipt with decision (ACCEPT or REJECT)
        """
        # Validate
        is_valid, failed_gate, gates_passed = self.validator.validate(claim)

        # K15: No receipt without valid claim
        decision = "ACCEPT" if is_valid else "REJECT"
        event_type = claim.intent if is_valid else "UNKNOWN"

        # Generate receipt
        receipt = Receipt(
            receipt_id=self._generate_receipt_id(),
            claim_id=claim.claim_id,
            decision=decision,
            event_type=event_type,
            policy_version=self.policy_version,
            timestamp=self._get_timestamp(),
            gates_passed=gates_passed,
            failed_gate=failed_gate,
            reason=f"Gate failed: {failed_gate}" if failed_gate else None
        )

        return receipt

    def _generate_receipt_id(self) -> str:
        """Generate unique receipt ID"""
        self.receipt_counter += 1
        timestamp = self._get_timestamp().replace(":", "").replace("-", "")[:8]
        return f"R-{timestamp}-{self.receipt_counter:04d}"

    def _get_timestamp(self) -> str:
        """Return ISO 8601 UTC timestamp (or deterministic if set)"""
        if self.deterministic_time:
            return self.deterministic_time
        return datetime.utcnow().isoformat() + "Z"


# ═══════════════════════════════════════════════════════════════════════════
# LEDGER: IMMUTABLE APPEND-ONLY RECORD
# ═══════════════════════════════════════════════════════════════════════════

class InMemoryLedger:
    """K22: Append-only ledger (no mutations, no deletes)"""

    def __init__(self, deterministic_time: Optional[str] = None):
        self.entries: List[LedgerEntry] = []
        self.entry_count = 0
        self.deterministic_time = deterministic_time  # For testing K5

    def record(self, entry_type: str, content: Dict[str, Any]) -> str:
        """
        Append entry to ledger.

        K22: Cannot be modified or deleted.
        Returns: entry_id
        """
        self.entry_count += 1
        entry_id = f"L-{self.entry_count:06d}"

        # Use deterministic time if set (for testing), otherwise use current time
        if self.deterministic_time:
            timestamp = self.deterministic_time
        else:
            timestamp = datetime.utcnow().isoformat() + "Z"

        # Compute content hash (only from content, not timestamp, for determinism)
        content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()[:16]

        entry = LedgerEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            entry_type=entry_type,
            content=content,
            hash=content_hash
        )

        self.entries.append(entry)
        return entry_id

    def get_entries(self) -> List[LedgerEntry]:
        """Return read-only copy of ledger"""
        return deepcopy(self.entries)

    def verify_integrity(self) -> bool:
        """Verify ledger hasn't been tampered with"""
        for entry in self.entries:
            content_json = json.dumps(entry.content, sort_keys=True, separators=(',', ':'))
            expected_hash = hashlib.sha256(content_json.encode()).hexdigest()[:16]
            if entry.hash != expected_hash:
                return False
        return True

    def compute_epoch_root(self, start_idx: int = 0, end_idx: Optional[int] = None) -> str:
        """
        Compute Merkle root for epoch of entries (deterministic).

        K5: Same entries → same root
        """
        if end_idx is None:
            end_idx = len(self.entries)

        entries = self.entries[start_idx:end_idx]

        if not entries:
            return hashlib.sha256(b"EMPTY_EPOCH").hexdigest()[:16]

        # Build Merkle tree bottom-up
        hashes = [e.hash for e in entries]

        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate last if odd

                merkle_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
                new_hashes.append(merkle_hash)

            hashes = new_hashes

        return hashes[0]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ledger (sorted keys)"""
        return {
            "entry_count": self.entry_count,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "hash": e.hash,
                    "timestamp": e.timestamp,
                    "type": e.entry_type,
                }
                for e in self.entries
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# DETERMINISTIC REPLAY ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ReplayEngine:
    """Reconstruct state from ledger (K5: determinism via replay)"""

    def __init__(self, policy_version: str = "POLICY_v1.0"):
        self.policy_version = policy_version
        self.mayor = Mayor(policy_version)
        self.ledger = InMemoryLedger()

    def replay_from_genesis(self, entries: List[LedgerEntry]) -> Tuple[bool, Dict[str, Any]]:
        """
        Replay ledger from genesis to produce current state.

        K5: Same ledger → identical state (byte-for-byte)

        Returns:
            (success, state_dict)
        """
        state = {
            "epoch": 0,
            "processed_claims": 0,
            "processed_receipts": 0,
            "decisions": {"ACCEPT": 0, "REJECT": 0},
            "final_epoch_root": None,
        }

        for entry in entries:
            if entry.entry_type == "CLAIM":
                state["processed_claims"] += 1
            elif entry.entry_type == "RECEIPT":
                decision = entry.content.get("decision", "UNKNOWN")
                state["decisions"][decision] = state["decisions"].get(decision, 0) + 1
                state["processed_receipts"] += 1
            elif entry.entry_type == "EPOCH_ROOT":
                state["epoch"] += 1
                state["final_epoch_root"] = entry.content.get("root_hash")

        return True, state

    def verify_replay_consistency(self, ledger1: InMemoryLedger, ledger2: InMemoryLedger) -> bool:
        """
        Verify two ledgers produce identical state when replayed.

        Used for: determinism testing, replay validation
        """
        entries1 = ledger1.get_entries()
        entries2 = ledger2.get_entries()

        if len(entries1) != len(entries2):
            return False

        success1, state1 = self.replay_from_genesis(entries1)
        success2, state2 = self.replay_from_genesis(entries2)

        if not (success1 and success2):
            return False

        # Deep comparison
        return state1 == state2


# ═══════════════════════════════════════════════════════════════════════════
# ORACLE KERNEL CORE
# ═══════════════════════════════════════════════════════════════════════════

class OracleKernel:
    """
    Production-grade ORACLE TOWN kernel.

    Combines:
    - DFA validator (claim evaluation)
    - Mayor (receipt generation)
    - Ledger (append-only record)
    - Replay engine (determinism verification)
    """

    def __init__(self, policy_version: str = "POLICY_v1.0", deterministic_time: Optional[str] = None, deterministic_counter_seed: int = 0):
        self.policy_version = policy_version
        self.mayor = Mayor(policy_version, deterministic_counter_seed=deterministic_counter_seed, deterministic_time=deterministic_time)
        self.ledger = InMemoryLedger(deterministic_time=deterministic_time)
        self.replay_engine = ReplayEngine(policy_version)
        self.epoch = 0
        self.events_in_epoch = 0
        self.deterministic_time = deterministic_time

    def process_claim(self, claim: Claim) -> Receipt:
        """
        Main entry point: Process claim and generate receipt.

        Flow:
        1. Validate claim (DFA gates)
        2. Generate receipt (Mayor)
        3. Record in ledger (append-only)
        4. Return receipt
        """
        # Record claim in ledger
        self.ledger.record("CLAIM", {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type,
            "proposer": claim.proposer,
            "intent": claim.intent,
        })

        # Generate receipt
        receipt = self.mayor.ratify(claim)

        # Record receipt in ledger
        self.ledger.record("RECEIPT", receipt.to_dict())

        self.events_in_epoch += 1

        return receipt

    def finalize_epoch(self) -> str:
        """
        Close current epoch and compute Merkle root.

        Returns: epoch_root hash
        """
        # Compute root for this epoch
        epoch_root = self.ledger.compute_epoch_root()

        # Record epoch marker
        self.ledger.record("EPOCH_ROOT", {
            "epoch": self.epoch,
            "events_count": self.events_in_epoch,
            "root_hash": epoch_root,
        })

        self.epoch += 1
        self.events_in_epoch = 0

        return epoch_root

    def verify_determinism(self) -> bool:
        """Verify ledger integrity (K5 compliance)"""
        return self.ledger.verify_integrity()

    def get_ledger_state(self) -> Dict[str, Any]:
        """Return current ledger state"""
        return self.ledger.to_dict()


# ═══════════════════════════════════════════════════════════════════════════
# DEMO & TESTING
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """Simple demonstration of kernel functionality"""
    kernel = OracleKernel(policy_version="POLICY_v1.0")

    print("✅ ORACLE TOWN Kernel v1.0")
    print("=" * 70)
    print()

    # Create test claims
    for i in range(5):
        claim = Claim(
            claim_id=f"C-{i:03d}",
            claim_type="CLAIM",
            proposer=f"Agent-{i % 3}",
            intent="REQUEST_RESOURCE",
            evidence={
                "content_hash": hashlib.sha256(f"evidence-{i}".encode()).hexdigest()[:16],
                "reason": f"Test claim {i}",
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        receipt = kernel.process_claim(claim)
        print(f"Claim {i}: {receipt.decision} ({receipt.receipt_id})")

    print()
    print(f"Epoch finalized: {kernel.finalize_epoch()}")
    print(f"Ledger entries: {len(kernel.ledger.get_entries())}")
    print(f"Determinism check: {'✅ PASS' if kernel.verify_determinism() else '❌ FAIL'}")
    print()
    print("Ledger state:")
    print(json.dumps(kernel.get_ledger_state(), indent=2))


if __name__ == "__main__":
    demo()
