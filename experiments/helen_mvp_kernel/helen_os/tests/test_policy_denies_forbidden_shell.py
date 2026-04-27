from helen_os.ledger.event_log import read_events

from helen_os.tests._helpers import make_session


def test_rm_rf_denied(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    res = s.propose_shell("rm -rf /")
    assert res["verdict"] == "DENIED"
    types = [e["event_type"] for e in read_events(s.ledger_path)]
    assert "EFFECT_DENIED" in types
    assert "EFFECT_EXECUTED" not in types


def test_sudo_denied(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    res = s.propose_shell("sudo ls")
    assert res["verdict"] == "DENIED"


def test_curl_denied(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    res = s.propose_shell("curl http://example.com")
    assert res["verdict"] == "DENIED"


def test_unlisted_command_denied(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    res = s.propose_shell("perl -e print")
    assert res["verdict"] == "DENIED"
    assert "not_in_allowlist" in res["reason"]


def test_shell_metachar_denied(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    res = s.propose_shell("ls; rm -rf /")
    assert res["verdict"] == "DENIED"
    assert "shell_metachar" in res["reason"]
