"""Minimal executor: emits EXECUTION_ENVELOPE_V1."""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed
from helen_os.governance.validators import validate_schema


def execute_skill(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Pure executor: task → deterministic envelope.

    Rules:
    - Input hash: canonical JSON of task
    - Output hash: canonical JSON of simulated output
    - No wall clock, no randomness
    - Schema-valid EXECUTION_ENVELOPE_V1

    Args:
        task: {"task_id": str, "skill_id": str, ...}

    Returns:
        EXECUTION_ENVELOPE_V1 object
    """
    # Deterministic output (no randomness)
    output = {"status": "success", "data": None}

    # Build envelope
    envelope = {
        "schema_name": "EXECUTION_ENVELOPE_V1",
        "schema_version": "1.0.0",
        "task_id": task["task_id"],
        "skill_id": task["skill_id"],
        "input_canonical_sha256": sha256_prefixed(task),
        "output_canonical_sha256": sha256_prefixed(output),
        "exit_code": 0,
        "wall_time_ms": 42,
        "resource_usage": {"cpu_ms": 10, "mem_mb": 5},
        "artifact_refs": [],
        "trace": {
            "tool_refs": [],
            "log_sha256": sha256_prefixed({"log": ""}),
        },
    }

    # Validate before returning
    valid, err = validate_schema(
        "EXECUTION_ENVELOPE_V1", "1.0.0", envelope
    )
    if not valid:
        raise RuntimeError(f"executor produced invalid envelope: {err}")

    return envelope
