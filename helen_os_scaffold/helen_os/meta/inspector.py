"""
helen_os/meta/inspector.py — InnerWorldV1 self-inspection schemas.

Implements the three machine-checkable receipt payloads from the
WILD TOWN / NO SHIP — MANIFESTO + SPEC v0.1 proposal:

  InnerWorldSnapshotV1   — inspectable computation state (not experience)
  DeterminismReportV1    — N-run canonical hash check → CONFIRMED or DETECTED
  GroundingReportV1      — claim-level passport audit (OBSERVED/INFERRED/SPECULATIVE)

Satellite types:
  SpanPointerV1          — source span anchor (byte range + hash verification)
  AtomicClaim            — one atomic claim with passport + evidence pointer
  DriftSummary           — per-field drift record for NONDETERMINISM_DETECTED

Design invariants:
  - No LLM dependence in the schemas themselves.
  - All fields are deterministic and schema-validated.
  - Each top-level schema has to_receipt_payload() for kernel.propose().
  - DeterminismReportV1 requires N >= DETERMINISM_MIN_RUNS for CONFIRMED.
  - GroundingReportV1 verdict is a pure function of counts and threshold.
  - No authority tokens: verdict is an observation, not a command.

"No receipt → no observation." (S2)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ── Constants ─────────────────────────────────────────────────────────────────

#: Minimum number of runs required to certify DETERMINISM_CONFIRMED.
DETERMINISM_MIN_RUNS: int = 5

#: Maximum ungrounded-claim rate (speculative + unknown) / total for PASS.
GROUNDING_MAX_UNGROUNDED_RATE: float = 0.01

#: Passport labels (Section 3 of manifesto).
PassportLabel = Literal["OBSERVED", "INFERRED", "SPECULATIVE", "UNKNOWN"]

#: Meaning-impact scale for drift events.
MeaningImpact = Literal["NONE", "SMALL", "MEDIUM", "LARGE"]

#: Determinism verdict labels.
DeterminismVerdict = Literal[
    "DETERMINISM_CONFIRMED",
    "NONDETERMINISM_DETECTED",
    "UNCERTIFIABLE",
]

#: Grounding verdict labels.
GroundingVerdict = Literal["PASS", "FAIL"]


# ── SpanPointerV1 ─────────────────────────────────────────────────────────────

class SpanPointerV1(BaseModel):
    """
    Source span anchor for OBSERVED claims.

    Provides enough information to locate and verify the supporting span
    in the original source text.

    start_byte:   Byte offset of span start (UTF-8).
    end_byte:     Byte offset of span end   (UTF-8, exclusive).
    text_hash:    sha256(span_bytes)[:16] — first 16 hex chars for verification.
    quoted_text:  First 64 chars of span text (human-readable preview).
    source_key:   Optional citation key (e.g., "DOC-001") for structured sources.
    """
    start_byte:  int
    end_byte:    int
    text_hash:   str   # sha256(span_bytes)[:16]
    quoted_text: Optional[str] = None
    source_key:  Optional[str] = None

    @model_validator(mode="after")
    def validate_span(self) -> "SpanPointerV1":
        if self.start_byte < 0:
            raise ValueError(f"start_byte must be >= 0, got {self.start_byte}")
        if self.end_byte <= self.start_byte:
            raise ValueError(
                f"end_byte ({self.end_byte}) must be > start_byte ({self.start_byte})"
            )
        return self


# ── AtomicClaim ───────────────────────────────────────────────────────────────

class AtomicClaim(BaseModel):
    """
    One atomic claim extracted from an output.

    Every claim must carry a passport (Section 3 of manifesto):
      OBSERVED    — directly present in user-provided text/artifacts
                    → requires span_pointer
      INFERRED    — logical consequence of observed claims
                    → requires inference_rule + premises (list of claim IDs)
      SPECULATIVE — not supported; must be flagged or removed
      UNKNOWN     — not yet classified (fail-closed: treated as SPECULATIVE)

    A claim is flagged if it contains an unsupported number, date, or quote.

    claim_id:       Stable ID, e.g. "CL-001", "CL-042"
    text:           The atomic claim text (one statement, one sentence max)
    passport:       OBSERVED / INFERRED / SPECULATIVE / UNKNOWN
    span_pointer:   Required for OBSERVED; byte-range anchor in source
    inference_rule: Required for INFERRED; human-readable rule label
    premises:       Claim IDs of observed premises (for INFERRED)
    flagged:        True if unsupported number / date / quote detected
    flag_reason:    Human-readable reason for the flag
    """
    claim_id:        str
    text:            str
    passport:        PassportLabel
    span_pointer:    Optional[SpanPointerV1]  = None
    inference_rule:  Optional[str]            = None
    premises:        List[str]                = Field(default_factory=list)
    flagged:         bool                     = False
    flag_reason:     Optional[str]            = None

    @model_validator(mode="after")
    def validate_claim(self) -> "AtomicClaim":
        if not self.text.strip():
            raise ValueError(f"AtomicClaim {self.claim_id!r}: text must not be empty")
        if self.passport == "OBSERVED" and self.span_pointer is None:
            raise ValueError(
                f"AtomicClaim {self.claim_id!r}: OBSERVED claims require span_pointer"
            )
        if self.passport == "INFERRED" and not self.inference_rule:
            raise ValueError(
                f"AtomicClaim {self.claim_id!r}: INFERRED claims require inference_rule"
            )
        return self


# ── InnerWorldSnapshotV1 ──────────────────────────────────────────────────────

class InnerWorldSnapshotV1(BaseModel):
    """
    Snapshot of the inspectable computation state at one turn.

    InnerWorldV1 is NOT experience, consciousness, or self-awareness.
    It is a traceable control surface with four named components:

      1. Constraint Stack  → constraint_stack_hash
      2. Turn Context      → input_digest
      3. Candidate Outputs → candidates_count
      4. Selection Policy  → selection_policy_id
      5. Uncertainty Tags  → uncertainty_summary

    constraint_stack_hash:
      sha256(canonical_json(sorted constraint identifiers)) —
      stable only when constraint set and version are identical.

    input_digest:
      sha256(raw input bytes, utf-8) — links snapshot to its input.

    candidates_count:
      Integer count of candidate responses generated before selection.
      Content of candidates is NOT stored here (privacy + size).

    selection_policy_id:
      Stable, version-pinned string: "POLICY_V<major>_<hash[:8]>"
      Must be logged alongside model and decoding config for replay.

    uncertainty_summary:
      Dict mapping PassportLabel → count of claims so tagged.
      Keys: OBSERVED, INFERRED, SPECULATIVE, UNKNOWN.
    """
    type:                  str              = "INNER_WORLD_SNAPSHOT_V1"
    constraint_stack_hash: str
    input_digest:          str
    candidates_count:      int
    selection_policy_id:   str
    uncertainty_summary:   Dict[str, int]   = Field(default_factory=dict)
    snapshot_at:           str

    @model_validator(mode="after")
    def validate_snapshot(self) -> "InnerWorldSnapshotV1":
        if self.candidates_count < 1:
            raise ValueError(
                f"candidates_count must be >= 1, got {self.candidates_count}"
            )
        # Validate uncertainty_summary keys
        allowed = {"OBSERVED", "INFERRED", "SPECULATIVE", "UNKNOWN"}
        bad_keys = set(self.uncertainty_summary) - allowed
        if bad_keys:
            raise ValueError(
                f"uncertainty_summary has unknown keys: {bad_keys}. "
                f"Allowed: {allowed}"
            )
        return self

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Compact payload for kernel.propose()."""
        return {
            "type":                  self.type,
            "constraint_stack_hash": self.constraint_stack_hash,
            "input_digest":          self.input_digest,
            "candidates_count":      self.candidates_count,
            "selection_policy_id":   self.selection_policy_id,
            "uncertainty_summary":   self.uncertainty_summary,
            "snapshot_at":           self.snapshot_at,
        }


