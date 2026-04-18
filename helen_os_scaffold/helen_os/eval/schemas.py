"""
helen_os/eval/schemas.py — Pydantic schemas for Town Eval Federation.

Schema hierarchy:
  ServitorCheckV1   — one atomic check (PASS / WARN / BLOCK)
  TownReportV1      — per-servitor report (aggregates N checks)
  EgregorReportV1   — egregore aggregate (aggregates N servitor reports)
  FedEvalV1         — godmode artifact (aggregates N egregore reports + receipt)

Verdict semantics:
  PASS  — check succeeded: invariant holds
  WARN  — check completed with degraded confidence (missing optional field, etc.)
  BLOCK — check failed: invariant violated — federation BLOCKED

Aggregation rule (strictly conservative):
  Any BLOCK → BLOCK
  All PASS  → PASS
  Otherwise → WARN

Design:
  - No LLM dependence.
  - All verdicts computed from observable, receipt-bound evidence.
  - FedEvalV1 stores receipt_id + cum_hash → every federation run is auditable.
  - No authority tokens: FedEvalV1.verdict is an observation, not a command.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Verdict ───────────────────────────────────────────────────────────────────

CheckVerdict = Literal["PASS", "WARN", "BLOCK"]


def aggregate_verdict(verdicts: List[CheckVerdict]) -> CheckVerdict:
    """
    Strictly conservative aggregation:
      Any BLOCK  → BLOCK
      All PASS   → PASS
      Otherwise  → WARN
    """
    if any(v == "BLOCK" for v in verdicts):
        return "BLOCK"
    if all(v == "PASS" for v in verdicts):
        return "PASS"
    return "WARN"


# ── ServitorCheckV1 ───────────────────────────────────────────────────────────

class ServitorCheckV1(BaseModel):
    """
    One atomic check emitted by a servitor.

    check_id:    Stable ID, e.g. "T0.1", "T1.EPOCH_MARK_V1_EPOCH1.json"
    description: Human-readable invariant statement
    verdict:     PASS / WARN / BLOCK
    detail:      Optional evidence or error message
    """
    check_id:    str
    description: str
    verdict:     CheckVerdict
    detail:      Optional[str] = None


# ── TownReportV1 ──────────────────────────────────────────────────────────────

class TownReportV1(BaseModel):
    """
    Per-servitor evaluation report.

    servitor_id:       "T0" – "T5"
    servitor_name:     "Integrity", "Manifest", "Replay", "Partition",
                       "Rollback", "Claim"
    verdict:           Aggregate of all checks (conservative: any BLOCK → BLOCK)
    checks:            List of atomic ServitorCheckV1 results
    evidence_receipts: Receipt IDs used as evidence (optional — servitors are
                       non-sovereign by default)
    run_at:            ISO8601 timestamp
    """
    type:              str          = "TOWN_REPORT_V1"
    servitor_id:       str
    servitor_name:     str
    verdict:           CheckVerdict
    checks:            List[ServitorCheckV1]
    evidence_receipts: List[str]    = Field(default_factory=list)
    run_at:            str

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Minimal payload for kernel.propose()."""
        return {
            "type":         self.type,
            "servitor_id":  self.servitor_id,
            "verdict":      self.verdict,
            "check_count":  len(self.checks),
            "pass_count":   sum(1 for c in self.checks if c.verdict == "PASS"),
            "block_count":  sum(1 for c in self.checks if c.verdict == "BLOCK"),
            "run_at":       self.run_at,
        }


# ── EgregorReportV1 ───────────────────────────────────────────────────────────

class EgregorReportV1(BaseModel):
    """
    Egregore evaluation report — composite of N servitor reports.

    Egregores:
      Alpha (Foundation)  = T0 (Integrity) + T1 (Manifest)
      Beta  (Simulation)  = T2 (Replay)    + T3 (Partition)
      Gamma (Sovereignty) = T4 (Rollback)  + T5 (Claim)

    egregore_id:      "Alpha" / "Beta" / "Gamma"
    egregore_name:    "Foundation" / "Simulation" / "Sovereignty"
    servitor_ids:     ["T0", "T1"] etc.
    verdict:          Conservative aggregate of servitor verdicts
    servitor_reports: Full TownReportV1 list
    run_at:           ISO8601 timestamp
    """
    type:             str          = "EGREGOR_REPORT_V1"
    egregore_id:      str
    egregore_name:    str
    servitor_ids:     List[str]
    verdict:          CheckVerdict
    servitor_reports: List[TownReportV1]
    run_at:           str

    def to_receipt_payload(self) -> Dict[str, Any]:
        return {
            "type":             self.type,
            "egregore_id":      self.egregore_id,
            "egregore_name":    self.egregore_name,
            "servitor_ids":     self.servitor_ids,
            "verdict":          self.verdict,
            "servitor_verdicts": {
                r.servitor_id: r.verdict for r in self.servitor_reports
            },
            "run_at":           self.run_at,
        }


# ── FedEvalV1 ─────────────────────────────────────────────────────────────────

class FedEvalV1(BaseModel):
    """
    Godmode federation evaluation artifact.

    This is the canonical output of the Town Eval Federation. It:
      - Aggregates 3 egregore reports (Alpha + Beta + Gamma = 6 servitors)
      - Emits a FED_EVAL_V1 receipt via kernel.propose()
      - receipt_id + cum_hash make every federation run auditable

    verdict:           Conservative aggregate of all egregore verdicts
    receipt_id:        Receipt ID from kernel.propose() (auditable anchor)
    cum_hash:          Final cum_hash of the governance kernel after emission
    """
    type:             str               = "FED_EVAL_V1"
    egregore_ids:     List[str]
    verdict:          CheckVerdict
    egregore_reports: List[EgregorReportV1]
    servitor_count:   int
    pass_count:       int
    block_count:      int
    warn_count:       int
    receipt_id:       str
    cum_hash:         str
    run_at:           str

    @property
    def is_pass(self) -> bool:
        return self.verdict == "PASS"

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Canonical dict for kernel.propose() — compact summary."""
        return {
            "type":            self.type,
            "egregore_ids":    self.egregore_ids,
            "verdict":         self.verdict,
            "servitor_count":  self.servitor_count,
            "pass_count":      self.pass_count,
            "block_count":     self.block_count,
            "warn_count":      self.warn_count,
            "egregore_verdicts": {
                er.egregore_id: er.verdict for er in self.egregore_reports
            },
        }
