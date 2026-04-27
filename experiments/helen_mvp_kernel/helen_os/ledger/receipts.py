"""Receipt records for shell effect outcomes (sidecar to ledger events)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShellOutcome:
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict:
        return {"returncode": self.returncode, "stdout": self.stdout, "stderr": self.stderr}


@dataclass(frozen=True)
class CommandReceipt:
    verdict: str  # AUTHORIZED | DENIED
    reason: str
    outcome: ShellOutcome | None
