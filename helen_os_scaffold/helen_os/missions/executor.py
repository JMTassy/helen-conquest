"""
helen_os/missions/executor.py — Safe step execution with receipt issuance.

Wraps step_executor.execute_step() with exception handling so that worker
crashes produce a FAIL receipt rather than propagating as unhandled exceptions.

Invariants:
  I1  Every execute() call returns an ExecutionReceiptV1 — never raises.
  I2  Receipt status is 'ok' iff worker_fn returned {"status": "ok", ...}.
  I3  Worker exceptions are caught and recorded in last_error.
  I4  Deterministic: same inputs → same receipt_id.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from .ids import canon, sha256_hex, stable_id
from .schemas import ExecutionReceiptV1

WorkerFn = Callable[[dict[str, Any]], dict[str, Any]]


def execute(
    *,
    step: "dict[str, Any]",
    worker_id: str,
    worker_fn: WorkerFn,
    tick: int = 0,
) -> tuple[dict[str, Any], ExecutionReceiptV1, list[str]]:
    """
    Execute a single step safely.

    Args:
        step:       MISSION_STEP_V1 dict (must have step_id, mission_id, step_kind, input_refs).
        worker_id:  Identifier of the worker executing this step.
        worker_fn:  Callable that takes inp-dict and returns out-dict.
        tick:       Logical clock tick for ordering.

    Returns:
        (updated_step_dict, receipt, output_refs)

    The returned step dict has:
        status = "succeeded" | "failed"
        output_refs = [trace_ref]
        receipt_refs = [receipt_id]  (only if status == "succeeded")
        last_error   = None | error_string
    """
    step = dict(step)  # shallow copy — do not mutate caller's dict

    mission_id  = step["mission_id"]
    step_id     = step["step_id"]
    step_kind   = step["step_kind"]
    input_refs  = list(step.get("input_refs", []))

    inp = {
        "mission_id": mission_id,
        "step_id":    step_id,
        "step_kind":  step_kind,
        "input_refs": input_refs,
    }
    input_hash = sha256_hex(canon(inp))

    last_error: str | None = None
    out: dict[str, Any] = {}

    try:
        out = worker_fn(inp)
    except Exception as exc:  # noqa: BLE001
        last_error = f"{type(exc).__name__}: {exc}"
        out = {"status": "fail", "error": last_error}

    output_hash = sha256_hex(canon(out))
    trace_ref   = "TRACE:" + sha256_hex(canon({"in": inp, "out": out}))[:16]
    output_refs = [trace_ref]

    receipt_payload = {
        "mission_id": mission_id,
        "step_id":    step_id,
        "worker_id":  worker_id,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "trace_ref":  trace_ref,
        "tick":       tick,
    }
    receipt_id = stable_id("R", receipt_payload)

    worker_ok = (out.get("status") == "ok") and last_error is None

    receipt = ExecutionReceiptV1(
        artifact_type="EXECUTION_RECEIPT_V1",
        receipt_id=receipt_id,
        mission_id=mission_id,
        step_id=step_id,
        worker_id=worker_id,
        status="ok" if worker_ok else "fail",
        input_hash=input_hash,
        output_hash=output_hash,
        trace_ref=trace_ref,
        created_at_tick=tick,
    )

    # Update step dict in-place (returned copy only)
    step_status = "succeeded" if worker_ok else "failed"
    step["status"]       = step_status
    step["output_refs"]  = output_refs
    step["receipt_refs"] = [receipt_id] if worker_ok else []
    step["last_error"]   = last_error or (None if worker_ok else out.get("error"))

    return step, receipt, output_refs


def execute_as_dict(
    *,
    step: dict[str, Any],
    worker_id: str,
    worker_fn: WorkerFn,
    tick: int = 0,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """
    Same as execute() but returns (step_dict, receipt_dict, output_refs).
    Useful when callers work fully in dict-space.
    """
    updated_step, receipt, output_refs = execute(
        step=step,
        worker_id=worker_id,
        worker_fn=worker_fn,
        tick=tick,
    )
    return updated_step, asdict(receipt), output_refs
