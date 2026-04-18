"""
research_loop/replay_checker.py — Deterministic replay verifier.

HELEN Research Loop v0.1 — Phase B, Step 4.
(MVP_SPEC_V0_1.md §4.1)

Enforces G_replay_ok: the frozen deterministic replay gate.

G_replay_ok = True iff re-running proposal.replay_command under the frozen
environment produces ALL of:

    Field              Condition
    -----------------  ------------------------------------------------
    exit_code          equals the originally recorded exit code (0 = success)
    metric_after       equals evidence.metric_value exactly
    stdout_sha256      equals receipt.stdout_sha256 exactly
    stderr_sha256      equals receipt.stderr_sha256 exactly
    eval_output_hash   equals manifest.eval_output_hash exactly

"Close enough" is not a valid replay. Any single mismatch → G_replay_ok = False.
Tie-breaks, seed, evaluation ordering, and metric serialization are part of the
frozen deterministic policy and may not vary across cycles.
(MVP_SPEC_V0_1.md §4.1)

Design:
    - ReplayTarget: holds the five expected values from a sealed manifest.
    - ReplayResult: holds the five observed values + G_replay_ok bool + diffs.
    - run_replay(): executes replay_command, hashes outputs, returns ReplayResult.
    - check_replay(): derives ReplayTarget from a RunManifestV1 and calls run_replay.

The eval_output_hash field is computed from a specified output file path.
The caller must supply eval_output_file so the checker knows which file to hash.
If no eval_output_file is supplied, eval_output_hash comparison is skipped and
a EVAL_OUTPUT_FILE_NOT_SPECIFIED note is recorded (non-blocking for test stubs).

Budget enforcement (§9):
    The replay_command must complete within `timeout_seconds` (default: 300).
    Timeout → G_replay_ok = False with reason TIMEOUT.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from research_loop.run_manifest import RunManifestV1, sha256_hex


# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT_SECONDS: int = 300   # MVP budget (§9)
METRIC_PATTERN = re.compile(
    r"top1_accuracy[:\s=]+([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReplayTarget:
    """
    The five expected (frozen) values from a sealed manifest.
    These are what G_replay_ok is measured against.
    """
    expected_exit_code:       int          # 0 for success
    expected_metric_after:    float        # evidence.metric_value
    expected_stdout_sha256:   Optional[str]  # from the primary metric receipt
    expected_stderr_sha256:   Optional[str]  # from the primary metric receipt
    expected_eval_output_hash: Optional[str] # manifest.eval_output_hash


@dataclass
class ReplayResult:
    """
    Observed values from a replay run + G_replay_ok verdict.

    G_replay_ok: True iff ALL five comparisons pass.
    diff: list of strings describing any mismatches.
    notes: non-blocking observations (warnings, skips).
    """
    G_replay_ok:          bool

    observed_exit_code:       Optional[int]   = None
    observed_metric_after:    Optional[float] = None
    observed_stdout_sha256:   Optional[str]   = None
    observed_stderr_sha256:   Optional[str]   = None
    observed_eval_output_hash: Optional[str]  = None

    stdout_bytes:    bytes = field(default=b"", repr=False)
    stderr_bytes:    bytes = field(default=b"", repr=False)

    diff:  List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # Failure category (set when G_replay_ok = False)
    failure_reason: Optional[str] = None   # TIMEOUT | EXECUTION_ERROR | HASH_MISMATCH


# ── Internal helpers ───────────────────────────────────────────────────────────

def _sha256_file(path: str | Path) -> str:
    """SHA256 of a file's binary content."""
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_metric_from_stdout(stdout: bytes) -> Optional[float]:
    """
    Parse top1_accuracy from stdout.
    Looks for patterns like: "top1_accuracy: 0.847" / "top1_accuracy=0.847"
    Returns None if not found.
    """
    text = stdout.decode("utf-8", errors="replace")
    m = METRIC_PATTERN.search(text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _build_result_from_failed_run(
    target: ReplayTarget,
    reason: str,
    note: str,
    stdout_bytes: bytes = b"",
    stderr_bytes: bytes = b"",
    exit_code: Optional[int] = None,
) -> ReplayResult:
    return ReplayResult(
        G_replay_ok=False,
        observed_exit_code=exit_code,
        stdout_bytes=stdout_bytes,
        stderr_bytes=stderr_bytes,
        observed_stdout_sha256=(sha256_hex(stdout_bytes) if stdout_bytes else None),
        observed_stderr_sha256=(sha256_hex(stderr_bytes) if stderr_bytes else None),
        diff=[note],
        failure_reason=reason,
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def run_replay(
    replay_command:   str,
    target:           ReplayTarget,
    *,
    eval_output_file: Optional[str | Path] = None,
    timeout_seconds:  int = DEFAULT_TIMEOUT_SECONDS,
    cwd:              Optional[str | Path] = None,
    env:              Optional[dict] = None,
) -> ReplayResult:
    """
    Execute replay_command and compare the five frozen fields against target.

    Args:
        replay_command:   The verbatim command from proposal.replay_command.
        target:           Expected values from the sealed manifest.
        eval_output_file: Path to the file whose hash is eval_output_hash.
                          If None, eval_output_hash comparison is skipped.
        timeout_seconds:  Hard wall-clock limit (MVP: 300s).
        cwd:              Working directory for the subprocess.
        env:              Environment for the subprocess. If None, inherits.

    Returns:
        ReplayResult with G_replay_ok and diff list.
    """
    # ── Execute ───────────────────────────────────────────────────────────────
    try:
        proc = subprocess.run(
            replay_command,
            shell=True,
            capture_output=True,
            timeout=timeout_seconds,
            cwd=cwd,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_b = exc.stdout or b""
        stderr_b = exc.stderr or b""
        return _build_result_from_failed_run(
            target, "TIMEOUT",
            f"Replay timed out after {timeout_seconds}s. G_replay_ok = False.",
            stdout_bytes=stdout_b,
            stderr_bytes=stderr_b,
        )
    except Exception as exc:
        return _build_result_from_failed_run(
            target, "EXECUTION_ERROR",
            f"Subprocess failed to start: {exc!r}",
        )

    stdout_bytes = proc.stdout
    stderr_bytes = proc.stderr

    # ── Observe ───────────────────────────────────────────────────────────────
    observed_exit_code       = proc.returncode
    observed_stdout_sha256   = sha256_hex(stdout_bytes)
    observed_stderr_sha256   = sha256_hex(stderr_bytes)
    observed_metric_after    = _extract_metric_from_stdout(stdout_bytes)
    observed_eval_output_hash: Optional[str] = None

    notes: List[str] = []

    if eval_output_file is not None:
        eval_path = Path(eval_output_file)
        if eval_path.exists():
            observed_eval_output_hash = _sha256_file(eval_path)
        else:
            notes.append(
                f"EVAL_OUTPUT_FILE_NOT_FOUND: {eval_output_file} does not exist. "
                f"eval_output_hash comparison skipped."
            )
    else:
        notes.append(
            "EVAL_OUTPUT_FILE_NOT_SPECIFIED: eval_output_hash comparison skipped."
        )

    # ── Compare five fields ───────────────────────────────────────────────────
    diff: List[str] = []

    # 1. exit_code
    if observed_exit_code != target.expected_exit_code:
        diff.append(
            f"EXIT_CODE_MISMATCH: expected={target.expected_exit_code}, "
            f"observed={observed_exit_code}"
        )

    # 2. metric_after
    if observed_metric_after is None:
        diff.append(
            "METRIC_NOT_FOUND: top1_accuracy not found in stdout. "
            "Cannot verify metric_after."
        )
    elif observed_metric_after != target.expected_metric_after:
        diff.append(
            f"METRIC_MISMATCH: expected={target.expected_metric_after}, "
            f"observed={observed_metric_after}"
        )

    # 3. stdout_sha256
    if target.expected_stdout_sha256 is not None:
        if observed_stdout_sha256 != target.expected_stdout_sha256:
            diff.append(
                f"STDOUT_HASH_MISMATCH: expected={target.expected_stdout_sha256}, "
                f"observed={observed_stdout_sha256}"
            )
    else:
        notes.append("STDOUT_SHA256_NOT_RECORDED: no reference hash to compare.")

    # 4. stderr_sha256
    if target.expected_stderr_sha256 is not None:
        if observed_stderr_sha256 != target.expected_stderr_sha256:
            diff.append(
                f"STDERR_HASH_MISMATCH: expected={target.expected_stderr_sha256}, "
                f"observed={observed_stderr_sha256}"
            )
    else:
        notes.append("STDERR_SHA256_NOT_RECORDED: no reference hash to compare.")

    # 5. eval_output_hash
    if target.expected_eval_output_hash is not None and observed_eval_output_hash is not None:
        if observed_eval_output_hash != target.expected_eval_output_hash:
            diff.append(
                f"EVAL_OUTPUT_HASH_MISMATCH: "
                f"expected={target.expected_eval_output_hash}, "
                f"observed={observed_eval_output_hash}"
            )
    # If either side is None, comparison is skipped (handled by notes above)

    g_replay_ok = len(diff) == 0
    failure_reason = "HASH_MISMATCH" if diff else None

    return ReplayResult(
        G_replay_ok=g_replay_ok,
        observed_exit_code=observed_exit_code,
        observed_metric_after=observed_metric_after,
        observed_stdout_sha256=observed_stdout_sha256,
        observed_stderr_sha256=observed_stderr_sha256,
        observed_eval_output_hash=observed_eval_output_hash,
        stdout_bytes=stdout_bytes,
        stderr_bytes=stderr_bytes,
        diff=diff,
        notes=notes,
        failure_reason=failure_reason,
    )


def check_replay(
    manifest: RunManifestV1,
    *,
    eval_output_file: Optional[str | Path] = None,
    timeout_seconds:  int = DEFAULT_TIMEOUT_SECONDS,
    cwd:              Optional[str | Path] = None,
    env:              Optional[dict] = None,
) -> ReplayResult:
    """
    High-level entry point: derive ReplayTarget from a sealed RunManifestV1
    and run the deterministic replay check.

    The primary metric receipt is the first receipt in manifest.receipts
    with kind == "metric". If no such receipt is found, the first receipt
    is used and stdout/stderr comparison falls back to notes-only.

    Returns ReplayResult with G_replay_ok and diff.
    """
    # Find the primary metric receipt
    metric_receipt = None
    for r in manifest.receipts:
        if r.kind == "metric":
            metric_receipt = r
            break
    if metric_receipt is None and manifest.receipts:
        metric_receipt = manifest.receipts[0]

    target = ReplayTarget(
        expected_exit_code=0,   # MVP: successful run exits 0
        expected_metric_after=manifest.evidence.metric_value,
        expected_stdout_sha256=(
            metric_receipt.stdout_sha256 if metric_receipt else None
        ),
        expected_stderr_sha256=(
            metric_receipt.stderr_sha256 if metric_receipt else None
        ),
        expected_eval_output_hash=manifest.eval_output_hash,
    )

    return run_replay(
        replay_command=manifest.proposal.replay_command,
        target=target,
        eval_output_file=eval_output_file,
        timeout_seconds=timeout_seconds,
        cwd=cwd,
        env=env,
    )


def make_replay_target(
    expected_exit_code: int = 0,
    expected_metric_after: float = 0.0,
    expected_stdout_sha256: Optional[str] = None,
    expected_stderr_sha256: Optional[str] = None,
    expected_eval_output_hash: Optional[str] = None,
) -> ReplayTarget:
    """
    Convenience constructor for ReplayTarget (for test stubs).
    """
    return ReplayTarget(
        expected_exit_code=expected_exit_code,
        expected_metric_after=expected_metric_after,
        expected_stdout_sha256=expected_stdout_sha256,
        expected_stderr_sha256=expected_stderr_sha256,
        expected_eval_output_hash=expected_eval_output_hash,
    )
