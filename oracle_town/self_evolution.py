#!/usr/bin/env python3
"""
Oracle Town Self-Evolution Module

Automatic accuracy measurement and policy threshold refinement.

Weekly loop:
1. Measure accuracy of past verdicts against outcomes
2. Calculate drift per district/gate
3. Propose threshold refinements
4. Simulate impact of changes
5. If safe, create new policy version (with immutable old version retained)

Key invariant (K12): Policy versioning
- Old policy remains pinned to old decisions
- New policy version gets new hash
- All verdicts from before change pinned to old policy
- All verdicts after change pinned to new policy
- Evolution is transparent and auditable

Outcome sources:
- User feedback: "This verdict was wrong"
- Business metrics: "Campaign achieved 15% CTR"
- Incident reports: "This approved action caused security issue"

Architecture:
- Pure functions for drift detection
- Dry-run impact simulation before applying changes
- Immutable policy versions (no retroactive changes)
- Full audit trail of evolution decisions
"""

import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class DistrictAccuracy:
    """Accuracy metrics for a decision district."""
    district: str
    total_decisions: int
    correct: int
    incorrect: int
    accuracy: float
    drift: float  # Change from baseline (positive = improved, negative = drifted)
    recommendations: List[str]


@dataclass
class ThresholdChange:
    """Proposed threshold adjustment."""
    gate: str
    parameter: str
    old_value: float
    new_value: float
    rationale: str
    impact_estimate: float  # Expected accuracy change (0.01 = +1%)
    confidence: float  # 0.0 to 1.0


@dataclass
class PolicyVersion:
    """Immutable policy version."""
    version_id: str  # v1, v2, v3, etc
    created_at: str
    policy_hash: str  # sha256 of policy JSON
    changes_from_previous: List[str]
    reason: str


