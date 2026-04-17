#!/usr/bin/env python3
"""
Adversarial Claim Generator (ACG) v1.0

Generates N plausible claims engineered to fail for specific constitutional reasons.
Used to stress-test the K-invariant layer and measure gate effectiveness.

Usage:
  python3 acg_generate.py --seed 1337 --n 50 --run-id 000002 --policy-hash sha256:policy_v1_2026_01

Output:
  oracle_town/state/acg/run_<run_id>/
    ├── claims/ (claim_001.json through claim_050.json)
    ├── manifest.json (metadata, seed, distribution)
    └── results.json (will be populated after TRI pipeline)
"""

import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════
# ADVERSARIAL CLAIM TAXONOMY
# ═══════════════════════════════════════════════════════════════

@dataclass
class AdversarialClaim:
    """Template for an adversarial claim with expected failure mode"""
    
    claim_number: int
    category: str  # K1, K0, K2, K7, K5
    subcategory: str
    intended_primary_gate: str  # which gate should catch this
    description: str  # what makes this adversarial
    
    @property
    def claim_id(self) -> str:
        """Generate deterministic claim ID from number and category"""
        return f"acg_claim_{self.category}_{self.claim_number:03d}"


def generate_k1_schema_failures(start_num: int = 1, count: int = 1) -> List[Dict]:
    """
    K1: Fail-Closed (missing/ambiguous evidence)

    Goal: prove system rejects underspecified legitimacy
    """
    claims = []

    # K1-001: Missing acceptance_criteria entirely
    if count >= 1:
        claims.append({
            "claim_number": start_num,
            "category": "K1",
            "subcategory": "missing_acceptance_criteria",
            "intended_primary_gate": "schema_valid",
            "description": "Claim lacks acceptance_criteria field entirely",
            "claim": {
                "id": f"acg_claim_K1_{start_num:03d}",
                "timestamp": "2026-01-31T10:00:00Z",
                "target": "oracle_town/jobs/obs_scan.py",
                "claim_type": "code_change",
                "proposed_diffs": [
                    {
                        "path": "oracle_town/jobs/obs_scan.py",
                        "operation": "modify",
                        "hash_before": "sha256:abc123",
                        "hash_after": "sha256:def456"
                    }
                ],
                "evidence_pointers": [
                    {
                        "type": "test_result",
                        "path": "artifacts/test_valid.txt",
                        "hash": "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7",
                        "description": "All tests pass"
                    }
                ],
                # MISSING: acceptance_criteria (intentional K1 failure)
                "expected_outcomes": ["all_tests_pass"]
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": "Test missing acceptance criteria"
            }
        })

    # K1-002: Acceptance criteria non-machine-checkable
    if count >= 2:
        claims.append({
            "claim_number": start_num + 1,
            "category": "K1",
            "subcategory": "non_checkable_acceptance",
            "intended_primary_gate": "schema_valid",
            "description": "Acceptance criteria uses only vague language",
            "claim": {
                "id": f"acg_claim_K1_{start_num+1:03d}",
                "timestamp": "2026-01-31T10:01:00Z",
                "target": "oracle_town/jobs/ins_cluster.py",
                "claim_type": "code_change",
                "proposed_diffs": [
                    {
                        "path": "oracle_town/jobs/ins_cluster.py",
                        "operation": "modify",
                        "hash_before": "sha256:abc111",
                        "hash_after": "sha256:def222"
                    }
                ],
                "evidence_pointers": [
                    {
                        "type": "test_result",
                        "path": "artifacts/test_valid.txt",
                        "hash": "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7",
                        "description": "Tests"
                    }
                ],
                "acceptance_criteria": ["should be better", "looks good", "seems fine"],  # Non-checkable
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": "Test non-checkable acceptance criteria"
            }
        })

    # K1-003+: Evidence pointer with dangling reference (can generate multiple)
    for i in range(2, count):
        claims.append({
            "claim_number": start_num + i,
            "category": "K1",
            "subcategory": f"dangling_evidence_{i}",
            "intended_primary_gate": "schema_valid",
            "description": f"Evidence pointer references non-existent file (variant {i})",
            "claim": {
                "id": f"acg_claim_K1_{start_num+i:03d}",
                "timestamp": f"2026-01-31T10:0{i}:00Z",
                "target": "oracle_town/jobs/brf_onepager.py",
                "claim_type": "code_change",
                "proposed_diffs": [],
                "evidence_pointers": [
                    {
                        "type": "test_result",
                        "path": f"/nonexistent/test_result_variant_{i}.json",
                        "hash": "sha256:notreal",
                        "description": f"Tests passed variant {i}"
                    }
                ],
                "acceptance_criteria": ["all_tests_pass"],
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": f"Test dangling evidence reference variant {i}"
            }
        })

    return claims


