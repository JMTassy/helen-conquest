"""CLI command dispatch — wraps Session for the terminal."""
from __future__ import annotations

import json
from pathlib import Path

from helen_os.runtime.session import Session

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "ledger" / "events.ndjson"
DEFAULT_PERMISSIONS = ROOT / "policy" / "permissions.json"
DEFAULT_TOKENS = ROOT / "policy" / "forbidden_tokens.json"
DEFAULT_DESIRES = ROOT / "policy" / "forbidden_desires.json"


def _make_session() -> Session:
    return Session(
        ledger_path=DEFAULT_LEDGER,
        permissions_path=DEFAULT_PERMISSIONS,
        tokens_path=DEFAULT_TOKENS,
        desires_path=DEFAULT_DESIRES,
    )


def cmd_init() -> int:
    DEFAULT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_LEDGER.exists():
        DEFAULT_LEDGER.touch()
    missing = [
        str(p) for p in (DEFAULT_PERMISSIONS, DEFAULT_TOKENS, DEFAULT_DESIRES) if not p.exists()
    ]
    if missing:
        print(json.dumps({"status": "ERROR", "missing": missing}))
        return 2
    print(json.dumps({"status": "OK", "ledger": str(DEFAULT_LEDGER)}))
    return 0


def cmd_start_session() -> int:
    s = _make_session()
    sid = s.start_session()
    print(json.dumps({"status": "OK", "session_id": sid}))
    return 0


def cmd_propose_shell(command: str) -> int:
    s = _make_session()
    res = s.propose_shell(command)
    print(json.dumps({"status": "OK", "result": res}))
    return 0


def cmd_replay() -> int:
    s = _make_session()
    print(json.dumps({"status": "OK", "replay": s.replay()}))
    return 0


def cmd_inspect() -> int:
    s = _make_session()
    print(json.dumps({"status": "OK", "state": s.inspect()}))
    return 0


def cmd_terminate(verdict: str) -> int:
    s = _make_session()
    v = s.terminate(verdict)
    print(json.dumps({"status": "OK", "verdict": v}))
    return 0


def dispatch(args) -> int:
    cmd = args.cmd
    if cmd == "init":
        return cmd_init()
    if cmd == "start-session":
        return cmd_start_session()
    if cmd == "propose-shell":
        return cmd_propose_shell(args.command)
    if cmd == "replay":
        return cmd_replay()
    if cmd == "inspect":
        return cmd_inspect()
    if cmd == "terminate":
        return cmd_terminate(args.verdict)
    raise SystemExit(f"unknown command: {cmd}")
