"""
helen_os/missions/ — HELEN V3 mission orchestration layer.

LAYER PLACEMENT:
  L0  cognition (dialogue, HER, claim packets)
  L1  proposal_service (single entrypoint, validates + promotes)
  L1.5 V3 stability filter (AEON/COMM/GROUND/DET stub → real later)
  L2  mission_reducer (deterministic finalization)
  L3  step_executor (worker execution, receipt issuance)
  L4  reaction_engine (events → new proposals only, no missions)
  L5  Town sovereignty (NOT in this module)

INVARIANTS:
  I1  Only proposal_service creates missions (no backdoor)
  I2  Only step_executor issues execution receipts
  I3  mission_reducer is pure deterministic (no I/O)
  I4  reaction_engine emits proposals only, never missions
  I5  Nothing in missions/ writes sovereign ledger
"""
