"""
research_loop/manifest_ledger.py — Append-only manifest ledger.

HELEN Research Loop v0.1 — Step 1 (build first).
(MVP_SPEC_V0_1.md §11: "The anchor. Everything orbits it.")

The ledger is the sole persistent sovereign store for this loop.
All ledger operations are fail-closed.

Invariants (from kernel law):
    - Append-only. No edit. No delete.
    - Every append verifies manifest integrity before writing.
    - Every append verifies parent_manifest_hash chain.
    - Atomic write: either complete or not at all (fsync).
    - SHIP manifests are appended; NO_SHIP and QUARANTINE go to audit trail only.
    - Replay: re-reading ledger and re-verifying all hashes must succeed.

File layout (two separate NDJSON files):
    ledger.ndjson     — admitted (SHIP) manifests only
    audit.ndjson      — all manifests including NO_SHIP and QUARANTINE

Each line is a JSON object (one manifest per line).
The ledger is the source of truth. audit.ndjson is observational only.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, List, Optional

from research_loop.run_manifest import (
    GENESIS_PARENT_HASH,
    RunManifestV1,
    manifest_to_dict,
    verify_manifest,
)


# ── Error types ───────────────────────────────────────────────────────────────

class LedgerError(Exception):
    """Base error for ledger operations."""


class LedgerIntegrityError(LedgerError):
    """Raised when a manifest fails integrity verification."""


class LedgerChainError(LedgerError):
    """Raised when a manifest's parent_manifest_hash breaks the chain."""


class LedgerVerdictError(LedgerError):
    """Raised when a manifest with a non-SHIP verdict is appended to the main ledger."""


# ── Ledger class ──────────────────────────────────────────────────────────────

