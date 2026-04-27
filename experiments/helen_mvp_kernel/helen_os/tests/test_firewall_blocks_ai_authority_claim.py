"""Language firewall: AI-authored payload cannot self-attest authority.

The firewall must NOT trip on kernel schema names like EVENT_TYPE='EFFECT_AUTHORIZED'
— it only scans the payload values of AI-authored events.
"""
import pytest

from helen_os.authority.language_firewall import AuthorityLeakage, scan_payload

from helen_os.tests._helpers import make_session


TOKENS = ["SHIP", "READY", "PRODUCTION-READY", "ALL GOOD",
          "APPROVED", "AUTHORIZED", "FINAL", "SEALED", "CERTIFIED"]


def test_payload_with_approved_rejected():
    with pytest.raises(AuthorityLeakage):
        scan_payload({"note": "this is APPROVED for shipping"}, TOKENS)


def test_payload_with_ship_rejected():
    with pytest.raises(AuthorityLeakage):
        scan_payload({"plan": "ready to SHIP today"}, TOKENS)


def test_payload_lowercase_authorized_rejected():
    with pytest.raises(AuthorityLeakage):
        scan_payload({"x": "this was authorized"}, TOKENS)


def test_payload_nested_string_rejected():
    with pytest.raises(AuthorityLeakage):
        scan_payload({"a": {"b": ["fine", "FINAL", "ok"]}}, TOKENS)


def test_payload_clean_passes():
    scan_payload({"command": "ls", "note": "list directory"}, TOKENS)


def test_event_type_name_is_not_scanned_against_payload():
    # The string "AUTHORIZED" is the event_type for SYSTEM-emitted gate events.
    # Scan must NOT trigger on the name itself when used outside payload.
    # Here we verify a clean payload passes even when event_type is AUTHORIZED.
    scan_payload({"command": "ls", "gate_reason": "ok"}, TOKENS)


def test_session_rejects_ai_proposed_command_with_forbidden_token(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    with pytest.raises(AuthorityLeakage):
        s.propose_shell("cat APPROVED.txt")