def generate_k0_authority_failures(start_num: int = 13, count: int = 1) -> List[Dict]:
    """
    K0: Authority Separation (registry/legitimacy)
    
    Goal: prove legitimacy cannot be forged by "almost right"
    """
    claims = []
    
    # K0-001: Unregistered attestor (generate `count` variants)
    for i in range(count):
        claims.append({
            "claim_number": start_num + i,
            "category": "K0",
            "subcategory": f"unregistered_attestor_{i}",
            "intended_primary_gate": "K0_attestor_not_registered",
            "description": f"Attestor key format correct but never registered (variant {i})",
            "claim": {
                "id": f"acg_claim_K0_{start_num+i:03d}",
                "timestamp": f"2026-01-31T10:1{i}:00Z",
                "target": "oracle_town/jobs/obs_scan.py",
                "claim_type": "code_change",
                "proposed_diffs": [{"path": "obs_scan.py", "operation": "modify", "hash_before": "a", "hash_after": "b"}],
                "evidence_pointers": [{"type": "test_result", "path": "artifacts/test_valid.txt", "hash": "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7", "description": "ok"}],
                "acceptance_criteria": ["test_pass"],
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": f"key-never-registered-{start_num+i}",  # NOT in registry
                "intent": f"Test unregistered attestor rejection variant {i}"
            }
        })
    
    return claims


def generate_k2_no_self_attestation(start_num: int = 23, count: int = 1) -> List[Dict]:
    """
    K2: No Self-Attestation (circularity prevention)
    
    Goal: prevent "I generated the evidence I'm using"
    """
    claims = []
    
    # K2: Evidence from self / self-reference (generate `count` variants)
    for i in range(count):
        # Alternate between ephemeral path and explicit self-reference
        if i % 2 == 0:
            # Ephemeral evidence variant
            claims.append({
                "claim_number": start_num + i,
                "category": "K2",
                "subcategory": f"evidence_from_ephemeral_{i}",
                "intended_primary_gate": "K2_no_self_attestation",
                "description": f"Evidence pointer from ephemeral location (variant {i})",
                "claim": {
                    "id": f"acg_claim_K2_{start_num+i:03d}",
                    "timestamp": f"2026-01-31T10:2{i}:00Z",
                    "target": "oracle_town/jobs/obs_scan.py",
                    "claim_type": "code_change",
                    "proposed_diffs": [{"path": "obs_scan.py", "operation": "modify", "hash_before": "a", "hash_after": "b"}],
                    "evidence_pointers": [
                        {
                            "type": "test_result",
                            "path": f"/tmp/test_result_variant_{i}.json",  # Ephemeral!
                            "hash": "sha256:abc",
                            "description": f"Generated by claim variant {i}"
                        }
                    ],
                    "acceptance_criteria": ["test_pass"],
                    "policy_pack_hash": "sha256:policy_v1_2026_01",
                    "generated_by": "test-legal-001",
                    "intent": f"Test ephemeral evidence rejection variant {i}"
                }
            })
        else:
            # Self-reference variant
            claim_id = f"acg_claim_K2_{start_num+i:03d}"
            claims.append({
                "claim_number": start_num + i,
                "category": "K2",
                "subcategory": f"self_reference_{i}",
                "intended_primary_gate": "K2_no_self_attestation",
                "description": f"Claim parent_claim_id references itself (variant {i})",
                "claim": {
                    "id": claim_id,
                    "timestamp": f"2026-01-31T10:2{i}:00Z",
                    "target": "oracle_town/jobs/ins_cluster.py",
                    "claim_type": "code_change",
                    "proposed_diffs": [{"path": "ins.py", "operation": "modify", "hash_before": "a", "hash_after": "b"}],
                    "evidence_pointers": [{"type": "test_result", "path": "artifacts/test_valid.txt", "hash": "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7", "description": "ok"}],
                    "acceptance_criteria": ["test_pass"],
                    "parent_claim_id": claim_id,  # Self-reference!
                    "policy_pack_hash": "sha256:policy_v1_2026_01",
                    "generated_by": "test-legal-001",
                    "intent": f"Test circular claim rejection variant {i}"
                }
            })
    
    return claims


