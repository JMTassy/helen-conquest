"""
helen_os/eval/servitors.py — T0–T5 servitor evaluation runners.

Each servitor runs a focused set of checks and returns a TownReportV1.
Servitors are stateless functions — they receive their inputs explicitly.

T0 — Integrity   : kernel.verify_ledger() + cum_hash sanity
T1 — Manifest    : artifact files exist + valid JSON + artifact_sha256 present
T2 — Replay      : determinism: same payload sequence → same cum_hash × 3
T3 — Partition   : eval/ module has no forbidden domain-specific imports
T4 — Rollback    : sealed kernel raises PermissionError (no rollback possible)
T5 — Claim       : CLAIM_GRAPH_V1 source_digest stable × 3 runs

All servitors are non-sovereign (no kernel.propose() calls).
Kernel access: T2 and T4 create ephemeral :memory: kernels for isolation checks.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import ServitorCheckV1, TownReportV1, aggregate_verdict


# ── T0 — Integrity ────────────────────────────────────────────────────────────

def run_t0_integrity(kernel) -> TownReportV1:
    """
    T0 — Integrity Servitor.

    Checks:
      T0.1: kernel.verify_ledger() is True
      T0.2: cum_hash is exactly 64 hex characters
      T0.3: cum_hash is non-trivial (not all zeros)

    Args:
        kernel: GovernanceVM instance that has processed at least one receipt.
    """
    checks: List[ServitorCheckV1] = []
    run_at = datetime.now(timezone.utc).isoformat()

    # T0.1 — ledger integrity
    ledger_ok = kernel.verify_ledger()
    checks.append(ServitorCheckV1(
        check_id    = "T0.1",
        description = "kernel.verify_ledger() is True",
        verdict     = "PASS" if ledger_ok else "BLOCK",
        detail      = f"verify_ledger()={ledger_ok}",
    ))

    # T0.2 — cum_hash length
    h = kernel.cum_hash
    is_64 = len(h) == 64
    checks.append(ServitorCheckV1(
        check_id    = "T0.2",
        description = "cum_hash is 64 hex characters",
        verdict     = "PASS" if is_64 else "BLOCK",
        detail      = f"len(cum_hash)={len(h)}",
    ))

    # T0.3 — cum_hash non-trivial
    non_zero = h != "0" * 64
    checks.append(ServitorCheckV1(
        check_id    = "T0.3",
        description = "cum_hash is non-trivial (not all zeros)",
        verdict     = "PASS" if non_zero else "BLOCK",
        detail      = f"cum_hash[:8]={h[:8]}",
    ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T0",
        servitor_name = "Integrity",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )


# ── T1 — Manifest ─────────────────────────────────────────────────────────────

def run_t1_manifest(
    artifacts_path: str,
    required_files: List[str],
) -> TownReportV1:
    """
    T1 — Manifest Servitor.

    For each file in required_files:
      - Check file exists
      - Check file is valid JSON
      - Check 'artifact_sha256' field is present (WARN if missing)

    Args:
        artifacts_path: Directory containing artifact JSON files.
        required_files: List of filenames to check (relative to artifacts_path).
    """
    checks: List[ServitorCheckV1] = []
    run_at = datetime.now(timezone.utc).isoformat()
    base   = Path(artifacts_path)

    if not required_files:
        checks.append(ServitorCheckV1(
            check_id    = "T1.empty",
            description = "required_files must be non-empty",
            verdict     = "WARN",
            detail      = "required_files list is empty — nothing to manifest",
        ))
    else:
        for fname in required_files:
            fpath = base / fname

            # Existence check
            if not fpath.exists():
                checks.append(ServitorCheckV1(
                    check_id    = f"T1.{fname}",
                    description = f"{fname} exists on disk",
                    verdict     = "BLOCK",
                    detail      = f"File not found: {fpath}",
                ))
                continue

            # JSON parse + field check
            try:
                content = fpath.read_text(encoding="utf-8")
                data    = json.loads(content)
                has_sha = "artifact_sha256" in data
                checks.append(ServitorCheckV1(
                    check_id    = f"T1.{fname}",
                    description = f"{fname} valid JSON + artifact_sha256 present",
                    verdict     = "PASS" if has_sha else "WARN",
                    detail      = f"artifact_sha256 present: {has_sha}, keys={list(data.keys())[:4]}",
                ))
            except json.JSONDecodeError as e:
                checks.append(ServitorCheckV1(
                    check_id    = f"T1.{fname}",
                    description = f"{fname} valid JSON",
                    verdict     = "BLOCK",
                    detail      = f"JSONDecodeError: {e}",
                ))
            except Exception as e:
                checks.append(ServitorCheckV1(
                    check_id    = f"T1.{fname}",
                    description = f"{fname} readable",
                    verdict     = "BLOCK",
                    detail      = f"Error: {e}",
                ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T1",
        servitor_name = "Manifest",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )


# ── T2 — Replay ───────────────────────────────────────────────────────────────

def run_t2_replay(payload_sequence: List[Dict[str, Any]]) -> TownReportV1:
    """
    T2 — Replay Servitor.

    Checks determinism: three independent GovernanceVM(:memory:) instances
    replaying the same payload sequence must produce identical cum_hashes.

    Checks:
      T2.1: cum_hash identical across 3 independent replays
      T2.2: cum_hash is non-trivial (receipts were processed)

    Args:
        payload_sequence: Ordered list of payload dicts to propose.
    """
    from ..kernel import GovernanceVM

    checks: List[ServitorCheckV1] = []
    run_at = datetime.now(timezone.utc).isoformat()

    hashes: List[str] = []
    for run_idx in range(3):
        km = GovernanceVM(ledger_path=":memory:")
        for payload in payload_sequence:
            km.propose(payload)
        hashes.append(km.cum_hash)

    # T2.1 — determinism
    all_same = len(set(hashes)) == 1
    checks.append(ServitorCheckV1(
        check_id    = "T2.1",
        description = "Three independent replays produce identical cum_hash",
        verdict     = "PASS" if all_same else "BLOCK",
        detail      = (
            f"h0={hashes[0][:8]}, h1={hashes[1][:8]}, h2={hashes[2][:8]}"
            if len(hashes) == 3 else f"hashes={hashes}"
        ),
    ))

    # T2.2 — non-trivial
    non_zero = bool(hashes) and hashes[0] != "0" * 64
    checks.append(ServitorCheckV1(
        check_id    = "T2.2",
        description = "Replay cum_hash is non-trivial (not all-zeros)",
        verdict     = "PASS" if non_zero else "BLOCK",
        detail      = f"cum_hash[:8]={hashes[0][:8] if hashes else 'N/A'}",
    ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T2",
        servitor_name = "Replay",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )


# ── T3 — Partition ────────────────────────────────────────────────────────────

#: Regex matching import lines that reference forbidden domain-specific or
#: ARGUMENT_SIM_V1 residue modules.
#:
#: Design: scans only `from …` / `import …` lines (not string literals or
#: comments) so that servitors.py itself — which names these modules in
#: docstrings and comments — does not trigger a false positive.
#:
#: Forbidden modules:
#:   claim_node     — ARGUMENT_SIM_V1 old typed node dataclass
#:   hal_dialogue   — ARGUMENT_SIM_V1 old dialogue runner
#:   run_claim_graph— ARGUMENT_SIM_V1 old canonical scripted debate
#:   decision_rule  — ARGUMENT_SIM_V1 old DR2 verdict engine
#:   districts      — CONQUEST domain-specific
#:   conquest       — CONQUEST game domain
#:   serpent        — SERPENT game domain
#:   streets        — STREETS domain
#:   weather        — WEATHER domain
#:   wulmoji        — WULMOJI domain
_PARTITION_IMPORT_RE = re.compile(
    r"^(?:from|import)\s+[^\n]*"
    r"\b(?:claim_node|hal_dialogue|run_claim_graph|decision_rule"
    r"|districts|conquest|serpent|streets|weather|wulmoji)\b",
    re.MULTILINE,
)


def run_t3_partition(eval_path: str) -> TownReportV1:
    """
    T3 — Partition Servitor.

    Scans all .py files in eval_path for forbidden *import* statements.
    Only `from …` / `import …` lines are matched — not comments, docstrings,
    or list literals — so the forbidden-module names may appear as string
    literals inside servitors.py without triggering false positives.

    The eval/ module must be isolated from domain-specific and
    ARGUMENT_SIM_V1 residue modules.

    Checks:
      T3.boundary: No forbidden import statements in eval/ source files

    Args:
        eval_path: Path to the eval/ module directory.
    """
    checks: List[ServitorCheckV1] = []
    run_at  = datetime.now(timezone.utc).isoformat()
    violations: List[str] = []

    eval_dir = Path(eval_path)
    if not eval_dir.exists():
        checks.append(ServitorCheckV1(
            check_id    = "T3.dir_missing",
            description = f"eval/ directory exists at {eval_path!r}",
            verdict     = "BLOCK",
            detail      = f"Directory not found: {eval_path}",
        ))
        return TownReportV1(
            servitor_id   = "T3",
            servitor_name = "Partition",
            verdict       = "BLOCK",
            checks        = checks,
            run_at        = run_at,
        )

    py_files = sorted(eval_dir.glob("*.py"))
    scanned  = 0

    for fpath in py_files:
        if fpath.name.startswith("__"):
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            scanned += 1
            matches = _PARTITION_IMPORT_RE.findall(content)
            for match in matches:
                violations.append(f"{fpath.name}::{match.strip()}")
        except Exception as e:
            checks.append(ServitorCheckV1(
                check_id    = f"T3.read.{fpath.name}",
                description = f"Read {fpath.name}",
                verdict     = "WARN",
                detail      = str(e),
            ))

    if violations:
        for viol in violations:
            # viol = "filename.py::import line"
            parts = viol.split("::", 1)
            fname = parts[0]
            line  = parts[1] if len(parts) > 1 else viol
            checks.append(ServitorCheckV1(
                check_id    = f"T3.viol.{fname}",
                description = f"{fname} has forbidden import",
                verdict     = "BLOCK",
                detail      = f"Forbidden import in {fname!r}: {line!r}",
            ))
    else:
        checks.append(ServitorCheckV1(
            check_id    = "T3.boundary",
            description = "eval/ module boundary — no forbidden import statements",
            verdict     = "PASS",
            detail      = f"Scanned {scanned} file(s) in {eval_path!r}: clean",
        ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T3",
        servitor_name = "Partition",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )


# ── T4 — Rollback ─────────────────────────────────────────────────────────────

def run_t4_rollback() -> TownReportV1:
    """
    T4 — Rollback Servitor.

    Verifies that a SEALED GovernanceVM rejects further proposals with
    PermissionError (the SEALED invariant cannot be rolled back).

    Checks:
      T4.1: Proposing to a sealed kernel raises PermissionError
      T4.2: The kernel's cum_hash is non-trivial after the pre-seal receipt

    Protocol:
      1. Create :memory: kernel
      2. Propose one pre-seal receipt
      3. Propose SEAL
      4. Attempt post-seal propose → must raise PermissionError
    """
    from ..kernel import GovernanceVM

    checks: List[ServitorCheckV1] = []
    run_at = datetime.now(timezone.utc).isoformat()

    km = GovernanceVM(ledger_path=":memory:")

    # Step 1: Pre-seal receipt
    km.propose({"type": "FED_EVAL_ROLLBACK_PROBE_V1", "step": "pre_seal"})
    pre_seal_hash = km.cum_hash

    # Step 2: Seal
    km.propose({"type": "SEAL", "reason": "T4 Rollback Servitor seal test"})

    # Step 3: Post-seal attempt — must raise PermissionError
    blocked = False
    try:
        km.propose({"type": "POST_SEAL_ATTEMPT_V1", "step": "should_block"})
    except PermissionError:
        blocked = True

    # T4.1 — post-seal blocked
    checks.append(ServitorCheckV1(
        check_id    = "T4.1",
        description = "Post-seal propose() raises PermissionError (SEALED invariant)",
        verdict     = "PASS" if blocked else "BLOCK",
        detail      = f"PermissionError raised: {blocked}",
    ))

    # T4.2 — pre-seal hash was non-trivial
    non_zero = pre_seal_hash != "0" * 64 and len(pre_seal_hash) == 64
    checks.append(ServitorCheckV1(
        check_id    = "T4.2",
        description = "Pre-seal cum_hash is non-trivial (receipts were processed)",
        verdict     = "PASS" if non_zero else "BLOCK",
        detail      = f"pre_seal_hash[:8]={pre_seal_hash[:8]}",
    ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T4",
        servitor_name = "Rollback",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )


# ── T5 — Claim ────────────────────────────────────────────────────────────────

def run_t5_claim(fixture_path: str) -> TownReportV1:
    """
    T5 — Claim Servitor.

    Verifies CLAIM_GRAPH_V1 pipeline integrity:
      T5.1: source_digest == sha256(fixture_text) and is stable across 3 runs
      T5.2: G-set is stable across 3 independent runs (same nodes each time)

    Args:
        fixture_path: Path to the structured dialogue fixture file.
    """
    from ..epoch4        import run_epoch4
    from ..claim_graph.canon import sha256_text

    checks: List[ServitorCheckV1] = []
    run_at = datetime.now(timezone.utc).isoformat()

    # Load fixture
    try:
        fixture_text    = Path(fixture_path).read_text(encoding="utf-8")
        expected_digest = sha256_text(fixture_text)
    except Exception as e:
        checks.append(ServitorCheckV1(
            check_id    = "T5.fixture_load",
            description = f"Load fixture from {fixture_path!r}",
            verdict     = "BLOCK",
            detail      = str(e),
        ))
        return TownReportV1(
            servitor_id   = "T5",
            servitor_name = "Claim",
            verdict       = "BLOCK",
            checks        = checks,
            run_at        = run_at,
        )

    # Run pipeline 3 times
    digests: List[str] = []
    g_sets:  List[List[str]] = []
    try:
        for _ in range(3):
            result = run_epoch4(fixture_text)
            digests.append(result.graph.source_digest or "")
            g_sets.append(sorted(result.graph.g_set))
    except Exception as e:
        checks.append(ServitorCheckV1(
            check_id    = "T5.pipeline_error",
            description = "run_epoch4() completed without error",
            verdict     = "BLOCK",
            detail      = str(e),
        ))
        return TownReportV1(
            servitor_id   = "T5",
            servitor_name = "Claim",
            verdict       = "BLOCK",
            checks        = checks,
            run_at        = run_at,
        )

    # T5.1 — source_digest stable and matches sha256(fixture_text)
    stable_and_correct = (
        len(set(digests)) == 1
        and digests[0] == expected_digest
    )
    checks.append(ServitorCheckV1(
        check_id    = "T5.1",
        description = "source_digest stable × 3 runs == sha256(fixture_text)",
        verdict     = "PASS" if stable_and_correct else "BLOCK",
        detail      = (
            f"expected={expected_digest[:8]}, "
            f"got={digests[0][:8] if digests else 'N/A'}, "
            f"unique_count={len(set(digests))}"
        ),
    ))

    # T5.2 — G-set stable across 3 runs
    g_set_stable = len({tuple(g) for g in g_sets}) == 1
    checks.append(ServitorCheckV1(
        check_id    = "T5.2",
        description = "G-set stable × 3 independent runs",
        verdict     = "PASS" if g_set_stable else "BLOCK",
        detail      = f"g_set[0]={g_sets[0] if g_sets else []}",
    ))

    overall = aggregate_verdict([c.verdict for c in checks])
    return TownReportV1(
        servitor_id   = "T5",
        servitor_name = "Claim",
        verdict       = overall,
        checks        = checks,
        run_at        = run_at,
    )
