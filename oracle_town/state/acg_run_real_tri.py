#!/usr/bin/env python3
"""
ACG Real TRI Runner

Feeds adversarial claims through the ACTUAL TRI gate (oracle_town/jobs/tri_gate.py)
and measures real gate performance, not simulated behavior.

Usage:
  python3 acg_run_real_tri.py --run-id 000002 --policy-hash sha256:policy_v1_2026_01
"""

import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def run_claim_through_tri(claim_file: Path, tri_script: Path, policy_hash: str, 
                          key_registry: Path, evidence_dir: Path, verbose: bool = False) -> Tuple[bool, Dict]:
    """
    Execute the REAL tri_gate.py on a single claim.
    
    Returns: (success: bool, verdict_dict: dict)
    """
    
    # Create temp output file
    output_file = claim_file.parent / f"verdict_{claim_file.stem}.json"
    
    cmd = [
        "python3",
        str(tri_script),
        "--claim", str(claim_file),
        "--output", str(output_file),
        "--policy-hash", policy_hash,
        "--key-registry", str(key_registry),
        "--evidence-dir", str(evidence_dir.resolve()),
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(__file__).parent.parent.parent)  # Run from repo root
        )
        
        if result.returncode != 0:
            return False, {"error": result.stderr}
        
        # Load the verdict that TRI produced
        if output_file.exists():
            with open(output_file) as f:
                verdict = json.load(f)
            return True, verdict
        else:
            return False, {"error": f"Output file not created: {output_file}"}
    
    except subprocess.TimeoutExpired:
        return False, {"error": "TRI execution timeout"}
    except Exception as e:
        return False, {"error": str(e)}


def extract_primary_fail_gate(verdict: Dict) -> str:
    """Extract the first FAIL gate from verdict checks."""
    checks = verdict.get("verdict", {}).get("checks_performed", [])
    for check in checks:
        if check.get("result") == "FAIL":
            return check.get("check", "unknown")
    return None


def extract_intended_gate(claim: Dict) -> str:
    """Extract intended primary gate from claim's ACG metadata."""
    acg_meta = claim.get("claim", {}).get("acg", {})
    return acg_meta.get("intended_primary_gate", "unknown")


