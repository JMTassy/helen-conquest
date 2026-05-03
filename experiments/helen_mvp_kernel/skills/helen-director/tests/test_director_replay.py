"""Director replay invariant test (stdlib only).

Per HELEN Video OS LaTeX spec §14:
    same brief + same seed -> same packet hashes (across N runs)

Per §13 MVP exclusions: no LLM, no cloud, no image gen, no RH claims.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from director import (  # noqa: E402
    PHI,
    canonical_json,
    emit_packet,
    make_packet,
    run_one,
    run_replay,
)
from timing import phi_shot_durations, prime_turn_indices  # noqa: E402

FIXTURE = SKILL_ROOT / "fixtures" / "helen_30s_sovereignty.json"


def _brief():
    import json
    with FIXTURE.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_phi_shot_durations_sum_to_T():
    durations = phi_shot_durations(30.0, 6)
    assert abs(sum(durations) - 30.0) < 1e-9, f"sum={sum(durations)}"


def test_phi_shot_durations_monotone_increasing():
    durations = phi_shot_durations(30.0, 6)
    for i in range(len(durations) - 1):
        assert durations[i] < durations[i + 1], f"not monotone at {i}: {durations}"


def test_prime_turn_indices_for_six_shots():
    pts = prime_turn_indices(6)
    assert pts == [2, 3, 5], f"expected [2,3,5] got {pts}"


def test_packet_has_all_required_artifacts():
    p = make_packet(_brief())
    assert "storyboard_md" in p
    assert "shot_table" in p
    assert "asset_binds" in p
    assert "math_constraints" in p
    assert len(p["shot_table"]) == 6


def test_shot_table_marks_prime_turns_correctly():
    p = make_packet(_brief())
    primes = {s["shot_id"]: s["math_constraints"]["prime_turn"] for s in p["shot_table"]}
    expected_primes = {"S001": False, "S002": True, "S003": True, "S004": False, "S005": True, "S006": False}
    assert primes == expected_primes, f"prime markings wrong: {primes}"


def test_constitutional_locks_in_math_constraints():
    p = make_packet(_brief())
    mc = p["math_constraints"]
    assert mc["decimal_precision"] == 12
    assert mc["braid_strands"] == [
        "face_identity", "pose_motion", "ledger_object",
        "light_interface", "camera_axis",
    ]


def test_replay_3x_consistent_via_run_replay():
    result = run_replay(FIXTURE, n=3)
    assert result["replay_consistent"] is True, f"drift: {result}"
    assert result["status"] == "PASS"


def test_emit_packet_writes_required_artifacts(tmp_path):
    receipt = emit_packet(_brief(), tmp_path)
    for name in [
        "STORYBOARD_V1.md",
        "shot_table.json",
        "asset_binds.json",
        "math_constraints.json",
        "DIRECTOR_PACKET_RECEIPT_V1.json",
    ]:
        assert (tmp_path / name).exists(), f"missing artifact: {name}"
    assert receipt["scope"] == "TEMPLE_SUBSANDBOX"
    assert receipt["sovereign_admitted"] is False
    assert receipt["status"] == "PASS"


def test_emit_refuses_forbidden_target(tmp_path):
    """Verify SovereignWriteRefused fires on forbidden paths."""
    from director import SovereignWriteRefused, REPO_ROOT
    forbidden = REPO_ROOT / "temple" / "subsandbox" / "renders" / "should_not_write"
    try:
        emit_packet(_brief(), forbidden)
    except SovereignWriteRefused:
        return
    raise AssertionError(f"expected SovereignWriteRefused for {forbidden}")


if __name__ == "__main__":
    tests = [
        test_phi_shot_durations_sum_to_T,
        test_phi_shot_durations_monotone_increasing,
        test_prime_turn_indices_for_six_shots,
        test_packet_has_all_required_artifacts,
        test_shot_table_marks_prime_turns_correctly,
        test_constitutional_locks_in_math_constraints,
        test_replay_3x_consistent_via_run_replay,
    ]
    # The two tmp_path-using tests need a tmp dir
    import tempfile
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e!r}")
            failed += 1
    # Run tmp-path tests with a real temp dir
    for fn in (test_emit_packet_writes_required_artifacts, test_emit_refuses_forbidden_target):
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
                print(f"  PASS  {fn.__name__}")
            except Exception as e:
                print(f"  FAIL  {fn.__name__}: {e!r}")
                failed += 1
    total = len(tests) + 2
    print()
    print(f"DIRECTOR REPLAY: {total - failed}/{total} passed")
    sys.exit(0 if failed == 0 else 1)
