"""
research_loop/run_manifest.py — RUN_MANIFEST_V1

HELEN Research Loop v0.1 — Frozen Manifest Schema.
(MVP_SPEC_V0_1.md §3.7)

The sovereign artifact of every research cycle.
Immutable once built. Hash-chained to its parent.
Authority law: only MAYOR/reducer may emit a manifest.
Memory law: only SHIP manifests feed future HER context.

Usage:
    manifest = build_run_manifest(
        manifest_id="MAN_001",
        ts_utc="2026-03-10T12:00:00Z",
        mission=mission,
        proposal=proposal,
        receipts=[r1, r2],
        evidence=evidence,
        issues=issues,
        gates=gates,
        parent_manifest_hash="0" * 64,
        config_hash="...",
        environment_hash="...",
        model_digest="...",
    )
    assert verify_manifest(manifest)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional

# ── Schema version pin ────────────────────────────────────────────────────────

MANIFEST_VERSION: str = "RUN_MANIFEST_V1"
GENESIS_PARENT_HASH: str = "0" * 64

Verdict = Literal["SHIP", "NO_SHIP", "QUARANTINE"]


# ── Canonical serialization (TCB boundary) ───────────────────────────────────

def canonical_json(obj: Any) -> bytes:
    """
    Deterministic JSON serialization.
    Invariant I2: same object always produces same bytes.
    No wall-clock entropy. No random keys. UTF-8. Sorted keys.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MissionV1:
    """Frozen mission descriptor. Domain and metric are constants for MVP."""
    mission_id:   str
    domain:       str   # "retrieval_ranking" for MVP
    objective:    str
    metric_name:  str   # "top1_accuracy" for MVP
    maximize:     bool = True


@dataclass(frozen=True)
class ProposalV1:
    """
    Non-sovereign proposer output.
    mutable_files must be exactly ["ranker.py"] for MVP.
    replay_command is the verbatim string used for replay verification.
    """
    proposal_id:    str
    proposer:       str          # always "HER"
    summary:        str          # ≤ 200 chars
    hypothesis:     str          # ≤ 500 chars
    mutable_files:  List[str]    # ["ranker.py"]
    replay_command: str


@dataclass(frozen=True)
class ExecutionReceiptV1:
    """
    Witnessed execution artifact.
    stdout_sha256 and stderr_sha256 are SHA256 of captured output.
    artifact_refs: ["metric:top1_accuracy=0.847", "commit:abc123", ...]
    """
    receipt_id:    str
    kind:          Literal["command", "metric", "test"]
    command:       str
    stdout_sha256: Optional[str] = None
    stderr_sha256: Optional[str] = None
    artifact_refs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceBundleV1:
    """
    Aggregated witness for a single cycle's execution.
    All receipt_ids must reference receipts in the manifest.
    dataset_hash: SHA256 of the frozen evaluation dataset file.
    """
    evidence_id:  str
    dataset_hash: str   # SHA256 of frozen_eval.jsonl
    metric_name:  str   # "top1_accuracy"
    metric_value: float
    receipt_ids:  List[str]
    notes:        List[str] = field(default_factory=list)


@dataclass(frozen=True)
class IssueItemV1:
    issue_id:  str
    severity:  Literal["low", "medium", "high", "blocker"]
    code:      str
    message:   str


@dataclass(frozen=True)
class IssueListV1:
    issue_list_id: str
    issues:        List[IssueItemV1]

    def has_blocker(self) -> bool:
        return any(i.severity == "blocker" for i in self.issues)


@dataclass(frozen=True)
class GateVectorV1:
    """
    Five gates computed by the kernel before verdict.
    All must be True for SHIP.
    G_kernel_integrity_ok = False → QUARANTINE (highest priority).
    """
    G_receipts_present:    bool
    G_replay_ok:           bool
    G_metric_improved:     bool
    G_no_blocking_issue:   bool
    G_kernel_integrity_ok: bool


@dataclass(frozen=True)
class VerdictV1:
    """
    Reducer output.
    SHIP: admitted, mutates state.
    NO_SHIP: rejected, no state mutation.
    QUARANTINE: integrity failure, audit-only.

    law_surface_version + law_surface_hash: explicitly bind this verdict to
    the legal regime under which it was computed. Any verdict comparison across
    law regimes requires a migration receipt.
    """
    verdict:              Verdict
    blocking_reason_codes: List[str]
    law_surface_version:  str = "LAW_SURFACE_V1"
    law_surface_hash:     str = "0" * 64   # sentinel; set to real hash in production


