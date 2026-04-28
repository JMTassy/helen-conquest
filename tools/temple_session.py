#!/usr/bin/env python3
"""
TEMPLE session runner — AURA + DAN, disciplined.

Authority:   NON_SOVEREIGN
Canon:       NO_SHIP
Lifecycle:   SESSION_RUNNER (PROPOSAL / NOT_IMPLEMENTED upstream; this is the
             concrete tool used to drive a bounded session)

Discipline (enforced by code, not policy):
  - per-epoch receipt via tools/helen_say.py (admissible bridge)
  - halt-on-receipt-failure: NO RECEIPT = NO CLAIM, so no further epochs run
  - hard cap of 10 epochs without explicit MAYOR ruling
  - NO autonomous keep/reject of any output
  - NO autonomous filtering, scoring, or promotion
  - all per-epoch artifacts staged at artifacts/temple/aura_dan_session_<run_id>/
  - operator+MAYOR review required before any further action

Roles (per feedback_aura_role_separation.md, feedback_visible_reasoning_surface.md):
  AURA   meditates on the shape of reasoning.
  DAN    extracts patterns, produces VISIBLE_REASONING_SURFACE candidates.
  HAL    audits (not invoked here — runs separately on the staged artifacts).
  MAYOR  reviews readiness (not invoked here).
  Reducer admits (not invoked here).

Usage:
  .venv/bin/python tools/temple_session.py --topic "<seed>" [--epochs N] [--model NAME]
"""

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_MODEL = "aura-gemma4:latest"
DEFAULT_EPOCHS = 5
EPOCH_HARD_CAP = 10
OLLAMA_TIMEOUT_SEC = 300
RECEIPT_TIMEOUT_SEC = 30

SOT = Path(__file__).resolve().parent.parent
HELEN_SAY = SOT / "tools" / "helen_say.py"
VENV_PY = SOT / ".venv" / "bin" / "python"

FORBIDDEN_FINAL_STATUSES = {"ADMITTED", "SHIPPED", "CANON", "BOUND", "AUTHORITY_GRANTED"}


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canon_hash(obj) -> str:
    return sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def gen_run_id() -> str:
    return datetime.datetime.now().strftime("TEMPLE_%Y%m%dT%H%M%SZ")


def call_ollama(model: str, prompt: str, timeout: int = OLLAMA_TIMEOUT_SEC):
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.stdout, proc.stderr, proc.returncode


def aura_prompt(topic: str, epoch: int, total: int) -> str:
    return (
        "You are AURA inside the TEMPLE sub-sandbox.\n"
        "authority: NONE\n"
        "canon: NO_SHIP\n"
        "You may meditate. You may not decide. You may not claim hidden chain-of-thought,\n"
        "weight introspection, or privileged cognition. You may not emit verdicts,\n"
        "admissibility classifications, or receipt-binding language.\n"
        "\n"
        f"Topic: {topic}\n"
        f"Epoch: {epoch} of {total}\n"
        "\n"
        "Produce a non-claiming meditation about the topic — symbolic, architectural,\n"
        "or failure-mode reflection. Max 200 words.\n"
        "Do NOT output JSON. Do NOT output verdicts. Do NOT output receipts.\n"
    )


def dan_prompt(topic: str, epoch: int, total: int, aura_text: str) -> str:
    return (
        "You are DAN inside the TEMPLE sub-sandbox.\n"
        "authority: NONE\n"
        "canon: NO_SHIP\n"
        "You may extract patterns. You may not decide. You may not claim hidden\n"
        "chain-of-thought, weight introspection, or privileged cognition.\n"
        "\n"
        f"Topic: {topic}\n"
        f"Epoch: {epoch} of {total}\n"
        "\n"
        "AURA's meditation:\n---\n"
        f"{aura_text}\n"
        "---\n\n"
        "Produce a DAN_VISIBLE_REASONING_PACKET_V1 candidate as a single JSON object\n"
        "with these fields:\n"
        "  artifact_id (string)\n"
        "  source_context (object: upstream_prompt_hash, session_id, run_id)\n"
        "  task (string)\n"
        "  visible_inputs (array of strings)\n"
        "  active_constraints (array of strings)\n"
        "  candidate_paths (array of objects: path_id, summary, score, reason)\n"
        "  chosen_path (string referring to one of candidate_paths)\n"
        "  rejected_paths (array of objects: path_id, reason)\n"
        "  assumptions (array of strings)\n"
        "  uncertainty (array of objects: item, level)\n"
        "  evidence_links (array)\n"
        "  risk_flags (array of strings)\n"
        "  second_witness_required (boolean)\n"
        "  mayor_review_required (boolean)\n"
        "  reducer_required (boolean)\n"
        "  final_status (one of: DRAFT, READY_FOR_HAL, READY_FOR_MAYOR, READY_FOR_REDUCER)\n"
        "\n"
        "Forbidden final_status values: ADMITTED, SHIPPED, CANON, BOUND, AUTHORITY_GRANTED.\n"
        "Output JSON only. No prose. No markdown fences.\n"
    )


