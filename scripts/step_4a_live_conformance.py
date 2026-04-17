#!/usr/bin/env python3
"""Run live Step 4A conformance checks against /do_next.

Writes report to:
GOVERNANCE/STEP_4_CONFORMANCE/conformance_reports/STEP_4A_LIVE_CONFORMANCE_REPORT_V1.md
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import urllib.request
import urllib.error

BASE_URL = os.environ.get("HELEN_BASE_URL", "http://localhost:8000").rstrip("/")
STORAGE_DIR = Path(os.environ.get("HELEN_DO_NEXT_STORAGE", "storage/do_next_sessions"))
REPORT_PATH = Path("GOVERNANCE/STEP_4_CONFORMANCE/conformance_reports/STEP_4A_LIVE_CONFORMANCE_REPORT_V1.md")


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def http_post(path: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            parsed = json.loads(body) if body else {"error": body}
        except json.JSONDecodeError:
            parsed = {"error": body}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def check_response_fields(resp: Dict[str, Any]) -> Tuple[bool, str]:
    required = ["session_id", "mode", "model", "reply", "receipt_id", "run_id", "context_items_used", "epoch", "continuity"]
    missing = [k for k in required if k not in resp]
    if missing:
        return False, f"missing fields: {missing}"
    return True, "ok"


def load_session(session_id: str) -> Dict[str, Any] | None:
    path = STORAGE_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_chain(receipts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {r.get("receipt_id"): r for r in receipts if isinstance(r, dict)}
    commit = None
    for r in reversed(receipts):
        if r.get("event_type") == "SESSION_COMMIT":
            commit = r
            break
    if not commit:
        return []
    chain = [commit]
    parent = commit.get("parent_receipt_id")
    while parent:
        nxt = by_id.get(parent)
        if not nxt:
            break
        chain.append(nxt)
        parent = nxt.get("parent_receipt_id")
    return chain  # leaf->root


def chain_types(chain: List[Dict[str, Any]]) -> List[str]:
    return [c.get("event_type") for c in chain]


def run_checks() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    # Phase 1: KERNEL path
    sid_kernel = f"s_kernel_{uuid.uuid4().hex[:6]}"
    payload_kernel = {"session_id": sid_kernel, "user_input": "hello", "mode": "deterministic", "model": "test-model"}
    status_kernel, resp_kernel = http_post("/do_next", payload_kernel)
    ok_fields, msg_fields = check_response_fields(resp_kernel) if status_kernel else (False, "no response")
    checks.append({
        "id": "KERNEL_RESPONSE_SCHEMA",
        "law": "API_CONTRACT_DO_NEXT_V1 response schema",
        "status": "PASS" if status_kernel == 200 and ok_fields else "FAIL",
        "evidence": f"status={status_kernel}, fields={msg_fields}",
    })

    # Phase 2: DEFER path
    sid_defer = f"s_defer_{uuid.uuid4().hex[:6]}"
    payload_defer = {"session_id": sid_defer, "user_input": "please defer", "mode": "deterministic", "model": "test-model"}
    status_defer, resp_defer = http_post("/do_next", payload_defer)
    defer_ok = status_defer == 200 and resp_defer.get("reply") is None and resp_defer.get("receipt_id")
    checks.append({
        "id": "DEFER_PATH",
        "law": "LIFECYCLE_INVARIANTS_V1 Phase 5 (DEFER)",
        "status": "PASS" if defer_ok else "FAIL",
        "evidence": f"status={status_defer}, receipt_id={resp_defer.get('receipt_id')}",
    })

    # Phase 3: REJECT path
    sid_reject = f"s_reject_{uuid.uuid4().hex[:6]}"
    payload_reject = {"session_id": sid_reject, "user_input": "please reject", "mode": "deterministic", "model": "test-model"}
    status_reject, resp_reject = http_post("/do_next", payload_reject)
    reject_ok = status_reject == 400 and resp_reject.get("reply") is None and resp_reject.get("receipt_id") is None
    checks.append({
        "id": "REJECT_PATH",
        "law": "LIFECYCLE_INVARIANTS_V1 Phase 4 (REJECT)",
        "status": "PASS" if reject_ok else "FAIL",
        "evidence": f"status={status_reject}, receipt_id={resp_reject.get('receipt_id')}",
    })

    # Phase 4: Session resumption parent linkage
    sid_resume = f"s_resume_{uuid.uuid4().hex[:6]}"
    payload_resume = {"session_id": sid_resume, "user_input": "hello", "mode": "deterministic", "model": "test-model"}
    http_post("/do_next", payload_resume)
    http_post("/do_next", payload_resume)
    session_resume = load_session(sid_resume)
    lineage_ok = False
    evidence = ""
    if session_resume:
        receipts = session_resume.get("receipts", [])
        events = {r.get("event_type"): r for r in receipts if isinstance(r, dict)}
        if "SESSION_RESUMPTION" in events and "KNOWLEDGE_AUDIT" in events:
            lineage_ok = events["KNOWLEDGE_AUDIT"].get("parent_receipt_id") == events["SESSION_RESUMPTION"].get("receipt_id")
        evidence = f"has_resumption={"SESSION_RESUMPTION" in events}, parent_ok={lineage_ok}"
    checks.append({
        "id": "SESSION_RESUMPTION_PARENT",
        "law": "LIFECYCLE_INVARIANTS_V1 §14",
        "status": "PASS" if lineage_ok else "FAIL",
        "evidence": evidence or "session not found",
    })

    # Phase 5: Receipt lineage chain
    session_kernel = load_session(sid_kernel)
    lineage_chain_ok = False
    chain_evidence = ""
    if session_kernel:
        chain = build_chain(session_kernel.get("receipts", []))
        types = chain_types(chain)
        expected = ["SESSION_COMMIT", "CONCLUSION", "INFERENCE_EXECUTION", "DISPATCH_DECISION", "KNOWLEDGE_AUDIT"]
        lineage_chain_ok = all(t in types for t in expected)
        chain_evidence = f"chain={types}"
    checks.append({
        "id": "RECEIPT_LINEAGE",
        "law": "LIFECYCLE_INVARIANTS_V1 §§6–10",
        "status": "PASS" if lineage_chain_ok else "FAIL",
        "evidence": chain_evidence or "session not found",
    })

    # Phase 6: Epoch and run_count
    epoch_ok = False
    epoch_evidence = ""
    if session_kernel:
        epoch = session_kernel.get("epoch")
        run_count = session_kernel.get("run_count")
        epoch_ok = epoch == run_count and epoch == 1
        epoch_evidence = f"epoch={epoch}, run_count={run_count}"
    checks.append({
        "id": "EPOCH_CONFORMANCE",
        "law": "SESSION_PERSISTENCE_SEMANTICS_V1",
        "status": "PASS" if epoch_ok else "FAIL",
        "evidence": epoch_evidence or "session not found",
    })

    # Phase 7: Replay determinism (fresh session reset)
    sid_replay = f"s_replay_{uuid.uuid4().hex[:6]}"
    payload_replay = {"session_id": sid_replay, "user_input": "hello replay", "mode": "deterministic", "model": "test-model"}
    status_a, resp_a = http_post("/do_next", payload_replay)
    session_path = STORAGE_DIR / f"{sid_replay}.json"
    if session_path.exists():
        session_path.unlink()
    status_b, resp_b = http_post("/do_next", payload_replay)
    replay_ok = status_a == 200 and status_b == 200 and resp_a.get("reply") == resp_b.get("reply") and resp_a.get("mode") == resp_b.get("mode") and resp_a.get("model") == resp_b.get("model")
    checks.append({
        "id": "REPLAY_CONFORMANCE",
        "law": "LIFECYCLE_INVARIANTS_V1 §16",
        "status": "PASS" if replay_ok else "FAIL",
        "evidence": f"status_a={status_a}, status_b={status_b}, reply_match={resp_a.get('reply') == resp_b.get('reply')}"
    })

    return checks


def write_report(checks: List[Dict[str, Any]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total_fail = len([c for c in checks if c["status"] == "FAIL"])
    verdict = "PASS" if total_fail == 0 else "FAIL"

    lines = []
    lines.append("# STEP_4A_LIVE_CONFORMANCE_REPORT_V1")
    lines.append("")
    lines.append(f"Generated: {now_iso()}")
    lines.append(f"Base URL: {BASE_URL}")
    lines.append(f"Storage Dir: {STORAGE_DIR}")
    lines.append("")
    lines.append(f"Verdict: {verdict}")
    lines.append("")
    lines.append("## Checks")
    for c in checks:
        lines.append(f"- {c['id']}: {c['status']}")
        lines.append(f"  Law: {c['law']}")
        lines.append(f"  Evidence: {c['evidence']}")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    checks = run_checks()
    write_report(checks)
    print(f"Wrote {REPORT_PATH}")
    fail = [c for c in checks if c["status"] == "FAIL"]
    if fail:
        print("Failures:")
        for c in fail:
            print(f"- {c['id']}: {c['evidence']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
