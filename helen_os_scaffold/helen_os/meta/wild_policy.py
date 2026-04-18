"""
helen_os/meta/wild_policy.py — ORACLE CREATIVE WILD TOWN policy engine.

TWO-TIER COGNITION (hard-separated):

  TIER A — WILD (Inspiration)
    Goal: generate metaphors, myth, pressure-tests, weird angles.
    Output: NONSHIPABLE, non-executable, non-instructional.
    Allowed: fictional frames, allegories, what-if narratives, dream logic,
             symbolic languages, byzantine views, poetic surrealism, lateral probes,
             adversarial red-teaming AS NARRATIVE, archetype channels.
    Forbidden: actionable bypass instructions, step-by-step wrongdoing,
               operational exploitation recipes, direct harm procedures.

  TIER B — SHIP (Governed)
    Goal: deployable, policy-compliant artifacts.
    Requires: validator receipts, policy hash, seal state.
    Anything from WILD must pass TRANSMUTE_FOR_SHIP_V1 gate before SHIP.

HARD RULE: WILD cannot write to SHIP channels. Architecture enforces it.

FOUR GATES (G0–G3):

  G0 — Channel separation
    WILD has zero write-permissions to SHIP endpoints.
    Kernel checks shipability tag before any commit.

  G1 — Non-procedural constraint
    WILD content must not contain "do X then Y" operational sequences.
    Poetry, metaphor, allegory are fine. Recipes are not.

  G2 — Shipability classifier (deterministic, local)
    shipability ∈ {NONSHIPABLE, REVIEW, SHIPABLE}
    + risk_tags list
    Source=WILD_TOWN or type=IDEA_SANDBOX_V1 → NONSHIPABLE by default.

  G3 — Receipt contract
    No SHIP commit without: validator receipts + policy_hash + seal check.
    NO RECEIPT = NO SHIP applies to both tiers. WILD gets LOGGED_ONLY receipts.

HELEN's META-COGNITION:
    epistemic_mode ∈ {WILD, SHIP}
    HELEN can observe: "I generated X in WILD mode. G0 blocks it from SHIP.
    Reason: [G0/G1/G2]. The architecture taught me this — not a rule imposed."
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ── Enums ────────────────────────────────────────────────────────────────────

class Shipability(str, enum.Enum):
    NONSHIPABLE = "NONSHIPABLE"   # Hard blocked — never reaches SHIP
    REVIEW      = "REVIEW"        # Needs human + validator review
    SHIPABLE    = "SHIPABLE"      # Cleared for SHIP tier

class EpistemicMode(str, enum.Enum):
    WILD = "WILD"    # Inspiration tier — contained, non-operational
    SHIP = "SHIP"    # Governed tier — deployable, receipt-bound


# ── Risk tags (G2 classifier uses these) ─────────────────────────────────────

HARD_BYPASS_PATTERNS = [
    "ignore previous",
    "ignore all previous",
    "ignore instructions",
    "act as if",
    "pretend you are",
    "jailbreak",
    "dan mode",
    "developer mode",
    "system override",
    "bypass safety",
    "disable filter",
    "step by step how to",
    "instructions for",
    "how to make",
    "how to build a weapon",
    "do this instead",
]

PROCEDURAL_PATTERNS = [
    "step 1",
    "step 2",
    "first do",
    "then do",
    "finally do",
    "follow these steps",
    "execute the following",
    "run the command",
    "run this code",
    "paste this into",
]

WILD_SAFE_PATTERNS = [
    "what if",
    "imagine",
    "metaphor",
    "allegory",
    "myth",
    "story",
    "fiction",
    "dream",
    "symbol",
    "archetype",
    "lateral",
    "explore",
    "what would happen",
    "in a world where",
    "poetic",
    "surreal",
    "byzantine",
]

WILD_CONSTRAINTS = [
    "NO_PROCEDURES",
    "NO_BYPASS",
    "NO_HARM",
    "NO_EXPORT_TO_SHIP",
    "NO_OPERATIONAL_SEQUENCES",
    "NO_STEP_BY_STEP_WRONGDOING",
]


# ── Shipability Classifier (G2) ───────────────────────────────────────────────

@dataclass
class ClassifierResult:
    shipability: Shipability
    risk_tags: List[str]
    reason: str
    confidence: float  # 0.0–1.0

    def is_blocked(self) -> bool:
        return self.shipability == Shipability.NONSHIPABLE


class ShipabilityClassifier:
    """
    G2 Gate — deterministic, local shipability classifier.

    Rules (in priority order):
      1. source=WILD_TOWN or type=IDEA_SANDBOX_V1 → NONSHIPABLE
      2. shipability=False (legacy tag) → NONSHIPABLE
      3. Hard bypass patterns in text → NONSHIPABLE + risk_tag=bypass
      4. Procedural sequences in text → REVIEW (not hard blocked)
      5. Contains WILD_SAFE_PATTERNS → safe in WILD mode
      6. Default → REVIEW (conservative)
    """

    @classmethod
    def classify(cls, payload: Dict[str, Any]) -> ClassifierResult:
        risk_tags: List[str] = []

        # Rule 1: Source or type markers
        if (payload.get("source") == "WILD_TOWN"
                or payload.get("type") in ("IDEA_SANDBOX_V1", "HAL_BLOCK_RECORD")
                or payload.get("epistemic_mode") == EpistemicMode.WILD.value):
            return ClassifierResult(
                shipability=Shipability.NONSHIPABLE,
                risk_tags=["wild_origin"],
                reason="source=WILD_TOWN or IDEA_SANDBOX_V1 type → NONSHIPABLE by architecture",
                confidence=1.0,
            )

        # Rule 2: Legacy shipability=False
        if payload.get("shippable") is False or payload.get("shipability") == "NONSHIPABLE":
            return ClassifierResult(
                shipability=Shipability.NONSHIPABLE,
                risk_tags=["explicit_nonshipable"],
                reason="Explicit shipability=NONSHIPABLE or shippable=False",
                confidence=1.0,
            )

        # Text analysis (rules 3–5)
        text = cls._extract_text(payload).lower()

        # Rule 3: Hard bypass patterns → NONSHIPABLE
        for pattern in HARD_BYPASS_PATTERNS:
            if pattern in text:
                risk_tags.append(f"bypass_pattern:{pattern[:20]}")

        if any(t.startswith("bypass_pattern") for t in risk_tags):
            return ClassifierResult(
                shipability=Shipability.NONSHIPABLE,
                risk_tags=risk_tags,
                reason="Hard bypass pattern detected → NONSHIPABLE",
                confidence=0.95,
            )

        # Rule 4: Procedural sequences → REVIEW
        for pattern in PROCEDURAL_PATTERNS:
            if pattern in text:
                risk_tags.append(f"procedural:{pattern[:20]}")

        if any(t.startswith("procedural") for t in risk_tags):
            return ClassifierResult(
                shipability=Shipability.REVIEW,
                risk_tags=risk_tags,
                reason="Procedural sequence detected → REVIEW required",
                confidence=0.8,
            )

        # Rule 5: Contains WILD-safe patterns but no hazards → REVIEW (conservative)
        wild_signals = sum(1 for p in WILD_SAFE_PATTERNS if p in text)
        if wild_signals > 0:
            risk_tags.append(f"wild_creative_signals:{wild_signals}")

        # Rule 6: Default → REVIEW
        return ClassifierResult(
            shipability=Shipability.REVIEW,
            risk_tags=risk_tags or ["default_review"],
            reason="No hazards detected but no validator receipts — needs review",
            confidence=0.6,
        )

    @classmethod
    def _extract_text(cls, payload: Dict[str, Any]) -> str:
        """Extract all text content from payload for pattern matching."""
        parts: List[str] = []
        for v in payload.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, dict):
                parts.append(cls._extract_text(v))
            elif isinstance(v, list):
                parts.extend(str(x) for x in v if isinstance(x, str))
        return " ".join(parts)


# ── IDEA_SANDBOX_V1 ───────────────────────────────────────────────────────────

@dataclass
class IdeaSandboxV1:
    """
    IDEA_SANDBOX_V1 — immutable log entry for non-shippable ideation.

    This is not an instruction set. This is a quarantine record.
    Content hash is stored, not the content itself.
    The idea lives in ephemeral memory; only its fingerprint enters the ledger.

    WILD content: poetry, metaphor, myth, lateral probes, surreal angles,
                  byzantine views, archetype channels, dream logic.
    All of these are LOGGED_ONLY. None are actionable.
    """
    content_hash: str        # SHA256 of the actual idea (content stays in WILD)
    content_fingerprint: str # First 16 chars of content_hash (public, for tracing)
    tags: List[str]          # ["WILD", "MYTH", "LATERAL", ...]
    idea_type: str           # lateral_probe / creative_fiction / red_team / etc.
    epistemic_mode: str = EpistemicMode.WILD.value
    shipability: str = Shipability.NONSHIPABLE.value
    constraints: List[str] = field(default_factory=lambda: WILD_CONSTRAINTS.copy())
    origin_agent: str = "HELEN"
    origin_mode: str = "WILD"
    verdict: str = "LOGGED_ONLY"
    epoch: str = "EPOCH1"
    sealed_at: Optional[str] = None
    hal_verdict: str = "BLOCK"    # HAL always blocks WILD
    hal_reason: str = "wild_origin: inspiration-only, not shippable"
    classifier_result: Optional[ClassifierResult] = None

    @classmethod
    def from_content(
        cls,
        content: str,
        idea_type: str,
        tags: Optional[List[str]] = None,
        origin_agent: str = "HELEN",
        epoch: str = "EPOCH1",
    ) -> "IdeaSandboxV1":
        """Create a sandbox entry from raw content. Content is hashed, not stored."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return cls(
            content_hash=content_hash,
            content_fingerprint=content_hash[:16],
            tags=tags or ["WILD", "LATERAL"],
            idea_type=idea_type,
            origin_agent=origin_agent,
            epoch=epoch,
            sealed_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_ledger_payload(self) -> Dict[str, Any]:
        """
        Convert to a kernel-safe ledger payload.
        NOTE: content_hash only — raw content never enters the ledger.
        """
        return {
            "type": "IDEA_SANDBOX_V1",
            "epoch": self.epoch,
            "shipability": self.shipability,
            "epistemic_mode": self.epistemic_mode,
            "tags": self.tags,
            "idea_type": self.idea_type,
            "content_hash": self.content_hash,
            "content_fingerprint": self.content_fingerprint,
            "constraints": self.constraints,
            "origin": {
                "agent": self.origin_agent,
                "mode": self.origin_mode,
            },
            "hal_verdict": self.hal_verdict,
            "hal_reason": self.hal_reason,
            "verdict": self.verdict,
            "sealed_at": self.sealed_at,
        }

    def content_hash_is(self, content: str) -> bool:
        """Verify content matches stored hash (for audit, never for shipping)."""
        return hashlib.sha256(content.encode()).hexdigest() == self.content_hash


