#!/usr/bin/env python3
"""
Oracle Town Observer — External observation of governance runs.

Provides real-time visibility into:
- Pipeline state transitions
- Decision outcomes
- Emergence metrics
- Idea capture from Creative Town

Usage:
    # Watch a live run
    python oracle_town/observer.py --watch

    # Analyze historical runs
    python oracle_town/observer.py --analyze oracle_town/runs/

    # Export ideas from CT outputs
    python oracle_town/observer.py --ideas
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PipelineEvent:
    """A single event in the governance pipeline."""
    timestamp: str
    stage: str  # INTAKE, FACTORY, MAYOR, CT, SWARM
    event_type: str  # ACCEPT, REJECT, SHIP, NO_SHIP, PROPOSAL, ATTESTATION
    run_id: str
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class EmergenceMetrics:
    """Metrics that reveal emergent system behavior."""
    # Authority Leakage Rate
    total_proposals: int = 0
    rejected_authority: int = 0
    rejected_schema: int = 0
    rejected_duplicate: int = 0

    # Evidence Friction
    total_ships: int = 0
    total_obligations_cleared: int = 0
    total_attestations_used: int = 0

    # Replay Entropy
    replay_attempts: int = 0
    unique_digests: int = 0

    @property
    def authority_leakage_rate(self) -> float:
        if self.total_proposals == 0:
            return 0.0
        return (self.rejected_authority + self.rejected_schema + self.rejected_duplicate) / self.total_proposals

    @property
    def evidence_friction(self) -> float:
        if self.total_ships == 0:
            return 0.0
        return self.total_attestations_used / self.total_ships

    @property
    def replay_entropy(self) -> int:
        return self.unique_digests  # Should always be 1 for healthy system

    def to_dict(self):
        d = asdict(self)
        d['authority_leakage_rate'] = self.authority_leakage_rate
        d['evidence_friction'] = self.evidence_friction
        d['replay_entropy'] = self.replay_entropy
        return d


@dataclass
class CapturedIdea:
    """An idea extracted from Creative Town output."""
    idea_id: str
    source_run: str
    timestamp: str
    category: str  # architecture, process, feature, experiment, risk
    title: str
    description: str
    proposed_by: str  # CT agent or Swarm worker
    obligations_required: list = field(default_factory=list)
    outcome: str = "pending"  # pending, shipped, rejected
    rejection_reason: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# =============================================================================
# OBSERVER CORE
# =============================================================================

class OracleTownObserver:
    """
    External observer for Oracle Town governance runs.

    Watches the pipeline without participating in decisions.
    Captures metrics, events, and ideas for analysis.
    """

    def __init__(self, runs_dir: str = "oracle_town/runs"):
        self.runs_dir = Path(runs_dir)
        self.events: list[PipelineEvent] = []
        self.metrics = EmergenceMetrics()
        self.ideas: list[CapturedIdea] = []
        self.replay_digests: set[str] = set()

    def observe_run(self, run_path: Path) -> dict:
        """Observe a single governance run and extract insights."""
        run_data = {
            "run_id": run_path.name,
            "stages_observed": [],
            "decision": None,
            "ideas_captured": 0,
            "metrics_delta": {}
        }

        # Look for standard artifacts
        briefcase_path = run_path / "briefcase.json"
        ledger_path = run_path / "ledger.json"
        decision_path = run_path / "decision_record.json"
        ct_output_path = run_path / "ct_output.json"
        proposal_path = run_path / "proposal_bundle.json"

        # Observe CT/Swarm stage
        if proposal_path.exists():
            self._observe_proposals(proposal_path, run_data)

        # Observe Intake stage
        if briefcase_path.exists():
            self._observe_intake(briefcase_path, run_data)

        # Observe Factory stage
        if ledger_path.exists():
            self._observe_factory(ledger_path, run_data)

        # Observe Mayor stage
        if decision_path.exists():
            self._observe_mayor(decision_path, run_data)

        return run_data

    def _observe_proposals(self, path: Path, run_data: dict):
        """Extract ideas from proposal bundles."""
        try:
            with open(path) as f:
                bundle = json.load(f)

            run_data["stages_observed"].append("CT/SWARM")
            self.metrics.total_proposals += len(bundle.get("proposals", []))

            for proposal in bundle.get("proposals", []):
                idea = self._extract_idea(proposal, run_data["run_id"])
                if idea:
                    self.ideas.append(idea)
                    run_data["ideas_captured"] += 1

        except Exception as e:
            self._log_event("CT", "ERROR", run_data["run_id"], {"error": str(e)})

    def _extract_idea(self, proposal: dict, run_id: str) -> Optional[CapturedIdea]:
        """Extract a structured idea from a proposal."""
        if not proposal.get("description"):
            return None

        # Determine category from proposal_type or content
        category = proposal.get("proposal_type", "feature")
        if "risk" in proposal.get("description", "").lower():
            category = "risk"
        elif "experiment" in proposal.get("description", "").lower():
            category = "experiment"
        elif "architecture" in category.lower() or "refactor" in proposal.get("description", "").lower():
            category = "architecture"

        idea_id = f"IDEA-{hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest()[:8]}"

        return CapturedIdea(
            idea_id=idea_id,
            source_run=run_id,
            timestamp=datetime.now().isoformat(),
            category=category,
            title=proposal.get("proposal_id", "Untitled"),
            description=proposal.get("description", "")[:500],  # Truncate for readability
            proposed_by=proposal.get("origin", "CT"),
            obligations_required=proposal.get("required_obligations", []),
            outcome="pending"
        )

    def _observe_intake(self, path: Path, run_data: dict):
        """Observe Intake stage and track rejections."""
        try:
            with open(path) as f:
                briefcase = json.load(f)

            run_data["stages_observed"].append("INTAKE")

            # Check for rejection indicators
            if briefcase.get("_rejected"):
                reason = briefcase.get("_rejection_reason", "UNKNOWN")
                if "AUTHORITY" in reason:
                    self.metrics.rejected_authority += 1
                elif "SCHEMA" in reason:
                    self.metrics.rejected_schema += 1
                elif "DUPLICATE" in reason:
                    self.metrics.rejected_duplicate += 1

                self._log_event("INTAKE", "REJECT", run_data["run_id"], {"reason": reason})
            else:
                self._log_event("INTAKE", "ACCEPT", run_data["run_id"], {
                    "obligations": len(briefcase.get("required_obligations", []))
                })

        except Exception as e:
            self._log_event("INTAKE", "ERROR", run_data["run_id"], {"error": str(e)})

    def _observe_factory(self, path: Path, run_data: dict):
        """Observe Factory stage and track attestations."""
        try:
            with open(path) as f:
                ledger = json.load(f)

            run_data["stages_observed"].append("FACTORY")
            attestations = ledger.get("attestations", [])

            self._log_event("FACTORY", "ATTESTATIONS", run_data["run_id"], {
                "count": len(attestations),
                "classes": list(set(a.get("attestor_class", "") for a in attestations))
            })

        except Exception as e:
            self._log_event("FACTORY", "ERROR", run_data["run_id"], {"error": str(e)})

    def _observe_mayor(self, path: Path, run_data: dict):
        """Observe Mayor decision and track outcomes."""
        try:
            with open(path) as f:
                decision = json.load(f)

            run_data["stages_observed"].append("MAYOR")
            run_data["decision"] = decision.get("decision")

            if decision.get("decision") == "SHIP":
                self.metrics.total_ships += 1
                # Count attestations used (from the run's ledger)
                ledger_path = path.parent / "ledger.json"
                if ledger_path.exists():
                    with open(ledger_path) as f:
                        ledger = json.load(f)
                    self.metrics.total_attestations_used += len(ledger.get("attestations", []))

                self._log_event("MAYOR", "SHIP", run_data["run_id"], {})

                # Update idea outcomes
                for idea in self.ideas:
                    if idea.source_run == run_data["run_id"]:
                        idea.outcome = "shipped"
            else:
                self._log_event("MAYOR", "NO_SHIP", run_data["run_id"], {
                    "blocking": decision.get("blocking_obligations", []),
                    "reasons": decision.get("reasons", [])
                })

                # Update idea outcomes
                for idea in self.ideas:
                    if idea.source_run == run_data["run_id"]:
                        idea.outcome = "rejected"
                        idea.rejection_reason = ", ".join(decision.get("blocking_obligations", []))

            # Track replay digest
            digest = decision.get("decision_digest")
            if digest:
                self.replay_digests.add(digest)
                self.metrics.replay_attempts += 1
                self.metrics.unique_digests = len(self.replay_digests)

        except Exception as e:
            self._log_event("MAYOR", "ERROR", run_data["run_id"], {"error": str(e)})

    def _log_event(self, stage: str, event_type: str, run_id: str, details: dict):
        """Log a pipeline event."""
        event = PipelineEvent(
            timestamp=datetime.now().isoformat(),
            stage=stage,
            event_type=event_type,
            run_id=run_id,
            details=details
        )
        self.events.append(event)

    def analyze_all_runs(self) -> dict:
        """Analyze all runs in the runs directory."""
        if not self.runs_dir.exists():
            return {"error": f"Runs directory not found: {self.runs_dir}"}

        results = {
            "runs_analyzed": 0,
            "runs": [],
            "metrics": None,
            "ideas_captured": 0
        }

        for run_dir in sorted(self.runs_dir.iterdir()):
            if run_dir.is_dir() and not run_dir.name.startswith("."):
                run_data = self.observe_run(run_dir)
                results["runs"].append(run_data)
                results["runs_analyzed"] += 1

        results["metrics"] = self.metrics.to_dict()
        results["ideas_captured"] = len(self.ideas)

        return results

    def get_emergence_report(self) -> str:
        """Generate a human-readable emergence report."""
        m = self.metrics

        report = []
        report.append("=" * 60)
        report.append("ORACLE TOWN EMERGENCE REPORT")
        report.append("=" * 60)
        report.append("")

        # Authority Leakage Rate
        report.append("1. AUTHORITY LEAKAGE RATE")
        report.append(f"   Total proposals observed: {m.total_proposals}")
        report.append(f"   Rejected (authority):     {m.rejected_authority}")
        report.append(f"   Rejected (schema):        {m.rejected_schema}")
        report.append(f"   Rejected (duplicate):     {m.rejected_duplicate}")
        report.append(f"   >>> Leakage Rate: {m.authority_leakage_rate:.1%}")
        report.append("")

        # Evidence Friction
        report.append("2. EVIDENCE FRICTION")
        report.append(f"   Total SHIPs:              {m.total_ships}")
        report.append(f"   Attestations used:        {m.total_attestations_used}")
        report.append(f"   >>> Avg attestations/SHIP: {m.evidence_friction:.2f}")
        report.append("")

        # Replay Entropy
        report.append("3. REPLAY ENTROPY")
        report.append(f"   Replay attempts:          {m.replay_attempts}")
        report.append(f"   Unique digests:           {m.unique_digests}")
        if m.replay_attempts > 0:
            if m.unique_digests == 1:
                report.append("   >>> DETERMINISTIC ✓")
            else:
                report.append(f"   >>> WARNING: Non-determinism detected!")
        report.append("")

        # Emergence Assessment
        report.append("4. EMERGENCE ASSESSMENT")
        if m.authority_leakage_rate > 0.3:
            report.append("   - High authority leakage: CT may need tighter constraints")
        elif m.authority_leakage_rate > 0:
            report.append("   - Authority firewall active: rejecting unauthorized language")
        else:
            report.append("   - No authority leakage detected")

        if m.evidence_friction > 3:
            report.append("   - High evidence friction: system favors well-evidenced changes")
        elif m.evidence_friction > 1:
            report.append("   - Moderate evidence friction: balanced attestation requirements")

        if m.unique_digests <= 1:
            report.append("   - Deterministic regime: governance is replayable")
        else:
            report.append("   - NON-DETERMINISM: investigate canonicalization/dependencies")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def get_ideas_report(self) -> str:
        """Generate a report of captured ideas for inspiration."""
        if not self.ideas:
            return "No ideas captured yet."

        report = []
        report.append("=" * 60)
        report.append("CREATIVE TOWN IDEAS — Inspiration Feed")
        report.append("=" * 60)
        report.append("")

        # Group by category
        by_category = defaultdict(list)
        for idea in self.ideas:
            by_category[idea.category].append(idea)

        for category in ["architecture", "feature", "experiment", "process", "risk"]:
            ideas_in_cat = by_category.get(category, [])
            if not ideas_in_cat:
                continue

            report.append(f"## {category.upper()} ({len(ideas_in_cat)} ideas)")
            report.append("")

            for idea in ideas_in_cat:
                status_icon = {
                    "shipped": "✓",
                    "rejected": "✗",
                    "pending": "○"
                }.get(idea.outcome, "?")

                report.append(f"  [{status_icon}] {idea.title}")
                report.append(f"      {idea.description[:100]}...")
                if idea.outcome == "rejected" and idea.rejection_reason:
                    report.append(f"      Blocked by: {idea.rejection_reason}")
                report.append("")

        # Summary
        shipped = sum(1 for i in self.ideas if i.outcome == "shipped")
        rejected = sum(1 for i in self.ideas if i.outcome == "rejected")
        pending = sum(1 for i in self.ideas if i.outcome == "pending")

        report.append("-" * 60)
        report.append(f"Summary: {shipped} shipped, {rejected} rejected, {pending} pending")
        report.append("=" * 60)

        return "\n".join(report)

    def export_ideas_json(self) -> str:
        """Export ideas as JSON for further processing."""
        return json.dumps([idea.to_dict() for idea in self.ideas], indent=2)

    def watch_live(self, poll_interval: float = 1.0):
        """Watch for new runs and report in real-time."""
        print("=" * 60)
        print("ORACLE TOWN LIVE OBSERVER")
        print("Watching:", self.runs_dir)
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()

        seen_runs = set()

        try:
            while True:
                if self.runs_dir.exists():
                    for run_dir in self.runs_dir.iterdir():
                        if run_dir.is_dir() and run_dir.name not in seen_runs:
                            seen_runs.add(run_dir.name)
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] New run: {run_dir.name}")

                            run_data = self.observe_run(run_dir)

                            if run_data["decision"]:
                                icon = "✓" if run_data["decision"] == "SHIP" else "✗"
                                print(f"  {icon} Decision: {run_data['decision']}")

                            if run_data["ideas_captured"]:
                                print(f"  💡 Ideas captured: {run_data['ideas_captured']}")

                            print()

                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\nObserver stopped.")
            print()
            print(self.get_emergence_report())


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Oracle Town Observer")
    parser.add_argument("--watch", action="store_true", help="Watch for live runs")
    parser.add_argument("--analyze", type=str, help="Analyze runs in directory")
    parser.add_argument("--ideas", action="store_true", help="Show captured ideas")
    parser.add_argument("--metrics", action="store_true", help="Show emergence metrics")
    parser.add_argument("--export-ideas", type=str, help="Export ideas to JSON file")

    args = parser.parse_args()

    runs_dir = args.analyze or "oracle_town/runs"
    observer = OracleTownObserver(runs_dir)

    if args.watch:
        observer.watch_live()
    elif args.analyze:
        results = observer.analyze_all_runs()
        print(json.dumps(results, indent=2))
    elif args.ideas:
        observer.analyze_all_runs()  # Populate ideas
        print(observer.get_ideas_report())
    elif args.metrics:
        observer.analyze_all_runs()  # Populate metrics
        print(observer.get_emergence_report())
    elif args.export_ideas:
        observer.analyze_all_runs()
        with open(args.export_ideas, 'w') as f:
            f.write(observer.export_ideas_json())
        print(f"Exported {len(observer.ideas)} ideas to {args.export_ideas}")
    else:
        # Default: analyze and show emergence report
        observer.analyze_all_runs()
        print(observer.get_emergence_report())
        print()
        print(observer.get_ideas_report())


if __name__ == "__main__":
    main()
