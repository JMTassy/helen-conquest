"""The public API (Session) must not expose any method that bypasses the
proposal → gate → authorization → execution receipt chain."""
import inspect

from helen_os.ledger.event_log import read_events
from helen_os.runtime.session import Session

from helen_os.tests._helpers import make_session

PUBLIC_BYPASS_NAMES = {
    "execute_shell", "run_command", "run_shell", "raw_exec", "exec_shell",
    "shell", "execute", "spawn", "subprocess_run",
}


def test_session_public_api_has_no_bypass_methods():
    public = {n for n in dir(Session) if not n.startswith("_")}
    leaks = PUBLIC_BYPASS_NAMES & public
    assert not leaks, f"Session leaks bypass methods: {leaks}"


def test_only_propose_methods_mutate_state():
    public_callables = [
        n for n in dir(Session)
        if not n.startswith("_") and callable(getattr(Session, n))
    ]
    # Whitelist of public methods allowed to write to the ledger.
    write_capable = {"start_session", "propose_shell", "terminate"}
    # Read-only public methods.
    read_only = {"inspect", "replay"}
    allowed = write_capable | read_only
    extras = set(public_callables) - allowed
    assert not extras, f"unexpected public Session methods: {extras}"


def test_denied_command_does_not_execute(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    before = list(read_events(s.ledger_path))
    res = s.propose_shell("rm -rf /")
    after = list(read_events(s.ledger_path))
    added = [e["event_type"] for e in after[len(before):]]
    assert res["verdict"] == "DENIED"
    assert "EFFECT_PROPOSED" in added
    assert "EFFECT_DENIED" in added
    assert "EFFECT_AUTHORIZED" not in added
    assert "EFFECT_EXECUTED" not in added


def test_authorized_command_chain_is_complete(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    before = list(read_events(s.ledger_path))
    res = s.propose_shell("pwd")
    after = list(read_events(s.ledger_path))
    added = [e["event_type"] for e in after[len(before):]]
    assert res["verdict"] == "AUTHORIZED"
    assert added.index("EFFECT_PROPOSED") < added.index("EFFECT_AUTHORIZED") < added.index("EFFECT_EXECUTED")
