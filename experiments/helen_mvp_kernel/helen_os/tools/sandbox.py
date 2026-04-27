"""Sandboxed shell execution. Internal — not exposed via Session public API.

Always invoked with shell=False; argv must already be split. The caller
(terminal_executor) is required to confirm the gate verdict before invoking.
"""
from __future__ import annotations

import shlex
import subprocess

from helen_os.ledger.receipts import ShellOutcome

DEFAULT_TIMEOUT_SECONDS = 5


class _SandboxError(Exception):
    pass


def _split(command: str) -> list[str]:
    parts = shlex.split(command)
    if not parts:
        raise _SandboxError("empty command")
    return parts


def _run_argv(argv: list[str], allowed: set[str], timeout: int) -> ShellOutcome:
    head = argv[0]
    if head not in allowed:
        raise _SandboxError(f"command head {head!r} not in allowed set")
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )
    return ShellOutcome(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _execute(command: str, allowed_set: set[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ShellOutcome:
    argv = _split(command)
    return _run_argv(argv, allowed_set, timeout)
