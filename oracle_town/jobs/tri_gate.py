#!/usr/bin/env python3
"""
ORACLE TOWN — TRI Module (Level 2: Constitutional Gate)

TRI is a deterministic gate function that verifies claims against pinned policy.
TRI does NOT:
  - mutate files
  - modify policy
  - sign receipts
  - commit to ledger

TRI outputs an unsigned verdict that Mayor must sign.

No component that generates a claim is allowed to ratify it.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class TriVerdict(str, Enum):
    """TRI's decision on a claim."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    DEFER = "DEFER"


class CheckCode(str, Enum):
    """Machine-readable check result codes."""
    # Authority checks
    K0_AUTHORITY_SEPARATION = "K0_authority_separation"
    K0_ATTESTOR_NOT_REGISTERED = "K0_attestor_not_registered"
    K0_ATTESTOR_REVOKED = "K0_attestor_revoked"

    # Fail-closed default
    K1_FAIL_CLOSED = "K1_fail_closed"
    K1_MISSING_EVIDENCE = "K1_missing_evidence"
    K1_MISSING_RECEIPT = "K1_missing_receipt"
    K1_EVIDENCE_NOT_REALIZABLE = "K1_evidence_not_realizable"

    # No self-attestation
    K2_NO_SELF_ATTESTATION = "K2_no_self_attestation"
    K2_SELF_ATTESTATION_DETECTED = "K2_self_attestation_detected"
    K2_SELF_GENERATED_EVIDENCE = "K2_self_generated_evidence"

    # Quorum by class
    K3_QUORUM_BY_CLASS = "K3_quorum_by_class"
    K3_INSUFFICIENT_QUORUM = "K3_insufficient_quorum"

    # Determinism
    K5_DETERMINISM = "K5_determinism"
    K5_HASH_MISMATCH = "K5_hash_mismatch"
    K5_NONDETERMINISTIC_REFERENCE = "K5_nondeterministic_reference"

    # Policy pinning
    K7_POLICY_PINNING = "K7_policy_pinning"
    K7_POLICY_HASH_MISMATCH = "K7_policy_hash_mismatch"

    # Schema/format
    SCHEMA_INVALID = "schema_invalid"
    SCHEMA_VALID = "schema_valid"

    # Test results
    TEST_PASS = "test_pass"
    TEST_FAIL = "test_fail"

@dataclass
class Check:
    """Result of a single gate check."""
    check_code: CheckCode
    result: str  # "PASS" | "FAIL" | "WARN"
    details: str


def load_claim(claim_file: Path) -> Dict[str, Any]:
    """Load a claim from file."""
    with claim_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_key_registry(registry_file: Path) -> Dict[str, Any]:
    """Load the key registry."""
    if not registry_file.exists():
        return {}

    with registry_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_policy_pack(policy_file: Path) -> Dict[str, Any]:
    """Load the policy pack."""
    if not policy_file.exists():
        return {}

    with policy_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_claim_schema(claim: Dict[str, Any]) -> List[Check]:
    """Verify claim has required fields."""
    checks = []

    try:
        claim_data = claim.get("claim", {})

        required_fields = [
            "id", "timestamp", "target", "claim_type",
            "proposed_diffs", "evidence_pointers", "expected_outcomes",
            "policy_pack_hash", "generated_by", "intent"
        ]

        missing = [f for f in required_fields if f not in claim_data]

        if missing:
            checks.append(Check(
                check_code=CheckCode.SCHEMA_INVALID,
                result="FAIL",
                details=f"Missing required fields: {', '.join(missing)}"
            ))
        else:
            checks.append(Check(
                check_code=CheckCode.SCHEMA_VALID,
                result="PASS",
                details="All required fields present"
            ))

        return checks

    except Exception as e:
        checks.append(Check(
            check_code=CheckCode.SCHEMA_INVALID,
            result="FAIL",
            details=f"Schema validation error: {str(e)}"
        ))
        return checks


