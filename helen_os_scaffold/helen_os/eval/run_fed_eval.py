"""
helen_os/eval/run_fed_eval.py — Canonical Town Eval Federation runner.

Spec: "TOWN_EVAL_FEDERATION_V1 — T0–T5 servitors → Alpha/Beta/Gamma egregores
       → Godmode → FED_EVAL_V1 receipt"

Pipeline:
  1. Servitors  (T0–T5): Run 6 independent checks → 6 TownReportV1
  2. Egregores  (3):     Aggregate pairs → 3 EgregorReportV1
     Alpha (Foundation)   = T0 + T1
     Beta  (Simulation)   = T2 + T3
     Gamma (Sovereignty)  = T4 + T5
  3. Godmode:            Aggregate egregores → FedEvalV1 + FED_EVAL_V1 receipt

Constants:
  CANONICAL_REPLAY_SEQUENCE — 3 deterministic payloads for T2 replay check
  REQUIRED_ARTIFACTS        — 5 artifact filenames for T1 manifest check
  DEFAULT_EVAL_PATH         — relative path to eval/ module
  DEFAULT_FIXTURE_PATH      — relative path to canonical fixture

"No receipt → no federation."
Non-sovereign: :memory: kernel by default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from .schemas   import FedEvalV1, TownReportV1, EgregorReportV1
from .servitors import (
    run_t0_integrity, run_t1_manifest,
    run_t2_replay,    run_t3_partition,
    run_t4_rollback,  run_t5_claim,
)
from .egregores import run_alpha_egregore, run_beta_egregore, run_gamma_egregore
from .godmode   import run_godmode


# ── Federation constants ───────────────────────────────────────────────────────

#: 3-step deterministic payload sequence for T2 Replay check.
CANONICAL_REPLAY_SEQUENCE: List[Dict[str, Any]] = [
    {"type": "FED_EVAL_PROBE_V1", "step": 1, "tag": "integrity"},
    {"type": "FED_EVAL_PROBE_V1", "step": 2, "tag": "replay"},
    {"type": "FED_EVAL_PROBE_V1", "step": 3, "tag": "partition"},
]

#: Canonical artifact files required by T1 Manifest check.
REQUIRED_ARTIFACTS: List[str] = [
    "EPOCH_MARK_V1_EPOCH1.json",
    "EPOCH_MARK_V1_EPOCH2.json",
    "EPOCH_MARK_V1_EPOCH3.json",
    "EPOCH_MARK_V1_CLAIM_GRAPH.json",
    "CLAIM_GRAPH_V1.json",
]

#: Default path to eval/ module (relative to helen_os_scaffold/).
DEFAULT_EVAL_PATH: str = os.path.join("helen_os", "eval")

#: Default path to canonical CLAIM_GRAPH_V1 fixture.
DEFAULT_FIXTURE_PATH: str = os.path.join("fixtures", "decay_dialogue_v1.txt")

#: Default path to artifacts directory.
DEFAULT_ARTIFACTS_PATH: str = "artifacts"


# ── Result container ──────────────────────────────────────────────────────────

@dataclass
class FedEvalRunResult:
    """
    Full result of run_fed_eval_canonical().

    Contains the FedEvalV1 godmode artifact plus all intermediate reports
    for debugging and test assertions.
    """
    fed_eval:     FedEvalV1
    t0_report:    TownReportV1
    t1_report:    TownReportV1
    t2_report:    TownReportV1
    t3_report:    TownReportV1
    t4_report:    TownReportV1
    t5_report:    TownReportV1
    alpha_report: EgregorReportV1
    beta_report:  EgregorReportV1
    gamma_report: EgregorReportV1

    @property
    def is_pass(self) -> bool:
        """True if godmode verdict is PASS."""
        return self.fed_eval.verdict == "PASS"

    @property
    def receipt_id(self) -> str:
        """FED_EVAL_V1 receipt ID (from GovernanceVM.propose())."""
        return self.fed_eval.receipt_id

    @property
    def cum_hash(self) -> str:
        """Final cum_hash of the godmode kernel after FED_EVAL_V1 receipt."""
        return self.fed_eval.cum_hash

    def summary(self) -> str:
        """One-line summary for debugging."""
        return (
            f"FED_EVAL_V1 verdict={self.fed_eval.verdict} "
            f"({self.fed_eval.pass_count}P "
            f"{self.fed_eval.warn_count}W "
            f"{self.fed_eval.block_count}B / "
            f"{self.fed_eval.servitor_count} servitors) "
            f"receipt={self.receipt_id}"
        )


# ── Canonical runner ──────────────────────────────────────────────────────────

def run_fed_eval_canonical(
    ledger_path:    str = ":memory:",
    fixture_path:   str = DEFAULT_FIXTURE_PATH,
    artifacts_path: str = DEFAULT_ARTIFACTS_PATH,
    eval_path:      str = DEFAULT_EVAL_PATH,
) -> FedEvalRunResult:
    """
    Run the canonical Town Eval Federation pipeline.

    Executes all 6 servitors, aggregates into 3 egregores, then runs
    Godmode to emit the FED_EVAL_V1 receipt.

    Args:
        ledger_path:    Godmode kernel path (default: :memory: — non-sovereign).
        fixture_path:   Path to CLAIM_GRAPH_V1 fixture (for T5 Claim check).
        artifacts_path: Path to artifacts directory (for T1 Manifest check).
        eval_path:      Path to eval/ module (for T3 Partition check).

    Returns:
        FedEvalRunResult with all intermediate reports + godmode FedEvalV1.

    Pipeline:
      T0 (Integrity)  ─┐
      T1 (Manifest)   ─┤─► Alpha (Foundation) ─┐
                        │                        │
      T2 (Replay)    ─┐│                        │
      T3 (Partition) ─┤─► Beta  (Simulation)  ──┤─► Godmode → FED_EVAL_V1
                        │                        │
      T4 (Rollback)  ─┐│                        │
      T5 (Claim)     ─┤─► Gamma (Sovereignty) ─┘
    """
    from ..kernel import GovernanceVM

    # ── Godmode kernel (receives FED_EVAL_V1 receipt) ─────────────────────────
    km = GovernanceVM(ledger_path=ledger_path)

    # ── Integrity kernel: seeded with one receipt so T0 sees non-trivial hash ──
    integrity_kernel = GovernanceVM(ledger_path=":memory:")
    integrity_kernel.propose({
        "type":    "FED_EVAL_SEED_V1",
        "purpose": "T0 Integrity Servitor probe seed",
    })

    # ── Servitors ─────────────────────────────────────────────────────────────
    t0 = run_t0_integrity(integrity_kernel)
    t1 = run_t1_manifest(artifacts_path, REQUIRED_ARTIFACTS)
    t2 = run_t2_replay(CANONICAL_REPLAY_SEQUENCE)
    t3 = run_t3_partition(eval_path)
    t4 = run_t4_rollback()
    t5 = run_t5_claim(fixture_path)

    # ── Egregores ─────────────────────────────────────────────────────────────
    alpha = run_alpha_egregore(t0, t1)
    beta  = run_beta_egregore(t2, t3)
    gamma = run_gamma_egregore(t4, t5)

    # ── Godmode → FED_EVAL_V1 receipt ─────────────────────────────────────────
    fed_eval = run_godmode([alpha, beta, gamma], kernel=km)

    return FedEvalRunResult(
        fed_eval     = fed_eval,
        t0_report    = t0,
        t1_report    = t1,
        t2_report    = t2,
        t3_report    = t3,
        t4_report    = t4,
        t5_report    = t5,
        alpha_report = alpha,
        beta_report  = beta,
        gamma_report = gamma,
    )