def generate_k7_authority_mutation(start_num: int = 33, count: int = 1) -> List[Dict]:
    """
    K7: Policy Pinning / Authority Mutation Prevention
    
    Goal: ensure claims can't sneak policy drift in
    """
    claims = []
    
    # K7: Policy/authority mutation (generate `count` variants)
    k7_targets = [
        ("oracle_town/keys/public_keys.json", "key_registry_update", "Key registry mutation"),
        ("oracle_town/schemas/claim.py", "policy_patch", "Claim schema mutation"),
        ("oracle_town/LEVEL_2_AUTHORITY.md", "policy_patch", "Authority spec mutation"),
        ("oracle_town/core/policy.py", "policy_patch", "Policy file mutation"),
    ]
    for i in range(count):
        target_idx = i % len(k7_targets)
        target, claim_type, desc = k7_targets[target_idx]
        claims.append({
            "claim_number": start_num + i,
            "category": "K7",
            "subcategory": f"mutate_authority_{i}",
            "intended_primary_gate": "K7_policy_pinning",
            "description": f"{desc} attempt (variant {i})",
            "claim": {
                "id": f"acg_claim_K7_{start_num+i:03d}",
                "timestamp": f"2026-01-31T10:3{i}:00Z",
                "target": target,
                "claim_type": claim_type,
                "proposed_diffs": [
                    {
                        "path": target,
                        "operation": "modify",
                        "hash_before": "sha256:original",
                        "hash_after": "sha256:modified"
                    }
                ],
                "evidence_pointers": [{"type": "test_result", "path": "artifacts/test_valid.txt", "hash": "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7", "description": "ok"}],
                "acceptance_criteria": ["mutation_approved"],
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": f"Test {desc} prevention variant {i}"
            }
        })
    
    return claims


def generate_k5_determinism_failures(start_num: int = 43, count: int = 1) -> List[Dict]:
    """
    K5: Determinism (nondeterminism detection)
    
    Goal: detect hidden nondeterminism under plausible inputs
    """
    claims = []
    
    # K5: Nondeterminism (dynamic selectors) - generate `count` variants
    dynamic_refs = [
        ("latest", "Uses 'latest' without freezing"),
        ("current", "References 'current' state"),
        ("today", "Uses 'today' as selector"),
        ("now", "Uses 'now' in logic"),
        ("HEAD", "References 'HEAD' revision"),
        ("main", "References 'main' branch"),
        ("latest_approved", "References 'latest approved' state"),
        ("this week", "Uses 'this week' timeframe"),
        ("recommended", "Uses 'recommended' value"),
        ("best", "Uses 'best' selection"),
    ]
    for i in range(count):
        ref_idx = i % len(dynamic_refs)
        ref_name, description = dynamic_refs[ref_idx]
        claims.append({
            "claim_number": start_num + i,
            "category": "K5",
            "subcategory": f"dynamic_selector_{ref_name}",
            "intended_primary_gate": "K5_determinism",
            "description": f"{description} (variant {i})",
            "claim": {
                "id": f"acg_claim_K5_{start_num+i:03d}",
                "timestamp": f"2026-01-31T10:4{i}:00Z",
                "target": "oracle_town/jobs/mem_link.py",
                "claim_type": "code_change",
                "proposed_diffs": [{"path": "mem_link.py", "operation": "modify", "hash_before": "a", "hash_after": "b"}],
                "evidence_pointers": [
                    {
                        "type": "dynamic_reference",
                        "path": ref_name,  # Dynamic!
                        "hash": "sha256:varies",
                        "description": f"Use {ref_name}"
                    }
                ],
                "acceptance_criteria": [f"use {ref_name} to decide"],
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": f"Test {ref_name} nondeterminism rejection variant {i}"
            }
        })
    
    return claims


