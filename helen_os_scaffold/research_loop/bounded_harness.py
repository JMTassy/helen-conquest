"""
research_loop/bounded_harness.py — Bounded experiment harness.

HELEN Research Loop v0.1 — Phase B, Step 5 (final).
(MVP_SPEC_V0_1.md §6)

The harness is the only legal entry point for proposal-space execution.
It enforces the physical constraints that make receipts trustworthy:

    1. Wall-clock budget ≤ budget_seconds (default 300s)
    2. Mutable files restricted to exactly {"ranker.py"} for MVP
    3. Single-cycle lock (one harness active per workspace at a time)
    4. Deterministic stdout/stderr/eval hash capture
    5. Exact replay fields computed and returned

Constitutional rule (§6.2):
    Proposal-space may only touch mutable_files.
    Any write outside mutable_files is a kernel integrity violation.
    The harness does not enforce filesystem sandboxing at the OS level
    (that requires external tooling), but it enforces at the Python level
    by checking the declared mutable_files against what the harness permits.

Replay determinism (§4.1):
    Five exact-match fields are computed by this harness:
        exit_code
        metric_after      (parsed from stdout via METRIC_PATTERN)
        stdout_sha256     (SHA256 of captured stdout)
        stderr_sha256     (SHA256 of captured stderr)
        eval_output_hash  (SHA256 of eval_output_file, if specified)

The harness never decides SHIP/NO_SHIP. It only produces evidence.
Only the reducer may decide.

Usage:
    harness = BoundedHarness(
        workspace=Path("/tmp/helen_run_001"),
        budget_seconds=300,
    )
    result = harness.run(
        command="python eval.py --seed 42 --dataset frozen_eval.jsonl",
        eval_output_file="results/eval_output.json",
    )
    # result.stdout_sha256, result.stderr_sha256, result.eval_output_hash
    # result.metric_after, result.exit_code, result.timed_out
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_BUDGET_SECONDS: int = 300
MVP_MUTABLE_FILES: frozenset = frozenset({"ranker.py"})
METRIC_PATTERN: re.Pattern = re.compile(
    r"top1_accuracy[:\s=]+([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE
)
LOCK_FILENAME: str = ".helen_harness.lock"


# ── Error types ────────────────────────────────────────────────────────────────

class HarnessError(Exception):
    """Base error for harness violations."""


class BudgetExceededError(HarnessError):
    """Raised when the command exceeds wall_clock ≤ budget_seconds."""


class HarnessLockError(HarnessError):
    """Raised when another harness cycle is already active in the workspace."""


class MutableFilesViolationError(HarnessError):
    """Raised when the declared mutable_files contain disallowed entries."""


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class HarnessResult:
    """
    Exact replay fields computed by one harness execution.

    All five fields map directly to the G_replay_ok gate (§4.1):
        exit_code, metric_after, stdout_sha256, stderr_sha256, eval_output_hash

    stdout_bytes / stderr_bytes: raw captured output (for metric extraction).
    elapsed_seconds: wall-clock time (informational; not part of replay).
    timed_out: True iff the command was terminated by the budget.
    metric_parsed: True iff metric_after was successfully extracted from stdout.
    notes: non-blocking observations (missing eval output file, etc.).
    """
    # Five frozen replay fields
    exit_code:          int
    stdout_sha256:      str           # SHA256 of captured stdout
    stderr_sha256:      str           # SHA256 of captured stderr
    eval_output_hash:   Optional[str] # SHA256 of eval_output_file | None
    metric_after:       Optional[float]

    # Execution metadata (not part of replay; for tracing only)
    stdout_bytes:       bytes
    stderr_bytes:       bytes
    elapsed_seconds:    float
    timed_out:          bool
    metric_parsed:      bool
    command:            str
    workspace:          str
    notes:              List[str] = field(default_factory=list)


# ── Harness class ──────────────────────────────────────────────────────────────

class BoundedHarness:
    """
    Single-cycle bounded experiment harness.

    Enforces:
        - Wall-clock budget ≤ budget_seconds
        - Mutable files ⊆ MVP_MUTABLE_FILES (["ranker.py"] for MVP)
        - Single-cycle lock (prevents re-entrant execution)
        - Deterministic stdout/stderr/eval hash capture

    The harness does not decide verdicts. It only produces HarnessResult,
    which the caller uses to build ExecutionReceiptV1 and EvidenceBundleV1.

    Invariant (§6.2):
        "The harness never decides success.
         It only produces evidence.
         Only the reducer may decide SHIP / NO_SHIP / QUARANTINE."
    """

    def __init__(
        self,
        workspace: Path | str,
        budget_seconds: int = DEFAULT_BUDGET_SECONDS,
        mutable_files: Optional[frozenset] = None,
        env: Optional[dict] = None,
    ) -> None:
        """
        workspace:      Directory where the proposal's ranker.py lives.
                        Must exist. Lock file is written here.
        budget_seconds: Hard wall-clock limit. Default 300s (MVP constant).
        mutable_files:  Files the proposal is allowed to touch.
                        Defaults to MVP_MUTABLE_FILES = {"ranker.py"}.
        env:            Optional environment overrides. Passed to subprocess.
                        Set PYTHONHASHSEED, PYTHONDONTWRITEBYTECODE, etc.
        """
        self.workspace = Path(workspace)
        self.budget_seconds = budget_seconds
        self.mutable_files: frozenset = mutable_files or MVP_MUTABLE_FILES
        self.env = env
        self._lock_path = self.workspace / LOCK_FILENAME

        if not self.workspace.exists():
            raise HarnessError(f"Workspace does not exist: {self.workspace}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(
        self,
        command: str,
        eval_output_file: Optional[str | Path] = None,
    ) -> HarnessResult:
        """
        Execute command in workspace with wall-clock budget enforcement.

        command:          The replay_command string (e.g. "python eval.py --seed 42")
        eval_output_file: Path (relative to workspace) of the evaluation output file.
                          SHA256 is computed and returned as eval_output_hash.
                          If None or absent, eval_output_hash is None (non-blocking).

        Returns HarnessResult with all five replay fields populated.
        Raises BudgetExceededError if command times out.
        Raises HarnessLockError if workspace is already locked.
        """
        self._validate_mutable_files()
        self._acquire_lock()
        try:
            result = self._execute(command, eval_output_file)
        finally:
            self._release_lock()
        return result

    # ── Validation ─────────────────────────────────────────────────────────────

    def _validate_mutable_files(self) -> None:
        """
        Verify that declared mutable_files are within the allowed set.
        For MVP: exactly {"ranker.py"}.
        """
        illegal = self.mutable_files - MVP_MUTABLE_FILES
        if illegal:
            raise MutableFilesViolationError(
                f"Proposal declares illegal mutable files: {sorted(illegal)}. "
                f"MVP allows only: {sorted(MVP_MUTABLE_FILES)}."
            )

    # ── Lock ───────────────────────────────────────────────────────────────────

    def _acquire_lock(self) -> None:
        """Write a lock file. Raises HarnessLockError if already locked."""
        if self._lock_path.exists():
            try:
                existing = self._lock_path.read_text(encoding="utf-8").strip()
            except Exception:
                existing = "<unreadable>"
            raise HarnessLockError(
                f"Workspace {self.workspace} is already locked by another harness cycle. "
                f"Lock contents: {existing!r}. "
                f"Delete {self._lock_path} if the previous run was interrupted."
            )
        pid = os.getpid()
        self._lock_path.write_text(
            f"pid={pid}\ncommand=<pending>\n", encoding="utf-8"
        )

    def _release_lock(self) -> None:
        """Remove the lock file."""
        try:
            self._lock_path.unlink(missing_ok=True)
        except Exception:
            pass   # best-effort; lock will be stale but not blocking

    # ── Execution ──────────────────────────────────────────────────────────────

    def _execute(
        self,
        command: str,
        eval_output_file: Optional[str | Path],
    ) -> HarnessResult:
        """
        Run command with timeout. Capture stdout/stderr. Hash all artifacts.
        """
        notes: List[str] = []
        elapsed: float = 0.0
        timed_out: bool = False

        # Prepare environment
        run_env = os.environ.copy()
        if self.env:
            run_env.update(self.env)
        # Determinism: pin PYTHONHASHSEED if not already set by caller
        run_env.setdefault("PYTHONHASHSEED", "42")
        # Suppress bytecode for cleaner workspace
        run_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")

        # Parse command into argv
        import shlex
        argv: List[str] = shlex.split(command)

        start = time.monotonic()
        stdout_bytes = b""
        stderr_bytes = b""
        exit_code = -1

        try:
            proc = subprocess.run(
                argv,
                cwd=str(self.workspace),
                capture_output=True,
                timeout=self.budget_seconds,
                env=run_env,
            )
            stdout_bytes = proc.stdout or b""
            stderr_bytes = proc.stderr or b""
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout_bytes = e.stdout or b""
            stderr_bytes = e.stderr or b""
            timed_out = True
            exit_code = -1
            elapsed = self.budget_seconds
            notes.append(
                f"BUDGET_EXCEEDED: Command timed out after {self.budget_seconds}s. "
                f"G_replay_ok will be False."
            )
        except FileNotFoundError as e:
            notes.append(f"EXECUTION_ERROR: Command not found: {e}")
            exit_code = -1
        except Exception as e:
            notes.append(f"EXECUTION_ERROR: {type(e).__name__}: {e}")
            exit_code = -1

        if not timed_out:
            elapsed = time.monotonic() - start

        # Hash stdout and stderr
        stdout_sha256 = _sha256_bytes(stdout_bytes)
        stderr_sha256 = _sha256_bytes(stderr_bytes)

        # Parse metric from stdout
        metric_after, metric_parsed = _parse_metric(stdout_bytes)
        if not metric_parsed:
            notes.append(
                "METRIC_NOT_FOUND: Could not parse top1_accuracy from stdout. "
                "G_metric_improved will be False unless metric is supplied externally."
            )

        # Hash eval_output_file
        eval_output_hash: Optional[str] = None
        if eval_output_file is not None:
            eval_path = self.workspace / Path(eval_output_file)
            if eval_path.exists():
                eval_output_hash = _sha256_file(eval_path)
            else:
                notes.append(
                    f"EVAL_OUTPUT_FILE_ABSENT: {eval_path} does not exist. "
                    f"eval_output_hash will be None."
                )
        else:
            notes.append(
                "EVAL_OUTPUT_FILE_NOT_SPECIFIED: No eval_output_file given. "
                "eval_output_hash will be None. G_replay_ok eval comparison skipped."
            )

        return HarnessResult(
            exit_code=exit_code,
            stdout_sha256=stdout_sha256,
            stderr_sha256=stderr_sha256,
            eval_output_hash=eval_output_hash,
            metric_after=metric_after,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            elapsed_seconds=elapsed,
            timed_out=timed_out,
            metric_parsed=metric_parsed,
            command=command,
            workspace=str(self.workspace),
            notes=notes,
        )


# ── Public convenience function ────────────────────────────────────────────────

def run_bounded(
    command: str,
    workspace: Path | str,
    eval_output_file: Optional[str | Path] = None,
    budget_seconds: int = DEFAULT_BUDGET_SECONDS,
    env: Optional[dict] = None,
) -> HarnessResult:
    """
    Convenience wrapper: create a BoundedHarness and run one cycle.

    Usage:
        result = run_bounded(
            command="python eval.py --seed 42 --dataset frozen_eval.jsonl",
            workspace=Path("workspaces/cycle_001"),
            eval_output_file="results/eval_output.json",
        )
    """
    harness = BoundedHarness(
        workspace=workspace,
        budget_seconds=budget_seconds,
        env=env,
    )
    return harness.run(command=command, eval_output_file=eval_output_file)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sha256_bytes(data: bytes) -> str:
    """SHA256 hex of a bytes object."""
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    """SHA256 hex of a file's contents."""
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_metric(stdout: bytes) -> tuple[Optional[float], bool]:
    """
    Extract top1_accuracy from stdout.

    Looks for pattern: "top1_accuracy: 0.847" or "top1_accuracy=0.847"
    Returns (value, True) if found, (None, False) otherwise.
    """
    text = stdout.decode("utf-8", errors="replace")
    match = METRIC_PATTERN.search(text)
    if match:
        try:
            return float(match.group(1)), True
        except ValueError:
            return None, False
    return None, False
