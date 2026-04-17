#!/usr/bin/env python3
"""
Generate deterministic audit manifest for Oracle Town artifacts.

Makes "which evidence was reviewed" auditable and replayable.
Output: receipts/oracle_town_audit_manifest.json with SHA256 hashes.

Usage:
  python3 scripts/make_audit_manifest.py --run runA [--output receipts/manifest.json]

The manifest includes:
  - All decision records (decision_record.json from each run)
  - All evidence files (policy.json, hashes.json, ledger.json)
  - All Bibliothèque submissions (if present)
  - Canonical JSON hash for replayability

This makes "audit happened" machine-verifiable.
"""

import json
import hashlib
import os
import sys
import time
from pathlib import Path
from datetime import datetime


def sha256_bytes(b: bytes) -> str:
    """Compute SHA256 of raw bytes."""
    return hashlib.sha256(b).hexdigest()


def collect_run_artifacts(run_path: Path) -> dict:
    """Collect all artifacts from a single run."""
    artifacts = {}

    # Core decision artifacts
    for filename in ["decision_record.json", "policy.json", "hashes.json", "ledger.json", "briefcase.json"]:
        filepath = run_path / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                raw = f.read()
            artifacts[f"run/{filename}"] = {
                "path": str(filepath),
                "size_bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "mtime_epoch": int(filepath.stat().st_mtime),
            }

    return artifacts


def collect_bibliotheque_artifacts(bibliotheque_dir: Path) -> dict:
    """Collect all Bibliothèque knowledge base submissions."""
    artifacts = {}

    if not bibliotheque_dir.exists():
        return artifacts

    # Walk through each type (math_proofs, code_archive, research, data, etc.)
    for type_dir in bibliotheque_dir.iterdir():
        if not type_dir.is_dir():
            continue

        # For each item in type_dir
        for item_dir in type_dir.iterdir():
            if not item_dir.is_dir():
                continue

            # Collect metadata.json and digest.sha256
            for filename in ["metadata.json", "digest.sha256", "parsed.json"]:
                filepath = item_dir / filename
                if filepath.exists():
                    with open(filepath, "rb") as f:
                        raw = f.read()

                    key = f"bibliotheque/{type_dir.name}/{item_dir.name}/{filename}"
                    artifacts[key] = {
                        "path": str(filepath),
                        "size_bytes": len(raw),
                        "sha256": sha256_bytes(raw),
                        "mtime_epoch": int(filepath.stat().st_mtime),
                    }

    return artifacts


def collect_evidence_artifacts() -> dict:
    """Collect evidence validation report."""
    artifacts = {}

    evidence_file = Path("ORACLE_TOWN_EMULATION_EVIDENCE.md")
    if evidence_file.exists():
        with open(evidence_file, "rb") as f:
            raw = f.read()
        artifacts["evidence/ORACLE_TOWN_EMULATION_EVIDENCE.md"] = {
            "path": str(evidence_file),
            "size_bytes": len(raw),
            "sha256": sha256_bytes(raw),
            "mtime_epoch": int(evidence_file.stat().st_mtime),
        }

    return artifacts


def generate_manifest(run_name: str = None, output_path: str = None) -> dict:
    """Generate comprehensive audit manifest."""
    root = Path.cwd()

    if output_path is None:
        output_path = "receipts/oracle_town_audit_manifest.json"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Collect artifacts
    artifacts = {}

    # If specific run requested, collect from that run
    if run_name:
        run_path = root / "oracle_town" / "runs" / run_name
        if run_path.exists():
            artifacts.update(collect_run_artifacts(run_path))
        else:
            print(f"Warning: run {run_name} not found", file=sys.stderr)
    else:
        # Collect from all runs
        runs_dir = root / "oracle_town" / "runs"
        if runs_dir.exists():
            for run_dir in sorted(runs_dir.iterdir()):
                if run_dir.is_dir():
                    artifacts.update(collect_run_artifacts(run_dir))

    # Always collect evidence and Bibliothèque
    artifacts.update(collect_evidence_artifacts())

    bibliotheque_dir = root / "oracle_town" / "memory" / "bibliotheque"
    artifacts.update(collect_bibliotheque_artifacts(bibliotheque_dir))

    # Deterministically order
    sorted_items = []
    for key in sorted(artifacts.keys()):
        item = artifacts[key]
        sorted_items.append({
            "id": key,
            **item
        })

    # Create manifest
    manifest = {
        "schema_version": "oracle_town_audit_manifest_v1",
        "generated_at_epoch": int(time.time()),
        "generated_at_iso": datetime.utcnow().isoformat() + "Z",
        "run_filter": run_name or "all_runs",
        "items_count": len(sorted_items),
        "items": sorted_items,
    }

    # Canonical manifest hash
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = sha256_bytes(canonical)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    return manifest


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate deterministic audit manifest for Oracle Town"
    )
    parser.add_argument("--run", default=None, help="Specific run to audit (default: all runs)")
    parser.add_argument("--output", default="receipts/oracle_town_audit_manifest.json",
                       help="Output manifest path")

    args = parser.parse_args()

    try:
        manifest = generate_manifest(run_name=args.run, output_path=args.output)

        print(f"✅ Manifest generated: {args.output}")
        print(f"   Artifacts audited: {manifest['items_count']}")
        print(f"   Manifest SHA256: {manifest['manifest_sha256']}")
        print()
        print("To verify manifest integrity:")
        print(f"  python3 scripts/verify_audit_manifest.py {args.output}")

        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