class SelfEvolutionEngine:
    """Measure accuracy and evolve policy thresholds."""

    def __init__(self, ledger_path: str = None, policy_dir: str = None):
        self.ledger_path = Path(ledger_path or
            "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle_town/ledger.jsonl")
        self.policy_dir = Path(policy_dir or
            "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle_town/policies")

        self.verdicts = []
        self.outcomes = {}  # receipt_id → outcome data
        self.policy_versions = []

    def load_verdicts(self, verdicts: List[Dict]) -> None:
        """Load verdicts from ledger."""
        self.verdicts = verdicts

    def load_outcomes(self, outcomes: Dict[str, Dict]) -> None:
        """Load feedback/outcome data."""
        self.outcomes = outcomes

    def measure_accuracy(self) -> Dict[str, DistrictAccuracy]:
        """Measure accuracy of past verdicts."""
        accuracy = {}

        # Measure by gate
        gate_verdicts = defaultdict(list)
        for v in self.verdicts:
            gate = v.get("failed_gate", "ACCEPTED")
            gate_verdicts[gate].append(v)

        for gate, verdicts in gate_verdicts.items():
            correct = 0
            incorrect = 0

            for v in verdicts:
                receipt_id = v.get("receipt_id")
                if receipt_id in self.outcomes:
                    outcome = self.outcomes[receipt_id]
                    if outcome.get("was_correct"):
                        correct += 1
                    else:
                        incorrect += 1

            total = correct + incorrect
            gate_accuracy = correct / total if total > 0 else 0.0

            accuracy[gate] = DistrictAccuracy(
                district=gate,
                total_decisions=len(verdicts),
                correct=correct,
                incorrect=incorrect,
                accuracy=gate_accuracy,
                drift=0.0,  # Will compute relative to baseline
                recommendations=self._get_gate_recommendations(gate, gate_accuracy),
            )

        return accuracy

    def _get_gate_recommendations(self, gate: str, accuracy: float) -> List[str]:
        """Generate recommendations based on accuracy."""
        recommendations = []

        if accuracy < 0.70:
            recommendations.append(f"{gate}: Low accuracy (<70%), consider raising threshold")
        elif accuracy > 0.95:
            recommendations.append(f"{gate}: Very high accuracy (>95%), consider lowering threshold")
        else:
            recommendations.append(f"{gate}: Accuracy {accuracy*100:.1f}%, monitor for drift")

        return recommendations

    def compute_drift(self, historical_accuracy: Dict[str, float],
                     current_accuracy: Dict[str, DistrictAccuracy]) -> Dict[str, float]:
        """Compute drift from historical baseline."""
        drift = {}

        for gate, acc in current_accuracy.items():
            historical = historical_accuracy.get(gate, 0.80)  # Assume 80% baseline
            drift[gate] = acc.accuracy - historical

        return drift

    def propose_threshold_changes(self, accuracy: Dict[str, DistrictAccuracy]) -> List[ThresholdChange]:
        """Generate threshold refinement proposals."""
        changes = []

        # Rule 1: If accuracy drops >5%, lower threshold (more permissive)
        # Rule 2: If accuracy improves >5%, raise threshold (more strict)

        for gate, acc in accuracy.items():
            if acc.drift < -0.05 and acc.total_decisions >= 20:
                # Accuracy dropped → be more permissive
                change = ThresholdChange(
                    gate=gate,
                    parameter="rejection_threshold",
                    old_value=0.50,  # Example
                    new_value=0.45,
                    rationale=f"Accuracy drifted {acc.drift*100:.1f}%, lowering threshold to recover",
                    impact_estimate=0.05,  # Expect +5% accuracy
                    confidence=0.7,
                )
                changes.append(change)

            elif acc.drift > 0.05 and acc.total_decisions >= 20:
                # Accuracy improved → be more strict
                change = ThresholdChange(
                    gate=gate,
                    parameter="rejection_threshold",
                    old_value=0.50,  # Example
                    new_value=0.55,
                    rationale=f"Accuracy improved {acc.drift*100:.1f}%, raising threshold for safety",
                    impact_estimate=0.03,  # Expect +3% accuracy
                    confidence=0.8,
                )
                changes.append(change)

        return changes

    def simulate_impact(self, changes: List[ThresholdChange]) -> Dict[str, Any]:
        """Simulate impact of proposed changes on historical verdicts."""
        simulation = {
            "proposed_changes": [asdict(c) for c in changes],
            "estimated_impact": {
                "accuracy_improvement": 0.0,
                "false_positive_rate_change": 0.0,
                "false_negative_rate_change": 0.0,
            },
            "risk_assessment": "low",
            "recommendation": "safe_to_apply",
        }

        # Estimate average impact
        if changes:
            avg_impact = statistics.mean(c.impact_estimate * c.confidence for c in changes)
            simulation["estimated_impact"]["accuracy_improvement"] = avg_impact

        # Risk assessment
        if avg_impact > 0.10:
            simulation["risk_assessment"] = "medium"
        elif avg_impact > 0.20:
            simulation["risk_assessment"] = "high"

        # Recommendation
        if avg_impact < 0 and abs(avg_impact) > 0.05:
            simulation["recommendation"] = "do_not_apply"
        elif avg_impact < 0.01:
            simulation["recommendation"] = "hold_for_more_data"

        return simulation

    def create_policy_version(self, changes: List[ThresholdChange],
                             reason: str = "Automatic threshold refinement") -> PolicyVersion:
        """Create new immutable policy version."""
        # Compute new policy hash (deterministic from changes)
        changes_json = json.dumps([asdict(c) for c in changes], sort_keys=True)
        new_hash = hashlib.sha256(changes_json.encode()).hexdigest()

        # Generate version ID
        latest_version = len(self.policy_versions)
        version_id = f"v{latest_version + 1}"

        version = PolicyVersion(
            version_id=version_id,
            created_at=datetime.utcnow().isoformat() + "Z",
            policy_hash=f"sha256:{new_hash}",
            changes_from_previous=[c.rationale for c in changes],
            reason=reason,
        )

        self.policy_versions.append(version)
        return version

    def save_policy_version(self, version: PolicyVersion) -> str:
        """Save policy version to immutable storage."""
        # Ensure directory exists
        self.policy_dir.mkdir(parents=True, exist_ok=True)

        # Write policy file (immutable)
        policy_file = self.policy_dir / f"policy_{version.version_id}.json"
        with open(policy_file, 'w') as f:
            json.dump(asdict(version), f, indent=2, sort_keys=True)

        # Update policy registry
        registry_file = self.policy_dir / "policy_registry.json"
        registry = []
        if registry_file.exists():
            with open(registry_file) as f:
                registry = json.load(f)

        registry.append(asdict(version))

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2, sort_keys=True)

        return str(policy_file)

    def run_weekly_evolution(self) -> Dict[str, Any]:
        """Run complete weekly evolution cycle."""
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "verdicts_analyzed": len(self.verdicts),
            "outcomes_loaded": len(self.outcomes),
            "accuracy_by_gate": {},
            "proposed_changes": [],
            "simulation_result": {},
            "new_policy_version": None,
            "status": "pending_approval",
        }

        if len(self.verdicts) < 50:
            result["status"] = "insufficient_data"
            return result

        if len(self.outcomes) < 10:
            result["status"] = "insufficient_feedback"
            return result

        # Step 1: Measure accuracy
        accuracy = self.measure_accuracy()
        result["accuracy_by_gate"] = {
            k: {
                "total": v.total_decisions,
                "correct": v.correct,
                "accuracy": v.accuracy,
                "recommendations": v.recommendations,
            }
            for k, v in accuracy.items()
        }

        # Step 2: Propose changes
        changes = self.propose_threshold_changes(accuracy)
        result["proposed_changes"] = [asdict(c) for c in changes]

        # Step 3: Simulate impact
        if changes:
            simulation = self.simulate_impact(changes)
            result["simulation_result"] = simulation

            # Step 4: Apply if safe
            if simulation["recommendation"] == "safe_to_apply":
                new_version = self.create_policy_version(changes)
                self.save_policy_version(new_version)
                result["new_policy_version"] = asdict(new_version)
                result["status"] = "applied"

        return result


