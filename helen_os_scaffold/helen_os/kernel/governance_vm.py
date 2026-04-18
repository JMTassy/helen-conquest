import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from ..town.ledger_writer_v2 import LedgerWriterV2

# Domain separation prefix for cumulative hash chain
DOMAIN_SEPARATOR = "HELEN_CUM_V1::"

class Receipt(BaseModel):
    id: str
    timestamp: str
    payload_hash: str
    cum_hash: str
    payload: Dict[str, Any]
    verdict: Optional[str] = None
    hal_verdict: Optional[Dict[str, Any]] = None
    seq: Optional[int] = None
    schema_version: str = "ledger_v2"

class GovernanceVM:
    """
    Sovereign (deterministic) state machine.
    'No receipt -> no ship'.
    """
    def __init__(self, ledger_path: str = ":memory:"):
        self.ledger_path = ledger_path
        self.writer = LedgerWriterV2(ledger_path)
        self.cum_hash = "0" * 64
        self.sealed = False
        self.pinned_env_hash = None
        self.active_policy = None
        self.active_soul = None
        self._load_state()

    def _load_state(self):
        """Initialize state by replaying the ledger."""
        if self.ledger_path == ":memory:":
            return  # Fresh in-memory ledger — nothing to replay
        if not os.path.exists(self.ledger_path):
            return
        
        current_hash = "0" * 64
        with open(self.ledger_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                receipt = Receipt(**data)
                
                # Check for SEAL events
                if receipt.payload.get("type") == "SEAL":
                    self.sealed = True
                
                if receipt.payload.get("type") == "SEAL_V2":
                    self.sealed = True
                    self.pinned_env_hash = receipt.payload.get("env_hash")

                # Check for dynamic updates
                if receipt.payload.get("type") == "POLICY_UPDATE":
                    self.active_policy = receipt.payload.get("policy")
                
                if receipt.payload.get("type") == "SOUL_UPDATE":
                    self.active_soul = receipt.payload.get("soul")
                
                current_hash = receipt.cum_hash
        
        self.cum_hash = current_hash

    def _canonicalize(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    # ── Banned ref types: dialogue laundering guard (D→E→L separation) ──────────
    # No SHIP mutation may cite dialog.ndjson or DIALOG_TURN_V1 refs directly.
    # Full guard: oracle_town/federation/validate_no_dialogue_laundering.py
    _BANNED_LEDGER_REF_TYPES: List[str] = [
        "DIALOG_TURN_V1", "DIALOG_LOG", "DIALOG_NDJSON",
        "DIALOGUE_TURN", "DIALOGUE_LOG",
    ]
    _BANNED_LEDGER_PATHS: List[str] = ["dialog.ndjson", "dialogue.ndjson", "helen_dialog/dialog"]
    _ALLOWED_LEDGER_REF_TYPES: List[str] = [
        "CLAIM_GRAPH_V1", "EVALUATION_RECEIPT", "GATE_RECEIPT",
        "LAW_INSCRIPTION_RECEIPT", "AUTHZ_RECEIPT_V1", "CROSS_RECEIPT_V1",
        "HAL_VERDICT_RECEIPT_V1", "BLOCK_RECEIPT_V1", "POLICY_UPDATE_RECEIPT_V1",
        "POLICY_UPDATE", "SOUL_UPDATE",
    ]

    def _check_dialogue_laundering(self, payload: Dict[str, Any]) -> None:
        """
        Inline D→E→L separation guard at the sovereign write gate.

        Rejects payloads that:
          - DL-002: cite DIALOG_TURN_V1 / DIALOG_LOG refs directly
          - DL-005: cite unknown ref types not in the allowlist (fail-closed)
          - DL-001: embed dialog.ndjson path strings in non-refs fields

        Full guard with error codes lives in:
          oracle_town/federation/validate_no_dialogue_laundering.py
        """
        refs = payload.get("refs", [])
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict):
                    ref_type = ref.get("type", "")
                    if ref_type in self._BANNED_LEDGER_REF_TYPES:
                        raise PermissionError(
                            f"DIALOGUE_LAUNDERING_FORBIDDEN [DL-002]: "
                            f"propose() payload refs contains banned type '{ref_type}'. "
                            "Lift dialogue through CLAIM_GRAPH_V1 pipeline first."
                        )
                    if ref_type and ref_type not in self._ALLOWED_LEDGER_REF_TYPES:
                        raise PermissionError(
                            f"DIALOGUE_LAUNDERING_FORBIDDEN [DL-005]: "
                            f"propose() payload refs contains unknown type '{ref_type}'. "
                            f"Allowlist: {self._ALLOWED_LEDGER_REF_TYPES}. Fail-closed."
                        )
        # Scan non-refs string fields for banned path patterns
        for key, val in payload.items():
            if key == "refs":
                continue
            if isinstance(val, str):
                for pattern in self._BANNED_LEDGER_PATHS:
                    if pattern in val:
                        raise PermissionError(
                            f"DIALOGUE_LAUNDERING_FORBIDDEN [DL-001]: "
                            f"propose() payload field '{key}' contains banned path '{pattern}'. "
                            "SHIP mutations must not cite dialog.ndjson directly."
                        )

    def propose(self, payload: Dict[str, Any], verdict: Optional[str] = None, hal_verdict: Optional[Dict[str, Any]] = None) -> Receipt:
        if self.sealed:
            raise PermissionError("LNSA_ERROR: Sovereign ledger is SEALED. No further mutations allowed.")

        # D→E→L gate: reject dialogue laundering before any state mutation
        self._check_dialogue_laundering(payload)

        # 1. Payload Hash
        canon_payload = self._canonicalize(payload)
        payload_hash = self._hash(canon_payload)

        # 2. Cumulative Hash: SHA256(DOMAIN || prev_cum_hash || payload_hash)
        new_cum_hash = self._hash(DOMAIN_SEPARATOR + self.cum_hash + payload_hash)
        
        timestamp = datetime.now(timezone.utc).isoformat()
        receipt_id = f"R-{payload_hash[:8]}"

        # Check if this is a SEAL or UPDATE command
        p_type = payload.get("type")
        if p_type in ["SEAL", "SEAL_V2"]:
            self.sealed = True
            if p_type == "SEAL_V2":
                self.pinned_env_hash = payload.get("env_hash")
        
        if p_type == "POLICY_UPDATE":
            self.active_policy = payload.get("policy")
        
        if p_type == "SOUL_UPDATE":
            self.active_soul = payload.get("soul")

        receipt = Receipt(
            id=receipt_id,
            timestamp=timestamp,
            payload_hash=payload_hash,
            cum_hash=new_cum_hash,
            payload=payload,
            verdict=verdict,
            hal_verdict=hal_verdict
        )

        # 3. Append to Ledger Atomically
        receipt_data = {
            "id": receipt_id,
            "timestamp": timestamp,
            "payload_hash": payload_hash,
            "cum_hash": new_cum_hash,
            "payload": payload,
            "verdict": verdict,
            "hal_verdict": hal_verdict
        }
        
        seq, _ = self.writer.append(receipt_data)
        receipt_data["seq"] = seq
        receipt_data["schema_version"] = "ledger_v2"
        
        receipt = Receipt(**receipt_data)
        
        # Update internal state
        self.cum_hash = new_cum_hash
        
        return receipt

    def verify_ledger(self) -> bool:
        """Replay the ledger to verify cumulative hashes."""
        # In-memory ledger: verify against the writer's in-memory buffer
        if self.ledger_path == ":memory:":
            return self.writer.verify_in_memory() if hasattr(self.writer, "verify_in_memory") else True
        current_hash = "0" * 64
        try:
            with open(self.ledger_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    receipt = Receipt(**data)
                    
                    # Verify payload hash
                    canon = self._canonicalize(receipt.payload)
                    p_hash = self._hash(canon)
                    if p_hash != receipt.payload_hash:
                        return False
                    
                    # Verify cum hash (with domain separation)
                    expected_cum = self._hash(DOMAIN_SEPARATOR + current_hash + p_hash)
                    if expected_cum != receipt.cum_hash:
                        return False
                    
                    current_hash = expected_cum
            return True
        except FileNotFoundError:
            return True

    def verify_environment(self, base_dir: str) -> bool:
        """
        Verifies current environment against pinned hash in the ledger.
        Returns True if no pinning exists.
        """
        if not self.pinned_env_hash:
            return True
            
        from ..tools.boot_verify import BootVerifier
        verifier = BootVerifier(base_dir)
        return verifier.compute_env_bundle_hash() == self.pinned_env_hash

    def get_active_policy(self) -> Optional[Dict[str, Any]]:
        """Return the latest policy from the ledger."""
        return self.active_policy

    def get_active_soul(self) -> Optional[Dict[str, Any]]:
        """Return the latest soul definition from the ledger."""
        return self.active_soul