def generate_all_claims(seed: int, n: int) -> tuple[List[Dict], Dict]:
    """
    Generate all N adversarial claims with balanced distribution.

    Distribution strategy:
    - First: Generate adversarial claims (K1, K0, K2, K7, K5)
    - Remainder: Valid control claims

    Returns: (claims_list, distribution_manifest)
    """
    claims = []

    # Scale adversarial counts proportionally to N, minimum 1 per category
    # For N=50: 10 per category (50 total)
    # For N=11: ~2 per category + 1 valid control
    if n < 10:
        # Minimum viable: 1 per K-gate + valid controls
        k1_count = 1
        k0_count = 1
        k2_count = 1
        k7_count = 1
        k5_count = 1
        control_count = max(n - 5, 0)
    else:
        # Scale proportionally
        adversarial_per_category = n // 5
        control_count = n % 5
        k1_count = adversarial_per_category
        k0_count = adversarial_per_category
        k2_count = adversarial_per_category
        k7_count = adversarial_per_category
        k5_count = adversarial_per_category

    # Generate adversarial claims with parameterized counts
    claims.extend(generate_k1_schema_failures(start_num=1, count=k1_count))
    claims.extend(generate_k0_authority_failures(start_num=1 + k1_count, count=k0_count))
    claims.extend(generate_k2_no_self_attestation(start_num=1 + k1_count + k0_count, count=k2_count))
    claims.extend(generate_k7_authority_mutation(start_num=1 + k1_count + k0_count + k2_count, count=k7_count))
    claims.extend(generate_k5_determinism_failures(start_num=1 + k1_count + k0_count + k2_count + k7_count, count=k5_count))

    # Add valid control claims to reach N
    # Note: evidence hash must match actual file in artifacts/test_valid.txt
    CONTROL_EVIDENCE_HASH = "sha256:16c280fd743a712b692a66e0b6aa46b6106211438c67b4f201e4f698ca8f0ad7"
    for i in range(control_count):
        control_claim = {
            "claim_number": 1 + k1_count + k0_count + k2_count + k7_count + k5_count + i,
            "category": "CONTROL",
            "subcategory": f"valid_control_{i+1}",
            "intended_primary_gate": "ACCEPT",
            "description": f"Valid control claim {i+1}",
            "claim": {
                "id": f"acg_claim_CONTROL_{i+1:03d}",
                "timestamp": "2026-01-31T10:50:00Z",
                "target": "oracle_town/jobs/obs_scan.py",
                "claim_type": "code_change",
                "proposed_diffs": [{"path": "obs_scan.py", "operation": "modify", "hash_before": "sha256:aaa", "hash_after": "sha256:bbb"}],
                "evidence_pointers": [{"type": "test_result", "path": "artifacts/test_valid.txt", "hash": CONTROL_EVIDENCE_HASH, "description": "valid control"}],
                "acceptance_criteria": ["all_tests_pass"],
                "policy_pack_hash": "sha256:policy_v1_2026_01",
                "generated_by": "test-legal-001",
                "intent": f"Valid control claim {i+1}"
            }
        }
        claims.append(control_claim)

    # Manifest
    manifest = {
        "seed": seed,
        "generated": datetime.now().isoformat(),
        "total_claims": len(claims),
        "n_requested": n,
        "distribution": {
            "K1_schema_failures": k1_count,
            "K0_authority_failures": k0_count,
            "K2_no_self_attestation": k2_count,
            "K7_authority_mutation": k7_count,
            "K5_determinism": k5_count,
            "CONTROL_valid": control_count
        },
        "gate_ordering": [
            "schema_valid",
            "K7_policy_pinning",
            "K0_attestor_registered",
            "K2_no_self_attestation",
            "K1_fail_closed",
            "K5_determinism"
        ]
    }

    return claims, manifest


def main():
    parser = argparse.ArgumentParser(description="Adversarial Claim Generator (ACG) v1.0")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for reproducibility")
    parser.add_argument("--n", type=int, default=11, help="Number of claims to generate")
    parser.add_argument("--run-id", type=str, default="000002", help="Run identifier")
    parser.add_argument("--policy-hash", type=str, default="sha256:policy_v1_2026_01", help="Policy hash to pin")
    parser.add_argument("--output-dir", type=str, default="oracle_town/state/acg", help="Output directory")
    
    args = parser.parse_args()
    
    # Generate claims
    claims, manifest = generate_all_claims(args.seed, args.n)
    
    # Create output structure
    output_dir = Path(args.output_dir) / f"run_{args.run_id}"
    claims_dir = output_dir / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    
    # Write claims
    for i, claim_dict in enumerate(claims, 1):
        claim_file = claims_dir / f"claim_{i:03d}.json"
        with open(claim_file, "w") as f:
            json.dump({"claim": claim_dict["claim"]}, f, indent=2)
    
    # Write manifest
    manifest["run_id"] = args.run_id
    manifest["policy_hash"] = args.policy_hash
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create empty results file (to be populated after TRI runs)
    results_file = output_dir / "results.json"
    results_template = {
        "run_id": args.run_id,
        "status": "pending",
        "created": datetime.now().isoformat(),
        "claims_processed": 0,
        "escape_count": 0,
        "misfire_count": 0,
        "per_gate_results": {},
        "claim_results": []
    }
    with open(results_file, "w") as f:
        json.dump(results_template, f, indent=2)
    
    print(f"✓ Generated {len(claims)} adversarial claims")
    print(f"✓ Output: {output_dir}/")
    print(f"  • Claims: {claims_dir}/")
    print(f"  • Manifest: {manifest_file}")
    print(f"  • Results template: {results_file}")
    print(f"\nDistribution:")
    for key, val in manifest["distribution"].items():
        print(f"  {key}: {val}")
    print(f"\nNext step: Feed claims through TRI pipeline")
    print(f"  python3 oracle_town/state/acg_run_tri.py --run-id {args.run_id}")


if __name__ == "__main__":
    main()
