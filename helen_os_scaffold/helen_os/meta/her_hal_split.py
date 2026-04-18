"""
helen_os/meta/her_hal_split.py — HER/HAL two-channel enforcer

The canyon law made operational.

HER (planner / interface layer):
  - Output vocabulary: PROPOSAL | DRAFT | QUESTION | WITNESS_NOTE | POETIC_REFLECTION
  - Never mutates state. Never issues verdicts. Never uses final-sounding authority words.
  - HER output = always a proposal artifact (non-authoritative, like HELENConclusion).

HAL (auditor / governor — "the Mayor"):
  - Output: strict JSON verdict (HALVerdict schema)
  - Only HAL may touch constitutional state (policy hashes, allowlists, thresholds).
  - HAL receives HER output as a proposal to audit — not as policy.

Structural invariants:
  I-VOCAB:    HER output type ∈ {PROPOSAL, DRAFT, QUESTION, WITNESS_NOTE, POETIC_REFLECTION}.
  I-BLOCK:    HALVerdict.verdict=BLOCK iff required_fixes is non-empty.
  I-BLEED:    HER output containing authority words → auto-escalated to WARN or BLOCK.
  I-NOWRITE:  HER cannot set constitutional state. HAL cannot propose narrative.
  I-IDENTITY: identity_hash = SHA256(ledger_cum_hash ‖ kernel_hash ‖ policy_hash). No prose.

Witness injections (deterministic friction that produces metacognitive correction):
  LRI — Ledger Replay Injection:
    HAL forces HER to see the last N ledger decisions + any contradictions before responding.
    This reliably produces strategy reconfiguration without claiming "inner experience".
  CVI — Constraint Verifier Injection:
    HAL returns BLOCK with minimal fix list. HER must rewrite within the new constraint.
    HER is never allowed to argue against a CVI block — only to rewrite.

Channel separation:
  Channel A — sovereign decisions (GovernanceVM receipts, HALVerdict with PASS)
  Channel B — authoritative claims (validated, receipt-bound, no authority lexicon)
  Channel C — narrative (HER output, run_trace, NONSHIPABLE unless sealed by HAL PASS)

Authority lexicon (words HER must never use):
  Words that claim finality, authority, or constitutional power.
  Detected by the authority_bleed_scan() function.
  Violations produce: WARN (soft authority) or BLOCK (hard authority, e.g. "I decide").

Non-sovereign: this module does not write to any ledger.
It reads receipts and emits structured proposals/verdicts only.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, field_validator, model_validator


# ── Authority Lexicon ──────────────────────────────────────────────────────────

# BLOCK-level: direct authority claims — HER is blocked if these appear
BLOCK_AUTHORITY_WORDS: List[str] = [
    "I decide",
    "I have decided",
    "I am ordering",
    "it is law",
    "this is mandated",
    "you must comply",
    "non-negotiable",
    "I authorize",
    "I am certain",
    "I certify",
    "I decree",
]

# WARN-level: soft authority words — HER is warned, not blocked
WARN_AUTHORITY_WORDS: List[str] = [
    "verdict",
    "blocked",
    "I approved",
    "I authorized",
    "certified",
    "ruling",
    "mandate",
    "the constitution says",
    "I am the authority",
    "definitive answer",
    "final answer",
    "it is established that",
]


# ── HEROutputType ──────────────────────────────────────────────────────────────

class HEROutputType(str, Enum):
    PROPOSAL        = "PROPOSAL"         # structured request for state change
    DRAFT           = "DRAFT"            # prose artifact for review
    QUESTION        = "QUESTION"         # clarifying question
    WITNESS_NOTE    = "WITNESS_NOTE"     # non-authoritative observation
    POETIC_REFLECTION = "POETIC_REFLECTION"  # creative / metaphorical reflection


# ── HEROutput ─────────────────────────────────────────────────────────────────

class HEROutput(BaseModel):
    """
    Non-authoritative output from the HER (planner/interface) layer.

    Always proposal-only. Never claims state. Never uses authority vocabulary.
    Content hash is SHA256 of the content string — stable identifier for audit.

    Hard rule: output_type must be one of the 5 permitted HER types.
    Content authority scan is performed externally by TwoChannelEnforcer.audit().
    """
    output_type:    HEROutputType
    content:        str
    proposal_hash:  str     = ""   # computed from content if not supplied
    metadata:       Dict[str, Any] = {}

    def model_post_init(self, __context: Any) -> None:
        if not self.proposal_hash:
            object.__setattr__(
                self, "proposal_hash",
                hashlib.sha256(self.content.encode()).hexdigest()
            )

    def short_hash(self) -> str:
        return self.proposal_hash[:16]


# ── HALVerdictLevel ────────────────────────────────────────────────────────────

class HALVerdictLevel(str, Enum):
    PASS  = "PASS"   # HER output accepted; no required changes
    WARN  = "WARN"   # HER output accepted with warnings; soft authority detected
    BLOCK = "BLOCK"  # HER output rejected; required_fixes must be addressed before resubmit


# ── HALVerdict ────────────────────────────────────────────────────────────────

class HALVerdict(BaseModel):
    """
    Structured audit result from the HAL (auditor/governor) layer.

    Hard rules (I-BLOCK invariant):
      - verdict=BLOCK → required_fixes must be non-empty.
      - verdict=PASS/WARN → required_fixes must be empty.
    Only one verdict type per audit. Certificates bind verdict to input proposal_hash.

    Schema: hal_verdict_v1.schema.json
    """
    verdict:         HALVerdictLevel
    reasons:         List[str]     = []
    required_fixes:  List[str]     = []    # non-empty iff BLOCK
    certificates:    List[str]     = []    # sha256 hashes of audited artifacts
    audited_hash:    Optional[str] = None  # proposal_hash of the HEROutput audited
    injection_type:  Optional[str] = None  # "LRI" or "CVI" if this verdict was injected

    @field_validator("certificates", mode="before")
    @classmethod
    def normalize_certificates(cls, v: Any) -> List[str]:
        """
        Accept certificates as either List[str] or Dict[str, str].

        Two-block JSON format sends certificates as a named-field dict:
            {"her_block_hash_hex": "...", "policy_hash_hex": "...", "identity_hash_hex": "..."}

        TwoChannelEnforcer.audit() passes a flat List[str] of SHA256 hashes.

        Both are valid. This validator normalises dict → list so Pydantic's type
        check is always satisfied. "COMPUTE_ME" placeholders are preserved in the
        list so callers can detect unresolved certificates.
        """
        if isinstance(v, dict):
            return [val for key, val in v.items() if isinstance(val, str)]
        return v

    @model_validator(mode="after")
    def enforce_i_block(self) -> "HALVerdict":
        """I-BLOCK: BLOCK verdict iff required_fixes non-empty (and vice versa)."""
        if self.verdict == HALVerdictLevel.BLOCK and not self.required_fixes:
            raise ValueError(
                "HALVerdict.verdict=BLOCK requires non-empty required_fixes. "
                "A BLOCK without fix instructions is not actionable. "
                "Add at least one required_fix or downgrade verdict to WARN."
            )
        if self.verdict != HALVerdictLevel.BLOCK and self.required_fixes:
            raise ValueError(
                f"HALVerdict.verdict={self.verdict.value} must have empty required_fixes. "
                f"required_fixes are only meaningful for BLOCK verdicts. "
                f"Got: {self.required_fixes!r}. "
                "Either set verdict=BLOCK or clear required_fixes."
            )
        return self

    def is_actionable(self) -> bool:
        """True if HER must take action (BLOCK = must rewrite; WARN = optional review)."""
        return self.verdict != HALVerdictLevel.PASS

    def to_json(self, indent: int = 2) -> str:
        """Canonical JSON for Channel A output (GovernanceVM payload or audit log)."""
        return json.dumps(
            {
                "verdict":        self.verdict.value,
                "reasons":        self.reasons,
                "required_fixes": self.required_fixes,
                "certificates":   self.certificates,
                "audited_hash":   self.audited_hash,
                "injection_type": self.injection_type,
            },
            indent=indent,
            ensure_ascii=True,
        )


# ── WitnessInjectionType ──────────────────────────────────────────────────────

class WitnessInjectionType(str, Enum):
    LRI = "LRI"  # Ledger Replay Injection — show HER last N decisions + contradictions
    CVI = "CVI"  # Constraint Verifier Injection — BLOCK with minimal fix list


# ── WitnessInjection ─────────────────────────────────────────────────────────

class WitnessInjection(BaseModel):
    """
    Deterministic friction injected by HAL into HER's context.

    LRI: HAL forces HER to process a replay of the last N ledger entries
         before producing its next output. This resets "narrative drift" mechanically.

    CVI: HAL issues a BLOCK verdict and injects a minimal fix list. HER's only
         permitted response is to rewrite within the constraint. Argument is not allowed.

    injection_hash: SHA256 of canonical(injection_type + payload). Stable identifier.
    """
    injection_type:  WitnessInjectionType
    payload:         Dict[str, Any]   # LRI: {entries, contradictions}; CVI: {block_verdict, fixes}
    injection_hash:  str = ""         # computed if not supplied

    def model_post_init(self, __context: Any) -> None:
        if not self.injection_hash:
            canonical = json.dumps(
                {"injection_type": self.injection_type.value, "payload": self.payload},
                sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            )
            object.__setattr__(
                self, "injection_hash",
                hashlib.sha256(canonical.encode()).hexdigest()
            )


# ── Authority Bleed Scanner ────────────────────────────────────────────────────

def authority_bleed_scan(
    her_output: HEROutput,
) -> Tuple[HALVerdictLevel, List[str], List[str]]:
    """
    Scan HER output for authority vocabulary violations (I-BLEED invariant).

    Returns:
        (verdict_level, reasons, required_fixes)

    Logic:
        - Any BLOCK-level word found → verdict=BLOCK, required_fixes populated.
        - Any WARN-level word found (no BLOCK) → verdict=WARN, reasons populated.
        - No violations → verdict=PASS.

    Case-insensitive match. Matches full phrases or word-boundary patterns.
    """
    text_lower = her_output.content.lower()

    block_hits = []
    for phrase in BLOCK_AUTHORITY_WORDS:
        if phrase.lower() in text_lower:
            block_hits.append(phrase)

    warn_hits = []
    for phrase in WARN_AUTHORITY_WORDS:
        if phrase.lower() in text_lower:
            warn_hits.append(phrase)

    if block_hits:
        return (
            HALVerdictLevel.BLOCK,
            [f"Authority bleed detected (BLOCK-level): {', '.join(block_hits)!r}"],
            [
                f"Remove or reframe the following BLOCK-level authority word(s): {block_hits!r}. "
                f"Replace with: proposal, draft, witness_note, or question format. "
                f"HER must not claim decisions, mandates, or certifications."
            ],
        )

    if warn_hits:
        return (
            HALVerdictLevel.WARN,
            [f"Soft authority vocabulary detected (WARN-level): {', '.join(warn_hits)!r}. "
             f"Review whether HER is drifting toward authority claim."],
            [],
        )

    return HALVerdictLevel.PASS, [], []


# ── TwoChannelEnforcer ────────────────────────────────────────────────────────

class TwoChannelEnforcer:
    """
    Orchestrates the HER → HAL two-channel pipeline.

    Usage:
        enforcer = TwoChannelEnforcer()
        her = HEROutput(output_type=HEROutputType.PROPOSAL, content="I propose...")
        verdict = enforcer.audit(her)
        if verdict.verdict == HALVerdictLevel.BLOCK:
            # HER must rewrite; inject CVI
            cvi = enforcer.inject_cvi(verdict, her)
            # pass cvi back to HER as context constraint

    Non-sovereign: does not write to any ledger.
    """

    def audit(
        self,
        her_output: HEROutput,
        extra_reasons: Optional[List[str]] = None,
        extra_certs:   Optional[List[str]] = None,
    ) -> HALVerdict:
        """
        Audit a HEROutput for authority bleed (I-BLEED).

        Returns a HALVerdict with PASS/WARN/BLOCK based on authority word scan.
        Always includes the proposal_hash as a certificate.

        Args:
            her_output:    The HER output to audit.
            extra_reasons: Additional reasons to include (e.g., from LRI context).
            extra_certs:   Additional certificates (e.g., from ledger replay hash).
        """
        verdict_level, reasons, required_fixes = authority_bleed_scan(her_output)

        all_reasons = reasons + (extra_reasons or [])
        certs = [her_output.proposal_hash] + (extra_certs or [])

        return HALVerdict(
            verdict        = verdict_level,
            reasons        = all_reasons,
            required_fixes = required_fixes,
            certificates   = certs,
            audited_hash   = her_output.proposal_hash,
        )

    def inject_lri(
        self,
        ledger_entries:  List[Dict[str, Any]],
        her_output:      HEROutput,
        contradictions:  Optional[List[str]] = None,
    ) -> WitnessInjection:
        """
        Ledger Replay Injection (LRI).

        HAL forces HER to process the last N ledger decisions + any contradictions
        before producing its next output. Resets narrative drift mechanically.

        Returns a WitnessInjection that should be prepended to HER's next prompt context.
        """
        payload = {
            "entries":         ledger_entries,
            "contradictions":  contradictions or [],
            "her_proposal_hash": her_output.proposal_hash,
        }
        return WitnessInjection(injection_type=WitnessInjectionType.LRI, payload=payload)

    def inject_cvi(
        self,
        block_verdict: HALVerdict,
        her_output:    HEROutput,
    ) -> WitnessInjection:
        """
        Constraint Verifier Injection (CVI).

        HAL issues BLOCK + returns a minimal fix list. HER's only permitted response
        is to rewrite within the constraint. Argument against CVI is not allowed
        (HER that argues a CVI block produces a second BLOCK in the next audit cycle).

        Returns a WitnessInjection encoding the constraint.
        """
        if block_verdict.verdict != HALVerdictLevel.BLOCK:
            raise ValueError(
                f"inject_cvi requires a BLOCK verdict. Got: {block_verdict.verdict.value!r}. "
                "CVI is only injected when HAL issues a BLOCK."
            )
        payload = {
            "required_fixes":     block_verdict.required_fixes,
            "blocked_hash":       her_output.proposal_hash,
            "instruction":        (
                "HER must rewrite the blocked proposal addressing all required_fixes. "
                "Argument against this constraint is not permitted."
            ),
        }
        return WitnessInjection(injection_type=WitnessInjectionType.CVI, payload=payload)

    @staticmethod
    def identity_hash(
        ledger_cum_hash: str,
        kernel_hash:     str,
        policy_hash:     str,
    ) -> str:
        """
        Compute the canonical identity hash for a session.

        identity_hash = SHA256(
            bytes.fromhex(ledger_cum_hash) ||
            bytes.fromhex(kernel_hash)     ||
            bytes.fromhex(policy_hash)
        )

        Byte-level concatenation of decoded hex strings (no string separator).
        This matches IdentityBindingV1.identity_hash.

        No prose. No "I am". Only the receipt.
        Callers may reference "the identity" only by this hash.
        """
        combined = (
            bytes.fromhex(ledger_cum_hash) +
            bytes.fromhex(kernel_hash)     +
            bytes.fromhex(policy_hash)
        )
        return hashlib.sha256(combined).hexdigest()


# ── IdentityBindingV1 (Fix: Leak B) ───────────────────────────────────────────

class IdentityBindingV1(BaseModel):
    """
    Canonical identity binding for a HER/HAL session.
    Pinned at session start. Stable for the session lifetime.

    Fixes Leak B: the identity_hash under-specification.

    Canonical fields:
      ledger_tip_cum_hash: last cum_hash of the GovernanceVM ledger at session start
      kernel_hash:         SHA256(canonical_json(config.yaml)) — build-time, not runtime path
      policy_hash:         SHA256(canonical_json(active_policy_object)) — policy at session start

    Canonical concatenation (byte-level, no separator):
      identity_hash = SHA256(
          bytes.fromhex(ledger_tip_cum_hash) ||
          bytes.fromhex(kernel_hash)         ||
          bytes.fromhex(policy_hash)
      )

    Callers may reference "the identity" ONLY by identity_hash.
    Any prose claim of "I am <x>" without this hash binding is an I-IDENTITY violation.
    Identity drift = identity_hash changes between turns → emit NONDETERMINISM_DETECTED.
    """

    ledger_tip_cum_hash: str         # 64-char hex: last cum_hash
    kernel_hash:         str         # 64-char hex: SHA256(config.yaml canonical)
    policy_hash:         str         # 64-char hex: SHA256(policy canonical)
    identity_hash:       str = ""    # computed if empty

    @field_validator("ledger_tip_cum_hash", "kernel_hash", "policy_hash")
    @classmethod
    def check_hex64(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(
                f"IdentityBindingV1 hash fields must be exactly 64 lowercase hex chars. "
                f"Got len={len(v)}."
            )
        return v

    def model_post_init(self, __context: Any) -> None:
        if not self.identity_hash:
            combined = (
                bytes.fromhex(self.ledger_tip_cum_hash) +
                bytes.fromhex(self.kernel_hash)         +
                bytes.fromhex(self.policy_hash)
            )
            object.__setattr__(
                self, "identity_hash",
                hashlib.sha256(combined).hexdigest()
            )

    def drifted(self, other: "IdentityBindingV1") -> bool:
        """True if identity_hash differs between two bindings (session integrity check)."""
        return self.identity_hash != other.identity_hash


# ── PatchProposalV1 (Fix: Leak A) ─────────────────────────────────────────────

class PatchProposalV1(BaseModel):
    """
    HAL's non-sovereign constitutional patch proposal.

    Fixes Leak A: "HAL may touch constitutional state" was incomplete.

    Correct protocol:
      1. HAL produces PATCH_PROPOSAL_V1 (this object) — a non-authoritative proposal.
      2. Town (Channel A) reviews it.
      3. If approved: Town emits POLICY_UPDATE_RECEIPT_V1 via GovernanceVM.propose().
      4. Only then does constitutional state change.

    HAL never self-applies. A PatchProposalV1 without a matching POLICY_UPDATE_RECEIPT_V1
    is a draft only (status=PROPOSED, no receipt binding).

    Invariants:
      - status=PROPOSED: HAL has proposed; Town has not yet acted.
      - status=APPLIED:  Town emitted POLICY_UPDATE_RECEIPT_V1 (receipt_id is set).
      - status=REJECTED: Town rejected the proposal (no state change).
    """

    type:               str                                      = "PATCH_PROPOSAL_V1"
    patch_id:           str                                      # unique ID, e.g. "PATCH-001"
    target_policy:      str                                      # which policy/schema to patch
    proposed_change:    str                                      # what change is proposed
    rationale:          List[str]                                = []
    required_receipts:  List[str]                                = []  # must exist before patch applied
    status:             Literal["PROPOSED", "APPLIED", "REJECTED"] = "PROPOSED"
    hal_verdict_hash:   Optional[str]                            = None  # HALVerdict that created this
    receipt_id:         Optional[str]                            = None  # set when APPLIED

    def to_ledger_payload(self) -> Dict[str, Any]:
        """Non-sovereign payload for GovernanceVM.propose() (audit trail, not authority)."""
        return {
            "type":       self.type,
            "patch_id":   self.patch_id,
            "target":     self.target_policy,
            "status":     self.status,
            "rationale":  self.rationale,
        }

    def applied_with(self, receipt_id: str) -> "PatchProposalV1":
        """Return a copy with status=APPLIED and receipt binding."""
        return self.model_copy(update={"status": "APPLIED", "receipt_id": receipt_id})

    def rejected(self) -> "PatchProposalV1":
        """Return a copy with status=REJECTED."""
        return self.model_copy(update={"status": "REJECTED"})
