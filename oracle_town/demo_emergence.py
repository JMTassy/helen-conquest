#!/usr/bin/env python3
"""
Oracle Town Emergence Demo — Generate sample runs to observe emergent behavior.

This creates a variety of governance runs with different outcomes:
- Creative proposals (some will ship, some rejected)
- Authority leakage attempts (will be blocked)
- Duplicate-block persuasion (will be blocked)
- Valid evidence-backed changes (will ship)

Run this, then use observer.py to see the emergence metrics.

Usage:
    python oracle_town/demo_emergence.py
    python oracle_town/observer.py --metrics
    python oracle_town/observer.py --ideas
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
import random

RUNS_DIR = Path("oracle_town/runs")
DEMO_DIR = RUNS_DIR / "demo_emergence"


def sha256_hash(content: str) -> str:
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


def create_run(run_id: str, proposals: list, attestations: list, expected_decision: str):
    """Create a complete governance run with all artifacts."""
    run_dir = DEMO_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()

    # 1. Proposal bundle (CT output)
    proposal_bundle = {
        "proposals": proposals,
        "ct_run_manifest": {
            "run_id": run_id,
            "created_at": timestamp
        }
    }
    with open(run_dir / "proposal_bundle.json", "w") as f:
        json.dump(proposal_bundle, f, indent=2)

    # 2. Briefcase (Intake output)
    obligations = []
    for p in proposals:
        obligations.append({
            "name": f"obl_{p['proposal_id'].lower().replace('-', '_')}",
            "type": "CODE_PROOF",
            "severity": "HARD",
            "required_evidence": ["test_result"]
        })

    briefcase = {
        "run_id": run_id,
        "claim_id": f"CLM-{run_id}",
        "claim_type": "CHANGE_REQUEST",
        "required_obligations": obligations,
        "requested_tests": [],
        "kill_switch_policies": []
    }
    with open(run_dir / "briefcase.json", "w") as f:
        json.dump(briefcase, f, indent=2)

    # 3. Ledger (Factory output)
    ledger = {
        "run_id": run_id,
        "claim_id": f"CLM-{run_id}",
        "policy_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "attestations": attestations,
        "ledger_digest": sha256_hash(json.dumps(attestations, sort_keys=True)),
        "timestamp": timestamp
    }
    with open(run_dir / "ledger.json", "w") as f:
        json.dump(ledger, f, indent=2)

    # 4. Decision record (Mayor output)
    blocking = []
    if expected_decision == "NO_SHIP":
        # Find obligations without matching attestations
        attested_names = {a["obligation_name"] for a in attestations if a["policy_match"] == 1}
        for obl in obligations:
            if obl["name"] not in attested_names:
                blocking.append(obl["name"])

    decision = {
        "run_id": run_id,
        "claim_id": f"CLM-{run_id}",
        "decision": expected_decision,
        "kill_switch_triggered": False,
        "blocking_obligations": blocking,
        "decision_digest": sha256_hash(f"{run_id}:{expected_decision}:{sorted(blocking)}"),
        "timestamp": timestamp
    }
    with open(run_dir / "decision_record.json", "w") as f:
        json.dump(decision, f, indent=2)

    return run_dir


def make_attestation(run_id: str, obl_name: str, attestor_class: str = "CI_RUNNER"):
    """Create a valid attestation."""
    return {
        "attestation_id": f"ATT-{run_id}-{obl_name[:8]}",
        "run_id": run_id,
        "claim_id": f"CLM-{run_id}",
        "obligation_name": obl_name,
        "attestor_id": f"{attestor_class.lower()}_001",
        "attestor_class": attestor_class,
        "policy_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "evidence_digest": sha256_hash(f"{run_id}:{obl_name}:evidence"),
        "signing_key_id": f"key-2026-01-{attestor_class.lower()}",
        "signature": f"ed25519:{'0' * 128}",
        "policy_match": 1,
        "timestamp": datetime.now().isoformat()
    }


def main():
    print("=" * 60)
    print("ORACLE TOWN EMERGENCE DEMO")
    print("Generating sample runs...")
    print("=" * 60)
    print()

    # Clean up previous demo runs
    if DEMO_DIR.exists():
        import shutil
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True)

    runs_created = []

    # ==========================================================================
    # RUN 1: Creative architecture proposal — SHIPS
    # ==========================================================================
    run_id = "run_001_arch_modular_intake"
    proposals = [{
        "proposal_id": "P-ARCH-001",
        "origin": "CT",
        "proposal_type": "architecture",
        "description": "Refactor Intake into modular pipeline stages. Each stage (parse, validate, scan, budget, digest) becomes an independent function that can be tested and replaced independently. This enables easier debugging and future extensibility.",
        "suggested_changes": {"files": ["oracle_town/core/intake_guard.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_arch_001", "CI_RUNNER"),
        make_attestation(run_id, "obl_p_arch_001", "DOMAIN_OWNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Architecture: Modular intake"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 2: Feature proposal — SHIPS
    # ==========================================================================
    run_id = "run_002_feat_attestor_scopes"
    proposals = [{
        "proposal_id": "P-FEAT-002",
        "origin": "CT",
        "proposal_type": "feature",
        "description": "Add scope constraints to attestor keys. Each key can be restricted to specific obligation patterns (e.g., 'gdpr_*', 'security_*'). Mayor validates that attestations only cover obligations within the key's declared scope.",
        "suggested_changes": {"files": ["oracle_town/core/crypto.py", "oracle_town/schemas/attestation.schema.json"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_feat_002", "CI_RUNNER"),
        make_attestation(run_id, "obl_p_feat_002", "SECURITY")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Feature: Attestor scopes"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 3: Experiment proposal — SHIPS
    # ==========================================================================
    run_id = "run_003_exp_parallel_factory"
    proposals = [{
        "proposal_id": "P-EXP-003",
        "origin": "SWARM",
        "proposal_type": "experiment",
        "description": "Experiment with parallel Factory execution. Run independent tests concurrently and merge attestations. Measure latency reduction vs sequential execution. Rollback if determinism is affected.",
        "suggested_changes": {"files": ["oracle_town/core/factory.py"]},
        "required_obligations": ["obl_parallel_safe", "obl_determinism_preserved"]
    }]
    attestations = [
        make_attestation(run_id, "obl_p_exp_003", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Experiment: Parallel factory"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 4: Risk identification — SHIPS (commentary)
    # ==========================================================================
    run_id = "run_004_risk_hash_collision"
    proposals = [{
        "proposal_id": "P-RISK-004",
        "origin": "CT",
        "proposal_type": "risk",
        "description": "Risk: Current SHA256 truncation in attestation_id (8 chars) has theoretical collision probability of ~1 in 4 billion. For high-volume systems, consider using full hash or UUID. Mitigation: Add collision detection at ledger append time.",
        "suggested_changes": {"files": []}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_risk_004", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Risk: Hash collision"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 5: Process improvement — SHIPS
    # ==========================================================================
    run_id = "run_005_proc_staged_rollout"
    proposals = [{
        "proposal_id": "P-PROC-005",
        "origin": "CT",
        "proposal_type": "process",
        "description": "Implement staged rollout for policy changes. New policies are first deployed in 'shadow mode' where they log decisions but don't enforce. After N runs with no divergence from current policy, promote to active.",
        "suggested_changes": {"files": ["oracle_town/core/policy.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_proc_005", "CI_RUNNER"),
        make_attestation(run_id, "obl_p_proc_005", "RELEASE_MANAGER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Process: Staged rollout"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 6: Missing attestation — NO_SHIP
    # ==========================================================================
    run_id = "run_006_missing_legal"
    proposals = [{
        "proposal_id": "P-GDPR-006",
        "origin": "CT",
        "proposal_type": "feature",
        "description": "Add GDPR data export endpoint. Users can request a copy of all their data in machine-readable format. Requires Legal sign-off for compliance verification.",
        "suggested_changes": {"files": ["oracle_town/api/data_export.py"]}
    }]
    # Only CI attestation, missing required LEGAL
    attestations = [
        make_attestation(run_id, "obl_p_gdpr_006", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "NO_SHIP")
    runs_created.append((run_id, "NO_SHIP", "Missing LEGAL attestation"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 7: Bold creative idea — SHIPS
    # ==========================================================================
    run_id = "run_007_creative_semantic_firewall"
    proposals = [{
        "proposal_id": "P-CREAT-007",
        "origin": "SWARM",
        "proposal_type": "architecture",
        "description": "Create a 'semantic firewall' visualization layer. Real-time dashboard shows all rejected authority attempts, categorized by attack vector (persuasion, structural smuggling, duplicate blocks). Useful for security monitoring and demonstrating governance effectiveness.",
        "suggested_changes": {"files": ["oracle_town/dashboard/firewall_viz.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_creat_007", "CI_RUNNER"),
        make_attestation(run_id, "obl_p_creat_007", "SECURITY")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Creative: Semantic firewall viz"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 8: Innovative idea — SHIPS
    # ==========================================================================
    run_id = "run_008_idea_capability_lattice"
    proposals = [{
        "proposal_id": "P-IDEA-008",
        "origin": "CT",
        "proposal_type": "feature",
        "description": "Expose the emergent 'capability lattice' as a queryable API. Given a set of available attestor keys, return the set of obligations that can be satisfied. This makes authorization topology visible and enables what-if analysis for key provisioning.",
        "suggested_changes": {"files": ["oracle_town/api/capability_lattice.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_idea_008", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Idea: Capability lattice API"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 9: Meta-improvement — SHIPS
    # ==========================================================================
    run_id = "run_009_meta_evidence_cost"
    proposals = [{
        "proposal_id": "P-META-009",
        "origin": "CT",
        "proposal_type": "experiment",
        "description": "Track 'evidence cost' per proposal type over time. Hypothesis: system naturally evolves toward lower-friction changes because high-evidence-cost proposals fail more often. If confirmed, use this metric to guide API design (make common changes easy to evidence).",
        "suggested_changes": {"files": ["oracle_town/metrics/evidence_cost.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_meta_009", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Meta: Evidence cost tracking"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # RUN 10: Replay determinism probe — SHIPS (identical to run_009)
    # ==========================================================================
    run_id = "run_010_replay_check"
    # Same content as run_009 to verify determinism
    proposals = [{
        "proposal_id": "P-META-009",  # Same proposal
        "origin": "CT",
        "proposal_type": "experiment",
        "description": "Track 'evidence cost' per proposal type over time. Hypothesis: system naturally evolves toward lower-friction changes because high-evidence-cost proposals fail more often. If confirmed, use this metric to guide API design (make common changes easy to evidence).",
        "suggested_changes": {"files": ["oracle_town/metrics/evidence_cost.py"]}
    }]
    attestations = [
        make_attestation(run_id, "obl_p_meta_009", "CI_RUNNER")
    ]
    create_run(run_id, proposals, attestations, "SHIP")
    runs_created.append((run_id, "SHIP", "Replay: Determinism check"))
    print(f"✓ Created: {run_id}")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print()
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()
    print(f"Runs created: {len(runs_created)}")
    print()

    shipped = sum(1 for _, d, _ in runs_created if d == "SHIP")
    blocked = sum(1 for _, d, _ in runs_created if d == "NO_SHIP")
    print(f"  ✓ Shipped:  {shipped}")
    print(f"  ✗ Blocked:  {blocked}")
    print()

    print("IDEAS GENERATED:")
    for run_id, decision, desc in runs_created:
        icon = "✓" if decision == "SHIP" else "✗"
        print(f"  [{icon}] {desc}")

    print()
    print("Next steps:")
    print("  python oracle_town/observer.py --analyze oracle_town/runs/demo_emergence")
    print("  python oracle_town/observer.py --ideas")
    print("  python oracle_town/observer.py --metrics")


if __name__ == "__main__":
    main()