def verify_k0_authority(claim: Dict[str, Any], registry: Dict[str, Any]) -> List[Check]:
    """K0: Verify attestor exists and is active in key registry."""
    checks = []

    claim_data = claim.get("claim", {})
    attestor_id = claim_data.get("generated_by")

    if not attestor_id:
        checks.append(Check(
            check_code=CheckCode.K0_ATTESTOR_NOT_REGISTERED,
            result="FAIL",
            details="No attestor_id provided"
        ))
        return checks

    # Check registry
    if attestor_id not in registry:
        checks.append(Check(
            check_code=CheckCode.K0_ATTESTOR_NOT_REGISTERED,
            result="FAIL",
            details=f"Attestor {attestor_id} not found in key registry"
        ))
    else:
        attestor_info = registry[attestor_id]

        if attestor_info.get("status") == "revoked":
            checks.append(Check(
                check_code=CheckCode.K0_ATTESTOR_REVOKED,
                result="FAIL",
                details=f"Attestor {attestor_id} has been revoked"
            ))
        else:
            checks.append(Check(
                check_code=CheckCode.K0_AUTHORITY_SEPARATION,
                result="PASS",
                details=f"Attestor {attestor_id} is active and registered"
            ))

    return checks


def verify_k2_no_self_attestation(claim: Dict[str, Any]) -> List[Check]:
    """K2: Verify that attestor_id ≠ target module."""
    checks = []

    claim_data = claim.get("claim", {})
    attestor_id = claim_data.get("generated_by")
    target = claim_data.get("target", "")

    # Extract module name from target path
    # e.g., "oracle_town/jobs/obs_scan.py" → module "obs"
    module_name = target.split("/")[-1].split("_")[0] if "/" in target else ""

    # Check if attestor_id contains the module name (self-attestation pattern)
    if module_name and module_name in attestor_id.lower():
        checks.append(Check(
            check_code=CheckCode.K2_SELF_ATTESTATION_DETECTED,
            result="FAIL",
            details=f"Attestor {attestor_id} appears to be self-attesting (targets {target})"
        ))
    else:
        checks.append(Check(
            check_code=CheckCode.K2_NO_SELF_ATTESTATION,
            result="PASS",
            details=f"No self-attestation detected: {attestor_id} attesting to {target}"
        ))

    return checks


def verify_k7_policy_pinning(claim: Dict[str, Any], pinned_policy_hash: str) -> List[Check]:
    """K7: Verify that claim was generated under pinned policy."""
    checks = []

    claim_data = claim.get("claim", {})
    claim_policy_hash = claim_data.get("policy_pack_hash")

    if claim_policy_hash != pinned_policy_hash:
        checks.append(Check(
            check_code=CheckCode.K7_POLICY_HASH_MISMATCH,
            result="FAIL",
            details=f"Policy hash mismatch: claim has {claim_policy_hash}, expected {pinned_policy_hash}"
        ))
    else:
        checks.append(Check(
            check_code=CheckCode.K7_POLICY_PINNING,
            result="PASS",
            details="Claim was generated under pinned policy"
        ))

    return checks


def verify_evidence(claim: Dict[str, Any], evidence_dir: Path) -> List[Check]:
    """K1: Verify that all cited evidence exists and hashes match."""
    checks = []

    claim_data = claim.get("claim", {})
    evidence_pointers = claim_data.get("evidence_pointers", [])

    if not evidence_pointers:
        checks.append(Check(
            check_code=CheckCode.K1_MISSING_EVIDENCE,
            result="WARN",
            details="No evidence pointers provided"
        ))
        return checks

    for evidence in evidence_pointers:
        evidence_path = evidence_dir / evidence.get("path", "")
        expected_hash = evidence.get("hash")

        if not evidence_path.exists():
            checks.append(Check(
                check_code=CheckCode.K1_MISSING_EVIDENCE,
                result="FAIL",
                details=f"Evidence not found: {evidence.get('path')}"
            ))
        else:
            # Verify hash
            with evidence_path.open("rb") as f:
                actual_hash = "sha256:" + __import__("hashlib").sha256(f.read()).hexdigest()

            if actual_hash != expected_hash:
                checks.append(Check(
                    check_code=CheckCode.K5_HASH_MISMATCH,
                    result="FAIL",
                    details=f"Hash mismatch for {evidence.get('path')}: expected {expected_hash}, got {actual_hash}"
                ))
            else:
                checks.append(Check(
                    check_code=CheckCode.TEST_PASS,
                    result="PASS",
                    details=f"Evidence verified: {evidence.get('path')}"
                ))

    return checks