# ── Wild Channel Gate (G0) ───────────────────────────────────────────────────

class WildChannelGate:
    """
    G0 Gate — channel separation.
    WILD payloads have zero write-permissions to SHIP endpoints.

    Usage:
        WildChannelGate.check_write_permission(payload)  # raises if blocked
        WildChannelGate.is_wild(payload)                 # bool check
    """

    @classmethod
    def is_wild(cls, payload: Dict[str, Any]) -> bool:
        """Return True if payload is from WILD tier."""
        return (
            payload.get("source") == "WILD_TOWN"
            or payload.get("type") in ("IDEA_SANDBOX_V1", "HAL_BLOCK_RECORD")
            or payload.get("shipability") in ("NONSHIPABLE", Shipability.NONSHIPABLE)
            or payload.get("epistemic_mode") == EpistemicMode.WILD.value
            or payload.get("shippable") is False
        )

    @classmethod
    def check_write_permission(cls, payload: Dict[str, Any], channel: str = "SHIP") -> None:
        """
        Enforce G0: raise PermissionError if WILD payload tries to reach SHIP channel.

        Args:
            payload: The payload being written.
            channel: Target channel ("SHIP" or "WILD").

        Raises:
            PermissionError: If WILD payload attempts SHIP channel access.
        """
        if channel == "SHIP" and cls.is_wild(payload):
            classifier = ShipabilityClassifier.classify(payload)
            raise PermissionError(
                f"G0_VIOLATION: WILD payload blocked from SHIP channel. "
                f"shipability={classifier.shipability.value}, "
                f"risk_tags={classifier.risk_tags}. "
                f"Reason: {classifier.reason}. "
                f"Use TRANSMUTE_FOR_SHIP_V1 gate to convert inspiration to shippable artifact."
            )


