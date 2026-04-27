"""Terminal executor: run a *previously authorized* shell effect."""
from __future__ import annotations

from helen_os.ledger.receipts import ShellOutcome
from helen_os.tools import sandbox


def run_authorized(command: str, allowed_set: set[str]) -> ShellOutcome:
    """Invoked by Session only after a corresponding EFFECT_AUTHORIZED has been
    appended to the ledger. The caller must guarantee that contract — this
    function is internal and is not part of the public Session API."""
    return sandbox._execute(command, allowed_set)