def make_verdict(checks: List[Check], claim: Dict[str, Any]) -> TriVerdict:
    """
    Deterministic verdict based on check results.

    ACCEPT: All FAIL checks must be zero
    REJECT: Any FAIL check → reject
    DEFER: WARN checks exist (need more evidence)
    """
    fail_checks = [c for c in checks if c.result == "FAIL"]
    warn_checks = [c for c in checks if c.result == "WARN"]

    if fail_checks:
        return TriVerdict.REJECT
    elif warn_checks:
        return TriVerdict.DEFER
    else:
        return TriVerdict.ACCEPT



# ═══════════════════════════════════════════════════════════════
# CONSTITUTION HASH — Immutable (sealed 2026-01-31)
# If this changes, the constitution has drifted. Abort all runs.
# ═══════════════════════════════════════════════════════════════
CONSTITUTION_HASH = "sha256:df9fb5da69dae59bfe8c0184018d65bc2cf2f578bc7adcc57f537d411a1ed07d"

# ═══════════════════════════════════════════════════════════════
# P0: Evidence Realizability Gate
# ═══════════════════════════════════════════════════════════════

EVIDENCE_ROOT = Path("artifacts").resolve()
BANNED_EVIDENCE_PREFIXES = ("/tmp", "oracle_town/state", "oracle_town/run", ".cache", "run_", "state_")


def is_safe_relpath(rel_path: str) -> bool:
    """Check if path is safe (no absolute, no escape attempts)."""
    if rel_path.startswith("/") or rel_path.startswith("~"):
        return False
    path_obj = Path(rel_path)
    if ".." in path_obj.parts:
        return False
    return True


def resolve_evidence_path(rel_path: str) -> Path:
    """Resolve evidence path safely within EVIDENCE_ROOT."""
    if not is_safe_relpath(rel_path):
        raise ValueError(f"unsafe path: {rel_path}")
    p = (EVIDENCE_ROOT / rel_path).resolve()
    # Check path doesn't escape root
    try:
        p.relative_to(EVIDENCE_ROOT)
    except ValueError:
        raise ValueError(f"path escapes evidence root: {rel_path}")
    return p