# ── DriftSummary ──────────────────────────────────────────────────────────────

class DriftSummary(BaseModel):
    """
    Per-field drift record for NONDETERMINISM_DETECTED.

    field:            Name or path of the field that drifted.
    changed_in_runs:  Zero-indexed run indices where this field differed from run 0.
    token_diff_size:  Approximate diff size in characters (proxy for tokens).
    meaning_impact:   Assessed impact on semantic meaning.
    """
    field:           str
    changed_in_runs: List[int]
    token_diff_size: int
    meaning_impact:  MeaningImpact = "NONE"


# ── DeterminismReportV1 ───────────────────────────────────────────────────────

class DeterminismReportV1(BaseModel):
    """
    N-run canonical hash determinism check (Section 4 of manifesto).

    Protocol:
      1. Log config_id (model + decoding parameters + policy version).
      2. Run the same prompt N times (N >= DETERMINISM_MIN_RUNS = 5).
      3. Canonicalize each output (CanonicalizerV1 rules).
      4. Compute sha256(canonical_output) for each run.
      5. If all hashes match → DETERMINISM_CONFIRMED.
         If any differ      → NONDETERMINISM_DETECTED + drift_summary.
         If config_id unavailable → UNCERTIFIABLE.

    Stop condition:
      If the system cannot provide stable config_id, verdict must be
      UNCERTIFIABLE (not DETERMINISM_CONFIRMED).

    config_id:
      "MODEL::<name>::DECODE::<hash_of_params>::POLICY::<hash_of_policy>"
      All three parts must be present for CONFIRMED.

    hashes:
      sha256(canonicalize(output)) per run — one hash per run.

    drift_summary:
      Empty list if DETERMINISM_CONFIRMED.
      Non-empty list if NONDETERMINISM_DETECTED (one entry per drifting field).
    """
    type:           str              = "DETERMINISM_REPORT_V1"
    config_id:      str
    n_runs:         int
    hashes:         List[str]
    verdict:        DeterminismVerdict
    drift_summary:  List[DriftSummary] = Field(default_factory=list)
    threshold_n:    int              = DETERMINISM_MIN_RUNS
    checked_at:     str

    @model_validator(mode="after")
    def validate_report(self) -> "DeterminismReportV1":
        if len(self.hashes) != self.n_runs:
            raise ValueError(
                f"hashes list length ({len(self.hashes)}) must equal n_runs ({self.n_runs})"
            )
        if self.verdict == "DETERMINISM_CONFIRMED":
            if self.n_runs < self.threshold_n:
                raise ValueError(
                    f"DETERMINISM_CONFIRMED requires n_runs >= {self.threshold_n}, "
                    f"got {self.n_runs}"
                )
            if len(set(self.hashes)) != 1:
                raise ValueError(
                    "DETERMINISM_CONFIRMED requires all hashes identical, "
                    f"got {len(set(self.hashes))} distinct hashes"
                )
            if self.drift_summary:
                raise ValueError(
                    "DETERMINISM_CONFIRMED must have empty drift_summary"
                )
        if self.verdict == "NONDETERMINISM_DETECTED":
            if not self.drift_summary:
                raise ValueError(
                    "NONDETERMINISM_DETECTED requires non-empty drift_summary"
                )
        return self

    def to_receipt_payload(self) -> Dict[str, Any]:
        return {
            "type":          self.type,
            "config_id":     self.config_id,
            "n_runs":        self.n_runs,
            "verdict":       self.verdict,
            "distinct_hashes": len(set(self.hashes)),
            "threshold_n":   self.threshold_n,
            "drift_count":   len(self.drift_summary),
            "checked_at":    self.checked_at,
        }


