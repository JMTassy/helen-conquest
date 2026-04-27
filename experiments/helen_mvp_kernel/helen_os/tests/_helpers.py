"""Test helpers — set up an isolated Session per tmp_path."""
from __future__ import annotations

from pathlib import Path

from helen_os.runtime.session import Session

ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "policy"


def make_session(tmp_path: Path) -> Session:
    ledger = tmp_path / "events.ndjson"
    return Session(
        ledger_path=ledger,
        permissions_path=POLICY_DIR / "permissions.json",
        tokens_path=POLICY_DIR / "forbidden_tokens.json",
        desires_path=POLICY_DIR / "forbidden_desires.json",
    )
