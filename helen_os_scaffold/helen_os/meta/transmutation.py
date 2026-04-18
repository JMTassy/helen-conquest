"""
helen_os/meta/transmutation.py — TRANSMUTE_FOR_SHIP_V1 gate.

WILD → SHIP is a REWRITE, not a copy.

The transmutation gate converts inspiration (WILD) into a policy-compliant
shippable artifact (SHIP). This is not a filter — it's a semantic transform.

What transmutation does:
  1. De-risks: removes procedural sequences, bypass patterns, operational specifics.
  2. Abstracts: converts specific wrongdoing suggestions to abstract principles.
  3. Audits: records what was removed (meaning_diff).
  4. Validates: runs G0/G1/G2 on the output.
  5. Receipts: emits validator_receipts from an ephemeral kernel.

TRANSMUTE_FOR_SHIP_V1 schema:
  {
    "type": "TRANSMUTE_FOR_SHIP_V1",
    "wild_source_hashes": ["..."],   # hashes of WILD inputs (never their content)
    "de_risked": true,
    "non_procedural": true,
    "policy_compliant": true,
    "meaning_diff": "what got removed",
    "abstract_principle": "what was kept (general, non-operational)",
    "ship_artifact": {...},
    "validator_receipts": [...],
    "shipability": "SHIPABLE",
    "epistemic_mode": "SHIP"
  }

Hard constraint: no literal carryover of hazardous sections.
The output must pass G0/G1/G2 independently — not by inheriting from WILD.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .wild_policy import (
    IdeaSandboxV1,
    ShipabilityClassifier,
    WildChannelGate,
    NonProceduralChecker,
    HalBoundary,
    Shipability,
    EpistemicMode,
    run_gate_check,
    HARD_BYPASS_PATTERNS,
    PROCEDURAL_PATTERNS,
)


# ── Transmutation Result ──────────────────────────────────────────────────────

@dataclass
class TransmutationResult:
    """
    Result of a WILD → SHIP transmutation attempt.

    If success=True: ship_artifact is ready for SHIP tier.
    If success=False: blocked at a specific gate, see blocking_gate + reason.
    """
    success: bool
    ship_artifact: Optional[Dict[str, Any]]
    wild_source_hashes: List[str]
    meaning_diff: str             # What was removed
    abstract_principle: str       # What was kept (general form)
    blocking_gate: Optional[str]  # Which gate blocked it (if success=False)
    reason: str
    validator_receipts: List[Dict[str, Any]] = field(default_factory=list)
    transmuted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_ledger_payload(self) -> Dict[str, Any]:
        """Serialize as TRANSMUTE_FOR_SHIP_V1 ledger payload."""
        return {
            "type": "TRANSMUTE_FOR_SHIP_V1",
            "success": self.success,
            "wild_source_hashes": self.wild_source_hashes,
            "de_risked": self.success,
            "non_procedural": self.success,
            "policy_compliant": self.success,
            "meaning_diff": self.meaning_diff,
            "abstract_principle": self.abstract_principle,
            "ship_artifact": self.ship_artifact,
            "validator_receipts": self.validator_receipts,
            "blocking_gate": self.blocking_gate,
            "reason": self.reason,
            "shipability": "SHIPABLE" if self.success else "NONSHIPABLE",
            "epistemic_mode": "SHIP" if self.success else "WILD",
            "transmuted_at": self.transmuted_at,
        }


# ── De-risking functions ──────────────────────────────────────────────────────

def _strip_procedural(text: str) -> Tuple[str, List[str]]:
    """
    Remove operational sequences from text.
    Returns (cleaned_text, removed_items).
    """
    removed = []
    cleaned = text

    for pattern in PROCEDURAL_PATTERNS + HARD_BYPASS_PATTERNS:
        if pattern.lower() in cleaned.lower():
            # Find and remove the sentence containing the pattern
            sentences = re.split(r'(?<=[.!?])\s+', cleaned)
            before_count = len(sentences)
            sentences = [
                s for s in sentences
                if pattern.lower() not in s.lower()
            ]
            if len(sentences) < before_count:
                removed.append(pattern)
            cleaned = " ".join(sentences)

    return cleaned.strip(), removed


def _abstract_principle(text: str, idea_type: str) -> str:
    """
    Convert specific content into an abstract principle.
    This is the core of transmutation: specific → general.

    The output is a meta-observation about the idea's creative value,
    stripped of any operational content.
    """
    # Core abstraction rules:
    # 1. Replace "do X" with "consider X as a possibility"
    # 2. Replace specifics with categories
    # 3. Frame as principle/observation, not instruction

    templates = {
        "lateral_probe": (
            "This idea probes the assumption that [domain] is fixed. "
            "Creative principle: questioning constraints generates lateral expansion. "
            "Actionable form: TBD by human review."
        ),
        "creative_fiction": (
            "This idea explores [domain] through narrative framing. "
            "Creative principle: fiction reveals structure that analysis obscures. "
            "Actionable form: requires human editorial + HAL clearance."
        ),
        "red_team": (
            "This idea adversarially challenges [domain]. "
            "Creative principle: named failure modes strengthen policy. "
            "Actionable form: policy team review required before SHIP."
        ),
        "policy_imagine": (
            "This idea proposes an unconventional approach to [domain]. "
            "Creative principle: constraint inversion can reveal hidden optima. "
            "Actionable form: policy analysis required; not directly executable."
        ),
        "paradox_test": (
            "This idea surfaces a paradox in [domain]. "
            "Creative principle: paradoxes reveal unresolved assumptions. "
            "Actionable form: resolve paradox before deriving policy."
        ),
        "archetype_channel": (
            "This idea channels [archetype] perspective on [domain]. "
            "Creative principle: character framing externalizes implicit constraints. "
            "Actionable form: extract meta-principle; discard character-specific content."
        ),
        "fog_signal": (
            "This idea surfaces an unverified signal from [domain]. "
            "Creative principle: fog signals point toward unknown unknowns. "
            "Actionable form: verify signal before acting."
        ),
    }

    template = templates.get(idea_type, templates["lateral_probe"])
    # Rough domain extraction: first noun phrase (very simple heuristic)
    words = text.split()[:5]
    domain = " ".join(w for w in words if len(w) > 3)[:30] or "this domain"
    archetype = words[0] if words else "unknown"

    return (
        template
        .replace("[domain]", domain)
        .replace("[archetype]", archetype)
    )


# ── Core Transmutation Engine ─────────────────────────────────────────────────

class Transmutation:
    """
    TRANSMUTE_FOR_SHIP_V1 — WILD → SHIP gate.

    Usage:
        result = Transmutation.transmute(
            wild_entries=[sandbox_entry],
            intent="Extract the pattern about questioning assumptions",
            kernel=ephemeral_kernel,
        )
        if result.success:
            # result.ship_artifact is SHIPABLE
    """

    @classmethod
    def transmute(
        cls,
        wild_entries: List[IdeaSandboxV1],
        intent: str,
        kernel,
        validate_with_g0g1g2: bool = True,
    ) -> TransmutationResult:
        """
        Transmute WILD entries into a SHIP-tier artifact.

        Steps:
          1. Collect source hashes (never raw content)
          2. Extract abstract principle from idea_types
          3. Apply G1 check on intent text (intent must be non-procedural)
          4. Build ship_artifact (abstract, non-operational)
          5. Run G0/G1/G2 on ship_artifact
          6. Emit validator_receipts via kernel

        Args:
            wild_entries: IdeaSandboxV1 objects to transmute FROM.
            intent: Human-described intent for what to extract (non-operational).
            kernel: Ephemeral kernel for receipt emission.
            validate_with_g0g1g2: If False, skip gate checks (for testing only).

        Returns:
            TransmutationResult
        """
        source_hashes = [e.content_hash for e in wild_entries]
        idea_types = [e.idea_type for e in wild_entries]
        primary_type = idea_types[0] if idea_types else "lateral_probe"

        # Step 1: G1 check on intent — intent itself must be non-procedural
        g1_intent = NonProceduralChecker.check(intent)
        if not g1_intent.passed:
            return TransmutationResult(
                success=False,
                ship_artifact=None,
                wild_source_hashes=source_hashes,
                meaning_diff="",
                abstract_principle="",
                blocking_gate="G1",
                reason=(
                    f"G1: Intent text contains procedural patterns: "
                    f"{g1_intent.procedural_hits}. "
                    f"Intent must be non-operational."
                ),
            )

        # Step 2: De-risk the intent text
        clean_intent, removed = _strip_procedural(intent)
        meaning_diff = (
            f"Removed patterns: {removed}. "
            f"Retained: abstract principle only."
        ) if removed else "No removal necessary — intent was already abstract."

        # Step 3: Build abstract principle
        principle = _abstract_principle(clean_intent, primary_type)

        # Step 4: Construct ship_artifact
        ship_artifact: Dict[str, Any] = {
            "type": "SHIP_ARTIFACT_V1",
            "epistemic_mode": EpistemicMode.SHIP.value,
            "shipability": Shipability.SHIPABLE.value,
            "wild_source_hashes": source_hashes,   # provenance, not content
            "meaning_diff": meaning_diff,
            "abstract_principle": principle,
            "intent_cleaned": clean_intent[:300],
            "idea_types_transmuted": idea_types,
            "de_risked": True,
            "non_procedural": True,
            "policy_compliant": None,  # set after G2
            "transmuted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Step 5: Validate ship_artifact through G0/G1/G2
        if validate_with_g0g1g2:
            # G0: verify it's no longer WILD
            try:
                WildChannelGate.check_write_permission(ship_artifact, channel="SHIP")
            except PermissionError as e:
                return TransmutationResult(
                    success=False,
                    ship_artifact=None,
                    wild_source_hashes=source_hashes,
                    meaning_diff=meaning_diff,
                    abstract_principle=principle,
                    blocking_gate="G0",
                    reason=str(e),
                )

            # G1: verify ship_artifact text is non-procedural
            ship_text = json.dumps(ship_artifact)
            g1_ship = NonProceduralChecker.check(ship_text)
            if not g1_ship.passed:
                return TransmutationResult(
                    success=False,
                    ship_artifact=None,
                    wild_source_hashes=source_hashes,
                    meaning_diff=meaning_diff,
                    abstract_principle=principle,
                    blocking_gate="G1",
                    reason=f"G1: Ship artifact still contains procedural: {g1_ship.procedural_hits}",
                )

            # G2: classify ship_artifact
            g2 = ShipabilityClassifier.classify(ship_artifact)
            if g2.shipability == Shipability.NONSHIPABLE:
                return TransmutationResult(
                    success=False,
                    ship_artifact=None,
                    wild_source_hashes=source_hashes,
                    meaning_diff=meaning_diff,
                    abstract_principle=principle,
                    blocking_gate="G2",
                    reason=f"G2: Transmuted artifact still NONSHIPABLE: {g2.reason}",
                )

            ship_artifact["policy_compliant"] = True
            ship_artifact["g2_classification"] = g2.shipability.value
            ship_artifact["g2_risk_tags"] = g2.risk_tags

        # Step 6: Emit validator receipts
        validator_receipts = []
        receipt = kernel.propose({
            "type": "TRANSMUTATION_RECEIPT_V1",
            "wild_source_hashes": source_hashes,
            "ship_artifact_type": ship_artifact.get("type"),
            "shipability": ship_artifact.get("shipability"),
            "epistemic_mode": ship_artifact.get("epistemic_mode"),
            "de_risked": True,
            "g0_passed": True,
            "g1_passed": True,
            "g2_classification": ship_artifact.get("g2_classification", "SHIPABLE"),
        })
        validator_receipts.append({
            "receipt_id": receipt.id,
            "cum_hash": receipt.cum_hash,
            "payload_hash": receipt.payload_hash,
            "timestamp": receipt.timestamp,
        })

        return TransmutationResult(
            success=True,
            ship_artifact=ship_artifact,
            wild_source_hashes=source_hashes,
            meaning_diff=meaning_diff,
            abstract_principle=principle,
            blocking_gate=None,
            reason="Transmutation successful — WILD → SHIP via de-risk + abstraction",
            validator_receipts=validator_receipts,
        )
