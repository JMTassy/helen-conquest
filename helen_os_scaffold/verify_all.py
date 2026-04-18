#!/usr/bin/env python3
"""
verify_all.py — One-command validator for all HELEN OS receipt schemas + linkages.

Checks:
  V1  — AUTHZ_RECEIPT_V1 structure (Pydantic round-trip)
  V2  — CROSS_RECEIPT_V1 structure (Pydantic round-trip)
  V3  — Canonical law objects (ProposedLawV1) — law_hash stability
  V4  — validate_authz_binding (valid pair passes, mismatched pair fails)
  V5  — validate_cross_receipt_allowlist (source in allowlist passes; absent fails)
  V6  — validate_receipt_linkage (combined check — L-AUTHZ + L-CROSS + L-BUNDLE + L-NOSELF)
  V7  — Kernel isolation scan (no GovernanceVM import in eval/ or meta/)
  V8  — JSON Schema files are valid JSON and contain required $schema/$id fields

Usage:
    python verify_all.py
    python verify_all.py --verbose

Returns:
    Exit code 0 if all checks pass.
    Exit code 1 if any check fails.

Non-sovereign: this script is a read-only audit tool. It does not write to any
ledger, modify any receipt, or claim authority. Output is diagnostic only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, List, Tuple


# ── Result helpers ─────────────────────────────────────────────────────────────

PASS  = "PASS"
FAIL  = "FAIL"
SKIP  = "SKIP"

Results: List[Tuple[str, str, str]] = []   # (check_id, status, note)

def record(check_id: str, status: str, note: str, verbose: bool = False) -> None:
    Results.append((check_id, status, note))
    mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "–"}.get(status, "?")
    if verbose or status != PASS:
        print(f"  {mark} [{check_id}] {note}")
    elif status == PASS:
        print(f"  {mark} [{check_id}] {note[:80]}")


def run_check(check_id: str, fn: Callable[[], Tuple[str, str]], verbose: bool) -> None:
    """Run a check function → (status, note). Catch unexpected exceptions."""
    try:
        status, note = fn()
    except Exception as exc:
        status, note = FAIL, f"Unexpected exception: {type(exc).__name__}: {exc}"
    record(check_id, status, note, verbose)


# ── Fake hex hashes ────────────────────────────────────────────────────────────

def _fake_hash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


# ── V1 — AUTHZ_RECEIPT_V1 Pydantic round-trip ─────────────────────────────────

def check_v1_authz_roundtrip() -> Tuple[str, str]:
    from helen_os.meta.authz_receipt import AuthzReceiptV1, AuthzReceiptRef

    vh = _fake_hash("verdict_payload_v1")
    vid = f"V-{vh[:8]}"

    authz = AuthzReceiptV1(
        rid       = "R-verify01",
        refs      = AuthzReceiptRef(verdict_id=vid, verdict_hash_hex=vh),
        authorizes = {"field": "ReducedConclusion.helen_proposal_used", "value": True},
        reason_codes = ["CANYON_AUTHORIZED"],
    )

    # Round-trip through dict
    d = authz.model_dump()
    authz2 = AuthzReceiptV1(**d)

    if authz.rid != authz2.rid:
        return FAIL, f"Round-trip mismatch: rid {authz.rid!r} vs {authz2.rid!r}"
    if authz.refs.verdict_hash_hex != authz2.refs.verdict_hash_hex:
        return FAIL, "Round-trip mismatch: verdict_hash_hex"

    # Structural hard rules
    try:
        AuthzReceiptV1(
            rid       = "R-bad01",
            refs      = AuthzReceiptRef(verdict_id=vid, verdict_hash_hex=vh),
            authorizes = {"field": "WRONG_FIELD", "value": True},
            reason_codes = ["CANYON_AUTHORIZED"],
        )
        return FAIL, "Expected ValidationError for wrong authorizes.field — none raised"
    except Exception:
        pass  # expected

    return PASS, f"AUTHZ_RECEIPT_V1 round-trip + hard-rules check passed (rid={authz.rid!r})"


# ── V2 — CROSS_RECEIPT_V1 Pydantic round-trip ─────────────────────────────────

def check_v2_cross_roundtrip() -> Tuple[str, str]:
    from helen_os.meta.cross_receipt_v1 import CrossReceiptV1

    tip  = _fake_hash("ledger_tip_A")
    bndl = _fake_hash("bundle_artifact_A")

    cr = CrossReceiptV1(
        rid             = "CR-verify01",
        source_town_id  = "TOWN_A",
        target_town_id  = "TOWN_B",
        ledger_tip_hash = tip,
        bundle_hash     = bndl,
        status          = "PENDING",
    )

    d   = cr.model_dump()
    cr2 = CrossReceiptV1(**d)

    if cr.bundle_hash != cr2.bundle_hash:
        return FAIL, "Round-trip mismatch: bundle_hash"

    # Self-federation must fail
    try:
        CrossReceiptV1(
            rid             = "CR-self01",
            source_town_id  = "TOWN_A",
            target_town_id  = "TOWN_A",
            ledger_tip_hash = tip,
            bundle_hash     = bndl,
        )
        return FAIL, "Expected ValidationError for self-federation — none raised"
    except Exception:
        pass

    # Bad rid prefix must fail
    try:
        CrossReceiptV1(
            rid             = "R-notcr",
            source_town_id  = "TOWN_A",
            target_town_id  = "TOWN_B",
            ledger_tip_hash = tip,
            bundle_hash     = bndl,
        )
        return FAIL, "Expected ValidationError for bad rid prefix — none raised"
    except Exception:
        pass

    return PASS, f"CROSS_RECEIPT_V1 round-trip + hard-rules check passed (rid={cr.rid!r})"


# ── V3 — Canonical law objects law_hash stability ─────────────────────────────

def check_v3_law_hash_stability() -> Tuple[str, str]:
    from helen_os.meta.proposed_law import (
        CANYON_NONINTERFERENCE_V1,
        HELEN_PROPOSAL_USE_RECEIPT_GATE_V1,
    )

    h1a = CANYON_NONINTERFERENCE_V1.law_hash()
    h1b = CANYON_NONINTERFERENCE_V1.law_hash()
    h2a = HELEN_PROPOSAL_USE_RECEIPT_GATE_V1.law_hash()
    h2b = HELEN_PROPOSAL_USE_RECEIPT_GATE_V1.law_hash()

    if h1a != h1b:
        return FAIL, "CANYON_NONINTERFERENCE_V1.law_hash() is not stable across calls"
    if h2a != h2b:
        return FAIL, "HELEN_PROPOSAL_USE_RECEIPT_GATE_V1.law_hash() is not stable"
    if h1a == h2a:
        return FAIL, "Two canonical laws have identical law_hash — expected distinct"

    return PASS, (
        f"Both canonical laws have stable distinct hashes: "
        f"CANYON={h1a[:16]}... GATE={h2a[:16]}..."
    )


# ── V4 — validate_authz_binding (valid → pass, mismatch → fail) ───────────────

def check_v4_authz_binding() -> Tuple[str, str]:
    from helen_os.meta.authz_receipt import (
        AuthzReceiptV1, AuthzReceiptRef,
        validate_authz_binding, AuthzBindingError,
    )

    vh  = _fake_hash("v4_verdict")
    vid = f"V-{vh[:8]}"

    authz = AuthzReceiptV1(
        rid          = "R-v4-valid",
        refs         = AuthzReceiptRef(verdict_id=vid, verdict_hash_hex=vh),
        authorizes   = {"field": "ReducedConclusion.helen_proposal_used", "value": True},
        reason_codes = ["CANYON_AUTHORIZED"],
    )

    # Valid binding
    try:
        validate_authz_binding(authz, vid, vh)
    except AuthzBindingError as exc:
        return FAIL, f"Valid binding raised AuthzBindingError unexpectedly: {exc}"

    # Wrong hash → must fail
    wrong_vh = _fake_hash("v4_wrong_hash")
    try:
        validate_authz_binding(authz, vid, wrong_vh)
        return FAIL, "Mismatched verdict_hash_hex did not raise AuthzBindingError"
    except AuthzBindingError:
        pass  # expected

    return PASS, "validate_authz_binding: valid passes, mismatch raises AuthzBindingError"


# ── V5 — validate_cross_receipt_allowlist (in → pass, absent → fail) ──────────

def check_v5_cross_allowlist() -> Tuple[str, str]:
    from helen_os.meta.cross_receipt_v1 import (
        CrossReceiptV1,
        validate_cross_receipt_allowlist,
        CrossReceiptBindingError,
    )

    tip  = _fake_hash("v5_tip")
    bndl = _fake_hash("v5_bundle")
    cr   = CrossReceiptV1(
        rid             = "CR-v5-01",
        source_town_id  = "TOWN_X",
        target_town_id  = "TOWN_Y",
        ledger_tip_hash = tip,
        bundle_hash     = bndl,
    )

    # Source in allowlist → pass
    try:
        validate_cross_receipt_allowlist(cr, ["TOWN_X", "TOWN_Z"])
    except CrossReceiptBindingError as exc:
        return FAIL, f"Valid allowlist raised CrossReceiptBindingError: {exc}"

    # Source not in allowlist → fail
    try:
        validate_cross_receipt_allowlist(cr, ["TOWN_Z"])
        return FAIL, "Source not in allowlist did not raise CrossReceiptBindingError"
    except CrossReceiptBindingError:
        pass

    # Empty allowlist → fail
    try:
        validate_cross_receipt_allowlist(cr, [])
        return FAIL, "Empty allowlist did not raise CrossReceiptBindingError"
    except CrossReceiptBindingError:
        pass

    return PASS, "validate_cross_receipt_allowlist: in-allowlist passes, absent/empty fails"


# ── V6 — validate_receipt_linkage combined check ──────────────────────────────

def check_v6_receipt_linkage() -> Tuple[str, str]:
    from helen_os.meta.authz_receipt import AuthzReceiptV1, AuthzReceiptRef
    from helen_os.meta.cross_receipt_v1 import CrossReceiptV1
    from helen_os.town.validate import validate_receipt_linkage

    vh  = _fake_hash("v6_verdict")
    vid = f"V-{vh[:8]}"
    tip = _fake_hash("v6_tip")
    bnd = _fake_hash("v6_bundle")

    authz = AuthzReceiptV1(
        rid          = "R-v6-01",
        refs         = AuthzReceiptRef(verdict_id=vid, verdict_hash_hex=vh),
        authorizes   = {"field": "ReducedConclusion.helen_proposal_used", "value": True},
        reason_codes = ["CANYON_AUTHORIZED"],
    )
    cr = CrossReceiptV1(
        rid             = "CR-v6-01",
        source_town_id  = "TOWN_A",
        target_town_id  = "TOWN_B",
        ledger_tip_hash = tip,
        bundle_hash     = bnd,
    )

    # All pass
    report = validate_receipt_linkage(
        authz_receipt    = authz,
        cross_receipt    = cr,
        allowlist        = ["TOWN_A"],
        verdict_id       = vid,
        verdict_hash_hex = vh,
    )
    if not report.all_pass:
        return FAIL, f"Expected all_pass=True, got errors: {report.errors}"

    # Cross + wrong allowlist → L-CROSS fails
    report2 = validate_receipt_linkage(
        cross_receipt = cr,
        allowlist     = ["TOWN_Z"],
    )
    if report2.all_pass:
        return FAIL, "Expected all_pass=False when source not in allowlist"

    return PASS, "validate_receipt_linkage: all-pass scenario + partial-fail scenario OK"


# ── V7 — Kernel isolation scan ────────────────────────────────────────────────

def check_v7_kernel_isolation() -> Tuple[str, str]:
    """Scan eval/ and meta/ for GovernanceVM imports (module-level)."""
    scaffold_dir = Path(__file__).parent
    forbidden_dirs = [
        scaffold_dir / "helen_os" / "eval",
        scaffold_dir / "helen_os" / "meta",
    ]

    violations = []
    pattern = re.compile(r"^\s*(from\s+helen_os\.kernel|import\s+helen_os\.kernel)", re.MULTILINE)

    for d in forbidden_dirs:
        if not d.exists():
            continue
        for py_file in sorted(d.glob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            if pattern.search(src):
                violations.append(str(py_file.relative_to(scaffold_dir)))

    if violations:
        return FAIL, (
            f"Kernel isolation violation — module-level GovernanceVM import found in: "
            + ", ".join(violations)
        )
    return PASS, "Kernel isolation: no module-level GovernanceVM imports in eval/ or meta/"


# ── V8 — JSON Schema files are valid JSON with $schema + $id ──────────────────

def check_v8_json_schemas() -> Tuple[str, str]:
    """
    Validate all .schema.json files in schemas/:
    - Must be valid JSON.
    - Must contain '$schema'.
    - draft-2020-12 schemas must also contain '$id'
      (draft-07 schemas pre-date the $id requirement — they are exempt).
    """
    scaffold_dir = Path(__file__).parent
    schema_dir   = scaffold_dir / "schemas"

    if not schema_dir.exists():
        return SKIP, "schemas/ directory not found"

    schema_files = sorted(schema_dir.glob("*.schema.json"))
    if not schema_files:
        return SKIP, "No .schema.json files in schemas/"

    DRAFT_2020_PREFIX = "https://json-schema.org/draft/2020-12"

    errors  = []
    details = []
    for f in schema_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{f.name}: invalid JSON — {exc}")
            continue

        schema_uri = data.get("$schema", "")
        if not schema_uri:
            errors.append(f"{f.name}: missing '$schema' field")
            continue

        # Only draft-2020-12 schemas are expected to have $id
        if schema_uri.startswith(DRAFT_2020_PREFIX) and "$id" not in data:
            errors.append(f"{f.name}: draft-2020-12 schema missing '$id' field")

        details.append(f.name)

    if errors:
        return FAIL, "JSON Schema issues: " + "; ".join(errors)

    return PASS, (
        f"All {len(schema_files)} schema files valid "
        f"($schema present, $id checked for draft-2020-12): "
        + ", ".join(details)
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="verify_all.py — HELEN OS receipt validator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all check details")
    args = parser.parse_args()

    verbose = args.verbose

    print("\n" + "═" * 60)
    print("  HELEN OS — verify_all.py (non-sovereign audit tool)")
    print("═" * 60)

    checks = [
        ("V1", "AUTHZ_RECEIPT_V1 round-trip + hard rules",          check_v1_authz_roundtrip),
        ("V2", "CROSS_RECEIPT_V1 round-trip + hard rules",          check_v2_cross_roundtrip),
        ("V3", "Canonical law objects law_hash stability",           check_v3_law_hash_stability),
        ("V4", "validate_authz_binding (valid/mismatch)",            check_v4_authz_binding),
        ("V5", "validate_cross_receipt_allowlist (in/absent/empty)", check_v5_cross_allowlist),
        ("V6", "validate_receipt_linkage (combined)",                check_v6_receipt_linkage),
        ("V7", "Kernel isolation scan (eval/ + meta/)",              check_v7_kernel_isolation),
        ("V8", "JSON Schema files ($schema + $id validity)",         check_v8_json_schemas),
    ]

    for check_id, description, fn in checks:
        print(f"\n[{check_id}] {description}")
        run_check(check_id, fn, verbose)

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = sum(1 for _, s, _ in Results if s == PASS)
    failed = sum(1 for _, s, _ in Results if s == FAIL)
    skipped = sum(1 for _, s, _ in Results if s == SKIP)
    total  = len(Results)

    print("\n" + "═" * 60)
    print(f"  RESULT: {passed}/{total} passed  |  {failed} failed  |  {skipped} skipped")

    if failed == 0:
        print("  STATUS: ALL PASS ✓  (non-sovereign audit complete)")
        print("═" * 60 + "\n")
        return 0
    else:
        print(f"  STATUS: FAIL ✗  ({failed} check(s) failed)")
        print("  Failures:")
        for cid, s, note in Results:
            if s == FAIL:
                print(f"    ✗ [{cid}] {note[:120]}")
        print("═" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
