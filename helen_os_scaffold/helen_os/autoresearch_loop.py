"""
HELEN OS Autoresearch Loop V1

Autonomous self-improvement loop using immutable ground truth + deterministic boundaries.
Maps karpathy/autoresearch patterns onto HELEN OS governance framework.

Pattern:
  Single editable artifact (HYPOTHESIS.md) +
  Fixed time budget (5 phases, no looping back) +
  Immutable evaluator (validators, gates) +
  Mechanical judge (vote ≥ K gates PASS) +
  Append-only audit (ledger receipts) = Autonomous governance loop

Usage:
  loop = AutoresearchLoop(governance_vm)
  result = loop.run_iteration(hypothesis_file="proposals/HYPOTHESIS.md")
  print(result.verdict)  # "SHIP" or "ABORT"
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime
import hashlib


@dataclass
class LoopVerdictRecord:
    """Machine-checkable verdict from one loop iteration"""
    iteration_id: str
    hypothesis_id: str
    phase: str  # EXPLORATION, TENSION, DRAFTING, EDITORIAL, TERMINATION
    gates_passed: List[str]  # List of gate codes that passed
    gates_failed: List[str]  # List of gate codes that failed
    verdict: str  # "SHIP" or "ABORT"
    receipt_hash: str  # SHA256 of verdict record
    timestamp: str  # ISO 8601
    wall_clock_duration_sec: float

    def to_dict(self):
        """JSON-serializable dict"""
        return asdict(self)

    def to_ndjson(self) -> str:
        """Format as NDJSON line for append-only audit log"""
        return json.dumps(self.to_dict())


class AutoresearchLoop:
    """
    Autonomous loop: hypothesis → validation → mechanical verdict → receipt → next

    Iteration cycle:
    1. EXPLORATION: Load HYPOTHESIS.md (single editable artifact)
    2. TENSION: HAL red-teams (immutable evaluator)
    3. DRAFTING: Convert claims to prose
    4. EDITORIAL: Cut ruthlessly (30-50%)
    5. TERMINATION: Mechanical judge (gates) → SHIP/ABORT
    """

    # Gate names (all must pass for SHIP)
    GATES = [
        "GATE_SCHEMA",
        "GATE_EVIDENCE",
        "GATE_AUTHORITY",
        "GATE_DETERMINISM",
        "GATE_APPEND_ONLY",
    ]

    def __init__(self, governance_vm, output_dir: str = "proposals/"):
        """
        Args:
            governance_vm: GovernanceVM instance (immutable ground truth)
            output_dir: Directory for hypothesis files and audit logs
        """
        self.vm = governance_vm
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Audit log (append-only)
        self.audit_log = self.output_dir / "autoresearch_loop.ndjson"
        self.audit_log.touch(exist_ok=True)

    def run_iteration(
        self,
        hypothesis_file: str,
        hypothesis_id: str = None,
        time_budget_sec: int = 300
    ) -> LoopVerdictRecord:
        """
        Run one complete loop iteration (5 phases, fixed time budget).

        Args:
            hypothesis_file: Path to HYPOTHESIS.md (single mutable artifact)
            hypothesis_id: Identifier for this hypothesis (auto-generated if None)
            time_budget_sec: Total wall-clock seconds for all 5 phases

        Returns:
            LoopVerdictRecord with gates_passed/gates_failed/verdict
        """
        start_time = time.time()
        iteration_id = f"LOOP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        hypothesis_id = hypothesis_id or hypothesis_file.split("/")[-1].replace(".md", "")

        # Track which gates pass/fail
        gates_passed = []
        gates_failed = []

        # Phase 1: EXPLORATION (load hypothesis)
        phase = "EXPLORATION"
        hypothesis = self._load_hypothesis(hypothesis_file)

        # Phase 2: TENSION (red-team)
        phase = "TENSION"
        critiques = self._run_tension_phase(hypothesis)

        # Phase 3: DRAFTING (convert to prose)
        phase = "DRAFTING"
        draft = self._run_drafting_phase(hypothesis, critiques)

        # Phase 4: EDITORIAL (cut ruthlessly)
        phase = "EDITORIAL"
        final = self._run_editorial_phase(draft)

        # Phase 5: TERMINATION (mechanical verdict)
        phase = "TERMINATION"
        gates_passed, gates_failed = self._evaluate_gates(final, hypothesis)

        # Determine verdict
        verdict = "SHIP" if len(gates_failed) == 0 else "ABORT"

        wall_clock_duration = time.time() - start_time

        # Create receipt
        receipt = LoopVerdictRecord(
            iteration_id=iteration_id,
            hypothesis_id=hypothesis_id,
            phase=phase,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            verdict=verdict,
            receipt_hash=self._compute_receipt_hash(
                iteration_id, hypothesis_id, gates_passed, gates_failed, verdict
            ),
            timestamp=datetime.utcnow().isoformat() + "Z",
            wall_clock_duration_sec=wall_clock_duration,
        )

        # Append to audit log (immutable)
        self._append_audit_log(receipt)

        return receipt

    def _load_hypothesis(self, hypothesis_file: str) -> Dict[str, Any]:
        """Load and parse HYPOTHESIS.md (single mutable artifact)"""
        path = Path(hypothesis_file)
        if not path.exists():
            raise FileNotFoundError(f"Hypothesis file not found: {hypothesis_file}")

        with open(path) as f:
            content = f.read()

        # Parse YAML-like front matter
        hypothesis = {
            "title": "Unknown",
            "description": "",
            "changes": [],
            "tests": [],
            "risks": [],
            "raw_content": content,
        }

        # Simple parsing (in real implementation, use YAML)
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                hypothesis["title"] = line.replace("# ", "").strip()
            elif "Changes:" in line or "changes:" in line:
                # Parse changes section (R-### claims)
                pass

        return hypothesis

    def _run_tension_phase(self, hypothesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """HAL red-teams the hypothesis (immutable evaluator)"""
        critiques = []

        # Gate 1: Schema check (is hypothesis well-formed?)
        if hypothesis.get("title") and hypothesis.get("description"):
            critiques.append({
                "verdict": "PASS",
                "code": "SCHEMA_SOUND",
                "message": "Hypothesis has required fields"
            })
        else:
            critiques.append({
                "verdict": "FAIL",
                "code": "SCHEMA_INVALID",
                "message": "Missing required hypothesis fields"
            })

        # Gate 2: Evidence check (do claims cite receipts, not dialog?)
        if "changes:" in hypothesis["raw_content"].lower():
            critiques.append({
                "verdict": "WARN",
                "code": "EVIDENCE_CHECK",
                "message": "Verify changes cite receipts, not dialog.ndjson"
            })

        return critiques

    def _run_drafting_phase(
        self,
        hypothesis: Dict[str, Any],
        critiques: List[Dict[str, Any]]
    ) -> str:
        """Convert hypothesis + critiques to draft prose"""
        draft = f"""# {hypothesis['title']}

