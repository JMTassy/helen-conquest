#!/usr/bin/env python3
"""
golden_loop_test.py

Deterministic end-to-end "Golden Loop" demo:
  claim.json -> (ENGINEERING + LEGAL attestations) -> mayor_input.json -> decision_record.json

Core invariant honored:
  NO RECEIPT = NO CLAIM
  (Mayor only upgrades from receipts / hash-bound artifacts)

This script is repo-first and self-contained:
- writes artifacts under: artifacts/runs/<RUN-ID>/
- uses canonical JSON + sha256 binding
- optionally validates JSON with jsonschema (if installed)
- includes minimal "receipt" stubs for WUL + (optional) K-ρ

Usage:
  python tools/golden_loop_test.py --run-id RUN-20260221-0001
  python tools/golden_loop_test.py --run-id RUN-... --requires-k-rho
  python tools/golden_loop_test.py --run-id RUN-... --fail-legal
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -------------------------
# Canonical JSON + hashing
# -------------------------


def canonical_dumps(obj: Any) -> str:
    """
    Deterministic JSON:
      - sorted keys
      - compact separators
      - UTF-8
      - forbids NaN/Infinity (Python doesn't emit them unless allow_nan=True)
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_canonical_json(obj: Any) -> str:
    return sha256_bytes(canonical_dumps(obj).encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_dumps(obj) + "\n", encoding="utf-8")


# -------------------------
# Minimal schemas (optional)
# -------------------------

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "oracle_town.claim.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema", "claim_id", "text", "claim_class", "requires"],
        "properties": {
            "schema": {"const": "oracle_town.claim.v1"},
            "claim_id": {"type": "string"},
            "text": {"type": "string"},
            "claim_class": {"type": "string"},
            "requires": {
                "type": "object",
                "required": ["k_rho", "wul"],
                "properties": {
                    "k_rho": {"type": "boolean"},
                    "wul": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
        "additionalProperties": True,
    },
    "oracle_town.district_attestation.v2": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema",
            "district",
            "attestation_id",
            "claim_id",
            "verdict",
            "reason_codes",
            "artifacts",
            "receipt_refs",
        ],
        "properties": {
            "schema": {"const": "oracle_town.district_attestation.v2"},
            "district": {"type": "string"},
            "attestation_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "verdict": {"enum": ["PASS", "FAIL", "ABSTAIN"]},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
            "artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["path", "sha256", "artifact_type"],
                    "properties": {
                        "path": {"type": "string"},
                        "sha256": {"type": "string"},
                        "artifact_type": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            "receipt_refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["path", "sha256"],
                    "properties": {
                        "path": {"type": "string"},
                        "sha256": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "additionalProperties": True,
    },
    "oracle_town.mayor_input.v2": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema", "run_id", "claim", "attestations", "policy"],
        "properties": {
            "schema": {"const": "oracle_town.mayor_input.v2"},
            "run_id": {"type": "string"},
            "claim": {"type": "object"},
            "attestations": {"type": "array"},
            "policy": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "oracle_town.decision_record.v2": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema",
            "run_id",
            "claim_id",
            "decision",
            "reason_codes",
            "active_constraint",
            "inputs",
            "bound_artifacts",
            "decision_sha256",
        ],
        "properties": {
            "schema": {"const": "oracle_town.decision_record.v2"},
            "run_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "decision": {"enum": ["DELIVER", "ABORT"]},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
            "active_constraint": {"type": "string"},
            "inputs": {"type": "object"},
            "bound_artifacts": {"type": "array"},
            "decision_sha256": {"type": "string"},
        },
        "additionalProperties": True,
    },
    # WUL slab minimal
    "helen.wul_slab.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema", "banners", "tags", "power", "content"],
        "properties": {
            "schema": {"const": "helen.wul_slab.v1"},
            "banners": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "power": {"type": "string"},
            "content": {"type": "string"},
        },
        "additionalProperties": True,
    },
    # Receipt stub (very small; you can replace with your receipt.schema.json later)
    "helen.receipt_stub.v1": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema", "plugin_id", "passed", "artifacts", "sha256"],
        "properties": {
            "schema": {"const": "helen.receipt_stub.v1"},
            "plugin_id": {"type": "string"},
            "passed": {"type": "boolean"},
            "artifacts": {"type": "array"},
            "sha256": {"type": "string"},
            "details": {"type": "object"},
        },
        "additionalProperties": True,
    },
}


def try_validate(schema_name: str, obj: Any) -> List[str]:
    """Return list of validation errors (empty means valid). If jsonschema missing, returns []."""
    try:
        import jsonschema  # type: ignore
    except Exception:
        return []

    schema = SCHEMAS[schema_name]
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted((e.message for e in validator.iter_errors(obj)), key=str)
    return errs


