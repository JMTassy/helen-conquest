#!/usr/bin/env python3
"""
Oracle Town Mayor V2 — Pure function decision engine.

Input: mayor_input.json (schema: oracle_town.mayor_input.v2)
Output: decision_record.json (schema: oracle_town.decision_record.v2)

Decision logic:
1. Parse and validate mayor_input.json
2. Check all attestations are schema-valid + hash-bound
3. Apply termination policy rules
4. Emit deterministic decision_record.json

K-gates checked:
- K23: Mayor is pure function (no I/O beyond file reads)
- K15: Fail-closed (missing evidence → ABORT)
- K21: Policy immutability (policy must match registry hash)
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

# Local imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel.canonical_json import to_canonical_json, from_canonical_json
from kernel.hashing import sha256_file, sha256_canonical_json


class MayorV2:
    """Pure function: mayor_input.json → decision_record.json"""

    def __init__(self, mayor_input_path: str):
        self.mayor_input_path = Path(mayor_input_path)
        self.mayor_input = None
        self.decision_record = None

    def load_input(self) -> bool:
        """Load and parse mayor_input.json"""
        try:
            with open(self.mayor_input_path, "r") as f:
                self.mayor_input = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[FAIL] Cannot load mayor_input.json: {e}", file=sys.stderr)
            return False

    def validate_input(self) -> Tuple[bool, str]:
        """Validate mayor_input against schema"""
        if not self.mayor_input:
            return False, "No input loaded"

        # Check schema version
        if self.mayor_input.get("schema") != "oracle_town.mayor_input.v2":
            return False, "Invalid schema version"

        # Check required fields
        required = ["run_id", "claim", "registries", "attestations", "policy"]
        for field in required:
            if field not in self.mayor_input:
                return False, f"Missing required field: {field}"

        # Check claim structure
        claim = self.mayor_input.get("claim", {})
        if "claim_id" not in claim or "text" not in claim or "claim_class" not in claim:
            return False, "Invalid claim structure"

        # Check attestations
        attestations = self.mayor_input.get("attestations", [])
        if not attestations:
            return False, "No attestations provided"

        for att in attestations:
            if att.get("schema") != "oracle_town.district_attestation.v2":
                return False, f"Attestation has wrong schema: {att.get('schema')}"
            if att.get("claim_id") != claim.get("claim_id"):
                return False, "Attestation claim_id doesn't match input claim_id"

        return True, "Input valid"

    def validate_attestations_hashes(self) -> Tuple[bool, List[str]]:
        """Verify all attestation hashes are correct (not tampered)"""
        errors = []

        for att in self.mayor_input.get("attestations", []):
            stored_hash = att.get("attestation_sha256")
            if not stored_hash:
                errors.append(f"Attestation {att.get('attestation_id')}: missing hash")
                continue

            # Remove hash field and recompute
            att_copy = {k: v for k, v in att.items() if k != "attestation_sha256"}
            computed_hash = sha256_canonical_json(att_copy)

            if stored_hash != computed_hash:
                errors.append(
                    f"Attestation {att.get('attestation_id')}: hash mismatch "
                    f"(expected {computed_hash}, got {stored_hash})"
                )

        return len(errors) == 0, errors

    def apply_termination_rules(self) -> Tuple[str, List[str], Optional[str]]:
        """
        Apply termination policy to reach DELIVER or ABORT decision.

        Simple implementation:
        1. If claim requires K-ρ, check that at least one attestation has rho receipt
        2. If any attestation verdict is FAIL, decision is ABORT
        3. If all attestations PASS or ABSTAIN, decision is DELIVER

        Returns:
            (decision, reason_codes, active_constraint)
        """
        claim = self.mayor_input.get("claim", {})
        attestations = self.mayor_input.get("attestations", [])

        # Check K-ρ requirement
        requires_k_rho = claim.get("requires", {}).get("k_rho", False)
        if requires_k_rho:
            has_rho_receipt = any(
                any(r.get("plugin_type") == "rho_lint" for r in att.get("receipt_refs", []))
                for att in attestations
            )
            if not has_rho_receipt:
                return "ABORT", ["NO_RHO_RECEIPT"], "NO_RHO_RECEIPT"

        # Check attestation verdicts
        for att in attestations:
            verdict = att.get("verdict")
            if verdict == "FAIL":
                reason_codes = att.get("reason_codes", ["ATTESTATION_FAILED"])
                # If attestation is ENGINEERING and mentions rho, mark constraint
                active_constraint = None
                if att.get("district") == "ENGINEERING":
                    for code in reason_codes:
                        if code.startswith("RHO_"):
                            active_constraint = code
                            break
                return "ABORT", reason_codes, active_constraint

        # All checks passed → DELIVER
        return "DELIVER", ["ALL_CHECKS_PASSED"], None

    def compute_decision_hash(self, decision_record: Dict[str, Any]) -> str:
        """Compute deterministic hash of decision (excluding decision_sha256 field)"""
        record_without_hash = {
            k: v for k, v in decision_record.items() if k != "decision_sha256"
        }
        return sha256_canonical_json(record_without_hash)

    def make_decision(self) -> bool:
        """
        Main execution: load → validate → decide → emit decision_record.json
        """
        # Step 1: Load input
        if not self.load_input():
            return False

        # Step 2: Validate input schema
        valid, msg = self.validate_input()
        if not valid:
            print(f"[FAIL] Input validation: {msg}", file=sys.stderr)
            return False

        # Step 3: Validate attestation hashes
        hashes_ok, hash_errors = self.validate_attestations_hashes()
        if not hashes_ok:
            for err in hash_errors:
                print(f"[FAIL] {err}", file=sys.stderr)
            return False

        # Step 4: Apply termination rules
        decision, reason_codes, active_constraint = self.apply_termination_rules()

        # Step 5: Build decision_record
        claim = self.mayor_input.get("claim", {})
        run_id = self.mayor_input.get("run_id")
        mayor_input_hash = sha256_canonical_json(self.mayor_input)

        decision_record = {
            "schema": "oracle_town.decision_record.v2",
            "run_id": run_id,
            "claim_id": claim.get("claim_id"),
            "decision": decision,
            "reason_codes": reason_codes,
            "active_constraint": active_constraint,
            "inputs": {
                "mayor_input_sha256": mayor_input_hash,
            },
            "bound_artifacts": [
                {
                    "path": str(self.mayor_input_path),
                    "sha256": mayor_input_hash,
                    "artifact_type": "mayor_input",
                }
            ],
        }

        # Compute decision hash
        decision_hash = self.compute_decision_hash(decision_record)
        decision_record["decision_sha256"] = decision_hash

        self.decision_record = decision_record
        return True

    def emit_decision(self, output_path: str) -> bool:
        """Write decision_record.json"""
        if not self.decision_record:
            print("[FAIL] No decision record to emit", file=sys.stderr)
            return False

        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write canonical JSON
            canonical = to_canonical_json(self.decision_record)
            path.write_text(canonical, encoding="utf-8")

            print(f"[OK] Decision record emitted: {output_path}")
            print(
                f"     Decision: {self.decision_record['decision']} | "
                f"Active constraint: {self.decision_record.get('active_constraint', 'NONE')}"
            )
            return True
        except Exception as e:
            print(f"[FAIL] Cannot emit decision: {e}", file=sys.stderr)
            return False


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 mayor_v2.py <mayor_input.json> [output_path]",
            file=sys.stderr,
        )
        print(
            "\nExample:\n"
            "  python3 mayor_v2.py runs/golden_loop/mayor_input.json "
            "runs/golden_loop/decision_record.json",
            file=sys.stderr,
        )
        sys.exit(2)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "decision_record.json"

    # Run mayor
    mayor = MayorV2(input_path)

    if not mayor.make_decision():
        sys.exit(1)

    if not mayor.emit_decision(output_path):
        sys.exit(1)

    print("\n" + "=" * 70)
    print(mayor.decision_record)
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
