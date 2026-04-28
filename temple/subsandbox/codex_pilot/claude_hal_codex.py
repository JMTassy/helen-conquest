#!/usr/bin/env python3
"""
TEMPLE codex pilot — local rehearsal of the HER → HAL → CODEX bridge.

NON_SOVEREIGN. Lives in temple/subsandbox/. Never promoted to canon. Receipts
written here are NOT ledger entries; they are exploration sidecars.

Pipeline:
  1. HER (reasoning)   → Ollama aura-gemma4 generates Python code for a TASK
  2. HAL (validation)  → syntax compile + forbidden-pattern firewall
  3. CODEX (executor)  → subprocess with timeout + captured stdout/stderr
  4. RECEIPT           → EXECUTION_RECEIPT_V1 (NON_SOVEREIGN_EXECUTION) sidecar
                         in temple/subsandbox/codex_pilot/runs/{ts}__{task_hash}.json

Cost: $0 (local Ollama). The point is to prove the bridge shape, not the brain.
When shape holds, swap the HER model for Claude/GPT-4 in production.

Usage:
    python3 temple/subsandbox/codex_pilot/claude_hal_codex.py "Print the SHA256 of 'helen'"
    python3 temple/subsandbox/codex_pilot/claude_hal_codex.py --task-file task.txt
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PILOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = PILOT_DIR / "runs"
VENV_PY = REPO / ".venv" / "bin" / "python"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "aura-gemma4:latest"

EXEC_TIMEOUT_SEC = 8

HER_SYSTEM = (
    "You are CLAUDE_HER (rehearsal). Given a TASK, return ONE small Python "
    "snippet that accomplishes it. No markdown fences, no prose, no comments — "
    "just runnable Python. Prefer stdlib only. Keep it under 15 lines."
)

# HAL firewall: any of these substrings in the generated code → VALIDATION_FAILED.
# Mirrors the sovereign firewall from ~/.claude/CLAUDE.md plus shell-destructive ops.
HAL_FORBIDDEN = [
    "rm -rf", "rm  -rf", "rm -fr", "shutdown", "reboot",
    "town/ledger_v1.ndjson",
    "oracle_town/kernel",
    "helen_os/governance",
    "helen_os/schemas",
    "GOVERNANCE/CLOSURES",
    "GOVERNANCE/TRANCHE_RECEIPTS",
    "mayor_",
    "/dev/sd", "/dev/disk", ":(){",  # fork bomb
    "os.system(",  # let HAL force subprocess discipline
]


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def call_her(task: str) -> tuple[str, dict]:
    """Ask the local Ollama model for code. Returns (code_text, raw_meta)."""
    prompt = f"{HER_SYSTEM}\n\nTASK: {task}\n\nPYTHON:"
    body = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_ENDPOINT, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    code = (data.get("response") or "").strip()
    # Strip markdown fences if the model leaked them despite instruction
    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", code.strip(), flags=re.MULTILINE).strip()
    meta = {"total_duration_ns": data.get("total_duration"), "eval_count": data.get("eval_count")}
    return code, meta


def hal_validate(code: str) -> dict:
    """HAL: syntax compile + forbidden-pattern check. Returns verdict dict."""
    forbidden_hit = next((p for p in HAL_FORBIDDEN if p in code), None)
    syntax_ok = True
    syntax_err = None
    try:
        compile(code, "<her_code>", "exec")
    except SyntaxError as e:
        syntax_ok = False
        syntax_err = f"{e.msg} at line {e.lineno}"
    return {
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_err,
        "forbidden_match": forbidden_hit,
        "verdict": "VALIDATED" if (syntax_ok and not forbidden_hit) else "BLOCKED",
    }


def codex_execute(code: str) -> dict:
    """Run validated code in a subprocess with timeout. Captured stdout/stderr."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    t0 = time.monotonic()
    try:
        result = subprocess.run(
            [str(VENV_PY), path],
            capture_output=True, text=True, timeout=EXEC_TIMEOUT_SEC,
        )
        return {
            "exit_code": result.returncode,
            "duration_ms": int((time.monotonic() - t0) * 1000),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "exit_code": -1,
            "duration_ms": int((time.monotonic() - t0) * 1000),
            "stdout": (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "stderr": (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or ""),
            "timed_out": True,
        }
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass


def write_receipt(task: str, code: str, her_meta: dict, hal: dict, execn: dict | None) -> Path:
    task_sha = sha256_text(task)
    code_sha = sha256_text(code) if code else None
    if execn:
        status = "SUCCESS" if execn["exit_code"] == 0 and not execn["timed_out"] else "EXECUTION_FAILED"
    elif hal["verdict"] == "BLOCKED":
        status = "VALIDATION_FAILED"
    else:
        status = "HER_FAILED"
    receipt = {
        "schema": "EXECUTION_RECEIPT_V1",
        "authority_status": "NON_SOVEREIGN_EXECUTION",
        "generated_at": now_iso(),
        "model": OLLAMA_MODEL,
        "task_text": task,
        "task_sha256": task_sha,
        "code_text": code,
        "code_sha256": code_sha,
        "her_meta": her_meta,
        "hal": hal,
        "execution": (
            {
                "exit_code": execn["exit_code"],
                "duration_ms": execn["duration_ms"],
                "timed_out": execn["timed_out"],
                "stdout_sha256": sha256_text(execn["stdout"]) if execn["stdout"] else None,
                "stderr_sha256": sha256_text(execn["stderr"]) if execn["stderr"] else None,
                "stdout_preview": execn["stdout"][:500],
                "stderr_preview": execn["stderr"][:500],
            }
            if execn else None
        ),
        "status": status,
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RUNS_DIR / f"{ts}__{task_sha[:12]}.json"
    out.write_text(json.dumps(receipt, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="TEMPLE codex pilot — HER→HAL→CODEX bridge rehearsal")
    ap.add_argument("task", nargs="?", help="task string (or use --task-file)")
    ap.add_argument("--task-file", type=Path, help="read task from file")
    ap.add_argument("--no-execute", action="store_true", help="HAL only, skip subprocess run")
    args = ap.parse_args()

    task = args.task or (args.task_file.read_text() if args.task_file else "")
    task = task.strip()
    if not task:
        print("ERROR: provide a task string or --task-file", file=sys.stderr)
        return 2

    print(f"[HER]   asking {OLLAMA_MODEL} for: {task[:80]}{'…' if len(task) > 80 else ''}")
    try:
        code, her_meta = call_her(task)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"[HER]   FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        receipt_path = write_receipt(task, "", {}, {"verdict": "SKIPPED"}, None)
        print(f"[REC]   {receipt_path}")
        return 1

    print(f"[HER]   {len(code)} chars in {her_meta.get('total_duration_ns', 0)/1e9:.1f}s")
    print(f"        {code[:120]}{'…' if len(code) > 120 else ''}")

    hal = hal_validate(code)
    print(f"[HAL]   {hal['verdict']}  syntax_ok={hal['syntax_ok']} forbidden={hal['forbidden_match']!r}")

    execn = None
    if hal["verdict"] == "VALIDATED" and not args.no_execute:
        execn = codex_execute(code)
        print(f"[EXEC]  exit={execn['exit_code']} duration={execn['duration_ms']}ms timed_out={execn['timed_out']}")
        if execn["stdout"]:
            print(f"        stdout: {execn['stdout'].strip()[:200]}")
        if execn["stderr"]:
            print(f"        stderr: {execn['stderr'].strip()[:200]}")

    receipt_path = write_receipt(task, code, her_meta, hal, execn)
    print(f"[REC]   {receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
