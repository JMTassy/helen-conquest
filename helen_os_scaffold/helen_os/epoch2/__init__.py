"""
helen_os/epoch2 — EPOCH2: Conquest Land Learning Loop.

EPOCH2 = LAW_LEARNING_ONLINE.

The learning loop:
  A. Pre-written hypotheses (3)
  B. Deterministic CONQUEST LAND sim (seed, ticks)
  C. Extract 5 instrumented metrics
  D. Sigma gate across seed set [42, 7, 99]
  E. Inscribe LAW_V1 entries for passing hypotheses

Plus: TOWN_BIRTH_PREDICATE_V1 — sovereignty requires proof bundle,
not just receipt accumulation.

"No receipt → no law."  Expansion of HELEN's world-model is
receipted or it does not count.
"""
from .metrics import EpochMetricsCollector, Metrics
from .sigma_gate import SigmaGate, SigmaResult
from .law_ledger import LawLedger, LawV1
from .town_birth import TownBirthPredicateV1, TownBirthBundle, TownBirthResult
from .run_epoch2 import run_epoch2_canonical, Epoch2RunResult, HYPOTHESES