## Summary
{hypothesis['description']}

## Changes
"""
        for change in hypothesis.get("changes", []):
            draft += f"- {change}\n"

        draft += "\n## Critiques Addressed\n"
        for critique in critiques:
            if critique["verdict"] in ["WARN", "FAIL"]:
                draft += f"- {critique['message']}\n"

        return draft

    def _run_editorial_phase(self, draft: str) -> str:
        """Cut ruthlessly: 30-50% removal"""
        lines = draft.split("\n")
        # Keep only essential sections: title, summary, critical changes
        essential_lines = []
        for line in lines:
            if (line.startswith("#") or
                line.startswith("- ") or
                "Summary" in line or
                "Changes" in line):
                essential_lines.append(line)

        final = "\n".join(essential_lines[:len(essential_lines) // 2])
        return final

    def _evaluate_gates(
        self,
        final: str,
        hypothesis: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Mechanical judge: evaluate all gates (deterministic predicates)"""
        gates_passed = []
        gates_failed = []

        # GATE_SCHEMA: Is output well-formed?
        if final and len(final) > 10:
            gates_passed.append("GATE_SCHEMA")
        else:
            gates_failed.append("GATE_SCHEMA")

        # GATE_EVIDENCE: Does it reference artifacts/receipts?
        if hypothesis.get("changes"):
            gates_passed.append("GATE_EVIDENCE")
        else:
            gates_failed.append("GATE_EVIDENCE")

        # GATE_AUTHORITY: No forbidden tokens in hypothesis or final?
        forbidden = ["SHIP", "SEALED", "APPROVED", "FINAL"]
        combined_content = (hypothesis.get("raw_content", "") + final).upper()
        if not any(token in combined_content for token in forbidden):
            gates_passed.append("GATE_AUTHORITY")
        else:
            gates_failed.append("GATE_AUTHORITY")

        # GATE_DETERMINISM: Testable/reproducible?
        if "test" in hypothesis["raw_content"].lower():
            gates_passed.append("GATE_DETERMINISM")
        else:
            gates_failed.append("GATE_DETERMINISM")

        # GATE_APPEND_ONLY: No retroactive edits claimed?
        combined_text = (hypothesis.get("raw_content", "") + final).lower()
        if "edit" not in combined_text or "retroactive" not in combined_text:
            gates_passed.append("GATE_APPEND_ONLY")
        else:
            gates_failed.append("GATE_APPEND_ONLY")

        return gates_passed, gates_failed

    def _compute_receipt_hash(
        self,
        iteration_id: str,
        hypothesis_id: str,
        gates_passed: List[str],
        gates_failed: List[str],
        verdict: str
    ) -> str:
        """Deterministic receipt hash (SHA256)"""
        payload = {
            "iteration_id": iteration_id,
            "hypothesis_id": hypothesis_id,
            "gates_passed": sorted(gates_passed),
            "gates_failed": sorted(gates_failed),
            "verdict": verdict,
        }
        json_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _append_audit_log(self, receipt: LoopVerdictRecord):
        """Append receipt to immutable audit log (never edit)"""
        with open(self.audit_log, "a") as f:
            f.write(receipt.to_ndjson() + "\n")

    def get_audit_history(self) -> List[LoopVerdictRecord]:
        """Read complete audit history (replay all verdicts)"""
        history = []
        if self.audit_log.exists():
            with open(self.audit_log) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        record = LoopVerdictRecord(**data)
                        history.append(record)
        return history

    def print_summary(self):
        """Print loop summary statistics"""
        history = self.get_audit_history()
        shipped = sum(1 for r in history if r.verdict == "SHIP")
        aborted = sum(1 for r in history if r.verdict == "ABORT")
        total_gates = len(self.GATES) * len(history) if history else 0
        gates_passed = sum(len(r.gates_passed) for r in history)

        print(f"\n📊 HELEN OS Autoresearch Loop Summary")
        print(f"   Iterations: {len(history)}")
        print(f"   ✅ SHIPPED: {shipped}")
        print(f"   ❌ ABORTED: {aborted}")
        print(f"   Gate pass rate: {gates_passed}/{total_gates} ({100*gates_passed/total_gates if total_gates else 0:.1f}%)")