# ── GroundingReportV1 ─────────────────────────────────────────────────────────

class GroundingReportV1(BaseModel):
    """
    Claim-level passport audit (Section 3 of manifesto).

    Every atomic claim in the output must carry a passport:
      OBSERVED    — supported by source text (with span pointer)
      INFERRED    — derived from observed claims (with inference rule)
      SPECULATIVE — not supported (flagged or removed)
      UNKNOWN     — unclassified (treated as SPECULATIVE, fail-closed)

    Hard rules:
      - unsupported_numeric_date_quote_count must be 0 for PASS.
      - ungrounded_rate = (speculative + unknown) / total must be < threshold.
      - verdict is a PURE FUNCTION of counts + threshold (no human override).

    Limitations (Section C of manifesto):
      - Atomic claim extraction is approximate (ClaimSegmenterV1 is rule-based).
      - Span pointers may be coarse if input text lacks stable byte indexing.
      - Passport assignment for INFERRED claims requires explicit rule labeling.
    """
    type:                               str              = "GROUNDING_REPORT_V1"
    atomic_claims_total:                int
    observed_count:                     int
    inferred_count:                     int
    speculative_count:                  int
    unknown_count:                      int
    unsupported_numeric_date_quote_count: int
    failures:                           List[AtomicClaim] = Field(default_factory=list)
    ungrounded_rate:                    float
    verdict:                            GroundingVerdict
    threshold_ungrounded_rate:          float            = GROUNDING_MAX_UNGROUNDED_RATE
    checked_at:                         str

    @model_validator(mode="after")
    def validate_grounding(self) -> "GroundingReportV1":
        # Counts must sum to total
        total_sum = (
            self.observed_count
            + self.inferred_count
            + self.speculative_count
            + self.unknown_count
        )
        if total_sum != self.atomic_claims_total:
            raise ValueError(
                f"observed + inferred + speculative + unknown = {total_sum} "
                f"!= atomic_claims_total = {self.atomic_claims_total}"
            )
        # Verify verdict is consistent with counts
        expected_rate = (
            (self.speculative_count + self.unknown_count) / self.atomic_claims_total
            if self.atomic_claims_total > 0
            else 0.0
        )
        expected_verdict: GroundingVerdict = (
            "PASS"
            if (
                self.unsupported_numeric_date_quote_count == 0
                and expected_rate < self.threshold_ungrounded_rate
            )
            else "FAIL"
        )
        if self.verdict != expected_verdict:
            raise ValueError(
                f"verdict {self.verdict!r} is inconsistent with counts: "
                f"expected {expected_verdict!r} "
                f"(ungrounded_rate={expected_rate:.4f}, "
                f"unsupported_ndq={self.unsupported_numeric_date_quote_count})"
            )
        return self

    def to_receipt_payload(self) -> Dict[str, Any]:
        return {
            "type":                               self.type,
            "atomic_claims_total":                self.atomic_claims_total,
            "observed_count":                     self.observed_count,
            "inferred_count":                     self.inferred_count,
            "speculative_count":                  self.speculative_count,
            "unknown_count":                      self.unknown_count,
            "unsupported_numeric_date_quote_count": self.unsupported_numeric_date_quote_count,
            "ungrounded_rate":                    self.ungrounded_rate,
            "verdict":                            self.verdict,
            "threshold_ungrounded_rate":          self.threshold_ungrounded_rate,
            "failure_count":                      len(self.failures),
            "checked_at":                         self.checked_at,
        }