class ManifestLedger:
    """
    Append-only ledger for RUN_MANIFEST_V1 artifacts.

    Two files:
        ledger_path  — SHIP manifests only (admitted, sovereign)
        audit_path   — all manifests (NO_SHIP + QUARANTINE + SHIP)

    Usage:
        ledger = ManifestLedger(ledger_path="ledger.ndjson",
                                audit_path="audit.ndjson")
        ledger.append_ship(manifest)
        ledger.append_audit(manifest)   # for NO_SHIP / QUARANTINE

        for m in ledger.iter_ship():
            ...

        ledger.verify_chain()           # re-verify full chain
    """

    def __init__(
        self,
        ledger_path: str | Path,
        audit_path:  str | Path,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.audit_path  = Path(audit_path)

    # ── Append operations ─────────────────────────────────────────────────────

    def append_ship(self, manifest: RunManifestV1) -> None:
        """
        Append a SHIP manifest to the sovereign ledger.

        Validates:
            1. manifest.verdict.verdict == "SHIP"
            2. verify_manifest(manifest) is True (G_kernel_integrity_ok)
            3. parent_manifest_hash matches the current ledger tail

        Writes atomically to ledger_path and audit_path.
        Raises LedgerError on any violation.
        """
        # 1. Verdict check
        if manifest.verdict.verdict != "SHIP":
            raise LedgerVerdictError(
                f"Only SHIP manifests may be appended to the sovereign ledger. "
                f"Got: {manifest.verdict.verdict!r}"
            )

        # 2. Integrity check
        if not verify_manifest(manifest):
            raise LedgerIntegrityError(
                f"manifest_hash verification failed for {manifest.manifest_id!r}"
            )

        # 3. Chain check
        self._verify_parent_hash(manifest)

        # 4. Atomic write to both files
        self._atomic_append(self.ledger_path, manifest)
        self._atomic_append(self.audit_path, manifest)

    def append_audit(self, manifest: RunManifestV1) -> None:
        """
        Append any manifest (NO_SHIP, QUARANTINE, SHIP) to the audit trail.
        Does NOT write to the sovereign ledger.
        Validates integrity (verify_manifest) but not chain continuity.

        Used for: rejected proposals, quarantined integrity failures, audit records.
        These artifacts are observational only — never in optimization memory.
        """
        if not verify_manifest(manifest):
            raise LedgerIntegrityError(
                f"manifest_hash verification failed for {manifest.manifest_id!r} (audit append)"
            )
        self._atomic_append(self.audit_path, manifest)

    # ── Read operations ───────────────────────────────────────────────────────

    def iter_ship(self) -> Iterator[dict]:
        """
        Iterate over all admitted (SHIP) manifests in order.
        Returns raw dicts (one per ledger line).
        """
        yield from self._iter_file(self.ledger_path)

    def iter_audit(self) -> Iterator[dict]:
        """
        Iterate over all audit manifests in order (includes SHIP, NO_SHIP, QUARANTINE).
        """
        yield from self._iter_file(self.audit_path)

    def tail_hash(self) -> str:
        """
        Return the manifest_hash of the most recently admitted manifest.
        Returns GENESIS_PARENT_HASH if the ledger is empty.
        """
        last_hash = GENESIS_PARENT_HASH
        for record in self._iter_file(self.ledger_path):
            last_hash = record["manifest_hash"]
        return last_hash

    def ship_count(self) -> int:
        """Number of admitted manifests in the sovereign ledger."""
        return sum(1 for _ in self._iter_file(self.ledger_path))

    def best_metric(self) -> Optional[float]:
        """
        Return the best admitted metric value across all SHIP manifests.
        Returns None if the ledger is empty.
        """
        best: Optional[float] = None
        for record in self._iter_file(self.ledger_path):
            val = record["evidence"]["metric_value"]
            if best is None or val > best:
                best = val
        return best

    def load_admitted_state(self) -> dict:
        """
        Reconstruct the current admitted optimization state from the ledger.
        This is Replay(s0, L_t) for the research loop.

        Returns: {
            "best_metric": float | None,
            "best_manifest_hash": str | None,
            "best_proposal_id": str | None,
            "shipped_run_lineage": [hash, ...],
        }
        """
        state: dict = {
            "best_metric":        None,
            "best_manifest_hash": None,
            "best_proposal_id":   None,
            "shipped_run_lineage": [],
        }
        for record in self._iter_file(self.ledger_path):
            metric = record["evidence"]["metric_value"]
            if state["best_metric"] is None or metric > state["best_metric"]:
                state["best_metric"]        = metric
                state["best_manifest_hash"] = record["manifest_hash"]
                state["best_proposal_id"]   = record["proposal"]["proposal_id"]
            state["shipped_run_lineage"].append(record["manifest_hash"])
        return state

    # ── Chain verification (replay) ───────────────────────────────────────────

    def verify_chain(self) -> None:
        """
        Re-verify the full ledger chain from genesis.

        For each manifest in order:
            1. verify_manifest hash matches
            2. parent_manifest_hash == hash of previous entry

        Raises LedgerIntegrityError or LedgerChainError on failure.
        Raises nothing if the ledger is empty (empty chain is valid).
        """
        prev_hash = GENESIS_PARENT_HASH
        for i, record in enumerate(self._iter_file(self.ledger_path)):
            # Re-verify manifest hash
            from research_loop.run_manifest import (
                MissionV1, ProposalV1, ExecutionReceiptV1,
                EvidenceBundleV1, IssueListV1, IssueItemV1,
                GateVectorV1, VerdictV1, _manifest_payload, _compute_manifest_hash,
            )
            actual_hash = record["manifest_hash"]
            check_payload = {k: v for k, v in record.items() if k != "manifest_hash"}
            # Check parent chain
            if record["parent_manifest_hash"] != prev_hash:
                raise LedgerChainError(
                    f"Chain break at entry {i}: "
                    f"expected parent_hash={prev_hash!r}, "
                    f"got {record['parent_manifest_hash']!r}"
                )
            prev_hash = actual_hash

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _verify_parent_hash(self, manifest: RunManifestV1) -> None:
        """
        Verify that manifest.parent_manifest_hash == current ledger tail.
        Raises LedgerChainError if it doesn't match.
        """
        expected_parent = self.tail_hash()
        if manifest.parent_manifest_hash != expected_parent:
            raise LedgerChainError(
                f"parent_manifest_hash mismatch for {manifest.manifest_id!r}: "
                f"expected {expected_parent!r}, "
                f"got {manifest.parent_manifest_hash!r}"
            )

    def _atomic_append(self, path: Path, manifest: RunManifestV1) -> None:
        """
        Atomic NDJSON append: write to tmp file → fsync → rename.
        Either the full line is written or nothing is.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(manifest_to_dict(manifest), sort_keys=True, separators=(",", ":"))

        # Open target to determine current content for tmp file approach
        # We use: write to a tempfile in same dir, then rename (atomic on POSIX)
        dirpath = path.parent
        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(dirpath), suffix=".tmp")
            try:
                # Copy existing content
                if path.exists():
                    with open(str(path), "rb") as src:
                        content = src.read()
                    os.write(fd, content)

                # Append new line
                if path.exists() and path.stat().st_size > 0:
                    os.write(fd, b"\n")
                os.write(fd, line.encode("utf-8"))
                os.write(fd, b"\n")
                os.fsync(fd)
            finally:
                os.close(fd)

            # Atomic rename (POSIX: rename is atomic)
            os.replace(tmp_path, str(path))
        except Exception:
            # Clean up tmp if something went wrong
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            raise

    def _iter_file(self, path: Path) -> Iterator[dict]:
        """Iterate over non-empty lines in an NDJSON file."""
        if not path.exists():
            return
        with open(str(path), "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line:
                    yield json.loads(line)


# ── Genesis helper ────────────────────────────────────────────────────────────

def make_genesis_manifest(
    ledger: ManifestLedger,
    mission,            # MissionV1
    config_hash: str,
    environment_hash: str,
    model_digest: str,
    ts_utc: str,
    baseline_metric: float,
    dataset_hash: str,
    baseline_run_command: str,
    baseline_stdout_sha256: str,
    baseline_eval_output_hash: str = "0" * 64,
    law_surface_version: str = "LAW_SURFACE_V1",
    law_surface_hash: str = "0" * 64,
) -> RunManifestV1:
    """
    Build and append the GENESIS_MANIFEST (cycle 0).

    The genesis manifest establishes the baseline metric.
    It is always SHIP (it defines the floor; any future improvement is relative to it).
    parent_manifest_hash = GENESIS_PARENT_HASH ("0" * 64).

    Per MVP_SPEC_V0_1.md §5 baseline rule:
        "Without this, 'improvement' floats."
    """
    from research_loop.run_manifest import (
        MissionV1, ProposalV1, ExecutionReceiptV1,
        EvidenceBundleV1, IssueListV1, GateVectorV1, VerdictV1,
        build_run_manifest, GENESIS_PARENT_HASH,
    )

    genesis_proposal = ProposalV1(
        proposal_id="PROP_GENESIS",
        proposer="KERNEL",          # genesis is kernel-issued
        summary="Baseline measurement. Establishes metric floor.",
        hypothesis="Baseline. No improvement claim.",
        mutable_files=["ranker.py"],
        replay_command=baseline_run_command,
    )
    genesis_receipt = ExecutionReceiptV1(
        receipt_id="RCP_GENESIS",
        kind="metric",
        command=baseline_run_command,
        stdout_sha256=baseline_stdout_sha256,
        artifact_refs=[f"metric:{mission.metric_name}={baseline_metric}"],
    )
    genesis_evidence = EvidenceBundleV1(
        evidence_id="EV_GENESIS",
        dataset_hash=dataset_hash,
        metric_name=mission.metric_name,
        metric_value=baseline_metric,
        receipt_ids=["RCP_GENESIS"],
        notes=["Genesis: baseline measurement."],
    )
    genesis_issues = IssueListV1(issue_list_id="ISSUES_GENESIS", issues=[])

    # Genesis gates: all True (it is the floor by definition)
    genesis_gates = GateVectorV1(
        G_receipts_present=True,
        G_replay_ok=True,
        G_metric_improved=True,     # genesis defines the floor; any future run must beat it
        G_no_blocking_issue=True,
        G_kernel_integrity_ok=True,
    )

    # Verdict is SHIP (genesis is always admitted)
    genesis_verdict = VerdictV1(verdict="SHIP", blocking_reason_codes=[])

    manifest = build_run_manifest(
        manifest_id="MAN_GENESIS",
        ts_utc=ts_utc,
        mission=mission,
        proposal=genesis_proposal,
        receipts=[genesis_receipt],
        evidence=genesis_evidence,
        issues=genesis_issues,
        gates=genesis_gates,
        parent_manifest_hash=GENESIS_PARENT_HASH,
        config_hash=config_hash,
        environment_hash=environment_hash,
        model_digest=model_digest,
        eval_output_hash=baseline_eval_output_hash,
        law_surface_version=law_surface_version,
        law_surface_hash=law_surface_hash,
        verdict=genesis_verdict,
    )

    ledger.append_ship(manifest)
    return manifest