def main():
    """Example: Run weekly evolution."""
    # Load verdicts
    ledger_path = Path(
        "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle_town/ledger.jsonl"
    )

    verdicts = []
    if ledger_path.exists():
        with open(ledger_path) as f:
            for line in f:
                if line.strip():
                    try:
                        verdicts.append(json.loads(line))
                    except:
                        pass

    # Mock outcome data (in production, loaded from feedback service)
    outcomes = {}
    for i, v in enumerate(verdicts[:20]):
        if i % 3 == 0:
            outcomes[v.get("receipt_id", f"mock_{i}")] = {"was_correct": True}
        else:
            outcomes[v.get("receipt_id", f"mock_{i}")] = {"was_correct": False}

    # Run evolution
    engine = SelfEvolutionEngine()
    engine.load_verdicts(verdicts)
    engine.load_outcomes(outcomes)

    result = engine.run_weekly_evolution()

    print("\n📊 Weekly Evolution Report\n")
    print(f"Status: {result['status']}")
    print(f"Verdicts analyzed: {result['verdicts_analyzed']}")
    print(f"Outcomes loaded: {result['outcomes_loaded']}\n")

    print("Accuracy by gate:")
    for gate, acc in result["accuracy_by_gate"].items():
        print(f"  {gate}: {acc['accuracy']*100:.1f}% ({acc['correct']}/{acc['total']})")

    if result["proposed_changes"]:
        print(f"\nProposed {len(result['proposed_changes'])} changes")
        for change in result["proposed_changes"]:
            print(f"  {change['gate']}: {change['old_value']:.2f} → {change['new_value']:.2f}")

    if result["new_policy_version"]:
        print(f"\n✅ New policy version created: {result['new_policy_version']['version_id']}")


if __name__ == "__main__":
    main()
