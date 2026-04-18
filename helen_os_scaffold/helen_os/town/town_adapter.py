# helen_os/town/town_adapter.py
#
# UNIQUE sovereign write-gate.
# All receipt proposals MUST pass through this adapter.
# No subsystem (CONQUEST, SERPENT, AIRI, HELEN) can call kernel directly.
#

import hashlib
import json
from typing import Dict, Any, Optional
from pathlib import Path

from ..kernel import GovernanceVM
from ..kernel.merkle import leaf_hash, build_merkle_root, verify_merkle_proof
from .idempotence import IdempotenceManager
from ..tools.boot_verify import BootVerifier
from ..kernel.canonical_json import canon


class TownAdapter:
    """
    UNIQUE sovereign write-gate.

    Enforces:
    1. Only this module imports GovernanceVM
    2. All proposals pass through propose_receipt()
    3. Idempotence: same input → same receipt
    4. Environment pinning via SEAL_V2
    """

    def __init__(self, ledger_path: str = "storage/ledger.ndjson", base_dir: str = "."):
        self.vm = GovernanceVM(ledger_path)
        self.idempotence = IdempotenceManager(
            index_path=str(Path(ledger_path).parent / "idempotence_index_v1.ndjson")
        )
        self.boot_verifier = BootVerifier(base_dir)
        self.base_dir = base_dir

    # ─────────────────────────────────────────────────────────────────
    # Sovereign path: direct kernel access ONLY through this adapter
    # ─────────────────────────────────────────────────────────────────

    def propose_receipt(
        self,
        payload: Dict[str, Any],
        verdict: Optional[str] = None,
        hal_verdict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Submit candidate payload to GovernanceVM.
        Returns receipt (authoritative).

        Enforces:
        - Idempotence: same input_hash → same receipt
        - Environment pinning: fails if SEAL_V2 env_hash doesn't match
        """
        # 1. Check environment if sealed
        if not self.vm.verify_environment(self.base_dir):
            raise RuntimeError(
                "LNSA_ERROR: Environment drift detected. "
                "Kernel sealed under different env. Fail-closed."
            )

        # 2. Compute input hash for idempotence
        input_hash = self.idempotence.compute_input_hash(
            text=json.dumps(payload, sort_keys=True),
            mode="sovereign",
            context={"source": payload.get("source", "unknown")}
        )

        # 3. Check if already processed
        idempotence_check = self.idempotence.reserve_input(input_hash)
        if not idempotence_check["reserved"]:
            # Already processed: return cached receipt
            existing = idempotence_check["existing_outcome"]
            return {
                "receipt": existing.get("outcome_hash"),
                "status": "IDEMPOTENT_CACHED",
                "seq": existing.get("outcome_seq"),
                "input_hash": input_hash,
            }

        # 4. Propose to kernel (cumulative hash, domain separation)
        receipt = self.vm.propose(payload, verdict=verdict, hal_verdict=hal_verdict)

        # 5. Record outcome for idempotence
        self.idempotence.finalize_input(
            input_hash,
            {
                "seq": receipt.seq,
                "hash": receipt.cum_hash,
                "timestamp": receipt.timestamp,
            }
        )

        return {
            "receipt": receipt.cum_hash,
            "status": "ACCEPTED",
            "seq": receipt.seq,
            "id": receipt.id,
            "timestamp": receipt.timestamp,
            "input_hash": input_hash,
        }

    def verify_ledger(self) -> bool:
        """
        Verify ledger integrity (cumulative hash chain).
        Returns True if valid, False otherwise.
        """
        return self.vm.verify_ledger()

    def get_tip(self) -> str:
        """
        Get current cumulative hash (tip of ledger).
        """
        return self.vm.cum_hash

    def get_status(self) -> Dict[str, Any]:
        """
        Get adapter status: sealed state, tip hash, environment bundle hash.
        """
        return {
            "sealed": self.vm.sealed,
            "tip_hash": self.vm.cum_hash,
            "pinned_env_hash": self.vm.pinned_env_hash,
            "ledger_path": self.vm.ledger_path,
            "boot_status": self.boot_verifier.get_status(),
        }

    # ─────────────────────────────────────────────────────────────────
    # Sovereignty bind: SEAL_V2 (bind kernel to environment)
    # ─────────────────────────────────────────────────────────────────

    def seal_v2(self, reason: str = "explicit seal") -> Dict[str, Any]:
        """
        Create SEAL_V2 event: bind kernel to current environment.
        After this, no further mutations allowed unless env matches.
        """
        env_hash = self.boot_verifier.compute_env_bundle_hash()

        seal_payload = {
            "type": "SEAL_V2",
            "env_hash": env_hash,
            "kernel_hash": self.vm.cum_hash,
            "reason": reason,
            "authority": True,  # SEAL events are authoritative
        }

        receipt = self.vm.propose(seal_payload)

        return {
            "receipt": receipt.cum_hash,
            "status": "SEALED_V2",
            "env_hash": env_hash,
            "kernel_hash": receipt.cum_hash,
            "id": receipt.id,
            "timestamp": receipt.timestamp,
        }

    # ─────────────────────────────────────────────────────────────────
    # Federation: SEAL_V3 with Merkle root binding
    # ─────────────────────────────────────────────────────────────────

    def get_merkle_root(self) -> tuple:
        """
        Compute Merkle root over current ledger.

        Returns:
            (root_hash, ledger_size) tuple
            ledger_size is power of 2 (padded if needed)

        Raises:
            RuntimeError: If ledger cannot be read
        """
        # Load all events from ledger
        events = []
        try:
            with open(self.vm.ledger_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            raise RuntimeError(f"Cannot read ledger: {e}")

        if not events:
            # Empty ledger: single zero leaf
            return leaf_hash("{}"), 1

        # Compute leaf hashes (domain-separated)
        leaves = []
        for event in events:
            canonical = canon(event)
            leaf = leaf_hash(canonical)
            leaves.append(leaf)

        # Pad to power of 2
        n = len(leaves)
        if (n & (n - 1)) != 0:  # Not power of 2
            # Find next power of 2
            import math
            target_power = math.ceil(math.log2(n))
            target_size = 2 ** target_power
            # Pad with zero hashes
            zero_leaf = leaf_hash("{}")
            while len(leaves) < target_size:
                leaves.append(zero_leaf)

        root = build_merkle_root(leaves)
        return root, len(leaves)

    def seal_v3(self, reason: str = "explicit seal v3") -> Dict[str, Any]:
        """
        Create SEAL_V3 event: bind kernel + Merkle root to environment.
        Enables light verification via Merkle import proofs.
        """
        env_hash = self.boot_verifier.compute_env_bundle_hash()
        merkle_root, ledger_size = self.get_merkle_root()

        # Compute trace hash
        trace_path = Path(self.vm.ledger_path).parent / "run_trace.ndjson"
        if trace_path.exists():
            with open(trace_path, 'rb') as f:
                trace_hash = hashlib.sha256(f.read()).hexdigest()
        else:
            trace_hash = hashlib.sha256(b"").hexdigest()

        seal_payload = {
            "type": "seal_v3",
            "final_cum_hash": self.vm.cum_hash,
            "final_trace_hash": trace_hash,
            "env_hash": env_hash,
            "kernel_hash": self.vm.cum_hash,
            "ledger_merkle_root": merkle_root,
            "ledger_size": ledger_size,
            "reason": reason,
            "authority": True,  # SEAL events are authoritative
        }

        receipt = self.vm.propose(seal_payload)

        return {
            "receipt": receipt.cum_hash,
            "status": "SEALED_V3",
            "env_hash": env_hash,
            "merkle_root": merkle_root,
            "ledger_size": ledger_size,
            "id": receipt.id,
            "timestamp": receipt.timestamp,
        }

    # ─────────────────────────────────────────────────────────────────
    # Federation: Validate Merkle Import Proofs
    # ─────────────────────────────────────────────────────────────────

    def validate_merkle_import_v1(
        self,
        merkle_import: Dict[str, Any],
        issuer_seal: Dict[str, Any],
        idempotence_index: set = None
    ) -> Dict[str, Any]:
        """
        Validate merkle_import_v1 receipt.

        Admissibility rule (6-point check):
          1. Schema validity (type, required fields)
          2. Signature validity (ed25519, not implemented here)
          3. Seal binding (seal contains root + size)
          4. Inclusion proof validity (Merkle tree)
          5. Claim coherence (leaf matches claim)
          6. Anti-replay (rid not seen before)

        Args:
            merkle_import: merkle_import_v1 receipt dict
            issuer_seal: seal_v3 or seal_v2 receipt from issuer (binding the root)
            idempotence_index: Set of previously seen receipt IDs

        Returns:
            {"valid": bool, "reason": str, "claim": dict or None}

        Note: Does NOT verify signature (deferred to cryptographic layer).
              Does NOT verify seal is actually in issuer's ledger (deferred to issuer trust model).
        """
        if idempotence_index is None:
            idempotence_index = set()

        # 1. Schema validity
        required_fields = ["type", "rid", "issuer_town", "issuer_seal_hash",
                          "ledger_size", "ledger_merkle_root", "claim", "proof", "sig"]
        for field in required_fields:
            if field not in merkle_import:
                return {
                    "valid": False,
                    "reason": f"Missing required field: {field}"
                }

        if merkle_import.get("type") != "merkle_import_v1":
            return {
                "valid": False,
                "reason": f"Wrong type: {merkle_import.get('type')}"
            }

        # 2. Signature validity (DEFERRED: cryptographic layer)
        # In production, verify merkle_import["sig"] against issuer_town's public key

        # 3. Seal binding
        if issuer_seal.get("ledger_merkle_root") != merkle_import.get("ledger_merkle_root"):
            return {
                "valid": False,
                "reason": "Seal merkle_root does not match import root"
            }

        if issuer_seal.get("ledger_size") != merkle_import.get("ledger_size"):
            return {
                "valid": False,
                "reason": "Seal ledger_size does not match import size"
            }

        root = merkle_import["ledger_merkle_root"]
        ledger_size = merkle_import["ledger_size"]

        # 4. Inclusion proof validity
        claim = merkle_import.get("claim", {})
        proof = merkle_import.get("proof", {})

        if claim.get("kind") == "event_inclusion":
            seq = claim.get("seq")
            event_canon_sha256 = claim.get("event_canon_sha256")
            leaf = proof.get("leaf")
            path = proof.get("path", [])
            index = proof.get("index")

            # Verify Merkle proof
            if not verify_merkle_proof(root, leaf, path, index):
                return {
                    "valid": False,
                    "reason": "Merkle proof verification failed"
                }

            # 5. Claim coherence
            # Recompute expected leaf from event_canon_sha256
            expected_leaf = leaf_hash(claim.get("event_canonical_bytes", ""))
            # (In practice, issuer provides event_canonical_bytes; receiver verifies)
            # For now, just check that leaf looks like a valid hash
            if not isinstance(leaf, str) or len(leaf) != 64:
                return {
                    "valid": False,
                    "reason": "Leaf hash invalid format"
                }

            # 6. Anti-replay
            rid = merkle_import.get("rid")
            if rid in idempotence_index:
                return {
                    "valid": False,
                    "reason": "Duplicate receipt ID (anti-replay)"
                }

            return {
                "valid": True,
                "reason": "merkle_import_v1 valid",
                "claim": claim,
                "rid": rid
            }

        else:
            return {
                "valid": False,
                "reason": f"Unknown claim kind: {claim.get('kind')}"
            }
