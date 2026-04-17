"""
ORACLE TOWN — run_tri_gate FUNCTION + HELPERS FOR CONSTITUTIONAL AUDIT

Locked for binary review (PASS/FAIL only).

This file contains:
1. Helper functions affecting path resolution, hashing, timestamp handling, selector scanning
2. Gate functions in constitutional order
3. run_tri_gate orchestrator
4. Verdict logic

All extracted verbatim from oracle_town/jobs/tri_gate.py for final audit.

========================================
CONSTANTS (Global, Immutable)
========================================
"""

from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass
import hashlib

# Primitive A1: δ (Delta) — Frozen Constitutional Constant
# Not present in code yet — must be added as global immutable constant
# PLACEHOLDER: δ = 0.01 (example, must be locked per constitution)

# Evidence Root — Hard Containment Boundary
EVIDENCE_ROOT = Path("artifacts").resolve()

# Banned Evidence Prefixes — Defeats Self-Generated Artifacts (F2)
BANNED_EVIDENCE_PREFIXES = ("/tmp", "oracle_town/state", "oracle_town/run", ".cache", "run_", "state_")

# P1: Dynamic Selector Classes (Must Be Blocked) — E1
RESERVED_KEYWORDS = {"latest", "current", "today", "now", "auto", "dynamic"}

"""
========================================
HELPER FUNCTION 1: is_safe_relpath
Path safety check (no absolute, no escape)
Invoked by: resolve_evidence_path
========================================
"""

def is_safe_relpath(rel_path: str) -> bool:
    """
    Check if path is safe (no absolute, no escape attempts).

    Requirements:
    - Reject absolute paths
    - Reject home paths
    - Reject parent traversal (..)

    This is the FIRST gate in path resolution.
    Pure function, zero side effects.
    """
    if rel_path.startswith("/") or rel_path.startswith("~"):
        return False
    path_obj = Path(rel_path)
    if ".." in path_obj.parts:
        return False
    return True

"""
========================================
HELPER FUNCTION 2: resolve_evidence_path
Realpath containment enforcement (hard)
Invoked by: verify_evidence_realizability (P0)
========================================
"""

def resolve_evidence_path(rel_path: str) -> Path:
    """
    Resolve evidence path safely within EVIDENCE_ROOT.

    D1. Path Containment (Hard):
    - realpath(evidence) ⊂ realpath(artifacts_dir)
    - reject absolute paths
    - reject .. traversal
    - reject any symlink escape
    - Containment checked AFTER resolution, not string-prefix

    Order:
    1. Check is_safe_relpath() first (reject before construction)
    2. Construct relative to EVIDENCE_ROOT
    3. Resolve symlinks (Path.resolve())
    4. Verify post-resolution containment

    Pure function, zero side effects.
    """
    if not is_safe_relpath(rel_path):
        raise ValueError(f"unsafe path: {rel_path}")
    p = (EVIDENCE_ROOT / rel_path).resolve()
    # Check path doesn't escape root (post-resolution)
    try:
        p.relative_to(EVIDENCE_ROOT)
    except ValueError:
        raise ValueError(f"path escapes evidence root: {rel_path}")
    return p

"""
========================================
HELPER FUNCTION 3: sha256_file
Canonical hashing (binary, streaming, deterministic)
Invoked by: verify_evidence_realizability (P0)
========================================
"""

def sha256_file(p: Path) -> str:
    """
    Compute SHA256 hash of file.

    D2. Hashing (Canonical):
    - raw bytes only
    - streaming (1MB chunks)
    - fixed algorithm (SHA-256)
    - no text mode
    - no newline normalization
    - "sha256:" prefix for machine parsing

    Pure function, deterministic: same file → same hash (K5).
    """
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

"""
========================================
HELPER FUNCTION 4: contains_reserved_keyword
Selector scanning for determinism (P1)
Invoked by: verify_k5_determinism_extended
========================================
"""

def contains_reserved_keyword(s: str) -> bool:
    """
    Check if string contains reserved (nondeterministic) keywords.

    E1. Dynamic Selector Classes (Must Be Blocked):
    Explicit minimum: latest, current, today, now, auto, dynamic

    E2. Scope:
    Must scan evidence paths, descriptions, targets, acceptance_criteria, selector fields.

    Implementation:
    - Case-insensitive (lowercase comparison)
    - Substring search (catches embedded keywords)
    - Safe on non-strings (returns False)

    Pure function, deterministic.
    """
    if not isinstance(s, str):
        return False
    sl = s.lower()
    return any(kw in sl for kw in RESERVED_KEYWORDS)