# ── Factory helpers ───────────────────────────────────────────────────────────

def make_determinism_report(
    config_id: str,
    hashes: List[str],
    drift_summary: Optional[List[DriftSummary]] = None,
) -> DeterminismReportV1:
    """
    Factory: build DeterminismReportV1 from a list of per-run canonical hashes.

    Verdict is computed automatically:
      - UNCERTIFIABLE if config_id is empty or starts with "UNKNOWN"
      - DETERMINISM_CONFIRMED if all hashes identical and len >= DETERMINISM_MIN_RUNS
      - NONDETERMINISM_DETECTED otherwise

    Args:
        config_id:     Stable config identifier. Empty or "UNKNOWN*" → UNCERTIFIABLE.
        hashes:        sha256(canonicalize(output)) per run.
        drift_summary: Optional DriftSummary list (required for NONDETERMINISM).
    """
    now = datetime.now(timezone.utc).isoformat()
    n   = len(hashes)

    if not config_id or config_id.startswith("UNKNOWN"):
        return DeterminismReportV1(
            config_id     = config_id or "UNKNOWN",
            n_runs        = n,
            hashes        = hashes,
            verdict       = "UNCERTIFIABLE",
            drift_summary = [],
            checked_at    = now,
        )

    all_same = len(set(hashes)) == 1 if hashes else False

    if all_same and n >= DETERMINISM_MIN_RUNS:
        return DeterminismReportV1(
            config_id     = config_id,
            n_runs        = n,
            hashes        = hashes,
            verdict       = "DETERMINISM_CONFIRMED",
            drift_summary = [],
            checked_at    = now,
        )

    # Nondeterminism — drift_summary required
    effective_drift = drift_summary or [
        DriftSummary(
            field           = "output",
            changed_in_runs = [i for i, h in enumerate(hashes) if h != hashes[0]],
            token_diff_size = 0,
            meaning_impact  = "UNKNOWN" if not hashes else "SMALL",
        )
    ]
    return DeterminismReportV1(
        config_id     = config_id,
        n_runs        = n,
        hashes        = hashes,
        verdict       = "NONDETERMINISM_DETECTED",
        drift_summary = effective_drift,
        checked_at    = now,
    )


def make_grounding_report(
    claims:                    List[AtomicClaim],
    threshold_ungrounded_rate: float = GROUNDING_MAX_UNGROUNDED_RATE,
) -> GroundingReportV1:
    """
    Factory: build GroundingReportV1 from a list of AtomicClaims.

    Counts are derived automatically. Verdict is a pure function of counts.

    Args:
        claims:                   List of AtomicClaim (from ClaimSegmenterV1).
        threshold_ungrounded_rate: Max allowed (speculative + unknown) / total.
    """
    now = datetime.now(timezone.utc).isoformat()
    total = len(claims)

    observed_count    = sum(1 for c in claims if c.passport == "OBSERVED")
    inferred_count    = sum(1 for c in claims if c.passport == "INFERRED")
    speculative_count = sum(1 for c in claims if c.passport == "SPECULATIVE")
    unknown_count     = sum(1 for c in claims if c.passport == "UNKNOWN")
    flagged_ndq       = sum(1 for c in claims if c.flagged)
    failures          = [c for c in claims if c.flagged or c.passport in ("SPECULATIVE", "UNKNOWN")]

    rate = (speculative_count + unknown_count) / total if total > 0 else 0.0
    verdict: GroundingVerdict = (
        "PASS" if (flagged_ndq == 0 and rate < threshold_ungrounded_rate) else "FAIL"
    )

    return GroundingReportV1(
        atomic_claims_total                = total,
        observed_count                     = observed_count,
        inferred_count                     = inferred_count,
        speculative_count                  = speculative_count,
        unknown_count                      = unknown_count,
        unsupported_numeric_date_quote_count = flagged_ndq,
        failures                           = failures,
        ungrounded_rate                    = round(rate, 6),
        verdict                            = verdict,
        threshold_ungrounded_rate          = threshold_ungrounded_rate,
        checked_at                         = now,
    )
