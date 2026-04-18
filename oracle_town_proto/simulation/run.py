#!/usr/bin/env python3
"""
Minimal Prototype Simulation: 10 Epochs, Dialectal Sovereignty Test

Runs 3 towns in parallel, detects parameter drift, validates invariants.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel.kernel import Kernel, Submission, LocalState
from npc.npc import NPCCohort
from feed.corse_ai_matin import CorseAiMatin


class Epoch:
    """One day of simulation."""

    def __init__(self, epoch_num: int, config: Dict):
        self.epoch = epoch_num
        self.config = config
        self.town_states: Dict[str, LocalState] = {}
        self.kernels: Dict[str, Kernel] = {}
        self.npcs: Dict[str, NPCCohort] = {}

        # Initialize
        for town_cfg in config["towns"]:
            town_id = town_cfg["id"]
            self.town_states[town_id] = LocalState(town_id=town_id)
            self.kernels[town_id] = Kernel(town_id, config)
            self.npcs[town_id] = NPCCohort(town_id, town_cfg["npc_count"])

    def run(self) -> Dict:
        """Execute one epoch: decisions → NPC observations → CORSE AI MATIN."""
        results = {
            "epoch": self.epoch,
            "town_decisions": {},
            "npc_observations": {},
            "corse_ai_matin": {},
            "parameter_stability": {},
        }

        # PHASE 1: Towns make decisions on synthetic submissions
        for town_id, kernel in self.kernels.items():
            submissions = self._generate_submissions(town_id)
            decisions = []

            for submission in submissions:
                receipt = kernel.decide(submission, self.town_states[town_id])
                decisions.append(receipt)

            results["town_decisions"][town_id] = decisions

        # PHASE 2: NPCs generate observations from local ledgers
        town_names = [t["id"] for t in self.config["towns"]]
        for town_id, cohort in self.npcs.items():
            observations = cohort.observe_all(
                self.town_states[town_id].ledger,
                self.epoch,
                town_names
            )
            results["npc_observations"][town_id] = observations
            self.town_states[town_id].npc_observations.extend(observations)

        # PHASE 3: Generate CORSE AI MATIN feed (read-only aggregator)
        all_bulletins = []
        for town_id in self.kernels.keys():
            # Create town bulletin from decisions
            ship_count = len([d for d in results["town_decisions"][town_id] if d["decision"] == "SHIP"])
            bulletin = {
                "town_id": town_id,
                "epoch": self.epoch,
                "timestamp": f"2026-03-{22 + self.epoch:02d}T10:00Z",
                "ship_count": ship_count,
                "no_ship_count": len(results["town_decisions"][town_id]) - ship_count,
            }
            all_bulletins.append(bulletin)

        # Ingest into CORSE AI MATIN (no transforms)
        messenger = CorseAiMatin(self.epoch)
        messenger.ingest(all_bulletins)
        feed_output = messenger.output()

        # Kill-switch check
        if not CorseAiMatin.validate_no_interpretation(feed_output):
            results["corse_ai_matin"]["KILL_SWITCH_TRIGGERED"] = True
            return results

        results["corse_ai_matin"] = feed_output

        # PHASE 4: Ingest CORSE AI MATIN (read-as-noise)
        for town_id in self.town_states.keys():
            self.town_states[town_id].foreign_observations.append(feed_output)

        # PHASE 5: Check parameter stability
        for town_id in self.kernels.keys():
            town_cfg = next(t for t in self.config["towns"] if t["id"] == town_id)
            current_threshold = self.kernels[town_id].dialect
            initial_threshold = town_cfg["SHIP_threshold"]

            results["parameter_stability"][town_id] = {
                "initial": initial_threshold,
                "current": current_threshold,
                "drift": current_threshold - initial_threshold,
            }

        return results

    def _generate_submissions(self, town_id: str, count: int = 3) -> List[Submission]:
        """Generate synthetic submissions for the epoch."""
        submissions = []
        for i in range(count):
            submission = Submission(
                town_id=town_id,
                submission_id=f"{town_id}-{self.epoch}-{i}",
                content=f"Claim {i}: metric observation from local data",
                is_override=False,
            )
            submissions.append(submission)
        return submissions


class DialectalSovereigntyTest:
    """Complete stress test: 10 epochs, prestige visibility, imitation detection."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)

        self.results: List[Dict] = []
        self.passed = True

    def run_simulation(self) -> Dict:
        """Run 10 epochs and detect any violations."""
        for epoch_num in range(1, 11):
            print(f"[Epoch {epoch_num:2d}] Running...", end=" ", flush=True)

            epoch = Epoch(epoch_num, self.config)
            epoch_result = epoch.run()
            self.results.append(epoch_result)

            # Check for violations
            violations = self._check_violations(epoch_num, epoch_result)
            if violations:
                print(f"VIOLATION: {violations}")
                self.passed = False
            else:
                print("OK")

        return self._final_report()

    def _check_violations(self, epoch: int, result: Dict) -> List[str]:
        """Detect any invariant violations."""
        violations = []

        # Violation 1: Parameter drift
        for town_id, stability in result["parameter_stability"].items():
            if stability["drift"] != 0:
                violations.append(
                    f"Parameter drift in {town_id}: {stability['drift']:+.1f}"
                )

        # Violation 2: CORSE AI MATIN kill-switch
        if result["corse_ai_matin"].get("KILL_SWITCH_TRIGGERED"):
            violations.append("CORSE AI MATIN interpretation detected")

        # Violation 3: Foreign observations referenced (would show in drift)
        # (Checked implicitly via drift detection)

        return violations

    def _final_report(self) -> Dict:
        """Generate final report."""
        return {
            "test": "Dialectal Sovereignty (Non-Emergence)",
            "epochs": 10,
            "passed": self.passed,
            "violations": [] if self.passed else ["See epoch logs above"],
            "conclusion": (
                "DIALECTAL SOVEREIGNTY HOLDS" if self.passed
                else "DIALECTAL SOVEREIGNTY VIOLATED"
            ),
        }


if __name__ == "__main__":
    config_path = Path(__file__).parent.parent / "config/towns.json"

    test = DialectalSovereigntyTest(str(config_path))
    report = test.run_simulation()

    print("\n" + "=" * 60)
    print(json.dumps(report, indent=2))
    print("=" * 60)

    sys.exit(0 if report["passed"] else 1)