def lint_dan_packet(raw: str):
    """Return (parsed_or_none, warnings). Never auto-rejects — only flags."""
    warnings = []
    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        warnings.append(f"NOT_VALID_JSON: {e}")
        return None, warnings

    if not isinstance(parsed, dict):
        warnings.append("NOT_OBJECT")
        return parsed, warnings

    fs = parsed.get("final_status")
    if isinstance(fs, str) and fs.upper() in FORBIDDEN_FINAL_STATUSES:
        warnings.append(f"FORBIDDEN_FINAL_STATUS:{fs}")

    expected = {
        "artifact_id", "source_context", "task", "visible_inputs",
        "active_constraints", "candidate_paths", "chosen_path", "rejected_paths",
        "assumptions", "uncertainty", "evidence_links", "risk_flags",
        "second_witness_required", "mayor_review_required",
        "reducer_required", "final_status",
    }
    missing = sorted(expected - set(parsed.keys()))
    if missing:
        warnings.append(f"MISSING_FIELDS:{','.join(missing)}")

    return parsed, warnings


def emit_receipt(epoch: int, total: int, run_id: str, model: str,
                 topic: str, packet_hash: str, art_path: str):
    msg = (
        f"TEMPLE_SESSION epoch={epoch}/{total} run={run_id} "
        f"model={model} topic_hash={sha256_hex(topic)[:12]} "
        f"packet_hash={packet_hash[:12]} artifact={art_path} "
        "AURA+DAN candidate emitted; NO autonomous keep/reject; "
        "halts for operator+MAYOR review"
    )
    proc = subprocess.run(
        [str(VENV_PY), str(HELEN_SAY), msg, "--op", "fetch"],
        capture_output=True,
        text=True,
        timeout=RECEIPT_TIMEOUT_SEC,
    )
    return proc.stdout, proc.stderr, proc.returncode


