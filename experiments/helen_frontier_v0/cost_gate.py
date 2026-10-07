"""Cost-aware cognition predicate — declared booleans only.

Mirrors the policy text versioned in JMTassy/helen-os AGENTS.md @ 51a4109f
("Cost-aware cognition and recurring loops"):

    Scheduler != CognitionTrigger
    NewEvidence AND DecisionRelevant AND Unresolved AND Testable AND NOT Duplicate

This module evaluates a *declaration* of those five conditions. A favourable
verdict means exactly: "declared conditions complete and favourable". It is
not validated evidence, not a permission to call a model, and not a realised
saving. Whether anything upstream consults this predicate before an expensive
call is NOT demonstrated by this module or its tests.

Strictness: every conjunct must be present, carry a real bool (``True``/``False``,
never 1/0 or "true"), and carry non-empty evidence. Anything else is refused.

NON_SOVEREIGN · authority=false · ledger_effect=none.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

CONJUNCTS: tuple[str, ...] = (
    "new_evidence",
    "decision_relevant",
    "unresolved",
    "testable",
    "not_duplicate",
)

DECLARED_FAVORABLE = "DECLARED_FAVORABLE"
DECLARED_UNFAVORABLE = "DECLARED_UNFAVORABLE"
REFUSED_MALFORMED = "REFUSED_MALFORMED"

MEANING = (
    "DECLARED_FAVORABLE means only: all five conditions were declared, each with a "
    "strict boolean True and non-empty evidence. It is not validated evidence, not a "
    "permission to spend, and not a measured saving."
)


@dataclass(frozen=True)
class CostGateResult:
    verdict: str
    failing: tuple[str, ...]
    errors: tuple[str, ...]
    meaning: str = MEANING

    @property
    def declared_favorable(self) -> bool:
        return self.verdict == DECLARED_FAVORABLE


def _evidence_is_nonempty(evidence: Any) -> bool:
    if isinstance(evidence, str):
        return bool(evidence.strip())
    if isinstance(evidence, (Mapping, list, tuple)):
        return len(evidence) > 0
    return False


def evaluate_cost_gate(declaration: Any) -> CostGateResult:
    """Evaluate a declaration of the five conjuncts. Fail-closed on any malformation."""
    errors: list[str] = []
    if not isinstance(declaration, Mapping):
        return CostGateResult(REFUSED_MALFORMED, (), (f"declaration must be a mapping, got {type(declaration).__name__}",))

    extra = sorted(set(declaration) - set(CONJUNCTS))
    if extra:
        errors.append(f"unexpected keys: {extra}")

    values: dict[str, bool] = {}
    for name in CONJUNCTS:
        if name not in declaration:
            errors.append(f"{name}: missing")
            continue
        entry = declaration[name]
        if not isinstance(entry, Mapping):
            errors.append(f"{name}: must be a mapping with 'value' and 'evidence'")
            continue
        entry_extra = sorted(set(entry) - {"value", "evidence"})
        if entry_extra:
            errors.append(f"{name}: unexpected keys {entry_extra}")
        if "value" not in entry:
            errors.append(f"{name}.value: missing")
        elif type(entry["value"]) is not bool:  # noqa: E721 - strictness is the point
            errors.append(f"{name}.value: must be a strict bool, got {type(entry['value']).__name__} {entry['value']!r}")
        else:
            values[name] = entry["value"]
        if "evidence" not in entry:
            errors.append(f"{name}.evidence: missing")
        elif not _evidence_is_nonempty(entry["evidence"]):
            errors.append(f"{name}.evidence: must be non-empty")

    if errors:
        return CostGateResult(REFUSED_MALFORMED, (), tuple(errors))

    failing = tuple(name for name in CONJUNCTS if values[name] is False)
    verdict = DECLARED_FAVORABLE if not failing else DECLARED_UNFAVORABLE
    return CostGateResult(verdict, failing, ())