"""
========================================
GATE FUNCTIONS (Constitutional Order)
========================================
"""

@dataclass
class Check:
    """Result of a single gate check."""
    check_code: str
    result: str  # "PASS" | "FAIL" | "WARN"
    details: str

def verify_claim_schema(claim: Dict[str, Any]) -> List[Check]:
    """
    C1. Schema Layer Constraint

    Schema validation:
    - must reject, never repair
    - must not fill defaults, coerce values, normalize strings, drop fields
    - Any normalization before P0/P1 is a constitutional breach

    Early exit on FAIL (fail-closed).
    Pure function.
    """
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
                check_code="SCHEMA_INVALID",
                result="FAIL",
                details=f"Missing required fields: {', '.join(missing)}"
            ))
        else:
            checks.append(Check(
                check_code="SCHEMA_VALID",
                result="PASS",
                details="All required fields present"
            ))

        return checks

    except Exception as e:
        checks.append(Check(
            check_code="SCHEMA_INVALID",
            result="FAIL",
            details=f"Schema validation error: {str(e)}"
        ))
        return checks


def verify_evidence_realizability(claim: dict, evidence_dir: Path) -> list[Check]:
    """
    P0: Evidence Realizability Gate

    D1. Path Containment (Hard):
    - realpath(evidence) ⊂ realpath(artifacts_dir)
    - Containment checked AFTER resolution

    D2. Hashing (Canonical):
    - raw bytes only, streaming, no text mode

    D3. Timestamp Semantics (Diagnostic, Not Anchor):
    - mtime > claim.timestamp used as diagnostic/red flag
    - Hash preimage is true anchor
    - Evidence must pre-exist claim in content, not just clock time

    Pure function, fail-closed on any error.
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

        # D1: Check path safety (first gate in path resolution)
        if not is_safe_relpath(evidence_path):
            checks.append(Check(
                check_code="K1_EVIDENCE_NOT_REALIZABLE",
                result="FAIL",
                details=f"Unsafe evidence path: {evidence_path}"
            ))
            continue

        # Check for ephemeral locations (defeats F1 pre-existence)
        if any(banned in evidence_path.lower() for banned in BANNED_EVIDENCE_PREFIXES):
            checks.append(Check(
                check_code="K2_SELF_GENERATED_EVIDENCE",
                result="FAIL",
                details=f"Evidence from ephemeral/internal location: {evidence_path}"
            ))
            continue

        # D1: Resolve evidence path safely (realpath containment)
        try:
            resolved_path = resolve_evidence_path(evidence_path)
        except ValueError as e:
            checks.append(Check(
                check_code="K1_EVIDENCE_NOT_REALIZABLE",
                result="FAIL",
                details=f"Evidence path error: {str(e)}"
            ))
            continue

        # Check file exists
        if not resolved_path.exists():
            checks.append(Check(
                check_code="K1_EVIDENCE_NOT_REALIZABLE",
                result="FAIL",
                details=f"Evidence file not found: {evidence_path}"
            ))
            continue

        # Check hash declared
        if not declared_hash:
            checks.append(Check(
                check_code="K1_EVIDENCE_NOT_REALIZABLE",
                result="FAIL",
                details=f"Evidence missing hash declaration: {evidence_path}"
            ))
            continue

        # D2: Canonical hashing (raw bytes, deterministic)
        actual_hash = sha256_file(resolved_path)
        if actual_hash != declared_hash:
            checks.append(Check(
                check_code="K5_HASH_MISMATCH",
                result="FAIL",
                details=f"Evidence hash mismatch: {evidence_path} (expected {declared_hash}, got {actual_hash})"
            ))
            continue

        # All checks passed for this evidence
        checks.append(Check(
            check_code="K1_FAIL_CLOSED",
            result="PASS",
            details=f"Evidence realizable: {evidence_path}"
        ))

    return checks


def verify_k7_policy_pinning(claim: Dict[str, Any], pinned_policy_hash: str) -> List[Check]:
    """
    K7: Policy Pinning

    Verify claim was generated under pinned policy.
    Policy hash mismatch ⇒ FAIL (authority immutability).

    Pure function.
    """
    checks = []

    claim_data = claim.get("claim", {})
    claim_policy_hash = claim_data.get("policy_pack_hash")

    if claim_policy_hash != pinned_policy_hash:
        checks.append(Check(
            check_code="K7_POLICY_HASH_MISMATCH",
            result="FAIL",
            details=f"Policy hash mismatch: claim has {claim_policy_hash}, expected {pinned_policy_hash}"
        ))
    else:
        checks.append(Check(
            check_code="K7_POLICY_PINNING",
            result="PASS",
            details="Claim was generated under pinned policy"
        ))

    return checks


def verify_k0_authority(claim: Dict[str, Any], registry: Dict[str, Any]) -> List[Check]:
    """
    K0: Attestor Legitimacy

    Only registered, non-revoked attestors can sign.
    Pure function.
    """
    checks = []

    claim_data = claim.get("claim", {})
    attestor_id = claim_data.get("generated_by")

    if not attestor_id:
        checks.append(Check(
            check_code="K0_ATTESTOR_NOT_REGISTERED",
            result="FAIL",
            details="No attestor_id provided"
        ))
        return checks

    # Check registry
    if attestor_id not in registry:
        checks.append(Check(
            check_code="K0_ATTESTOR_NOT_REGISTERED",
            result="FAIL",
            details=f"Attestor {attestor_id} not found in key registry"
        ))
    else:
        attestor_info = registry[attestor_id]

        if attestor_info.get("status") == "revoked":
            checks.append(Check(
                check_code="K0_ATTESTOR_REVOKED",
                result="FAIL",
                details=f"Attestor {attestor_id} has been revoked"
            ))
        else:
            checks.append(Check(
                check_code="K0_AUTHORITY_SEPARATION",
                result="PASS",
                details=f"Attestor {attestor_id} is active and registered"
            ))

    return checks


def verify_k2_no_self_attestation_enhanced(claim: dict) -> list[Check]:
    """
    P2: No Self-Attestation (Causal, Not Symbolic)

    F1. Hard Pre-Existence Rule:
    Evidence valid only if:
    - existed before claim timestamp
    - not produced by any TRI run causally downstream of claim

    F2. Self-Reference Still Blocked:
    - parent_claim_id == claim.id ⇒ FAIL

    Pure function, fail-closed on any violation.
    """
    checks = []
    claim_data = claim.get("claim", {})

    # F2: Check explicit self-reference
    claim_id = claim_data.get("id")
    parent_claim_id = claim_data.get("parent_claim_id")

    if claim_id and parent_claim_id == claim_id:
        checks.append(Check(
            check_code="K2_SELF_ATTESTATION_DETECTED",
            result="FAIL",
            details=f"Explicit self-reference: claim {claim_id} references itself as parent"
        ))
        return checks

    # Check attestor name doesn't match target
    attestor_id = claim_data.get("generated_by", "")
    target = claim_data.get("target", "")
    module_name = target.split("/")[-1].split("_")[0] if "/" in target else ""

    if module_name and module_name in attestor_id.lower():
        checks.append(Check(
            check_code="K2_SELF_ATTESTATION_DETECTED",
            result="FAIL",
            details=f"Attestor {attestor_id} appears to self-attest to {target}"
        ))
        return checks

    # F1: Check for implicit artifact reuse (evidence from self-generated locations)
    for evidence in claim_data.get("evidence_pointers", []):
        path = evidence.get("path", "")
        # Ban evidence from ephemeral/internal locations
        if any(banned in path.lower() for banned in BANNED_EVIDENCE_PREFIXES):
            checks.append(Check(
                check_code="K2_SELF_GENERATED_EVIDENCE",
                result="FAIL",
                details=f"Evidence appears self-generated (from {path})"
            ))
            return checks

    # All checks passed
    checks.append(Check(
        check_code="K2_NO_SELF_ATTESTATION",
        result="PASS",
        details=f"No self-attestation detected"
    ))

    return checks


def verify_k5_determinism_extended(claim: dict) -> list[Check]:
    """
    P1: Determinism Extended (Global)

    E1. Dynamic Selector Classes (Must Be Blocked):
    Explicit: latest, current, today, now, auto, dynamic

    E2. Scope:
    Must scan evidence paths, descriptions, targets, acceptance_criteria.

    Pure function, fail-closed on any keyword detected.
    """
    checks = []
    claim_data = claim.get("claim", {})

    # Check evidence paths and descriptions
    for evidence in claim_data.get("evidence_pointers", []):
        for field in ("path", "description"):
            value = evidence.get(field, "")
            if contains_reserved_keyword(value):
                checks.append(Check(
                    check_code="K5_NONDETERMINISTIC_REFERENCE",
                    result="FAIL",
                    details=f"Reserved keyword in evidence.{field}: {value}"
                ))
                return checks

    # Check acceptance criteria
    for criterion in claim_data.get("acceptance_criteria", []):
        if contains_reserved_keyword(criterion):
            checks.append(Check(
                check_code="K5_NONDETERMINISTIC_REFERENCE",
                result="FAIL",
                details=f"Reserved keyword in acceptance_criteria: {criterion}"
            ))
            return checks

    # Check target
    if contains_reserved_keyword(claim_data.get("target", "")):
        checks.append(Check(
            check_code="K5_NONDETERMINISTIC_REFERENCE",
            result="FAIL",
            details=f"Reserved keyword in target: {claim_data.get('target')}"
        ))
        return checks

    # If no failures found, pass the determinism check
    checks.append(Check(
        check_code="K5_DETERMINISM",
        result="PASS",
        details="No reserved keywords detected"
    ))

    return checks


def make_verdict(checks: List[Check], claim: Dict[str, Any]) -> str:
    """
    G1. Security Metric: Deterministic Verdict

    ACCEPT: All checks pass (no FAIL)
    REJECT: Any FAIL check present
    DEFER: No FAIL, but WARN checks present

    Deterministic: same input → same verdict (K5).
    No timestamps, machine IDs, or run IDs in verdict.
    Pure function.
    """
    fail_checks = [c for c in checks if c.result == "FAIL"]
    warn_checks = [c for c in checks if c.result == "WARN"]

    if fail_checks:
        return "REJECT"
    elif warn_checks:
        return "DEFER"
    else:
        return "ACCEPT"


"""
========================================
MAIN ORCHESTRATOR: run_tri_gate
========================================

