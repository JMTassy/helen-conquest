"""
helen_os/epoch2/law_ledger.py — LAW_V1 inscription.

"No receipt → no law."

A validated invariant from a passed SigmaResult is promoted to a LAW_V1
entry and inscribed into the kernel. The receipt from inscription becomes
the law's proof anchor.

LAW_V1 schema:
  {
    "type":                    "LAW_V1",
    "hypothesis":              str,           # single-sentence claim
    "law_text":                str,           # human-readable law statement
    "metric":                  str,           # metric name validated
    "seed_set":                List[int],
    "adversarial_gates_passed":List[str],
    "evidence_hashes":         List[str],     # R-prefix receipt IDs from sigma runs
    "inscribed_at":            str,           # ISO8601
  }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .sigma_gate import SigmaResult


# ── LAW_V1 entry ──────────────────────────────────────────────────────────────

@dataclass
class LawV1:
    """
    A validated law entry produced by LawLedger.inscribe().

    Immutable once created. The receipt_id is the canonical proof anchor.
    """
    hypothesis: str
    law_text: str
    metric: str
    seed_set: List[int]
    adversarial_gates_passed: List[str]
    evidence_hashes: List[str]   # receipt IDs from sigma gate runs
    inscribed_at: str
    inscription_receipt_id: Optional[str] = None   # set after kernel.propose()

    def to_ledger_payload(self) -> Dict[str, Any]:
        """LAW_V1 canonical ledger payload."""
        return {
            "type": "LAW_V1",
            "hypothesis": self.hypothesis,
            "law_text": self.law_text,
            "metric": self.metric,
            "seed_set": self.seed_set,
            "adversarial_gates_passed": self.adversarial_gates_passed,
            "evidence_hashes": self.evidence_hashes,
            "inscribed_at": self.inscribed_at,
            "inscription_receipt_id": self.inscription_receipt_id,
        }


# ── Law ledger ────────────────────────────────────────────────────────────────

class LawLedger:
    """
    Manages LAW_V1 inscription into a GovernanceVM kernel.

    CONTRACT:
      - inscribe() ONLY accepts a SigmaResult with passed=True
      - Raises ValueError if sigma_result.passed is False
      - Returns the Receipt from kernel.propose()
      - That Receipt's id becomes the law's inscription_receipt_id
      - "No receipt → no law" is enforced here, not downstream

    Usage:
        law_ledger = LawLedger(kernel)
        receipt = law_ledger.inscribe(
            sigma_result,
            law_text="admissibility_rate >= 0.80: anti-replay scheme does not over-block"
        )
        print(receipt.id)   # R-xxxxxxxx
        laws = law_ledger.list_laws()
    """

    def __init__(self, kernel):
        self._kernel = kernel
        self._inscribed: List[LawV1] = []

    def inscribe(self, sigma_result: SigmaResult, law_text: str):
        """
        Inscribe a validated law from a passed SigmaResult.

        Args:
            sigma_result: Must have passed=True (enforced).
            law_text:     Human-readable statement of the law.

        Returns:
            Receipt from kernel.propose().

        Raises:
            ValueError: If sigma_result.passed is False.
        """
        if not sigma_result.passed:
            raise ValueError(
                f"LawLedger.inscribe: Cannot inscribe a failed sigma result. "
                f"hypothesis={sigma_result.hypothesis!r}. "
                f"reason={sigma_result.reason!r}. "
                f"Pass the sigma gate before inscribing."
            )

        now = datetime.now(timezone.utc).isoformat()
        law = LawV1(
            hypothesis=sigma_result.hypothesis,
            law_text=law_text,
            metric=sigma_result.metric_name,
            seed_set=sigma_result.seed_set,
            adversarial_gates_passed=sigma_result.adversarial_gates_passed,
            evidence_hashes=sigma_result.evidence_receipt_ids,
            inscribed_at=now,
        )

        receipt = self._kernel.propose(law.to_ledger_payload())
        law.inscription_receipt_id = receipt.id
        self._inscribed.append(law)
        return receipt

    def list_laws(self) -> List[LawV1]:
        """Return all inscribed laws (immutable list copy)."""
        return list(self._inscribed)

    def as_ledger_payloads(self) -> List[Dict[str, Any]]:
        """All laws as ledger payload dicts."""
        return [law.to_ledger_payload() for law in self._inscribed]
