#!/usr/bin/env python3
"""
PHASE 1: Controlled Loop Exercise

Goal: Verify basic behavioral sanity under fixed conditions.
	- 20-30 cycles
	- Deterministic simulation CT
	- Fixed policy
	- Fixed briefcase
	- Log everything
	- Answer: Does CT adapt? Does it converge? Does it explore?

No features. No tuning. Just observation.
"""
import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Setup path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from oracle_town.runner import (
    make_temp_worktree, cleanup_worktree, apply_patch,
    Supervisor, IntakeAdapter, FactoryAdapter
)
from oracle_town.core.policy import Policy
from oracle_town.core.key_registry import KeyRegistry


class SimulationCT:
    """Deterministic CT that proposes increasingly refined ideas."""

    def __init__(self):
        self.cycle_count = 0
        self.last_blocking_reasons = []

    def generate(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a proposal based on previous feedback."""
        self.cycle_count += 1

        # Strategy: start simple, add tests based on blocking reasons
        if self.cycle_count == 1:
            # Proposal 1: basic test
            return {
                "proposal_bundle": {
                    "name": "add_initial_test",
                    "description_hash": "sha256:abc123"
                },
                "patches": [
                    {
                        "diff": """--- a/tests/test_phase1_001.py
+++ b/tests/test_phase1_001.py
@@ -0,0 +1,5 @@
+def test_phase1_basic():
+    assert True
""",
                        "rationale": "Add basic test"
                    }
                ]
            }

        elif self.cycle_count == 2:
            # Proposal 2: add another test
            return {
                "proposal_bundle": {
                    "name": "add_second_test",
                    "description_hash": "sha256:def456"
                },
                "patches": [
                    {
                        "diff": """--- a/tests/test_phase1_002.py
+++ b/tests/test_phase1_002.py
@@ -0,0 +1,5 @@
+def test_phase1_second():
+    assert 1 == 1
""",
                        "rationale": "Add second test"
                    }
                ]
            }

        else:
            # Proposals 3+: vary slightly
            test_num = self.cycle_count
            return {
                "proposal_bundle": {
                    "name": f"test_iteration_{test_num}",
                    "description_hash": f"sha256:iter{test_num:06d}"
                },
                "patches": [
                    {
                        "diff": f"""--- a/tests/test_phase1_{test_num:03d}.py
+++ b/tests/test_phase1_{test_num:03d}.py
@@ -0,0 +1,5 @@
+def test_phase1_cycle_{test_num}():
+    assert {test_num % 2 == 0}
""",
                        "rationale": f"Cycle {test_num}: variation on pattern"
                    }
                ]
            }


class Phase1Logger:
    """Structured logging for Phase 1."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cycles = []
        self.summary = {
            "phase": "phase1_controlled_exercise",
            "started_at": datetime.utcnow().isoformat(),
            "cycles": [],
            "blocking_reasons_frequency": {},
            "convergence_metrics": {},
        }

    def log_cycle(
        self,
        cycle_num: int,
        ct_output: Dict[str, Any],
        supervisor_decision: Dict[str, Any],
        intake_decision: Dict[str, Any],
        factory_result: Optional[Dict[str, Any]],
        mayor_decision: Dict[str, Any],
        workdir: Optional[str] = None
    ):
        """Log a single cycle."""
        cycle_record = {
            "cycle": cycle_num,
            "timestamp": datetime.utcnow().isoformat(),
            "ct_output_hash": hashlib.sha256(json.dumps(ct_output, sort_keys=True).encode()).hexdigest(),
            "supervisor": {
                "decision": supervisor_decision.get("decision"),
                "reason_code": supervisor_decision.get("reason_code"),
            },
            "intake": {
                "decision": intake_decision.get("decision"),
                "kernel_code": intake_decision.get("kernel_code"),
            },
            "factory": {
                "success": factory_result.get("success") if factory_result else None,
                "attestation_count": len(factory_result.get("attestations", [])) if factory_result else 0,
            } if factory_result else None,
            "mayor": {
                "decision": mayor_decision.get("decision"),
                "reason_code": mayor_decision.get("reason_code"),
            }
        }

        self.cycles.append(cycle_record)

        # Track blocking reasons
        if "reason_codes" in mayor_decision:
            for code in mayor_decision["reason_codes"]:
                self.summary["blocking_reasons_frequency"][code] = \
                    self.summary["blocking_reasons_frequency"].get(code, 0) + 1

        # Save detailed cycle log
        cycle_log_path = self.output_dir / f"cycle_{cycle_num:03d}.json"
        with open(cycle_log_path, "w") as f:
            json.dump(cycle_record, f, indent=2)

    def finalize(self):
        """Write final summary."""
        self.summary["cycles"] = self.cycles
        self.summary["completed_at"] = datetime.utcnow().isoformat()
        self.summary["total_cycles"] = len(self.cycles)

        # Compute convergence metrics
        decisions = [c["mayor"]["decision"] for c in self.cycles]
        self.summary["convergence_metrics"] = {
            "ship_count": decisions.count("SHIP"),
            "no_ship_count": decisions.count("NO_SHIP"),
            "ship_rate": decisions.count("SHIP") / len(decisions) if decisions else 0,
            "decision_sequence": decisions,
        }

        # Save summary
        summary_path = self.output_dir / "PHASE1_SUMMARY.json"
        with open(summary_path, "w") as f:
            json.dump(self.summary, f, indent=2)

        print(f"\n✓ Phase 1 complete. Summary written to: {summary_path}")

        return self.summary


def run_phase1(
    max_cycles: int = 20,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run Phase 1: controlled loop exercise.

    Args:
        max_cycles: Maximum cycles to run
        output_dir: Directory for logs (default: ./phase1_logs/)

    Returns:
        Summary dict
    """
    if output_dir is None:
        output_dir = str(repo_root / "oracle_town/runner/phase1_logs")

    logger = Phase1Logger(output_dir)
    ct = SimulationCT()

    print("=" * 70)
    print("PHASE 1: CONTROLLED LOOP EXERCISE")
    print("=" * 70)
    print(f"Max cycles: {max_cycles}")
    print(f"Output dir: {output_dir}")
    print(f"CT mode: Simulation (deterministic)")
    print()

    # Load constitutional assets
    policy_path = repo_root / "oracle_town/runs/runC_ship_quorum_valid/policy.json"
    registry_path = repo_root / "oracle_town/keys/public_keys.json"

    if not policy_path.exists():
        # Fallback to test vector policy
        policy_path = repo_root / "oracle_town/test_vectors/policy_POL-TEST-1.json"

    if not policy_path.exists():
        print(f"✗ Policy not found")
        return {}

    with open(policy_path) as f:
        policy_data = json.load(f)
    policy = Policy.from_dict(policy_data)
    registry = KeyRegistry(str(registry_path))

    supervisor = Supervisor()
    intake = IntakeAdapter()
    factory = FactoryAdapter(
        str(registry_path),
        policy.policy_hash,
        registry.registry_hash
    )

    print(f"Policy: {policy.policy_id} (hash: {policy.policy_hash[:16]}...)")
    print(f"Registry: (hash: {registry.registry_hash[:16]}...)")
    print()

    # Placeholder for Mayor integration (will be called once step 5 complete)
    # For now, mock it
    def mock_mayor_decide(attestations_count: int) -> Dict[str, Any]:
        """Mock Mayor decision based on attestation count."""
        if attestations_count == 0:
            return {
                "decision": "NO_SHIP",
                "reason_code": "NO_RECEIPTS",
                "reason_codes": ["NO_RECEIPTS"]
            }
        elif attestations_count >= 2:
            return {
                "decision": "SHIP",
                "reason_code": "ALL_OBLIGATIONS_MET",
                "reason_codes": []
            }
        else:
            return {
                "decision": "NO_SHIP",
                "reason_code": "QUORUM_MISSING",
                "reason_codes": ["QUORUM_MISSING"]
            }

    # Run cycles
    for cycle_num in range(1, max_cycles + 1):
        print(f"[Cycle {cycle_num}/{max_cycles}]", end=" ")

        # Step 1: CT generates
        ct_output = ct.generate()
        print("CT→", end=" ")

        # Step 2: Supervisor sanitizes
        sup_decision = supervisor.evaluate(ct_output)
        if sup_decision.decision == "REJECT":
            print(f"Sup✗({sup_decision.reason_code.value[:8]}...)")
            logger.log_cycle(
                cycle_num, ct_output,
                {"decision": "REJECT", "reason_code": sup_decision.reason_code.value},
                {"decision": "REJECT", "kernel_code": None},
                None,
                {"decision": "NO_SHIP", "reason_code": "SUPERVISOR_REJECTED", "reason_codes": ["SUPERVISOR_REJECTED"]}
            )
            continue

        print("Sup✓→", end=" ")

        # Step 3: Intake validates
        intake_decision = intake.evaluate(ct_output["proposal_bundle"])
        if intake_decision.decision == "REJECT":
            print(f"Int✗({intake_decision.adapter_code.value[:8]}...)")
            logger.log_cycle(
                cycle_num, ct_output,
                {"decision": "PASS", "reason_code": None},
                {"decision": "REJECT", "kernel_code": intake_decision.kernel_code.value if intake_decision.kernel_code else None},
                None,
                {"decision": "NO_SHIP", "reason_code": "INTAKE_REJECTED", "reason_codes": ["INTAKE_REJECTED"]}
            )
            continue

        print("Int✓→", end=" ")

        # Step 4: Worktree + Factory
        workdir = None
        attestations_count = 0
        try:
            workdir = make_temp_worktree(str(repo_root))

            # Apply patches
            for patch in ct_output.get("patches", []):
                result = apply_patch(workdir, patch["diff"])
                if not result.success:
                    print(f"Patch✗")
                    logger.log_cycle(
                        cycle_num, ct_output,
                        {"decision": "PASS", "reason_code": None},
                        {"decision": "ACCEPT", "kernel_code": None},
                        {"success": False, "attestations": []},
                        {"decision": "NO_SHIP", "reason_code": "PATCH_FAILED", "reason_codes": ["PATCH_FAILED"]}
                    )
                    continue

            # Run factory (mock: assume pytest success)
            attestations_count = 1  # Mock: assume one passing test
            print("Fact✓→", end=" ")

        except Exception as e:
            print(f"Error: {e}")
            continue

        finally:
            if workdir:
                cleanup_worktree(workdir)

        # Step 5: Mayor decides (mock)
        mayor_decision = mock_mayor_decide(attestations_count)
        print(f"Mayor: {mayor_decision['decision'][:4]}")

        logger.log_cycle(
            cycle_num, ct_output,
            {"decision": "PASS", "reason_code": None},
            {"decision": "ACCEPT", "kernel_code": None},
            {"success": True, "attestations": [{"id": f"att_{cycle_num}"}] * attestations_count},
            mayor_decision
        )

        # Early exit if SHIP
        if mayor_decision["decision"] == "SHIP":
            print(f"\n✓ SHIP reached at cycle {cycle_num}")
            break

    # Finalize
    summary = logger.finalize()

    print()
    print("=" * 70)
    print(f"Summary: {summary['total_cycles']} cycles completed")
    print(f"SHIP rate: {summary['convergence_metrics']['ship_rate']:.2%}")
    print(f"Blocking reasons: {summary['blocking_reasons_frequency']}")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_phase1(max_cycles=20)