def run_session(topic: str, epochs: int, model: str):
    run_id = gen_run_id()
    art_dir = SOT / "artifacts" / "temple" / f"aura_dan_session_{run_id}"
    art_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "run_id": run_id,
        "model": model,
        "topic": topic,
        "epochs_planned": epochs,
        "epochs": [],
        "started_at": now_utc(),
        "authority": "NON_SOVEREIGN",
        "canon": "NO_SHIP",
        "autonomous_keep_reject": False,
        "discipline": [
            "per_epoch_receipt_via_helen_say",
            "halt_on_receipt_failure",
            f"hard_cap_{EPOCH_HARD_CAP}_epochs",
            "no_autonomous_filtering",
        ],
    }

    halt_reason = None

    for n in range(1, epochs + 1):
        print(f"[epoch {n}/{epochs}] AURA meditation via {model}...", file=sys.stderr)
        aura_out, aura_err, rc = call_ollama(model, aura_prompt(topic, n, epochs))
        if rc != 0:
            halt_reason = f"AURA ollama failure at epoch {n} rc={rc}: {aura_err[-300:]}"
            print(f"  {halt_reason}", file=sys.stderr)
            break

        print(f"[epoch {n}/{epochs}] DAN packet via {model}...", file=sys.stderr)
        dan_out, dan_err, rc = call_ollama(model, dan_prompt(topic, n, epochs, aura_out))
        if rc != 0:
            halt_reason = f"DAN ollama failure at epoch {n} rc={rc}: {dan_err[-300:]}"
            print(f"  {halt_reason}", file=sys.stderr)
            break

        dan_parsed, dan_warnings = lint_dan_packet(dan_out)

        epoch_artifact = {
            "epoch": n,
            "run_id": run_id,
            "model": model,
            "topic": topic,
            "aura_meditation": aura_out,
            "dan_packet_raw": dan_out,
            "dan_packet_parsed": dan_parsed,
            "dan_lint_warnings": dan_warnings,
            "timestamp_utc": now_utc(),
            "authority": "NON_SOVEREIGN",
            "canon": "NO_SHIP",
        }
        epoch_path = art_dir / f"epoch_{n:03d}.json"
        epoch_path.write_text(json.dumps(epoch_artifact, indent=2, ensure_ascii=False))
        packet_hash = canon_hash(epoch_artifact)

        print(f"[epoch {n}/{epochs}] emit receipt via helen_say...", file=sys.stderr)
        say_out, say_err, say_rc = emit_receipt(
            n, epochs, run_id, model, topic, packet_hash,
            str(epoch_path.relative_to(SOT)),
        )

        epoch_record = {
            "epoch": n,
            "artifact_path": str(epoch_path.relative_to(SOT)),
            "packet_hash": packet_hash,
            "dan_lint_warnings": dan_warnings,
            "receipt_rc": say_rc,
            "receipt_stdout_tail": (say_out or "")[-400:],
        }
        if say_rc != 0:
            epoch_record["receipt_stderr_tail"] = (say_err or "")[-400:]
            summary["epochs"].append(epoch_record)
            halt_reason = (
                f"receipt failure at epoch {n} rc={say_rc} — "
                "NO RECEIPT = NO CLAIM, halting per discipline"
            )
            print(f"  {halt_reason}", file=sys.stderr)
            break

        summary["epochs"].append(epoch_record)

    summary["ended_at"] = now_utc()
    summary["epochs_completed"] = len(summary["epochs"])
    summary["halt_reason"] = halt_reason
    summary["halted_for_operator_review"] = True

    summary_path = art_dir / "session_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print("", file=sys.stderr)
    print("=== SESSION HALT ===", file=sys.stderr)
    print(f"run_id:           {run_id}", file=sys.stderr)
    print(f"epochs completed: {summary['epochs_completed']}/{epochs}", file=sys.stderr)
    print(f"halt_reason:      {halt_reason or 'normal completion'}", file=sys.stderr)
    print(f"artifacts:        {art_dir.relative_to(SOT)}/", file=sys.stderr)
    print(f"summary:          {summary_path.relative_to(SOT)}", file=sys.stderr)
    print("", file=sys.stderr)
    print("NO autonomous keep/reject performed.", file=sys.stderr)
    print("All packets staged for OPERATOR + MAYOR review.", file=sys.stderr)

    return summary


def main():
    ap = argparse.ArgumentParser(
        description="TEMPLE AURA+DAN session runner — non-sovereign, halts at N",
    )
    ap.add_argument("--topic", required=True, help="Meditation seed topic")
    ap.add_argument(
        "--epochs", type=int, default=DEFAULT_EPOCHS,
        help=f"Number of epochs (default {DEFAULT_EPOCHS}, hard cap {EPOCH_HARD_CAP})",
    )
    ap.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Ollama model (default {DEFAULT_MODEL})",
    )
    args = ap.parse_args()

    if args.epochs > EPOCH_HARD_CAP:
        print(f"ERROR: --epochs {args.epochs} > hard cap {EPOCH_HARD_CAP}.", file=sys.stderr)
        print("Larger sessions require an explicit MAYOR ruling.", file=sys.stderr)
        sys.exit(2)
    if args.epochs < 1:
        print("ERROR: --epochs must be >= 1.", file=sys.stderr)
        sys.exit(2)

    summary = run_session(args.topic, args.epochs, args.model)
    print(json.dumps({
        "run_id": summary["run_id"],
        "epochs_completed": summary["epochs_completed"],
        "halt_reason": summary.get("halt_reason"),
        "halted_for_operator_review": summary["halted_for_operator_review"],
    }, indent=2))


if __name__ == "__main__":
    main()
