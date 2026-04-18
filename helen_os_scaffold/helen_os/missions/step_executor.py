from __future__ import annotations
from typing import Any
from .ids import canon, sha256_hex, stable_id
from .schemas import ExecutionReceiptV1

def execute_step(
    *,
    worker_id: str,
    mission_id: str,
    step_id: str,
    step_kind: str,
    input_refs: list[str],
    worker_fn,
    tick: int = 0,
) -> tuple[list[str], ExecutionReceiptV1]:
    """Run worker_fn in sandbox. Returns (output_refs, execution_receipt)."""
    inp = {"mission_id": mission_id, "step_id": step_id, "step_kind": step_kind, "input_refs": input_refs}
    input_hash = sha256_hex(canon(inp))

    out = worker_fn(inp)
    output_hash = sha256_hex(canon(out))

    trace_ref = "TRACE:" + sha256_hex(canon({"in": inp, "out": out}))[:16]
    output_refs = [trace_ref]

    receipt_payload = {
        "mission_id": mission_id, "step_id": step_id, "worker_id": worker_id,
        "input_hash": input_hash, "output_hash": output_hash,
        "trace_ref": trace_ref, "tick": tick,
    }
    receipt_id = stable_id("R", receipt_payload)

    receipt = ExecutionReceiptV1(
        artifact_type="EXECUTION_RECEIPT_V1",
        receipt_id=receipt_id,
        mission_id=mission_id,
        step_id=step_id,
        worker_id=worker_id,
        status="ok" if out.get("status") == "ok" else "fail",
        input_hash=input_hash,
        output_hash=output_hash,
        trace_ref=trace_ref,
        created_at_tick=tick,
    )
    return output_refs, receipt