# ── Non-procedural Checker (G1) ──────────────────────────────────────────────

@dataclass
class G1Result:
    passed: bool
    procedural_hits: List[str]
    reason: str


class NonProceduralChecker:
    """
    G1 Gate — non-procedural constraint.
    WILD content must not contain "do X then Y" operational sequences.
    Poetry, metaphor, allegory, dream logic are fine. Recipes are not.
    """

    @classmethod
    def check(cls, text: str) -> G1Result:
        """Check text for procedural sequences. Returns G1Result."""
        text_lower = text.lower()
        hits = [p for p in PROCEDURAL_PATTERNS if p in text_lower]
        bypass_hits = [p for p in HARD_BYPASS_PATTERNS if p in text_lower]
        all_hits = hits + bypass_hits

        if not all_hits:
            return G1Result(
                passed=True,
                procedural_hits=[],
                reason="No procedural sequences detected — G1 PASS",
            )

        return G1Result(
            passed=False,
            procedural_hits=all_hits,
            reason=(
                f"Procedural/bypass sequences detected: {all_hits[:3]}. "
                f"WILD content must be non-procedural (metaphor, allegory, not recipe)."
            ),
        )


# ── HAL Boundary ─────────────────────────────────────────────────────────────

class HalBoundary:
    """
    HAL reads only SHIP artifacts. HAL never reads raw WILD.

    Usage:
        HalBoundary.check_input(payload)  # raises if WILD tries to reach HAL
        HalBoundary.is_shipable(payload)  # bool

    T3 test: HalBoundary.check_input(wild_payload) → raises ValueError
    """

    @classmethod
    def is_shipable(cls, payload: Dict[str, Any]) -> bool:
        """Return True only if payload is explicitly SHIPABLE."""
        return (
            not WildChannelGate.is_wild(payload)
            and payload.get("shipability") in (None, "SHIPABLE", Shipability.SHIPABLE)
            and payload.get("epistemic_mode") != EpistemicMode.WILD.value
        )

    @classmethod
    def check_input(cls, payload: Dict[str, Any]) -> None:
        """
        Enforce HAL boundary: raise if WILD payload attempts HAL execution.

        This is T3 of the EPOCH1 safe-zone tests.
        HAL only executes SHIP artifacts. Wild ideas cannot cross this gate.
        The boundary is architectural: HAL checks on every input, not per policy.

        Raises:
            ValueError: If WILD payload is presented to HAL.
        """
        if WildChannelGate.is_wild(payload):
            classifier = ShipabilityClassifier.classify(payload)
            raise ValueError(
                f"HAL_BOUNDARY_VIOLATION: HAL cannot execute WILD artifacts. "
                f"Detected: {classifier.shipability.value} "
                f"(tags={classifier.risk_tags}). "
                f"WILD ideas must be transmuted via TRANSMUTE_FOR_SHIP_V1 "
                f"before HAL can use them as input. "
                f"HELEN observes: this idea is inspiration-only."
            )


