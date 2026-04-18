"""
helen_os/eval — Town Eval Federation (T0–T5, Egregores, Godmode)

Architecture:
  1. ServitorCheckV1    — one atomic check result (PASS / WARN / BLOCK)
  2. TownReportV1       — per-servitor report (6 servitors: T0–T5)
  3. EgregorReportV1    — egregore aggregate (3 egregores: Alpha / Beta / Gamma)
  4. FedEvalV1          — godmode FED_EVAL_V1 receipt artifact
  5. run_fed_eval_canonical() — canonical runner: servitors → egregores → godmode → receipt

Servitors (T0–T5):
  T0 — Integrity   : ledger chain valid, cum_hash non-trivial
  T1 — Manifest    : canonical artifact files exist + artifact_sha256 present
  T2 — Replay      : same payload sequence → identical cum_hash × 3
  T3 — Partition   : eval/ module isolated from domain-specific modules
  T4 — Rollback    : sealed kernel rejects further proposals
  T5 — Claim       : CLAIM_GRAPH_V1 source_digest stable × 3 runs

Egregores:
  Alpha (Foundation)   = T0 + T1
  Beta  (Simulation)   = T2 + T3
  Gamma (Sovereignty)  = T4 + T5

Godmode:
  Aggregates Alpha + Beta + Gamma → FED_EVAL_V1 receipt via kernel.propose()

"No receipt → no federation."
Non-sovereign: :memory: kernels only.
"""

from .schemas    import ServitorCheckV1, TownReportV1, EgregorReportV1, FedEvalV1
from .servitors  import (
    run_t0_integrity, run_t1_manifest,
    run_t2_replay,    run_t3_partition,
    run_t4_rollback,  run_t5_claim,
)
from .egregores  import run_alpha_egregore, run_beta_egregore, run_gamma_egregore
from .godmode    import run_godmode
from .run_fed_eval import run_fed_eval_canonical, FedEvalRunResult

__all__ = [
    # Schemas
    "ServitorCheckV1", "TownReportV1", "EgregorReportV1", "FedEvalV1",
    # Servitors
    "run_t0_integrity", "run_t1_manifest",
    "run_t2_replay",    "run_t3_partition",
    "run_t4_rollback",  "run_t5_claim",
    # Egregores
    "run_alpha_egregore", "run_beta_egregore", "run_gamma_egregore",
    # Godmode
    "run_godmode",
    # Canonical runner
    "run_fed_eval_canonical", "FedEvalRunResult",
]