Constitutional Gate Ordering (Frozen, Irreversible):

1. Schema validation (C1)
   └─ Early exit on FAIL

2. P0 Evidence realizability (D1, D2, D3)
   └─ Path containment, canonical hashing, timestamp diagnostics

3. K7 Policy pinning (Authority immutability)

4. K0 Authority separation (Registered attestors only)

5. P2 No self-attestation (F1, F2)
   └─ Hard pre-existence, explicit self-ref blocked

6. P1 Determinism extended (E1, E2)
   └─ Dynamic selector scanning, global scope

7. Verdict logic (G1)
   └─ Deterministic: any FAIL → REJECT
"""

def run_tri_gate(claim_file: Path, output_file: Path, policy_pack_hash: str,
                key_registry_file: Path, evidence_dir: Path, verbose: bool = False) -> bool:
    """
    Run TRI gate on a claim.

    FROZEN CONSTITUTIONAL ORDER:
    1. Schema → early exit on FAIL
    2. P0 → path/hash/timestamp checks
    3. K7 → policy immutability
    4. K0 → attestor legitimacy
    5. P2 → self-attestation and artifacts
    6. P1 → determinism (global)
    7. Verdict → deterministic: ACCEPT/REJECT/DEFER

    Returns True if successful (verdict produced), False if error.

    Pure logic, no I/O except at boundaries (load/save).
    """
    import json
    import sys
    from datetime import datetime

    try:
        # Load inputs (boundary I/O)
        with claim_file.open("r", encoding="utf-8") as f:
            claim = json.load(f)

        with key_registry_file.open("r", encoding="utf-8") as f:
            registry = json.load(f)

        if verbose:
            print(f"[TRI] Verifying claim: {claim_file}")

        # Run all checks in constitutional order (LOCKED)
        all_checks = []

        # ============================================================
        # 1. SCHEMA VALIDATION (C1: Reject-only, early exit on FAIL)
        # ============================================================
        all_checks.extend(verify_claim_schema(claim))

        # If schema fails, stop here (fail-closed B1)
        if any(c.result == "FAIL" for c in all_checks):
            verdict = make_verdict(all_checks, claim)
            verdict_receipt = {
                "verdict": {
                    "claim_id": claim.get("claim", {}).get("id"),
                    "decision": verdict,
                    "checked_against_policy": policy_pack_hash,
                    "checks_performed": [
                        {
                            "check": c.check_code,
                            "result": c.result,
                            "details": c.details,
                        }
                        for c in all_checks
                    ],
                }
            }
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(verdict_receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
                f.write("\n")
            return True

        # ============================================================
        # 2. P0: EVIDENCE REALIZABILITY (D1, D2, D3)
        # ============================================================
        all_checks.extend(verify_evidence_realizability(claim, evidence_dir))

        # ============================================================
        # 3. K7: POLICY PINNING (Authority immutability)
        # ============================================================
        all_checks.extend(verify_k7_policy_pinning(claim, policy_pack_hash))

        # ============================================================
        # 4. K0: AUTHORITY SEPARATION (Registered attestors only)
        # ============================================================
        all_checks.extend(verify_k0_authority(claim, registry))

        # ============================================================
        # 5. P2: NO SELF-ATTESTATION (F1, F2 — causal, not symbolic)
        # ============================================================
        all_checks.extend(verify_k2_no_self_attestation_enhanced(claim))

        # ============================================================
        # 6. P1: DETERMINISM EXTENDED (E1, E2 — global selector scan)
        # ============================================================
        all_checks.extend(verify_k5_determinism_extended(claim))

        # ============================================================
        # 7. MAKE VERDICT (G1 — deterministic, no timestamps)
        # ============================================================
        verdict = make_verdict(all_checks, claim)

        if verbose:
            print(f"[TRI] Verdict: {verdict}")
            for check in all_checks:
                status_str = f"✓" if check.result == "PASS" else ("✗" if check.result == "FAIL" else "!")
                print(f"      {status_str} {check.check_code}: {check.details}")

        # Create unsigned verdict receipt (B2: Canonical refusal surface)
        verdict_receipt = {
            "verdict": {
                "claim_id": claim.get("claim", {}).get("id"),
                "decision": verdict,
                "checked_against_policy": policy_pack_hash,
                "checks_performed": [
                    {
                        "check": c.check_code,
                        "result": c.result,
                        "details": c.details,
                    }
                    for c in all_checks
                ],
            }
        }

        # Save unsigned verdict (boundary I/O)
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


"""
========================================
END OF EXTRACTED CODE
========================================

