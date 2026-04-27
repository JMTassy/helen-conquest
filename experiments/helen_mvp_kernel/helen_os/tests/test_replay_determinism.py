from helen_os.kernel.reducer import fold
from helen_os.kernel.state import state_hash
from helen_os.ledger.event_log import read_events

from helen_os.tests._helpers import make_session


def test_replay_is_deterministic(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    s.propose_shell("ls")
    s.propose_shell("pwd")
    s.propose_shell("rm -rf /tmp/whatever")  # denied
    s.terminate("NO_SHIP")

    events = read_events(s.ledger_path)
    state_a = fold(events, forbidden_tokens=s.forbidden_tokens)
    state_b = fold(events, forbidden_tokens=s.forbidden_tokens)
    assert state_hash(state_a) == state_hash(state_b)
    assert state_a.to_dict() == state_b.to_dict()
