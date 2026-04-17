#!/usr/bin/env python3
"""
ORACLE TOWN — Mayor Signer (Level 2: Authority Binding)

Mayor is the only component that can sign TRI verdicts into receipts.
Mayor signature makes a verdict legally binding in Oracle Town.

Mayor does not:
  - evaluate claims
  - change verdicts
  - decide guilt or innocence
  - have opinions

Mayor only:
  - reads TRI verdict
  - signs it (if authorized)
  - commits receipt to ledger
  - logs the action

This script implements the signing function.
The actual decision logic (who is Mayor, what authorization rules apply) is external.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class MayorReceipt:
    """A signed verdict receipt (makes verdict legally binding)."""
    claim_id: str
    verdict: str  # ACCEPT | REJECT | DEFER
    mayor_signature: str  # ed25519 signature (placeholder in this version)
    timestamp_signed: str  # ISO 8601
    policy_pack_hash: str  # pinned policy at time of signing
    legal_binding: bool = True
    world_mutation_allowed: bool = False  # True only if verdict == ACCEPT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt": {
                "claim_id": self.claim_id,
                "verdict": self.verdict,
                "mayor_signature": self.mayor_signature,
                "timestamp_signed": self.timestamp_signed,
                "policy_pack_hash": self.policy_pack_hash,
                "legal_binding": self.legal_binding,
                "world_mutation_allowed": self.world_mutation_allowed,
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON (canonical format)."""
        data = self.to_dict()
        return json.dumps(data, sort_keys=True, indent=indent, ensure_ascii=True) + "\n"

    def save(self, path: Path) -> None:
        """Write receipt to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.to_json())


def create_mayor_signature(claim_id: str, verdict: str, policy_hash: str) -> str:
    """
    Create a Mayor signature.

    In production, this would use Ed25519 from a secure key store.
    For now, we create a placeholder that includes the verdict hash.

    Format: ed25519:MAYOR_<hash>
    """
    payload = f"{claim_id}:{verdict}:{policy_hash}".encode('utf-8')
    signature_hash = hashlib.sha256(payload).hexdigest()[:16]
    return f"ed25519:MAYOR_{signature_hash}"


def load_tri_verdict(verdict_file: Path) -> Dict[str, Any]:
    """Load an unsigned TRI verdict."""
    with verdict_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def sign_verdict(verdict_file: Path, policy_pack_hash: str, output_file: Path,
                verbose: bool = False) -> bool:
    """
    Sign a TRI verdict (convert to legally binding receipt).

    This is the Mayor's function: take an unsigned verdict and bind it.
    """
    try:
        # Load unsigned verdict
        verdict_data = load_tri_verdict(verdict_file)
        verdict_info = verdict_data.get("verdict", {})

        claim_id = verdict_info.get("claim_id")
        decision = verdict_info.get("decision")

        if verbose:
            print(f"[MAYOR] Signing verdict for claim: {claim_id}")
            print(f"[MAYOR] Decision: {decision}")

        # Create signature
        mayor_sig = create_mayor_signature(claim_id, decision, policy_pack_hash)

        # Determine if world mutation is allowed
        world_mutation_allowed = (decision == "ACCEPT")

        # Create receipt
        receipt = MayorReceipt(
            claim_id=claim_id,
            verdict=decision,
            mayor_signature=mayor_sig,
            timestamp_signed=datetime.utcnow().isoformat() + "Z",
            policy_pack_hash=policy_pack_hash,
            legal_binding=True,
            world_mutation_allowed=world_mutation_allowed,
        )

        # Save signed receipt
        receipt.save(output_file)

        if verbose:
            print(f"[MAYOR] Receipt signed and saved: {output_file}")
            print(f"[MAYOR] World mutation allowed: {world_mutation_allowed}")

        return True

    except Exception as e:
        print(f"[MAYOR] Error signing verdict: {str(e)}", file=sys.stderr)
        return False


def commit_to_ledger(claim_file: Path, verdict_file: Path, receipt_file: Path,
                    ledger_base: Path, claim_id: str, verbose: bool = False) -> bool:
    """
    Commit a signed receipt to the append-only ledger.

    Ledger structure:
    ledger/
      YYYY/
        MM/
          claim_id/
            claim.json
            tri_verdict.json
            mayor_receipt.json
    """
    try:
        # Parse claim ID to get date
        # Format: claim_YYYYMMDD_...
        date_part = claim_id.split("_")[1] if "_" in claim_id else "000000"
        year = date_part[0:4] if len(date_part) >= 4 else "0000"
        month = date_part[4:6] if len(date_part) >= 6 else "00"

        # Create ledger entry directory
        ledger_entry_dir = ledger_base / year / month / claim_id
        ledger_entry_dir.mkdir(parents=True, exist_ok=True)

        # Copy files to ledger
        import shutil

        shutil.copy2(claim_file, ledger_entry_dir / "claim.json")
        shutil.copy2(verdict_file, ledger_entry_dir / "tri_verdict.json")
        shutil.copy2(receipt_file, ledger_entry_dir / "mayor_receipt.json")

        if verbose:
            print(f"[MAYOR] Committed to ledger: {ledger_entry_dir}")

        return True

    except Exception as e:
        print(f"[MAYOR] Error committing to ledger: {str(e)}", file=sys.stderr)
        return False


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ORACLE TOWN Mayor: Sign TRI verdicts and commit to ledger"
    )
    ap.add_argument("--verdict", required=True, help="Path to tri_verdict.json (unsigned)")
    ap.add_argument("--claim", required=True, help="Path to original claim.json")
    ap.add_argument("--output", required=True, help="Output mayor_receipt.json (signed)")
    ap.add_argument("--policy-hash", required=True, help="Pinned policy pack SHA-256 hash")
    ap.add_argument("--ledger", default="oracle_town/ledger",
                    help="Base ledger directory")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    args = ap.parse_args()

    verdict_file = Path(args.verdict)
    claim_file = Path(args.claim)
    output_file = Path(args.output)
    ledger_base = Path(args.ledger)

    # Extract claim ID from file name or load from claim
    try:
        with claim_file.open("r") as f:
            claim_data = json.load(f)
        claim_id = claim_data.get("claim", {}).get("id", "unknown")
    except:
        claim_id = verdict_file.stem

    # Sign the verdict
    success = sign_verdict(
        verdict_file=verdict_file,
        policy_pack_hash=args.policy_hash,
        output_file=output_file,
        verbose=args.verbose,
    )

    if not success:
        sys.exit(1)

    # Commit to ledger
    success = commit_to_ledger(
        claim_file=claim_file,
        verdict_file=verdict_file,
        receipt_file=output_file,
        ledger_base=ledger_base,
        claim_id=claim_id,
        verbose=args.verbose,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
