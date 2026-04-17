#!/usr/bin/env python3
"""
HELEN K-τ Coherence Linter
===========================
Emits a Tier-I coherence certificate (τ) for any agentic path change.

τ = min(μ_BOUNDARY, μ_IO, μ_DETERMINISM, μ_ALLOWLIST, μ_SCHEMA)
DELIVER iff τ > 0 (or agentic_change = False)
ABORT   iff τ ≤ 0 (with witness j* = argmin μ_j)

Artifacts emitted:
  artifacts/k_tau_manifest.json  — frozen config snapshot
  artifacts/k_tau_trace.ndjson   — per-invariant margin trace
  artifacts/k_tau_summary.json   — τ, witness, counterexample

NO RECEIPT = NO CLAIM.  (Core Law, HELEN / LNSA)
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────────────

INVARIANTS = ["mu_BOUNDARY", "mu_IO", "mu_DETERMINISM", "mu_ALLOWLIST", "mu_SCHEMA"]

DEFAULT_AGENTIC_PATHS = [
    "kernel/",
    "oracle_town/",
    "ORACLEbot/",
    "plugins/",
    "LNSA.py",
    "HELEN.md",
    "HELEN_REACTIVATION_SUMMARY.md",
]

DEFAULT_NON_AGENTIC_PREFIXES = [
    "docs/",
    "paper/",
    "README",
    "CONQUEST_",
    "content/",
    "street1.html",
    "tests/",
]

DEFAULT_FORBID_IMPORT_GLOBS = [
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "boto3",
    "subprocess",
    "socket",
]

DEFAULT_FORBID_TIME_CALLS = [
    "time.time(",
    "datetime.now(",
    "date.today(",
    "perf_counter(",
]

DEFAULT_FORBID_UNSEEDED_RANDOM = [
    "random.random(",
    "random.randint(",
    "np.random",
    "numpy.random",
]

DEFAULT_TOOL_REGISTRY_FILES = [
    "plugins/",
    "oracle_town/core/",
]

DEFAULT_SCHEMA_DIRS = [
    "schemas/",
]

# ─── Utilities ────────────────────────────────────────────────────────────────

def die(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def sh(cmd: List[str]) -> str:
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"command failed: {' '.join(cmd)}")
    return r.stdout


def repo_root() -> Path:
    """Walk up from this script to find repo root (parents[1] from scripts/)."""
    return Path(__file__).resolve().parents[1]


def get_commit() -> str:
    try:
        return sh(["git", "rev-parse", "HEAD"]).strip()
    except Exception:
        return "UNKNOWN-NO-GIT"


def list_changed_files(mode: str, explicit: List[str]) -> List[str]:
    if mode == "manifest_list":
        return [f.strip() for f in explicit if f.strip()]
    # git_diff: try HEAD~1..HEAD first (CI), fallback to working tree
    for cmd in (
        ["git", "diff", "--name-only", "HEAD~1..HEAD"],
        ["git", "diff", "--name-only"],
    ):
        try:
            out = sh(cmd)
            files = [x for x in out.splitlines() if x.strip()]
            if files:
                return files
        except Exception:
            continue
    return []


def is_agentic_change(changed: List[str], agentic_paths: List[str]) -> bool:
    for f in changed:
        for ap in agentic_paths:
            if ap.endswith("/") and f.startswith(ap):
                return True
            if f == ap:
                return True
    return False


def scan_text_file(p: Path, needles: List[str]) -> Optional[str]:
    """Return the first needle found in file, or None."""
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    for n in needles:
        if n in txt:
            return n
    return None


def read_text(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


# ─── Five Invariant Checks ────────────────────────────────────────────────────

def mu_boundary(
    root: Path,
    changed: List[str],
    agentic: bool,
    forbid_imports: List[str],
) -> Tuple[float, List[str], str]:
    """μ_BOUNDARY: kernel/ and oracle_town/core/ must not import external libs."""
    if not agentic:
        return (+1.0, [], "non-agentic change: skipped")

    offenders: List[str] = []
    for f in changed:
        if not (f.startswith("kernel/") or f.startswith("oracle_town/core/")):
            continue
        p = root / f
        if not p.exists() or p.is_dir():
            continue
        needles = (
            [f"import {x}" for x in forbid_imports]
            + [f"from {x} " for x in forbid_imports]
            + [f"from {x}." for x in forbid_imports]
            + [f"require('{x}" for x in forbid_imports]
            + [f'require("{x}' for x in forbid_imports]
        )
        hit = scan_text_file(p, needles)
        if hit:
            offenders.append(f"{f} :: {hit}")

    if offenders:
        detail = "forbidden imports in kernel/oracle_town boundary"
        files = [o.split(" :: ")[0] for o in offenders]
        return (-1.0, files, detail + " | " + "; ".join(offenders[:5]))
    return (+1.0, [], "ok")


def mu_io(
    root: Path,
    changed: List[str],
    agentic: bool,
) -> Tuple[float, List[str], str]:
    """μ_IO: kernel/ writes must mention artifacts/ or receipts/."""
    if not agentic:
        return (+1.0, [], "non-agentic change: skipped")

    offenders: List[str] = []
    write_tokens = ["open(", "write_text(", "write_bytes(", ".write("]
    allowed_roots = ["artifacts/", "receipts/"]

    for f in changed:
        if not f.startswith("kernel/"):
            continue
        p = root / f
        if not p.exists() or p.is_dir():
            continue
        txt = read_text(p)
        if txt is None:
            continue
        has_write = any(tok in txt for tok in write_tokens)
        if has_write:
            has_root = any(root_name in txt for root_name in allowed_roots)
            if not has_root:
                offenders.append(f)

    if offenders:
        return (-1.0, offenders, "kernel IO writes without allowlisted root (artifacts/ or receipts/)")
    return (+1.0, [], "ok")


def mu_determinism(
    root: Path,
    changed: List[str],
    agentic: bool,
) -> Tuple[float, List[str], str]:
    """μ_DETERMINISM: no unseeded randomness or wall-clock time in agentic files."""
    if not agentic:
        return (+1.0, [], "non-agentic change: skipped")

    offenders: List[str] = []
    needles = DEFAULT_FORBID_TIME_CALLS + DEFAULT_FORBID_UNSEEDED_RANDOM

    for f in changed:
        if not (f.endswith(".py") or f.endswith(".js") or f.endswith(".cjs")):
            continue
        p = root / f
        if not p.exists() or p.is_dir():
            continue
        hit = scan_text_file(p, needles)
        if hit:
            offenders.append(f"{f} :: {hit}")

    if offenders:
        files = [o.split(" :: ")[0] for o in offenders]
        return (-1.0, files, "time/unseeded randomness found | " + "; ".join(offenders[:5]))
    return (+1.0, [], "ok")


def mu_allowlist(
    root: Path,
    changed: List[str],
    agentic: bool,
    tool_registry_files: List[str],
) -> Tuple[float, List[str], str]:
    """μ_ALLOWLIST: if plugins/ touched, registry must also be updated."""
    if not agentic:
        return (+1.0, [], "non-agentic change: skipped")

    touched_plugins = any(f.startswith("plugins/") for f in changed)
    if not touched_plugins:
        return (+1.0, [], "ok")

    # Registry updated = at least one tool_registry_file path touched
    registry_touched = any(
        any(f.startswith(t) for t in tool_registry_files) or f in tool_registry_files
        for f in changed
    )
    if registry_touched:
        return (+1.0, [], "ok")

    return (-1.0, ["plugins/"], "plugins changed but no registry file updated — add to tool_registry_files")


def mu_schema(
    root: Path,
    changed: List[str],
    agentic: bool,
) -> Tuple[float, List[str], str]:
    """μ_SCHEMA: all changed .json/.ndjson/.jsonl must parse."""
    offenders: List[str] = []
    for f in changed:
        if not (f.endswith(".json") or f.endswith(".ndjson") or f.endswith(".jsonl")):
            continue
        p = root / f
        if not p.exists() or p.is_dir():
            continue
        try:
            if f.endswith(".ndjson") or f.endswith(".jsonl"):
                for i, line in enumerate(
                    p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1
                ):
                    if not line.strip():
                        continue
                    json.loads(line)
            else:
                json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            offenders.append(f"{f} :: parse error ({e})")

    if offenders:
        files = [o.split(" :: ")[0] for o in offenders]
        return (-1.0, files, "JSON/NDJSON parse failures | " + "; ".join(offenders[:5]))
    return (+1.0, [], "ok")


# ─── IO Helpers ───────────────────────────────────────────────────────────────

def write_ndjson(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="HELEN K-τ linter — emits Tier-I coherence certificate"
    )
    ap.add_argument("--run-id", default="RUN-KTAU-LOCAL", help="Run identifier")
    ap.add_argument(
        "--mode",
        choices=["git_diff", "manifest_list"],
        default="git_diff",
        help="How changed files are detected",
    )
    ap.add_argument(
        "--changed",
        nargs="*",
        default=[],
        help="Explicit file list (use with --mode manifest_list)",
    )
    ap.add_argument(
        "--out-dir",
        default="artifacts",
        help="Directory to write k_tau_* artifacts",
    )
    args = ap.parse_args()

    root = repo_root()
    os.chdir(root)

    # ── Change detection ──────────────────────────────────────────────────────
    changed = list_changed_files(args.mode, args.changed)
    agentic_paths = DEFAULT_AGENTIC_PATHS
    agentic = is_agentic_change(changed, agentic_paths)

    # ── Compute five margins ──────────────────────────────────────────────────
    m: Dict[str, float] = {}
    counter_files: Dict[str, List[str]] = {}
    details: Dict[str, str] = {}

    m["mu_BOUNDARY"], counter_files["mu_BOUNDARY"], details["mu_BOUNDARY"] = mu_boundary(
        root, changed, agentic, DEFAULT_FORBID_IMPORT_GLOBS
    )
    m["mu_IO"], counter_files["mu_IO"], details["mu_IO"] = mu_io(root, changed, agentic)
    m["mu_DETERMINISM"], counter_files["mu_DETERMINISM"], details["mu_DETERMINISM"] = mu_determinism(
        root, changed, agentic
    )
    m["mu_ALLOWLIST"], counter_files["mu_ALLOWLIST"], details["mu_ALLOWLIST"] = mu_allowlist(
        root, changed, agentic, DEFAULT_TOOL_REGISTRY_FILES
    )
    m["mu_SCHEMA"], counter_files["mu_SCHEMA"], details["mu_SCHEMA"] = mu_schema(
        root, changed, agentic
    )

    # ── Strict-min τ and witness j* ───────────────────────────────────────────
    tau = min(m.values()) if m else +1.0
    witness = min(m, key=lambda k: m[k]) if m else "mu_SCHEMA"

    # ── Minimal counterexample slice ──────────────────────────────────────────
    cfiles = counter_files.get(witness, [])
    cdetail = details.get(witness, "n/a")
    if not cfiles and tau <= 0:
        cfiles = changed[:5]
    if not cdetail:
        cdetail = "ok"

    # ── Determine outcome ─────────────────────────────────────────────────────
    # DELIVER if: no agentic change, OR all margins pass (τ > 0)
    outcome = "DELIVER" if (not agentic or tau > 0) else "ABORT"

    # ── Emit artifacts ────────────────────────────────────────────────────────
    out_dir = root / args.out_dir

    manifest = {
        "schema_version": "K_TAU_MANIFEST_V1",
        "run_id": args.run_id,
        "scope": {
            "agentic_paths": agentic_paths,
            "non_agentic_paths": DEFAULT_NON_AGENTIC_PREFIXES,
            "change_detector": args.mode,
        },
        "audit": {"delta_audit": 0.0},
        "environment": {
            "commit": get_commit(),
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
        },
        "invariants": {
            "mu_BOUNDARY": {"forbid_import_globs": DEFAULT_FORBID_IMPORT_GLOBS},
            "mu_IO": {"allow_write_roots": ["artifacts/", "receipts/"]},
            "mu_DETERMINISM": {
                "forbid_time_calls": DEFAULT_FORBID_TIME_CALLS,
                "forbid_unseeded_random": DEFAULT_FORBID_UNSEEDED_RANDOM,
            },
            "mu_ALLOWLIST": {"tool_registry_files": DEFAULT_TOOL_REGISTRY_FILES},
            "mu_SCHEMA": {"schema_dirs": DEFAULT_SCHEMA_DIRS},
        },
    }
    write_json(out_dir / "k_tau_manifest.json", manifest)

    trace = {"t": 0, **m, "tau": tau, "witness": witness}
    trace_path = out_dir / "k_tau_trace.ndjson"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text("", encoding="utf-8")  # overwrite each run
    write_ndjson(trace_path, trace)

    summary = {
        "schema_version": "K_TAU_SUMMARY_V1",
        "run_id": args.run_id,
        "tau": tau,
        "witness_invariant": witness,
        "margins": m,
        "counterexample": {"files": cfiles, "detail": cdetail},
        "agentic_change": agentic,
        "changed_files": changed,
    }
    write_json(out_dir / "k_tau_summary.json", summary)

    # ── HELEN-style receipt line ──────────────────────────────────────────────
    status_str = "PASS ✅" if outcome == "DELIVER" else "FAIL ❌"
    print(f"[K-τ] {status_str} — coherence receipt")
    print(f"  run_id           : {args.run_id}")
    print(f"  agentic_change   : {agentic}")
    print(f"  changed_files    : {len(changed)}")
    print(f"  tau              : {tau:.3f}")
    print(f"  witness_j*       : {witness}")
    print(f"  margins          : " + "  ".join(f"{k}={v:.1f}" for k, v in m.items()))
    print(f"  counterexample   : {cfiles[:5]}")
    print(f"  HELEN outcome    : {outcome}")
    if outcome == "ABORT":
        print(f"  reason_codes     : [ACTIVE_CONSTRAINT={witness}]")
        print(f"  detail           : {cdetail}")
    print()
    print(f"  artifacts/k_tau_manifest.json → written")
    print(f"  artifacts/k_tau_trace.ndjson  → written")
    print(f"  artifacts/k_tau_summary.json  → written")

    sys.exit(0 if outcome == "DELIVER" else 1)


if __name__ == "__main__":
    main()