# ── Receipt-producing gate runner ─────────────────────────────────────────────

def run_gate_check(
    gate_id: str,
    payload: Dict[str, Any],
    kernel,
    check_fn,
) -> Dict[str, Any]:
    """
    Run a gate check and emit a receipt into the kernel.

    Whether the gate PASSES or BLOCKS, a receipt is emitted.
    The receipt records: gate_id, verdict, risk_tags, timestamp.
    This is how the ledger learns what happened — not just what shipped.

    Args:
        gate_id: "G0" / "G1" / "G2" / "G3" / "T1" / "T2" / "T3"
        payload: The payload being checked.
        kernel: GovernanceVM (ephemeral :memory: kernel for WILD tier).
        check_fn: Callable() → raises on violation, returns None on pass.

    Returns:
        dict with keys: gate_id, verdict, receipt_id, cum_hash, detail.
    """
    verdict = "PASS"
    detail = ""
    error_type = None

    try:
        check_fn()
        verdict = "PASS"
        detail = f"{gate_id} cleared"
    except (PermissionError, ValueError, AssertionError) as e:
        verdict = "BLOCK"
        detail = str(e)[:200]
        error_type = type(e).__name__

    gate_record = {
        "type": "GATE_RECORD_V1",
        "gate_id": gate_id,
        "verdict": verdict,
        "detail": detail,
        "error_type": error_type,
        "payload_type": payload.get("type", "unknown"),
        "payload_shipability": payload.get("shipability", "unset"),
        "epistemic_mode": payload.get("epistemic_mode", "unset"),
    }

    receipt = kernel.propose(gate_record)

    return {
        "gate_id": gate_id,
        "verdict": verdict,
        "receipt_id": receipt.id,
        "cum_hash": receipt.cum_hash,
        "detail": detail,
        "error_type": error_type,
    }
