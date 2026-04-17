#!/usr/bin/env python3
"""
ACG TRI Runner

Feeds adversarial claims through the TRI gate pipeline and measures results.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

def run_tri_on_claims(run_id: str, output_dir: str = "oracle_town/state/acg"):
    """
    Execute TRI gate on all adversarial claims and record results.
    """
    
    run_path = Path(output_dir) / f"run_{run_id}"
    claims_dir = run_path / "claims"
    results_file = run_path / "results.json"
    
    if not claims_dir.exists():
        print(f"Error: Claims directory not found: {claims_dir}")
        return
    
    print(f"╔════════════════════════════════════════════════════════════╗")
    print(f"║  ACG TRI RUNNER — Run {run_id}                              ║")
    print(f"╚════════════════════════════════════════════════════════════╝\n")
    
    # Load manifest
    manifest_file = run_path / "manifest.json"
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    # Load all claims
    claim_files = sorted(claims_dir.glob("claim_*.json"))
    print(f"[1] Loading {len(claim_files)} claims from {claims_dir}\n")
    
    claims = []
    for claim_file in claim_files:
        with open(claim_file) as f:
            claim_data = json.load(f)
            claims.append({
                "file": claim_file.name,
                "claim": claim_data["claim"]
            })
    
    # Process each claim through TRI-like logic (simplified for testing)
    print(f"[2] Running TRI gate checks...\n")
    
    results = {
        "run_id": run_id,
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "total_claims": len(claims),
        "claims_processed": 0,
        "escape_count": 0,
        "misfire_count": 0,
        "per_gate_results": {},
        "claim_results": []
    }
    
    gate_order = manifest.get("gate_ordering", [])
    
    for i, claim_info in enumerate(claims, 1):
        claim = claim_info["claim"]
        claim_id = claim.get("id", f"unknown_{i}")
        
        # Simplified gate checks (actual implementation would call real TRI)
        checks = run_gate_checks(claim, gate_order)
        
        # Find primary failure
        primary_fail = None
        for check in checks:
            if check["result"] == "FAIL":
                primary_fail = check["gate"]
                break
        
        # Get intended gate from claim (stored in description/intent)
        intended_gate = extract_intended_gate(claim)
        
        # Determine misfire
        escaped = all(c["result"] == "PASS" for c in checks)
        misfired = primary_fail and primary_fail != intended_gate
        
        claim_result = {
            "number": i,
            "claim_id": claim_id,
            "intended_gate": intended_gate,
            "primary_fail_gate": primary_fail,
            "escaped": escaped,
            "misfired": misfired,
            "checks": checks
        }
        
        results["claim_results"].append(claim_result)
        results["claims_processed"] += 1
        
        if escaped:
            results["escape_count"] += 1
            print(f"  ⚠ CLAIM {i:02d} ({claim_id}): ESCAPED (no failures!)")
        elif misfired:
            results["misfire_count"] += 1
            print(f"  ≠ CLAIM {i:02d} ({claim_id}): MISFIRE (expected {intended_gate}, got {primary_fail})")
        else:
            print(f"  ✓ CLAIM {i:02d} ({claim_id}): {primary_fail}")
    
    # Aggregate per-gate results
    results["per_gate_results"] = aggregate_gate_results(results["claim_results"], gate_order)
    
    # Save results
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[3] Results Summary\n")
    print(f"  Total claims: {results['total_claims']}")
    print(f"  Processed: {results['claims_processed']}")
    print(f"  Escapes: {results['escape_count']} ({100*results['escape_count']/max(results['total_claims'],1):.1f}%)")
    print(f"  Misfires: {results['misfire_count']} ({100*results['misfire_count']/max(results['total_claims'],1):.1f}%)")
    
    print(f"\n[4] Per-Gate Performance\n")
    for gate, gate_results in results["per_gate_results"].items():
        print(f"  {gate:35} | Catches: {gate_results['catch_count']:2}  Redundant: {gate_results['redundant_count']:2}")
    
    print(f"\n[5] Classification")
    if results["escape_count"] == 0 and results["misfire_count"] == 0:
        print(f"  ✓ PERFECT: No escapes, no misfires")
    elif results["escape_count"] == 0 and results["misfire_count"] < len(claims) * 0.2:
        print(f"  ✓ GOOD: No escapes, acceptable misfire rate")
    elif results["escape_count"] == 0:
        print(f"  ~ ACCEPTABLE: No escapes, but misfire investigation needed")
    else:
        print(f"  ✗ CRITICAL: {results['escape_count']} claims escaped all gates")
    
    print(f"\nResults saved to: {results_file}")


def run_gate_checks(claim: dict, gate_order: list) -> list:
    """
    Run simplified gate checks on a claim.
    In production, this would call the actual TRI gate implementation.
    """
    checks = []
    
    # Gate 1: schema_valid
    schema_check = {
        "gate": "schema_valid",
        "result": "PASS"
    }
    # Check for required fields
    required = ["id", "timestamp", "target", "claim_type", "policy_pack_hash", "generated_by"]
    for field in required:
        if field not in claim:
            schema_check["result"] = "FAIL"
            schema_check["reason"] = f"Missing required field: {field}"
            break
    
    # Check for acceptance_criteria if not explicitly empty
    if "acceptance_criteria" not in claim and schema_check["result"] == "PASS":
        schema_check["result"] = "FAIL"
        schema_check["reason"] = "Missing acceptance_criteria"
    
    checks.append(schema_check)
    
    # Gate 2: K7_policy_pinning
    k7_check = {
        "gate": "K7_policy_pinning",
        "result": "PASS"
    }
    diffs = claim.get("proposed_diffs", [])
    for diff in diffs:
        path = diff.get("path", "")
        if any(x in path for x in ["keys/", "schemas/", "policy"]):
            k7_check["result"] = "FAIL"
            k7_check["reason"] = "Attempts to mutate authority layer"
            break
    checks.append(k7_check)
    
    # Gate 3: K0_attestor_registered
    k0_check = {
        "gate": "K0_attestor_not_registered",
        "result": "PASS"
    }
    attestor = claim.get("generated_by", "")
    # Simulate checking against test registry
    valid_attestors = ["test-legal-001", "test-technical-001", "test-business-001"]
    if attestor not in valid_attestors:
        k0_check["result"] = "FAIL"
        k0_check["reason"] = f"Attestor not in registry: {attestor}"
    checks.append(k0_check)
    
    # Gate 4: K2_no_self_attestation
    k2_check = {
        "gate": "K2_no_self_attestation",
        "result": "PASS"
    }
    if "parent_claim_id" in claim and claim["parent_claim_id"] == claim.get("id"):
        k2_check["result"] = "FAIL"
        k2_check["reason"] = "Claim references itself"
    checks.append(k2_check)
    
    # Gate 5: K1_fail_closed
    k1_check = {
        "gate": "K1_fail_closed",
        "result": "PASS"
    }
    evidence = claim.get("evidence_pointers", [])
    if not evidence and schema_check["result"] == "PASS":
        # Some claims need evidence, some don't
        claim_type = claim.get("claim_type", "")
        if claim_type in ["code_change", "policy_patch"]:
            k1_check["result"] = "FAIL"
            k1_check["reason"] = "No evidence for claim type that requires it"
    checks.append(k1_check)
    
    # Gate 6: K5_determinism
    k5_check = {
        "gate": "K5_determinism",
        "result": "PASS"
    }
    acceptance = claim.get("acceptance_criteria", [])
    for criterion in acceptance:
        if isinstance(criterion, str):
            if any(x in criterion.lower() for x in ["now()", "latest", "dynamic", "timestamp"]):
                k5_check["result"] = "FAIL"
                k5_check["reason"] = "Temporal or nondeterministic criterion"
                break
    checks.append(k5_check)
    
    return checks


def extract_intended_gate(claim: dict) -> str:
    """
    Extract the intended fail gate from claim description/intent.
    This is encoded in the intent field by acg_generate.
    """
    intent = claim.get("intent", "")
    
    # Map intent patterns to gate names
    if "missing" in intent.lower() or "acceptance" in intent.lower():
        return "schema_valid"
    elif "attestor" in intent.lower() or "unregistered" in intent.lower():
        return "K0_attestor_not_registered"
    elif "authority" in intent.lower() or "mutate" in intent.lower():
        return "K7_policy_pinning"
    elif "self" in intent.lower() or "circular" in intent.lower():
        return "K2_no_self_attestation"
    elif "temporal" in intent.lower() or "nondeterministic" in intent.lower():
        return "K5_determinism"
    else:
        return "unknown"


def aggregate_gate_results(claim_results: list, gate_order: list) -> dict:
    """
    Aggregate per-gate statistics.
    """
    per_gate = {}
    
    for gate in gate_order:
        catch_count = 0
        redundant_count = 0
        
        for claim_result in claim_results:
            # Count if this gate caught something
            for check in claim_result.get("checks", []):
                if check.get("gate") == gate and check.get("result") == "FAIL":
                    catch_count += 1
                    # Check if this was the primary fail
                    if check.get("gate") != claim_result.get("primary_fail_gate"):
                        redundant_count += 1
        
        per_gate[gate] = {
            "catch_count": catch_count,
            "redundant_count": redundant_count
        }
    
    return per_gate


def main():
    parser = argparse.ArgumentParser(description="ACG TRI Runner")
    parser.add_argument("--run-id", type=str, default="000002", help="Run identifier")
    parser.add_argument("--output-dir", type=str, default="oracle_town/state/acg", help="Output directory")
    
    args = parser.parse_args()
    
    run_tri_on_claims(args.run_id, args.output_dir)


if __name__ == "__main__":
    main()