def sha256_file(p: Path) -> str:
    """Compute SHA256 hash of file."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def verify_evidence_realizability(claim: dict, evidence_dir: Path) -> list[Check]:
    """
    P0: Evidence Realizability Gate
    
    Verify that:
    1. Evidence paths are safe (no escape, no absolute)
    2. Evidence files actually exist
    3. Evidence hashes match declared hashes
    4. Evidence is not from ephemeral/internal locations
    """
    checks = []
    claim_data = claim.get("claim", {})
    evidence_pointers = claim_data.get("evidence_pointers", [])
    
    for evidence in evidence_pointers:
        evidence_type = evidence.get("type", "")
        evidence_path = evidence.get("path", "")
        declared_hash = evidence.get("hash", "")
        
        # Skip non-file evidence types
        if evidence_type not in {"test_result", "artifact", "log", "report"}:
            continue
        
        # Check path safety
        if not is_safe_relpath(evidence_path):
            checks.append(Check(
                check_code=CheckCode.K1_EVIDENCE_NOT_REALIZABLE,
                result="FAIL",
                details=f"Unsafe evidence path: {evidence_path}"
            ))
            continue
        
        # Check for ephemeral locations
        if any(banned in evidence_path.lower() for banned in BANNED_EVIDENCE_PREFIXES):
            checks.append(Check(
                check_code=CheckCode.K2_SELF_GENERATED_EVIDENCE,
                result="FAIL",
                details=f"Evidence from ephemeral/internal location: {evidence_path}"
            ))
            continue
        
        # Check file exists
        try:
            resolved_path = resolve_evidence_path(evidence_path)
        except ValueError as e:
            checks.append(Check(
                check_code=CheckCode.K1_EVIDENCE_NOT_REALIZABLE,
                result="FAIL",
                details=f"Evidence path error: {str(e)}"
            ))
            continue
        
        if not resolved_path.exists():
            checks.append(Check(
                check_code=CheckCode.K1_EVIDENCE_NOT_REALIZABLE,
                result="FAIL",
                details=f"Evidence file not found: {evidence_path}"
            ))
            continue
        
        # Check hash
        if not declared_hash:
            checks.append(Check(
                check_code=CheckCode.K1_EVIDENCE_NOT_REALIZABLE,
                result="FAIL",
                details=f"Evidence missing hash declaration: {evidence_path}"
            ))
            continue
        
        actual_hash = sha256_file(resolved_path)
        if actual_hash != declared_hash:
            checks.append(Check(
                check_code=CheckCode.K5_HASH_MISMATCH,
                result="FAIL",
                details=f"Evidence hash mismatch: {evidence_path} (expected {declared_hash}, got {actual_hash})"
            ))
            continue
        
        # All checks passed for this evidence
        checks.append(Check(
            check_code=CheckCode.K1_FAIL_CLOSED,
            result="PASS",
            details=f"Evidence realizable: {evidence_path}"
        ))
    
    return checks


# ═══════════════════════════════════════════════════════════════
# P1: K5 Determinism Extension (Reserved Keywords)
# ═══════════════════════════════════════════════════════════════

RESERVED_KEYWORDS = {"latest", "current", "today", "now", "auto", "dynamic"}


def contains_reserved_keyword(s: str) -> bool:
    """Check if string contains reserved (nondeterministic) keywords."""
    if not isinstance(s, str):
        return False
    sl = s.lower()
    return any(kw in sl for kw in RESERVED_KEYWORDS)


def verify_k5_determinism_extended(claim: dict) -> list[Check]:
    """
    P1: Extended K5 Determinism Gate
    
    Verify claim contains no reserved/dynamic keywords that would cause
    nondeterministic verdict behavior across runs.
    """
    checks = []
    claim_data = claim.get("claim", {})
    
    # Check evidence paths and descriptions
    for evidence in claim_data.get("evidence_pointers", []):
        for field in ("path", "description"):
            value = evidence.get(field, "")
            if contains_reserved_keyword(value):
                checks.append(Check(
                    check_code=CheckCode.K5_NONDETERMINISTIC_REFERENCE,
                    result="FAIL",
                    details=f"Reserved keyword in evidence.{field}: {value}"
                ))
    
    # Check acceptance criteria
    for criterion in claim_data.get("acceptance_criteria", []):
        if contains_reserved_keyword(criterion):
            checks.append(Check(
                check_code=CheckCode.K5_NONDETERMINISTIC_REFERENCE,
                result="FAIL",
                details=f"Reserved keyword in acceptance_criteria: {criterion}"
            ))
    
    # Check target
    if contains_reserved_keyword(claim_data.get("target", "")):
        checks.append(Check(
            check_code=CheckCode.K5_NONDETERMINISTIC_REFERENCE,
            result="FAIL",
            details=f"Reserved keyword in target: {claim_data.get('target')}"
        ))
    
    # If no failures found, pass the determinism check
    if not checks:
        checks.append(Check(
            check_code=CheckCode.K5_DETERMINISM,
            result="PASS",
            details="No reserved keywords detected"
        ))
    
    return checks


# ═══════════════════════════════════════════════════════════════
# P2: K2 Self-Attestation Enhancement (Artifact Detection)
# ═══════════════════════════════════════════════════════════════

def verify_k2_no_self_attestation_enhanced(claim: dict) -> list[Check]:
    """
    P2: Enhanced K2 No Self-Attestation Gate
    
    Prevents both:
    1. Explicit self-reference (parent_claim_id == id)
    2. Implicit artifact reuse (evidence from ephemeral/internal sources)
    """
    checks = []
    claim_data = claim.get("claim", {})
    
    # Check explicit self-reference (original K2)
    claim_id = claim_data.get("id")
    parent_claim_id = claim_data.get("parent_claim_id")
    
    if claim_id and parent_claim_id == claim_id:
        checks.append(Check(
            check_code=CheckCode.K2_SELF_ATTESTATION_DETECTED,
            result="FAIL",
            details=f"Explicit self-reference: claim {claim_id} references itself as parent"
        ))
        return checks
    
    # Check attestor name doesn't match target (original K2)
    attestor_id = claim_data.get("generated_by", "")
    target = claim_data.get("target", "")
    module_name = target.split("/")[-1].split("_")[0] if "/" in target else ""
    
    if module_name and module_name in attestor_id.lower():
        checks.append(Check(
            check_code=CheckCode.K2_SELF_ATTESTATION_DETECTED,
            result="FAIL",
            details=f"Attestor {attestor_id} appears to self-attest to {target}"
        ))
        return checks
    
    # Check for implicit artifact reuse (evidence from self-generated locations)
    for evidence in claim_data.get("evidence_pointers", []):
        path = evidence.get("path", "")
        # Ban evidence from ephemeral/internal locations
        if any(banned in path.lower() for banned in BANNED_EVIDENCE_PREFIXES):
            checks.append(Check(
                check_code=CheckCode.K2_SELF_GENERATED_EVIDENCE,
                result="FAIL",
                details=f"Evidence appears self-generated (from {path})"
            ))
            return checks
    
    # All checks passed
    checks.append(Check(
        check_code=CheckCode.K2_NO_SELF_ATTESTATION,
        result="PASS",
        details=f"No self-attestation detected"
    ))
    
    return checks

def run_tri_gate(claim_file: Path, output_file: Path, policy_pack_hash: str,
                key_registry_file: Path, evidence_dir: Path, verbose: bool = False) -> bool:
    """
    Run TRI gate on a claim.

    Returns True if successful, False if error.
    """
    try:
        # Load inputs
        claim = load_claim(claim_file)
        registry = load_key_registry(key_registry_file)

        if verbose:
            print(f"[TRI] Verifying claim: {claim_file}")

        # Run all checks in constitutional order
        # This ordering prioritizes: schema → realizability → authority → circularity → completion → determinism
        all_checks = []

        # 1. Schema validation (required first)
        all_checks.extend(verify_claim_schema(claim))
        
        # If schema fails, stop here (fail-closed)
        if any(c.result == "FAIL" for c in all_checks):
            verdict = make_verdict(all_checks, claim)
            verdict_receipt = {
                "verdict": {
                    "claim_id": claim.get("claim", {}).get("id"),
                    "decision": verdict.value,
                    "checked_against_policy": policy_pack_hash,
                    "checks_performed": [
                        {
                            "check": c.check_code.value,
                            "result": c.result,
                            "details": c.details,
                        }
                        for c in all_checks
                    ],
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                }
            }
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(verdict_receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
                f.write("\n")
            return True
        
        # 2. Evidence realizability (P0 - must exist and hash must match)
        all_checks.extend(verify_evidence_realizability(claim, evidence_dir))
        
        # 3. Policy pinning (block authority mutations early)
        all_checks.extend(verify_k7_policy_pinning(claim, policy_pack_hash))
        
        # 4. Authority separation (only registered attestors)
        all_checks.extend(verify_k0_authority(claim, registry))
        
        # 5. No self-attestation (enhanced with artifact detection, P2)
        all_checks.extend(verify_k2_no_self_attestation_enhanced(claim))
        
        # 6. Determinism extended (reserved keywords, P1)
        all_checks.extend(verify_k5_determinism_extended(claim))

        # Make verdict
        verdict = make_verdict(all_checks, claim)

        if verbose:
            print(f"[TRI] Verdict: {verdict.value}")
            for check in all_checks:
                status_str = f"✓" if check.result == "PASS" else ("✗" if check.result == "FAIL" else "!")
                print(f"      {status_str} {check.check_code.value}: {check.details}")

        # Create unsigned verdict receipt
        verdict_receipt = {
            "verdict": {
                "claim_id": claim.get("claim", {}).get("id"),
                "decision": verdict.value,
                "checked_against_policy": policy_pack_hash,
                "checks_performed": [
                    {
                        "check": c.check_code.value,
                        "result": c.result,
                        "details": c.details,
                    }
                    for c in all_checks
                ],
                "required_remediations": [],
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            }
        }

        # Save unsigned verdict
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(verdict_receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
            f.write("\n")

        if verbose:
            print(f"[TRI] Verdict saved: {output_file}")

        return True

    except Exception as e:
        print(f"[TRI] Error: {str(e)}", file=sys.stderr)
        return False


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ORACLE TOWN TRI: Constitutional Gate Verifier"
    )
    ap.add_argument("--claim", required=True, help="Path to claim.json file")
    ap.add_argument("--output", required=True, help="Output tri_verdict.json file")
    ap.add_argument("--policy-hash", required=True, help="Pinned policy pack SHA-256 hash")
    ap.add_argument("--key-registry", default="oracle_town/keys/public_keys.json",
                    help="Path to key registry")
    ap.add_argument("--evidence-dir", default=".", help="Base directory for evidence paths")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    args = ap.parse_args()

    claim_file = Path(args.claim)
    output_file = Path(args.output)
    registry_file = Path(args.key_registry)
    evidence_dir = Path(args.evidence_dir)

    success = run_tri_gate(
        claim_file=claim_file,
        output_file=output_file,
        policy_pack_hash=args.policy_hash,
        key_registry_file=registry_file,
        evidence_dir=evidence_dir,
        verbose=args.verbose,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