@dataclass(frozen=True)
class RunManifestV1:
    """
    The sovereign artifact. Immutable once built.
    manifest_hash = SHA256(canonical_json(all_fields_except_manifest_hash)).
    parent_manifest_hash links this to the previous admitted manifest.

    eval_output_hash: SHA256 of the evaluation output file produced by
    replay_command. Required so G_replay_ok can compare this hash exactly
    on re-run (§4.1 frozen deterministic replay definition).
    """
    manifest_version:    str    # "RUN_MANIFEST_V1"
    manifest_id:         str
    ts_utc:              str    # ISO 8601 UTC (observational only, not used in hash)

    mission:             MissionV1
    proposal:            ProposalV1
    receipts:            List[ExecutionReceiptV1]
    evidence:            EvidenceBundleV1
    issues:              IssueListV1
    gates:               GateVectorV1
    verdict:             VerdictV1

    parent_manifest_hash: str   # SHA256 of parent | GENESIS_PARENT_HASH
    config_hash:          str   # SHA256 of frozen config
    environment_hash:     str   # SHA256 of frozen environment manifest
    model_digest:         str   # SHA256 of model weights / version pin
    eval_output_hash:     str   # SHA256 of evaluation output file (replay gate §4.1)
    law_surface_version:  str   # e.g. "LAW_SURFACE_V1" — legal regime identifier
    law_surface_hash:     str   # SHA256 of law_surface.yaml — explicit constitutional pin

    manifest_hash:        str   # SHA256 of all above (canonical)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _manifest_payload(
    manifest_id:          str,
    ts_utc:               str,
    mission:              MissionV1,
    proposal:             ProposalV1,
    receipts:             List[ExecutionReceiptV1],
    evidence:             EvidenceBundleV1,
    issues:               IssueListV1,
    gates:                GateVectorV1,
    verdict:              VerdictV1,
    parent_manifest_hash: str,
    config_hash:          str,
    environment_hash:     str,
    model_digest:         str,
    eval_output_hash:     str,
    law_surface_version:  str,
    law_surface_hash:     str,
) -> Dict[str, Any]:
    """
    Deterministic payload dict (excluding manifest_hash).
    All hashes are computed from canonical_json(this dict).
    eval_output_hash is a load-bearing field: required for G_replay_ok (§4.1).
    law_surface_version + law_surface_hash: bind manifest to its legal regime.
    Any verdict comparison across law regimes requires a migration receipt.
    """
    return {
        "manifest_version":    MANIFEST_VERSION,
        "manifest_id":         manifest_id,
        "ts_utc":              ts_utc,
        "mission":             asdict(mission),
        "proposal":            asdict(proposal),
        "receipts":            [asdict(r) for r in receipts],
        "evidence":            asdict(evidence),
        "issues": {
            "issue_list_id": issues.issue_list_id,
            "issues":        [asdict(i) for i in issues.issues],
        },
        "gates":               asdict(gates),
        "verdict":             asdict(verdict),
        "parent_manifest_hash": parent_manifest_hash,
        "config_hash":         config_hash,
        "environment_hash":    environment_hash,
        "model_digest":        model_digest,
        "eval_output_hash":    eval_output_hash,
        "law_surface_version": law_surface_version,
        "law_surface_hash":    law_surface_hash,
    }


def _compute_manifest_hash(payload: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(payload))


# ── Validation ────────────────────────────────────────────────────────────────

ALLOWED_REASON_CODES = frozenset({
    "MISSING_RECEIPTS",
    "REPLAY_FAILED",
    "METRIC_NOT_IMPROVED",
    "BLOCKING_ISSUE",
    "KERNEL_INTEGRITY_FAILED",
})


class ManifestValidationError(ValueError):
    """Raised when a manifest violates a structural invariant."""