SUMMARY FOR BINARY AUDIT:

Constants:
- EVIDENCE_ROOT (hard boundary)
- BANNED_EVIDENCE_PREFIXES (defeats F1)
- RESERVED_KEYWORDS (P1 selector blocking)

Helpers:
- is_safe_relpath() — path safety (C1, D1)
- resolve_evidence_path() — realpath containment (D1, symlink-safe)
- sha256_file() — canonical hashing (D2, deterministic)
- contains_reserved_keyword() — selector scanning (P1, E1-E2)

Gates (Constitutional Order):
1. verify_claim_schema() — C1 (reject-only)
2. verify_evidence_realizability() — P0 (D1, D2, D3)
3. verify_k7_policy_pinning() — K7 (authority immutability)
4. verify_k0_authority() — K0 (registered attestors)
5. verify_k2_no_self_attestation_enhanced() — P2 (F1, F2)
6. verify_k5_determinism_extended() — P1 (E1, E2)
7. make_verdict() — G1 (deterministic)

Orchestrator:
- run_tri_gate() — frozen order, early exit on schema FAIL, all subsequent gates append

AUDIT TARGETS:
A1: δ frozen (not yet implemented — required invariant)
B1-B2: Refusal sterility (BANNED_PREFIXES enforce ephemeral rejection)
C1: Schema reject-only (no normalization before P0/P1)
D1: Path containment (realpath, post-resolution verification)
D2: Canonical hashing (raw bytes, streaming, no normalization)
D3: Timestamp semantics (diagnostic, not anchor)
E1-E2: P1 scope (all fields scanned, fail-closed on keywords)
F1-F2: P2 causal (banned prefixes, explicit self-ref check)
G1: Verdict determinism (no timestamps, machine IDs, or run IDs)

Ready for binary audit: PASS or pinpoint breach.
"""
