"""
helen_os/epoch3 — HELEN Internal Sim Loop (CONQUEST: HELEN Internal Sim Loop Spec)

Image spec:
  1. Input:       QuestBank (3 quest types)
  2. Simulation:  SimLoop (Phase A→B→C: Observe/Experiment/Integrate)
  3. Evaluation:  EvaluationGate (3 gates: Contradiction/Reality/Temporal)
  4. Output:      QuestLoopResult (Cognitive Growth / Temporal Awareness / Adaptive Strategies)
  Loop:           run_epoch3_canonical() → LOOP COMPLETES → INITIATE NEXT QUEST

Non-sovereign: all computation in :memory: kernels.
"""

from .quest_bank  import Quest, QuestType, CounterfactualSpec, QUEST_BANK, get_quest
from .sim_loop    import SimLoop, SimLoopResult, PhaseAResult, PhaseBResult, PhaseCResult
from .evaluation  import EvaluationGate, EvaluationResult
from .run_epoch3  import run_epoch3_canonical, Epoch3RunResult, QuestLoopResult

__all__ = [
    "Quest", "QuestType", "CounterfactualSpec", "QUEST_BANK", "get_quest",
    "SimLoop", "SimLoopResult", "PhaseAResult", "PhaseBResult", "PhaseCResult",
    "EvaluationGate", "EvaluationResult",
    "run_epoch3_canonical", "Epoch3RunResult", "QuestLoopResult",
]