# -------------------------
# Paths + artifact binding
# -------------------------


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str
    artifact_type: str


def bind_file(path: Path, artifact_type: str) -> ArtifactRef:
    return ArtifactRef(
        path=str(path.as_posix()), sha256=sha256_file(path), artifact_type=artifact_type
    )


# -------------------------
# Receipts (stubbed)
# -------------------------


def make_receipt_stub(
    plugin_id: str,
    passed: bool,
    artifacts: List[ArtifactRef],
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = {
        "schema": "helen.receipt_stub.v1",
        "plugin_id": plugin_id,
        "passed": bool(passed),
        "artifacts": [
            {
                "path": a.path,
                "sha256": a.sha256,
                "artifact_type": a.artifact_type,
            }
            for a in artifacts
        ],
        "details": details or {},
    }
    obj["sha256"] = sha256_canonical_json(
        {k: v for k, v in obj.items() if k != "sha256"}
    )
    return obj


# -------------------------
# WUL lint (minimal)
# -------------------------


def wul_lint(slab: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    banners = slab.get("banners", [])
    tags = slab.get("tags", [])
    power = slab.get("power", None)

    if banners.count("WUL") < 2:
        issues.append("WUL_BANNER_MISSING_OR_NOT_DUPLICATED")
    if "NO_RECEIPT_NO_CLAIM" not in tags:
        issues.append("WUL_MISSING_TAG:NO_RECEIPT_NO_CLAIM")
    if power not in ("0", "NONE"):
        issues.append("WUL_POWER_NOT_ZERO")

    return (len(issues) == 0, issues)


# -------------------------
# Mayor predicate (pure)
# -------------------------


def mayor_decide(mayor_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic decision predicate:
      - ABORT if any district verdict == FAIL
      - If claim.requires.wul == true: require WUL_LINT receipt passed
      - If claim.requires.k_rho == true: require RHO_LINT receipt passed AND inf_rho>0 in receipt details
    """
    run_id = mayor_input["run_id"]
    claim = mayor_input["claim"]
    claim_id = claim["claim_id"]
    requires = claim.get("requires", {"wul": False, "k_rho": False})

    reason_codes: List[str] = []
    active_constraint = "NONE"

    # district failures
    for att in mayor_input["attestations"]:
        if att.get("verdict") == "FAIL":
            reason_codes.append("DISTRICT_FAIL:" + att.get("district", "UNKNOWN"))
            # preserve district reason codes as additional structure
            for rc in att.get("reason_codes", []):
                reason_codes.append("DISTRICT_REASON:" + str(rc))

    # helper: find receipt by plugin_id
    def find_receipt(plugin_id: str) -> Optional[Dict[str, Any]]:
        for r in mayor_input.get("receipts", []):
            if r.get("plugin_id") == plugin_id:
                return r
        return None

    # WUL gate
    if requires.get("wul", False):
        r = find_receipt("plugin.wul_lint")
        if not r:
            reason_codes.append("NO_WUL_RECEIPT")
        elif not r.get("passed", False):
            reason_codes.append("WUL_LINT_FAIL")

    # K-ρ gate
    if requires.get("k_rho", False):
        r = find_receipt("plugin.rho_lint")
        if not r:
            reason_codes.append("NO_RHO_RECEIPT")
        else:
            if not r.get("passed", False):
                reason_codes.append("RHO_LINT_FAIL")
            else:
                inf_rho = float(r.get("details", {}).get("inf_rho", -1.0))
                if not (inf_rho > 0.0):
                    reason_codes.append("INF_RHO_NONPOSITIVE")
                    active_constraint = str(
                        r.get("details", {}).get("active_constraint", "UNKNOWN")
                    )

    decision = "DELIVER" if len(reason_codes) == 0 else "ABORT"

    decision_record = {
        "schema": "oracle_town.decision_record.v2",
        "run_id": run_id,
        "claim_id": claim_id,
        "decision": decision,
        "reason_codes": reason_codes,
        "active_constraint": active_constraint,
        "inputs": {
            "mayor_input_sha256": sha256_canonical_json(mayor_input),
        },
        "bound_artifacts": [
            # mayor binds the referenced artifacts by hash
            {"path": a["path"], "sha256": a["sha256"]}
            for a in mayor_input.get("bound_artifacts", [])
        ],
    }
    decision_record["decision_sha256"] = sha256_canonical_json(
        {k: v for k, v in decision_record.items() if k != "decision_sha256"}
    )
    return decision_record


# -------------------------
# Golden Loop builder
# -------------------------


def build_and_run(
    run_id: str,
    requires_k_rho: bool,
    fail_legal: bool,
    fail_engineering: bool,
    out_root: Path,
) -> None:
    run_dir = out_root / run_id
    inputs_dir = run_dir / "inputs"
    districts_dir = run_dir / "districts"
    mayor_dir = run_dir / "mayor"
    outputs_dir = run_dir / "outputs"
    receipts_dir = run_dir / "receipts"
    artifacts_dir = run_dir / "artifacts"

    for d in [inputs_dir, districts_dir, mayor_dir, outputs_dir, receipts_dir, artifacts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1) claim
    claim = {
        "schema": "oracle_town.claim.v1",
        "claim_id": "C-GL-0001",
        "text": "Demonstrate Golden Loop: claim -> districts -> mayor -> decision_record.",
        "claim_class": "PLANNING" if not requires_k_rho else "VIABILITY",
        "requires": {"k_rho": bool(requires_k_rho), "wul": True},
    }
    claim_path = inputs_dir / "claim.json"
    write_json(claim_path, claim)
    _assert_valid("oracle_town.claim.v1", claim)

    # 2) WUL slab (normative context; not "facts")
    slab = {
        "schema": "helen.wul_slab.v1",
        "banners": ["WUL", "WUL"],
        "tags": ["PLANNING", "NON_SOVEREIGN", "NO_RECEIPT_NO_CLAIM"],
        "power": "0",
        "content": (
            "📜 golden loop demo slab\n"
            "NO RECEIPT = NO CLAIM\n"
            "districts may propose; mayor decides as pure function of attestations\n"
        ),
    }
    slab_path = artifacts_dir / "golden_loop_v1.slab.json"
    write_json(slab_path, slab)
    _assert_valid("helen.wul_slab.v1", slab)

    wul_passed, wul_issues = wul_lint(slab)

    # 3) receipts: wul_lint + hash (stubbed)
    slab_ref = bind_file(slab_path, "wul_slab")
    wul_receipt = make_receipt_stub(
        plugin_id="plugin.wul_lint",
        passed=wul_passed,
        artifacts=[slab_ref],
        details={"issues": wul_issues},
    )
    wul_receipt_path = receipts_dir / "plugin.wul_lint.receipt.json"
    write_json(wul_receipt_path, wul_receipt)
    _assert_valid("helen.receipt_stub.v1", wul_receipt)

    # Optional: rho receipt (stubbed, deterministic)
    rho_receipt = None
    rho_receipt_path = None
    if requires_k_rho:
        # A tiny deterministic witness: choose PASS/FAIL by toggles
        # Here we PASS by default with inf_rho=0.1; you can flip to show ABORT.
        rho_details = {
            "inf_rho": 0.1,
            "t_star": 0,
            "active_constraint": "mu_Z",
        }
        rho_receipt = make_receipt_stub(
            plugin_id="plugin.rho_lint",
            passed=True,
            artifacts=[slab_ref],  # in real runs you'd bind rho_summary + rho_trace + rho receipts
            details=rho_details,
        )
        rho_receipt_path = receipts_dir / "plugin.rho_lint.receipt.json"
        write_json(rho_receipt_path, rho_receipt)
        _assert_valid("helen.receipt_stub.v1", rho_receipt)

    # 4) district attestations (hash-bound references)
    # ENGINEERING
    eng_artifacts = [
        {
            "path": str(slab_path.as_posix()),
            "sha256": slab_ref.sha256,
            "artifact_type": "wul_slab",
        },
    ]
    eng_receipts = [
        {
            "path": str(wul_receipt_path.as_posix()),
            "sha256": sha256_file(wul_receipt_path),
        },
    ]
    if requires_k_rho and rho_receipt_path:
        eng_receipts.append(
            {
                "path": str(rho_receipt_path.as_posix()),
                "sha256": sha256_file(rho_receipt_path),
            }
        )

    eng_att = {
        "schema": "oracle_town.district_attestation.v2",
        "district": "ENGINEERING",
        "attestation_id": "A-ENG-GL-0001",
        "claim_id": claim["claim_id"],
        "verdict": "FAIL" if fail_engineering else "PASS",
        "reason_codes": (
            ["PLAN_FEASIBLE_WITH_DEPENDENCIES"]
            if not fail_engineering
            else ["ENGINEERING_BLOCKED"]
        ),
        "artifacts": eng_artifacts,
        "receipt_refs": eng_receipts,
    }
    eng_att["attestation_sha256"] = sha256_canonical_json(
        {k: v for k, v in eng_att.items() if k != "attestation_sha256"}
    )
    eng_path = districts_dir / "engineering.attestation.json"
    write_json(eng_path, eng_att)
    _assert_valid("oracle_town.district_attestation.v2", eng_att)

    # LEGAL
    leg_artifacts = [
        {
            "path": str(slab_path.as_posix()),
            "sha256": slab_ref.sha256,
            "artifact_type": "wul_slab",
        },
    ]
    leg_receipts = [
        {
            "path": str(wul_receipt_path.as_posix()),
            "sha256": sha256_file(wul_receipt_path),
        },
    ]
    leg_att = {
        "schema": "oracle_town.district_attestation.v2",
        "district": "LEGAL",
        "attestation_id": "A-LEG-GL-0001",
        "claim_id": claim["claim_id"],
        "verdict": "FAIL" if fail_legal else "PASS",
        "reason_codes": (
            ["NO_MISLEADING_PREDICTIONS"]
            if not fail_legal
            else ["LEGAL_BLOCKED"]
        ),
        "artifacts": leg_artifacts,
        "receipt_refs": leg_receipts,
    }
    leg_att["attestation_sha256"] = sha256_canonical_json(
        {k: v for k, v in leg_att.items() if k != "attestation_sha256"}
    )
    leg_path = districts_dir / "legal.attestation.json"
    write_json(leg_path, leg_att)
    _assert_valid("oracle_town.district_attestation.v2", leg_att)

    # 5) compile mayor_input.json (single input contract)
    mayor_input = {
        "schema": "oracle_town.mayor_input.v2",
        "run_id": run_id,
        "claim": claim,
        "attestations": [eng_att, leg_att],
        "policy": {
            "mode": "DELIVER_OR_ABORT",
            "termination_policy_ref": "termination_policy.json (demo-inline)",
        },
        # In V2, Mayor only upgrades from receipts, never from prose.
        "receipts": [wul_receipt] + ([rho_receipt] if rho_receipt else []),
        "bound_artifacts": [
            {"path": str(claim_path.as_posix()), "sha256": sha256_file(claim_path)},
            {"path": str(slab_path.as_posix()), "sha256": slab_ref.sha256},
            {"path": str(eng_path.as_posix()), "sha256": sha256_file(eng_path)},
            {"path": str(leg_path.as_posix()), "sha256": sha256_file(leg_path)},
            {
                "path": str(wul_receipt_path.as_posix()),
                "sha256": sha256_file(wul_receipt_path),
            },
        ]
        + (
            [
                {
                    "path": str(rho_receipt_path.as_posix()),
                    "sha256": sha256_file(rho_receipt_path),
                }
            ]
            if rho_receipt_path
            else []
        ),
    }
    mayor_input_path = mayor_dir / "mayor_input.json"
    write_json(mayor_input_path, mayor_input)
    _assert_valid("oracle_town.mayor_input.v2", mayor_input)

    # 6) mayor decision
    decision_record = mayor_decide(mayor_input)
    decision_path = outputs_dir / "decision_record.json"
    write_json(decision_path, decision_record)
    _assert_valid("oracle_town.decision_record.v2", decision_record)

    # 7) print summary
    print("GOLDEN LOOP COMPLETE")
    print(f"run_dir: {run_dir.as_posix()}")
    print(f"decision: {decision_record['decision']}")
    if decision_record["reason_codes"]:
        print("reasons:")
        for r in decision_record["reason_codes"]:
            print(" -", r)
    print("outputs:")
    print(" -", decision_path.as_posix())
    print("hashes:")
    print(" - mayor_input_sha256:", decision_record["inputs"]["mayor_input_sha256"])
    print(" - decision_sha256   :", decision_record["decision_sha256"])


def _assert_valid(schema_name: str, obj: Any) -> None:
    errs = try_validate(schema_name, obj)
    if errs:
        raise SystemExit(
            f"SCHEMA_VALIDATION_FAIL ({schema_name}):\n - " + "\n - ".join(errs)
        )


# -------------------------
# CLI
# -------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--out-root",
        default="artifacts/runs",
        help="root folder for run artifacts",
    )
    ap.add_argument(
        "--requires-k-rho",
        action="store_true",
        help="force K-ρ gate in Mayor predicate",
    )
    ap.add_argument(
        "--fail-legal",
        action="store_true",
        help="make LEGAL district fail",
    )
    ap.add_argument(
        "--fail-engineering",
        action="store_true",
        help="make ENGINEERING district fail",
    )
    args = ap.parse_args()

    build_and_run(
        run_id=args.run_id,
        requires_k_rho=args.requires_k_rho,
        fail_legal=args.fail_legal,
        fail_engineering=args.fail_engineering,
        out_root=Path(args.out_root),
    )


if __name__ == "__main__":
    main()
