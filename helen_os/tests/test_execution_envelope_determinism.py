"""Test: Executor produces deterministic envelopes."""
from __future__ import annotations

from helen_os.executor.helen_executor_v1 import execute_skill
from helen_os.governance.canonical import sha256_prefixed


def test_same_input_same_envelope():
    """Identical task input produces identical envelope."""
    task = {"task_id": "T1", "skill_id": "S1", "payload": {"x": 1}}

    e1 = execute_skill(task)
    e2 = execute_skill(task)

    # Envelopes must be byte-identical
    hash_1 = sha256_prefixed(e1)
    hash_2 = sha256_prefixed(e2)

    assert hash_1 == hash_2, "Envelopes must be deterministic"
    assert e1["input_canonical_sha256"] == e2["input_canonical_sha256"]
    assert e1["output_canonical_sha256"] == e2["output_canonical_sha256"]
