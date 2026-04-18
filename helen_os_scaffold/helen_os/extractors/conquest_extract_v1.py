"""
helen_os/extractors/conquest_extract_v1.py

Extract neutral facts from CONQUEST_TICK_V1 to MemoryKernel.
No free-form prose. No authority tokens. No style leakage.
"""

from typing import Any, Dict


def extract_tick_to_memory(memory: Any, tick_event: Dict[str, Any]) -> None:
    """
    Extract tick event facts to memory (safe, neutral subset).

    Args:
        memory: MemoryKernel instance
        tick_event: CONQUEST_TICK_V1 dict
    """
    if not isinstance(tick_event, dict):
        return

    epoch = tick_event.get("epoch")
    state_after = tick_event.get("state_after", {})
    metrics = tick_event.get("metrics", {})

    # Extract neutral facts only
    # No free text, no authority tokens

    # Fact 1: last epoch
    if epoch is not None:
        memory.add_fact(
            key="conquest.last_epoch",
            value=int(epoch),
            actor="system",
            status="OBSERVED",
        )

    # Fact 2: current score
    score = state_after.get("score")
    if score is not None:
        memory.add_fact(
            key="conquest.score",
            value=int(score),
            actor="system",
            status="OBSERVED",
        )

    # Fact 3: delta (change in score)
    delta = metrics.get("delta_score")
    if delta is not None:
        memory.add_fact(
            key="conquest.last_delta_score",
            value=int(delta),
            actor="system",
            status="OBSERVED",
        )

    # Fact 4: stability metric
    stability = metrics.get("stability")
    if stability is not None:
        memory.add_fact(
            key="conquest.last_stability",
            value=float(stability),
            actor="system",
            status="OBSERVED",
        )
