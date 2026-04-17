#!/usr/bin/env python3
"""
Auto-Reflection Loop for Demonstrating Emergent Properties

Runs governance scenarios, detects emergence patterns, and verifies determinism.

Emergence Categories:
- E1: Quorum Convergence (independent attestors reach quorum)
- E2: Kill-Switch Propagation (single block halts run)
- E3: Policy-Bound Clustering (attestations cluster by obligation)
- E4: Rejection Cascades (reason ordering)
- E5: Trust Networks (key-class bindings)
"""

import json
import hashlib
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from oracle_town.core.mayor_rsm import MayorRSM, DecisionRecord
from oracle_town.core.policy import Policy


@dataclass
class EmergenceEvidence:
    """Evidence of an emergent property"""
    emergence_type: str  # E1, E2, E3, E4, E5
    description: str
    run_id: str
    timestamp: str
    evidence_data: Dict[str, Any]
    determinism_verified: bool
    replay_hash: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReflectionCycle:
    """One cycle of the reflection loop"""
    cycle_id: str
    scenarios_run: int
    emergence_detected: List[EmergenceEvidence]
    all_decisions_deterministic: bool
    cycle_hash: str

    def to_dict(self) -> Dict:
        return {
            "cycle_id": self.cycle_id,
            "scenarios_run": self.scenarios_run,
            "emergence_detected": [e.to_dict() for e in self.emergence_detected],
            "all_decisions_deterministic": self.all_decisions_deterministic,
            "cycle_hash": self.cycle_hash,
        }


class ScenarioGenerator:
    """Generate governance scenarios for emergence testing"""

    SCENARIO_TEMPLATES = [
        ("runA_missing_legal", "briefcase_base", "E1"),  # Missing quorum
        ("runB_revoked_key", "briefcase_base", "E4"),    # Revocation cascade
        ("runC_valid_quorum", "briefcase_base", "E1"),   # Quorum convergence
        ("runD_class_mismatch", "briefcase_base", "E4"), # Class mismatch cascade
        ("runE_key_rotation", "briefcase_base", "E4"),   # Key rotation cascade
        ("runF_allowlist_escape", "briefcase_security_review", "E5"),  # Trust network
        ("runG_policy_replay", "briefcase_base", "E3"),  # Policy clustering
        ("runH_registry_drift", "briefcase_base", "E5"), # Trust network drift
    ]

    def __init__(self, vectors_dir: Path, keys_dir: Path):
        self.vectors_dir = vectors_dir
        self.keys_dir = keys_dir

    def generate_scenario(self, template_tuple: Tuple[str, str, str]) -> Dict[str, Any]:
        """Generate a scenario from template tuple"""
        ledger_suffix, briefcase_name, expected_emergence = template_tuple

        policy = self._load_policy()
        briefcase = self._load_briefcase(briefcase_name)
        ledger = self._load_ledger(ledger_suffix)

        # Sync run_id
        briefcase["run_id"] = ledger["run_id"]

        # Special handling for Run G (policy replay attack)
        if "runG" in ledger_suffix:
            policy.policy_hash = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        return {
            "template": ledger_suffix,
            "policy": policy,
            "briefcase": briefcase,
            "ledger": ledger,
            "expected_emergence": expected_emergence,
        }

    def _load_policy(self) -> Policy:
        with open(self.vectors_dir / "policy_POL-TEST-1.json") as f:
            return Policy.from_dict(json.load(f))

    def _load_briefcase(self, name: str) -> Dict:
        with open(self.vectors_dir / f"{name}.json") as f:
            return json.load(f)

    def _load_ledger(self, suffix: str) -> Dict:
        with open(self.vectors_dir / f"ledger_{suffix}.json") as f:
            return json.load(f)