def run_real_tri_on_suite(run_id: str, policy_hash: str, output_dir: str = "oracle_town/state/acg", 
                          verbose: bool = False) -> None:
    """
    Execute REAL TRI against all claims in the run.
    """
    
    run_path = Path(output_dir) / f"run_{run_id}"
    claims_dir = run_path / "claims"
    manifest_file = run_path / "manifest.json"
    results_file = run_path / "results.json"
    
    if not claims_dir.exists():
        print(f"✗ Claims directory not found: {claims_dir}")
        return
    
    # TRI script location
    tri_script = Path("oracle_town/jobs/tri_gate.py")
    if not tri_script.exists():
        print(f"✗ TRI script not found: {tri_script}")
        return
    
    # Key registry
    key_registry = Path("oracle_town/keys/test_public_keys.json")
    if not key_registry.exists():
        print(f"✗ Key registry not found: {key_registry}")
        return
    
    # Evidence root
    evidence_dir = Path.cwd()
    
    print(f"╔════════════════════════════════════════════════════════════╗")
    print(f"║  ACG REAL TRI RUNNER — Run {run_id}                         ║")
    print(f"║  Using ACTUAL oracle_town/jobs/tri_gate.py                 ║")
    print(f"╚════════════════════════════════════════════════════════════╝\n")
    
    # Load manifest
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    # Load all claims
    claim_files = sorted(claims_dir.glob("claim_*.json"))
    print(f"[1] Loading {len(claim_files)} claims\n")
    
    # Run each claim through real TRI
    print(f"[2] Running claims through REAL TRI gate\n")
    
    results = {
        "run_id": run_id,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "policy_hash": policy_hash,
        "tri_script": str(tri_script),
        "total_claims": len(claim_files),
        "claims_processed": 0,
        "escape_count": 0,
        "misfire_count": 0,
        "per_gate_results": {},
        "claim_results": []
    }
    
    gate_hits = {}  # Track which gates caught what
    
    for i, claim_file in enumerate(claim_files, 1):
        claim_id = claim_file.stem
        
        # Load claim to get metadata
        with open(claim_file) as f:
            claim = json.load(f)
        
        intended_gate = extract_intended_gate(claim)
        
        # Run through REAL TRI
        success, verdict = run_claim_through_tri(
            claim_file=claim_file,
            tri_script=tri_script,
            policy_hash=policy_hash,
            key_registry=key_registry,
            evidence_dir=evidence_dir,
            verbose=verbose
        )
        
        if not success:
            print(f"  ✗ CLAIM {i:02d} ({claim_id}): TRI EXECUTION ERROR - {verdict.get('error')}")
            continue
        
        results["claims_processed"] += 1
        
        # Analyze verdict
        decision = verdict.get("verdict", {}).get("decision", "UNKNOWN")
        checks = verdict.get("verdict", {}).get("checks_performed", [])
        
        # Find primary fail gate
        primary_fail = extract_primary_fail_gate(verdict)
        
        # Determine escape and misfire
        escaped = decision == "ACCEPT" or (decision != "REJECT" and primary_fail is None)
        misfired = primary_fail and primary_fail != intended_gate and primary_fail is not None
        
        # Record per-gate hits
        for check in checks:
            gate_name = check.get("check", "unknown")
            result = check.get("result", "UNKNOWN")
            
            if gate_name not in gate_hits:
                gate_hits[gate_name] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            
            gate_hits[gate_name][result] = gate_hits[gate_name].get(result, 0) + 1
        
        # Store claim result
        claim_result = {
            "number": i,
            "claim_id": claim_id,
            "intended_gate": intended_gate,
            "decision": decision,
            "primary_fail_gate": primary_fail,
            "escaped": escaped,
            "misfired": misfired,
            "checks": [
                {
                    "check": c.get("check"),
                    "result": c.get("result"),
                    "details": c.get("details", "")
                }
                for c in checks
            ]
        }
        
        results["claim_results"].append(claim_result)
        
        if escaped:
            results["escape_count"] += 1
            status = "⚠ ESCAPED"
        elif misfired:
            results["misfire_count"] += 1
            status = f"≠ MISFIRE (expected {intended_gate}, got {primary_fail})"
        else:
            status = f"✓ {primary_fail}"
        
        print(f"  {status:50} CLAIM {i:02d} ({claim_id})")
    
    # Aggregate per-gate results
    results["per_gate_results"] = gate_hits
    
    # Save results
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n[3] Real TRI Results Summary\n")
    print(f"  Total claims: {results['total_claims']}")
    print(f"  Processed: {results['claims_processed']}")
    print(f"  Escapes: {results['escape_count']} ({100*results['escape_count']/max(results['total_claims'],1):.1f}%)")
    print(f"  Misfires: {results['misfire_count']} ({100*results['misfire_count']/max(results['total_claims'],1):.1f}%)")
    
    print(f"\n[4] Per-Gate Performance (REAL TRI RESULTS)\n")
    for gate_name in sorted(gate_hits.keys()):
        gate_result = gate_hits[gate_name]
        pass_count = gate_result.get("PASS", 0)
        fail_count = gate_result.get("FAIL", 0)
        warn_count = gate_result.get("WARN", 0)
        total = pass_count + fail_count + warn_count
        pass_rate = 100 * pass_count / total if total > 0 else 0
        
        print(f"  {gate_name:40} | P:{pass_count:2} F:{fail_count:2} W:{warn_count:2} ({pass_rate:.0f}%)")
    
    print(f"\n[5] Verdict")
    if results["escape_count"] == 0 and results["misfire_count"] == 0:
        print(f"  ✓ PERFECT: All claims caught, no escapes, no misfires")
    elif results["escape_count"] == 0:
        print(f"  ✓ GOOD: No escapes, acceptable misfire rate (<20%)")
    elif results["escape_count"] < len(claim_files) * 0.1:
        print(f"  ~ ACCEPTABLE: Low escape rate, investigate remaining")
    else:
        print(f"  ✗ CRITICAL: {results['escape_count']} escapes remain")
    
    results["status"] = "complete"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(description="ACG Real TRI Runner")
    parser.add_argument("--run-id", type=str, default="000002", help="Run identifier")
    parser.add_argument("--policy-hash", type=str, default="sha256:policy_v1_2026_01", 
                        help="Policy hash for TRI verification")
    parser.add_argument("--output-dir", type=str, default="oracle_town/state/acg", 
                        help="ACG output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose TRI output")
    
    args = parser.parse_args()
    
    run_real_tri_on_suite(args.run_id, args.policy_hash, args.output_dir, args.verbose)


if __name__ == "__main__":
    main()
