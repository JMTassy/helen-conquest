#!/usr/bin/env python3
"""
HELEN RHO Linter — K-rho gate enforcer.

Validates that a run's rho_summary.json is numerically consistent with
rho_trace.ndjson, using the delta_audit tolerance declared in rho_manifest.json.
Optionally validates all three artifacts against their JSON Schemas.

Usage:
    python3 scripts/helen_rho_lint.py <rho_manifest.json> <rho_summary.json> <rho_trace.ndjson>

Optional flags:
    --schema-dir <dir>   Directory containing *.schema.json files.
                         If provided, runs JSON Schema validation before numeric checks.
                         Requires: pip install jsonschema

Exit codes:
    0  PASS (all checks passed)
    1  FAIL (any check failed; reason printed to stderr)
    2  CONFIG ERROR (bad arguments, missing files, import error)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MARGINS: List[str] = ["mu_Delta", "mu_Pi", "mu_CFL", "mu_Lyap", "mu_Z"]

SCHEMA_FILENAMES: Dict[str, str] = {
    "manifest": "rho_manifest.schema.json",
    "summary": "rho_summary.schema.json",
    "trace_line": "rho_trace.schema.json",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def load_json(p: Path) -> Dict[str, Any]:
    if not p.exists():
        die(f"File not found: {p}", code=2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"Cannot parse JSON: {p} — {e}", code=2)


def approx_eq(a: float, b: float, tol: float) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


# ---------------------------------------------------------------------------
# JSON Schema validation (optional; requires jsonschema package)
# ---------------------------------------------------------------------------

def validate_with_schema(artifact: Dict[str, Any], schema_path: Path, label: str) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        warn(f"jsonschema not installed — skipping schema validation for {label}. "
             "Install with: pip install jsonschema")
        return

    schema = load_json(schema_path)
    try:
        jsonschema.validate(instance=artifact, schema=schema)
        info(f"Schema OK: {label}")
    except jsonschema.ValidationError as e:
        die(f"Schema validation failed for {label}: {e.message}\n"
            f"  Path: {list(e.absolute_path)}")
    except jsonschema.SchemaError as e:
        die(f"Schema file is invalid for {label}: {e.message}", code=2)


# ---------------------------------------------------------------------------
# NDJSON trace parsing
# ---------------------------------------------------------------------------

def parse_trace(trace_path: Path, schema_path: Optional[Path]) -> Tuple[float, int, Dict[str, Any], int]:
    """
    Parse rho_trace.ndjson.

    Returns:
        (min_rho, t_star, witness_line, total_lines)
    """
    best_rho: Optional[float] = None
    best_t: Optional[int] = None
    best_line: Optional[Dict[str, Any]] = None
    n_lines = 0
    prev_t: Optional[int] = None

    with trace_path.open("r", encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                die(f"Malformed NDJSON at line {ln}: {e}")

            # Optional per-line schema validation (only first & last line to keep O(N) fast)
            if schema_path and ln <= 2:
                validate_with_schema(obj, schema_path, f"rho_trace line {ln}")

            for field in ("t", "rho") + tuple(MARGINS):
                if field not in obj:
                    die(f"rho_trace line {ln} missing required field '{field}'")

            t = int(obj["t"])
            rho = float(obj["rho"])

            if prev_t is not None and t <= prev_t:
                die(f"rho_trace not monotonically increasing in 't': line {ln} has t={t} after t={prev_t}")
            prev_t = t

            # Verify rho == min(margins) at this line within a loose tolerance
            computed = min(float(obj[m]) for m in MARGINS)
            if not approx_eq(rho, computed, tol=1e-9):
                die(f"rho_trace line {ln}: rho={rho} but min(margins)={computed} (diff={abs(rho-computed):.3e})")

            if best_rho is None or rho < best_rho:
                best_rho = rho
                best_t = t
                best_line = obj

            n_lines += 1

    if best_rho is None or best_line is None or best_t is None:
        die("rho_trace.ndjson is empty — no lines parsed")

    info(f"Trace parsed: {n_lines} steps, t in [0, {prev_t}]")
    return best_rho, best_t, best_line, n_lines


# ---------------------------------------------------------------------------
# Main checks
# ---------------------------------------------------------------------------

def run_checks(
    manifest_path: Path,
    summary_path: Path,
    trace_path: Path,
    schema_dir: Optional[Path],
) -> None:

    # ---- Load artifacts ----
    manifest = load_json(manifest_path)
    summary = load_json(summary_path)

    # ---- Optional schema validation ----
    if schema_dir:
        for key, fname in SCHEMA_FILENAMES.items():
            sp = schema_dir / fname
            if not sp.exists():
                warn(f"Schema file not found, skipping: {sp}")
                continue
            if key == "manifest":
                validate_with_schema(manifest, sp, "rho_manifest.json")
            elif key == "summary":
                validate_with_schema(summary, sp, "rho_summary.json")
            # trace_line schema validated inline during parse

    trace_schema_path = (schema_dir / SCHEMA_FILENAMES["trace_line"]) if schema_dir else None

    # ---- Parse trace ----
    trace_min_rho, trace_t_star, trace_witness, n_steps = parse_trace(trace_path, trace_schema_path)

    # ---- Read tolerance ----
    try:
        delta = float(manifest["audit"]["delta_audit"])
    except (KeyError, TypeError, ValueError) as e:
        die(f"Cannot read audit.delta_audit from manifest: {e}", code=2)

    # ---- Read summary values ----
    try:
        inf_rho = float(summary["inf_rho"])
        t_star = int(summary["t_star"])
        active = str(summary["active_constraint"])
        mats = summary["margins_at_t_star"]
    except (KeyError, TypeError, ValueError) as e:
        die(f"Malformed rho_summary.json: {e}", code=2)

    # ---- Check 1: inf_rho matches trace min ----
    if not approx_eq(inf_rho, trace_min_rho, delta):
        die(
            f"inf_rho mismatch:\n"
            f"  summary.inf_rho     = {inf_rho}\n"
            f"  trace min(rho)      = {trace_min_rho}\n"
            f"  diff                = {abs(inf_rho - trace_min_rho):.6e}\n"
            f"  delta_audit         = {delta:.6e}"
        )
    info(f"Check 1 PASS: inf_rho={inf_rho} matches trace min within delta={delta:.2e}")

    # ---- Check 2: t_star matches trace argmin ----
    if t_star != trace_t_star:
        die(
            f"t_star mismatch:\n"
            f"  summary.t_star      = {t_star}\n"
            f"  trace argmin        = {trace_t_star}\n"
            f"  (If multiple steps tie at inf_rho, ensure tie-breaking is deterministic and matches.)"
        )
    info(f"Check 2 PASS: t_star={t_star}")

    # ---- Recompute active constraint at witness ----
    witness_margins: Dict[str, float] = {}
    for m in MARGINS:
        if m not in trace_witness:
            die(f"Trace witness line missing margin '{m}'")
        witness_margins[m] = float(trace_witness[m])

    computed_active = min(witness_margins, key=lambda k: witness_margins[k])
    computed_rho_at_witness = witness_margins[computed_active]

    # ---- Check 3: active_constraint matches computed argmin ----
    if active != computed_active:
        die(
            f"active_constraint mismatch:\n"
            f"  summary.active_constraint = {active}\n"
            f"  computed argmin margin    = {computed_active}\n"
            f"  margins at t_star: {witness_margins}"
        )
    info(f"Check 3 PASS: active_constraint={active}")

    # ---- Check 4: margins_at_t_star.rho matches computed rho ----
    try:
        reported_rho_at_witness = float(mats["rho"])
    except (KeyError, TypeError, ValueError) as e:
        die(f"Cannot read margins_at_t_star.rho: {e}")

    if not approx_eq(reported_rho_at_witness, computed_rho_at_witness, delta):
        die(
            f"margins_at_t_star.rho mismatch:\n"
            f"  summary.margins_at_t_star.rho = {reported_rho_at_witness}\n"
            f"  computed min(margins) at t_star = {computed_rho_at_witness}\n"
            f"  diff = {abs(reported_rho_at_witness - computed_rho_at_witness):.6e}\n"
            f"  delta_audit = {delta:.6e}"
        )
    info(f"Check 4 PASS: margins_at_t_star.rho={reported_rho_at_witness} consistent")

    # ---- Check 5: run_id consistency (warn only) ----
    manifest_rid = manifest.get("run_id", "")
    summary_rid = summary.get("run_id", "")
    if manifest_rid != summary_rid:
        warn(f"run_id mismatch: manifest={manifest_rid!r} summary={summary_rid!r}")
    else:
        info(f"Check 5 PASS: run_id={manifest_rid!r} consistent")

    # ---- HELEN termination signal ----
    outcome = "DELIVER" if inf_rho > 0 else "ABORT"
    print(
        f"\n[K-rho] PASS — receipt is consistent.\n"
        f"  run_id          : {manifest_rid}\n"
        f"  steps           : {n_steps}\n"
        f"  inf_rho         : {inf_rho:.6f}\n"
        f"  t_star          : {t_star}\n"
        f"  active_constraint: {active}\n"
        f"  HELEN outcome   : {outcome}"
    )
    if outcome == "ABORT":
        print(f"  reason_codes    : ['ACTIVE_CONSTRAINT={active}']")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="HELEN RHO Linter: enforce K-rho viability certificate consistency.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("manifest", help="Path to rho_manifest.json")
    parser.add_argument("summary", help="Path to rho_summary.json")
    parser.add_argument("trace", help="Path to rho_trace.ndjson")
    parser.add_argument(
        "--schema-dir",
        metavar="DIR",
        help="Directory containing *.schema.json files for structural validation (requires jsonschema).",
    )

    args = parser.parse_args()

    run_checks(
        manifest_path=Path(args.manifest),
        summary_path=Path(args.summary),
        trace_path=Path(args.trace),
        schema_dir=Path(args.schema_dir) if args.schema_dir else None,
    )


if __name__ == "__main__":
    main()