class EmergenceDetector:
    """Detect emergent properties from governance outcomes"""

    def detect(
        self,
        scenario: Dict[str, Any],
        decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """Detect emergence from scenario + decision"""
        emergence_type = scenario["expected_emergence"]

        if emergence_type == "E1":
            return self._detect_quorum_convergence(scenario, decision)
        elif emergence_type == "E2":
            return self._detect_kill_switch_propagation(scenario, decision)
        elif emergence_type == "E3":
            return self._detect_policy_clustering(scenario, decision)
        elif emergence_type == "E4":
            return self._detect_rejection_cascade(scenario, decision)
        elif emergence_type == "E5":
            return self._detect_trust_network(scenario, decision)
        else:
            return None

    def _detect_quorum_convergence(
        self, scenario: Dict, decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """E1: Detect independent attestors converging (or failing to converge) on quorum"""
        ledger = scenario["ledger"]
        attestations = ledger.get("attestations", [])

        # Check classes present with policy_match=1
        classes = set(a["attestor_class"] for a in attestations if a.get("policy_match") == 1)

        if decision.decision == "SHIP":
            desc = f"Quorum convergence SUCCESS: {len(classes)} classes independently attested"
        else:
            desc = f"Quorum convergence FAILED: only {len(classes)} classes present, need more"

        return EmergenceEvidence(
            emergence_type="E1",
            description=desc,
            run_id=decision.run_id,
            timestamp=datetime.utcnow().isoformat(),
            evidence_data={
                "classes_present": sorted(list(classes)),
                "attestation_count": len(attestations),
                "decision": decision.decision,
                "blocking_reasons": decision.blocking_reasons,
            },
            determinism_verified=False,
            replay_hash="",
        )

    def _detect_kill_switch_propagation(
        self, scenario: Dict, decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """E2: Detect kill-switch causing immediate global halt"""
        if decision.decision == "NO_SHIP" and decision.blocking_reasons:
            # Check if any reason mentions critical authority
            for reason in decision.blocking_reasons:
                if any(kw in reason.upper() for kw in ["LEGAL", "SECURITY", "KILL"]):
                    return EmergenceEvidence(
                        emergence_type="E2",
                        description="Kill-switch propagation: critical class blocked run",
                        run_id=decision.run_id,
                        timestamp=datetime.utcnow().isoformat(),
                        evidence_data={
                            "blocking_reasons": decision.blocking_reasons,
                            "decision": decision.decision,
                        },
                        determinism_verified=False,
                        replay_hash="",
                    )
        return None

    def _detect_policy_clustering(
        self, scenario: Dict, decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """E3: Detect policy-bound effects (version pinning, hash matching)"""
        ledger = scenario["ledger"]
        attestations = ledger.get("attestations", [])

        # Check policy hash distribution
        policy_hashes = set(a.get("policy_hash", "") for a in attestations)

        return EmergenceEvidence(
            emergence_type="E3",
            description=f"Policy clustering: {len(policy_hashes)} distinct policy hashes in attestations",
            run_id=decision.run_id,
            timestamp=datetime.utcnow().isoformat(),
            evidence_data={
                "policy_hashes": list(policy_hashes),
                "decision": decision.decision,
                "blocking_reasons": decision.blocking_reasons,
            },
            determinism_verified=False,
            replay_hash="",
        )

    def _detect_rejection_cascade(
        self, scenario: Dict, decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """E4: Detect which check fired first in rejection"""
        if decision.decision == "NO_SHIP" and decision.blocking_reasons:
            first_reason = decision.blocking_reasons[0]
            # Categorize the first blocker
            if "REVOK" in first_reason.upper():
                cascade_type = "KEY_REVOCATION"
            elif "CLASS" in first_reason.upper() or "MISMATCH" in first_reason.upper():
                cascade_type = "CLASS_MISMATCH"
            elif "SIGNATURE" in first_reason.upper():
                cascade_type = "SIGNATURE_INVALID"
            elif "POLICY" in first_reason.upper():
                cascade_type = "POLICY_VIOLATION"
            elif "QUORUM" in first_reason.upper():
                cascade_type = "QUORUM_FAILURE"
            else:
                cascade_type = "OTHER"

            return EmergenceEvidence(
                emergence_type="E4",
                description=f"Rejection cascade [{cascade_type}]: {first_reason[:60]}...",
                run_id=decision.run_id,
                timestamp=datetime.utcnow().isoformat(),
                evidence_data={
                    "cascade_type": cascade_type,
                    "reason_order": decision.blocking_reasons,
                    "first_blocker": first_reason,
                    "total_reasons": len(decision.blocking_reasons),
                },
                determinism_verified=False,
                replay_hash="",
            )
        return None

    def _detect_trust_network(
        self, scenario: Dict, decision: DecisionRecord
    ) -> Optional[EmergenceEvidence]:
        """E5: Detect registry-bound trust network effects"""
        ledger = scenario["ledger"]
        attestations = ledger.get("attestations", [])

        # Map keys to classes
        key_classes = {}
        for a in attestations:
            key_id = a.get("signing_key_id", "unknown")
            key_classes[key_id] = a.get("attestor_class", "unknown")

        # Check if any trust boundary was violated
        trust_violation = any(
            "ALLOWLIST" in r.upper() or "SCOPE" in r.upper()
            for r in decision.blocking_reasons
        )

        return EmergenceEvidence(
            emergence_type="E5",
            description=f"Trust network: {len(key_classes)} keys, violation={trust_violation}",
            run_id=decision.run_id,
            timestamp=datetime.utcnow().isoformat(),
            evidence_data={
                "key_class_bindings": key_classes,
                "unique_keys": len(key_classes),
                "trust_violation": trust_violation,
                "decision": decision.decision,
            },
            determinism_verified=False,
            replay_hash="",
        )


class DeterminismVerifier:
    """Verify decisions are deterministic across replays"""

    def __init__(self, mayor: MayorRSM):
        self.mayor = mayor

    def verify(
        self,
        policy: Policy,
        briefcase: Dict,
        ledger: Dict,
        replays: int = 10
    ) -> Tuple[bool, str]:
        """Run N replays and verify identical decision digest"""
        digests = []
        for _ in range(replays):
            decision = self.mayor.decide(policy, briefcase, ledger)
            digests.append(decision.decision_digest)

        unique = set(digests)
        is_deterministic = len(unique) == 1

        return (is_deterministic, digests[0] if is_deterministic else "NON_DETERMINISTIC")


class EmergenceLoop:
    """Main auto-reflection loop"""

    def __init__(self, vectors_dir: Path, keys_dir: Path):
        self.vectors_dir = vectors_dir
        self.keys_dir = keys_dir
        self.generator = ScenarioGenerator(vectors_dir, keys_dir)
        self.detector = EmergenceDetector()
        self.mayor = MayorRSM(public_keys_path=str(keys_dir / "public_keys.json"))
        self.verifier = DeterminismVerifier(self.mayor)

    def run_cycle(self, verbose: bool = True) -> ReflectionCycle:
        """Run one reflection cycle"""
        cycle_id = f"CYCLE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        emergence_list = []
        all_deterministic = True

        for template_tuple in ScenarioGenerator.SCENARIO_TEMPLATES:
            # Generate scenario
            scenario = self.generator.generate_scenario(template_tuple)

            # Execute governance
            decision = self.mayor.decide(
                scenario["policy"],
                scenario["briefcase"],
                scenario["ledger"]
            )

            if verbose:
                print(f"  {scenario['template']}: {decision.decision}")

            # Detect emergence
            evidence = self.detector.detect(scenario, decision)
            if evidence:
                # Verify determinism
                is_det, replay_hash = self.verifier.verify(
                    scenario["policy"],
                    scenario["briefcase"],
                    scenario["ledger"],
                    replays=10
                )
                evidence.determinism_verified = is_det
                evidence.replay_hash = replay_hash
                emergence_list.append(evidence)

                if not is_det:
                    all_deterministic = False

        # Compute cycle hash
        cycle_data = {
            "cycle_id": cycle_id,
            "emergence_count": len(emergence_list),
            "emergence_types": sorted([e.emergence_type for e in emergence_list]),
        }
        cycle_hash = hashlib.sha256(
            json.dumps(cycle_data, sort_keys=True).encode()
        ).hexdigest()

        return ReflectionCycle(
            cycle_id=cycle_id,
            scenarios_run=len(ScenarioGenerator.SCENARIO_TEMPLATES),
            emergence_detected=emergence_list,
            all_decisions_deterministic=all_deterministic,
            cycle_hash=f"sha256:{cycle_hash}",
        )

    def run_multi_cycle(self, num_cycles: int = 3, verbose: bool = True) -> List[ReflectionCycle]:
        """Run multiple reflection cycles"""
        cycles = []
        for i in range(num_cycles):
            if verbose:
                print(f"\n{'='*60}")
                print(f"REFLECTION CYCLE {i+1}/{num_cycles}")
                print(f"{'='*60}")

            cycle = self.run_cycle(verbose=verbose)
            cycles.append(cycle)

            if verbose:
                print(f"\nCycle ID: {cycle.cycle_id}")
                print(f"Scenarios Run: {cycle.scenarios_run}")
                print(f"Emergence Detected: {len(cycle.emergence_detected)}")
                print(f"All Deterministic: {cycle.all_decisions_deterministic}")

                for evidence in cycle.emergence_detected:
                    print(f"\n  [{evidence.emergence_type}] {evidence.description}")
                    print(f"      Determinism: {evidence.determinism_verified}")
                    print(f"      Replay Hash: {evidence.replay_hash[:40]}...")

        return cycles


def main():
    """Run the auto-reflection loop"""
    parser = argparse.ArgumentParser(description="Oracle Town Auto-Reflection Loop")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles to run")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    vectors_dir = Path(__file__).parent / "test_vectors"
    keys_dir = Path(__file__).parent / "keys"

    loop = EmergenceLoop(vectors_dir, keys_dir)

    verbose = not args.quiet
    if verbose:
        print("="*60)
        print("ORACLE TOWN AUTO-REFLECTION LOOP")
        print("Demonstrating Emergent Properties")
        print("="*60)

    cycles = loop.run_multi_cycle(num_cycles=args.cycles, verbose=verbose)

    # Summary
    total_emergence = sum(len(c.emergence_detected) for c in cycles)
    all_det = all(c.all_decisions_deterministic for c in cycles)

    # Emergence type distribution
    type_counts = {}
    for c in cycles:
        for e in c.emergence_detected:
            type_counts[e.emergence_type] = type_counts.get(e.emergence_type, 0) + 1

    if verbose:
        print("\n" + "="*60)
        print("REFLECTION SUMMARY")
        print("="*60)
        print(f"Total Cycles: {len(cycles)}")
        print(f"Total Emergence Evidence: {total_emergence}")
        print(f"All Decisions Deterministic: {all_det}")
        print("\nEmergence Distribution:")
        for t, count in sorted(type_counts.items()):
            print(f"  {t}: {count}")
        print("\n" + "="*60)
        print("AUTO-REFLECTION COMPLETE")
        print("="*60)

    # Export if requested
    if args.export:
        export_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_cycles": len(cycles),
            "total_emergence": total_emergence,
            "all_deterministic": all_det,
            "type_distribution": type_counts,
            "cycles": [c.to_dict() for c in cycles],
        }
        with open(args.export, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"\nExported to: {args.export}")


if __name__ == "__main__":
    main()
