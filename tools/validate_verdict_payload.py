#!/usr/bin/env python3
"""
validate_verdict_payload.py v1.0.0
Validates VERDICT events in NDJSON ledger against VERDICT_PAYLOAD_V1 schema.

Checks per VERDICT event (type == "verdict"):
  1. payload.schema == "VERDICT_PAYLOAD_V1"
  2. verdict_kind in {PASS, WARN, BLOCK, SHIP, ABORT}
  3. verdict_id present and non-empty
  4. subject: required sub-fields present
  5. decision.outcome in {DELIVER, HOLD, ABORT}
  6. decision.reason_codes: non-empty, sorted, format-valid (^[A-Z0-9_]{3,64}$)
  7. decision.required_fixes: sorted, format-valid (if non-empty)
  8. decision.certificates: sorted, format-valid (if non-empty)
  9. decision.mutations non-empty → outcome in {HOLD, ABORT}
  10. anchors: all required fields present, hex64 fields valid

Design: core validation raises ValueError.  CLI wrapper catches and exits 1.
"""
import sys
import os as _os
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
import json
import re
from kernel.canonical_json import canon_json_bytes

VERDICT_KIND_VALUES = {"PASS", "WARN", "BLOCK", "SHIP", "ABORT"}
OUTCOME_VALUES = {"DELIVER", "HOLD", "ABORT"}
CODE_RE = re.compile(r"^[A-Z0-9_]{3,64}$")
HEX64_RE = re.compile(r"^[a-f0-9]{64}$")

REQUIRED_ANCHOR_FIELDS = [
    "run_id",
    "kernel_hash_hex",
    "policy_hash_hex",
    "ledger_length_at_verdict",
    "ledger_cum_hash_hex",
    "identity_hash_hex",
]
ANCHOR_HEX64_FIELDS = [
    "kernel_hash_hex",
    "policy_hash_hex",
    "ledger_cum_hash_hex",
    "identity_hash_hex",
]


def _validate_code(code: str, path: str) -> None:
    if not CODE_RE.match(code):
        raise ValueError(f"{path}: code '{code}' does not match ^[A-Z0-9_]{{3,64}}$")


def _validate_sorted_codes(arr: list, arr_name: str, seq: int) -> None:
    for code in arr:
        _validate_code(code, f"seq={seq} {arr_name}[]")
    if arr != sorted(arr):
        raise ValueError(
            f"seq={seq} {arr_name} is not lexicographically sorted: {arr}"
        )


def _validate_hex64(val: str, field: str, seq: int) -> None:
    if not HEX64_RE.match(val):
        raise ValueError(
            f"seq={seq} {field}: '{val}' is not a 64-char lowercase hex string"
        )


def validate_verdict_payload(seq: int, payload: dict) -> None:
    """
    Validate a single VERDICT event payload.
    Raises ValueError with a descriptive message on first failure.
    """
    # ── schema discriminator ────────────────────────────────────────────────
    schema = payload.get("schema")
    if schema != "VERDICT_PAYLOAD_V1":
        raise ValueError(
            f"seq={seq} payload.schema must be 'VERDICT_PAYLOAD_V1', got '{schema}'"
        )

    # ── verdict_kind ────────────────────────────────────────────────────────
    vk = payload.get("verdict_kind")
    if vk not in VERDICT_KIND_VALUES:
        raise ValueError(
            f"seq={seq} verdict_kind '{vk}' not in {sorted(VERDICT_KIND_VALUES)}"
        )

    # ── verdict_id ──────────────────────────────────────────────────────────
    vid = payload.get("verdict_id", "")
    if not vid:
        raise ValueError(f"seq={seq} verdict_id is missing or empty")

    # ── subject ─────────────────────────────────────────────────────────────
    subject = payload.get("subject")
    if not isinstance(subject, dict):
        raise ValueError(f"seq={seq} payload.subject must be an object")
    for sf in ("subject_id", "subject_type"):
        if not subject.get(sf):
            raise ValueError(
                f"seq={seq} payload.subject.{sf} is missing or empty"
            )

    # ── decision ────────────────────────────────────────────────────────────
    decision = payload.get("decision")
    if not isinstance(decision, dict):
        raise ValueError(f"seq={seq} payload.decision must be an object")

    outcome = decision.get("outcome")
    if outcome not in OUTCOME_VALUES:
        raise ValueError(
            f"seq={seq} decision.outcome '{outcome}' not in {sorted(OUTCOME_VALUES)}"
        )

    reason_codes = decision.get("reason_codes")
    if not isinstance(reason_codes, list) or len(reason_codes) < 1:
        raise ValueError(
            f"seq={seq} decision.reason_codes must be a non-empty array"
        )
    _validate_sorted_codes(reason_codes, "decision.reason_codes", seq)

    required_fixes = decision.get("required_fixes", [])
    if not isinstance(required_fixes, list):
        raise ValueError(f"seq={seq} decision.required_fixes must be an array")
    if required_fixes:
        _validate_sorted_codes(required_fixes, "decision.required_fixes", seq)

    certificates = decision.get("certificates", [])
    if not isinstance(certificates, list):
        raise ValueError(f"seq={seq} decision.certificates must be an array")
    if certificates:
        _validate_sorted_codes(certificates, "decision.certificates", seq)

    mutations = decision.get("mutations", [])
    if mutations and outcome not in {"HOLD", "ABORT"}:
        raise ValueError(
            f"seq={seq} decision.mutations is non-empty but outcome='{outcome}' "
            "(mutations require outcome HOLD or ABORT)"
        )

    # ── anchors ─────────────────────────────────────────────────────────────
    anchors = payload.get("anchors")
    if not isinstance(anchors, dict):
        raise ValueError(f"seq={seq} payload.anchors must be an object")

    for af in REQUIRED_ANCHOR_FIELDS:
        if af not in anchors:
            raise ValueError(f"seq={seq} anchors.{af} is missing")

    for hf in ANCHOR_HEX64_FIELDS:
        _validate_hex64(anchors[hf], f"anchors.{hf}", seq)

    if not isinstance(anchors.get("ledger_length_at_verdict"), int):
        raise ValueError(
            f"seq={seq} anchors.ledger_length_at_verdict must be an integer"
        )


def main(ledger_path: str) -> None:
    """
    Validate all VERDICT events in the ledger file.
    Exits 1 on first failure, prints [PASS] on success.
    """
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[FAIL] File not found: {ledger_path}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        print("[PASS] Empty ledger (0 VERDICT events to validate)", file=sys.stderr)
        return

    verdict_count = 0
    for line_num, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[FAIL] Line {line_num}: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        event_type = obj.get("type", "").upper()
        if event_type != "VERDICT":
            continue

        seq = obj.get("seq", line_num - 1)
        payload = obj.get("payload", {})

        # Only validate VERDICT_PAYLOAD_V1 events; skip legacy events
        if payload.get("schema") != "VERDICT_PAYLOAD_V1":
            continue

        try:
            validate_verdict_payload(seq, payload)
        except ValueError as e:
            print(f"[FAIL] Line {line_num}: {e}", file=sys.stderr)
            sys.exit(1)

        verdict_count += 1

    print(
        f"[PASS] verdict_payload validated ({verdict_count} VERDICT_PAYLOAD_V1 events)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 validate_verdict_payload.py <ledger.ndjson>",
            file=sys.stderr,
        )
        sys.exit(2)
    main(sys.argv[1])