def validate_manifest_inputs(
    mission:  MissionV1,
    proposal: ProposalV1,
    receipts: List[ExecutionReceiptV1],
    evidence: EvidenceBundleV1,
    issues:   IssueListV1,
    gates:    GateVectorV1,
    verdict:  VerdictV1,
) -> None:
    """
    Validate structural invariants before building.
    Raises ManifestValidationError on any violation.
    """
    if not mission.metric_name:
        raise ManifestValidationError("Mission metric_name must be non-empty.")

    if not proposal.mutable_files:
        raise ManifestValidationError("Proposal must declare at least one mutable file.")

    if not proposal.replay_command:
        raise ManifestValidationError("Proposal must declare a replay_command.")

    if not proposal.proposer:
        raise ManifestValidationError("Proposal proposer must be non-empty.")

    if not receipts:
        raise ManifestValidationError("At least one execution receipt is required.")

    receipt_ids = {r.receipt_id for r in receipts}
    missing = [rid for rid in evidence.receipt_ids if rid not in receipt_ids]
    if missing:
        raise ManifestValidationError(
            f"Evidence references missing receipt(s): {missing}"
        )

    for code in verdict.blocking_reason_codes:
        if code not in ALLOWED_REASON_CODES:
            raise ManifestValidationError(f"Unknown blocking reason code: {code!r}")

    if verdict.verdict == "SHIP" and verdict.blocking_reason_codes:
        raise ManifestValidationError(
            "SHIP verdict must carry zero blocking reason codes."
        )

    if verdict.verdict == "NO_SHIP" and not verdict.blocking_reason_codes:
        raise ManifestValidationError(
            "NO_SHIP verdict must carry at least one blocking reason code."
        )

    # Gate/issue consistency
    if issues.has_blocker() and gates.G_no_blocking_issue:
        raise ManifestValidationError(
            "Gate mismatch: blocker issues present but G_no_blocking_issue=True."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def build_run_manifest(
    *,
    manifest_id:          str,
    ts_utc:               str,
    mission:              MissionV1,
    proposal:             ProposalV1,
    receipts:             List[ExecutionReceiptV1],
    evidence:             EvidenceBundleV1,
    issues:               IssueListV1,
    gates:                GateVectorV1,
    parent_manifest_hash: str,
    config_hash:          str,
    environment_hash:     str,
    model_digest:         str,
    eval_output_hash:     str,
    law_surface_version:  str,
    law_surface_hash:     str,
    verdict:              Optional[VerdictV1] = None,
) -> RunManifestV1:
    """
    Build an immutable RunManifestV1.

    eval_output_hash: SHA256 of the evaluation output file produced by
    the replay_command. Required by §4.1 (G_replay_ok frozen deterministic
    replay definition). Must be supplied by the executor/harness.

    If verdict is None, it is computed deterministically from gates
    (use this path for normal cycle operation).
    If verdict is provided, it is validated for consistency (use this
    path for replay / test scenarios).

    Returns a frozen RunManifestV1 with manifest_hash sealed.
    Raises ManifestValidationError on any invariant violation.
    """
    # Import here to avoid circular import; verdict_reducer is a thin dep
    from research_loop.verdict_reducer import compute_verdict
    if verdict is None:
        verdict = compute_verdict(gates)

    validate_manifest_inputs(
        mission, proposal, receipts, evidence, issues, gates, verdict
    )

    payload = _manifest_payload(
        manifest_id=manifest_id,
        ts_utc=ts_utc,
        mission=mission,
        proposal=proposal,
        receipts=receipts,
        evidence=evidence,
        issues=issues,
        gates=gates,
        verdict=verdict,
        parent_manifest_hash=parent_manifest_hash,
        config_hash=config_hash,
        environment_hash=environment_hash,
        model_digest=model_digest,
        eval_output_hash=eval_output_hash,
        law_surface_version=law_surface_version,
        law_surface_hash=law_surface_hash,
    )
    manifest_hash = _compute_manifest_hash(payload)

    return RunManifestV1(
        manifest_version=MANIFEST_VERSION,
        manifest_id=manifest_id,
        ts_utc=ts_utc,
        mission=mission,
        proposal=proposal,
        receipts=receipts,
        evidence=evidence,
        issues=issues,
        gates=gates,
        verdict=verdict,
        parent_manifest_hash=parent_manifest_hash,
        config_hash=config_hash,
        environment_hash=environment_hash,
        model_digest=model_digest,
        eval_output_hash=eval_output_hash,
        law_surface_version=law_surface_version,
        law_surface_hash=law_surface_hash,
        manifest_hash=manifest_hash,
    )


def verify_manifest(manifest: RunManifestV1) -> bool:
    """
    Deterministic integrity check.
    Returns True iff manifest_hash matches canonical recomputation.
    This is the G_kernel_integrity_ok gate.
    """
    payload = _manifest_payload(
        manifest_id=manifest.manifest_id,
        ts_utc=manifest.ts_utc,
        mission=manifest.mission,
        proposal=manifest.proposal,
        receipts=manifest.receipts,
        evidence=manifest.evidence,
        issues=manifest.issues,
        gates=manifest.gates,
        verdict=manifest.verdict,
        parent_manifest_hash=manifest.parent_manifest_hash,
        config_hash=manifest.config_hash,
        environment_hash=manifest.environment_hash,
        model_digest=manifest.model_digest,
        eval_output_hash=manifest.eval_output_hash,
        law_surface_version=manifest.law_surface_version,
        law_surface_hash=manifest.law_surface_hash,
    )
    expected = _compute_manifest_hash(payload)
    return expected == manifest.manifest_hash


def manifest_to_dict(manifest: RunManifestV1) -> Dict[str, Any]:
    """Full dict representation (for ledger serialization)."""
    d = asdict(manifest)
    return d
