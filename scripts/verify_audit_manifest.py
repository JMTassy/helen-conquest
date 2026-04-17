#!/usr/bin/env python3
"""
Verify integrity of Oracle Town audit manifest.

Checks:
  1. Manifest SHA256 is correct (canonical JSON hash)
  2. Each artifact's SHA256 matches actual file bytes
  3. No artifacts are missing
  4. Manifest structure is valid

Usage:
  python3 scripts/verify_audit_manifest.py receipts/oracle_town_audit_manifest.json

Exit codes:
  0 = all checks pass
  1 = integrity failed (artifact modified, missing, or hash mismatch)
"""

import json
import hashlib
import sys
from pathlib import Path


def sha256_bytes(b: bytes) -> str:
    """Compute SHA256 of raw bytes."""
    return hashlib.sha256(b).hexdigest()


def verify_manifest(manifest_path: str) -> bool:
    """Verify manifest integrity."""
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return False

    # Load manifest
    with open(manifest_file, "rb") as f:
        manifest_bytes = f.read()

    manifest = json.loads(manifest_bytes)

    print(f"Oracle Town Audit Manifest Verification")
    print(f"========================================")
    print(f"Manifest: {manifest_path}")
    print(f"Generated: {manifest.get('generated_at_iso', 'unknown')}")
    print(f"Run filter: {manifest.get('run_filter', 'all_runs')}")
    print(f"Artifacts: {manifest.get('items_count', 0)}")
    print()

    # Check schema version
    if manifest.get("schema_version") != "oracle_town_audit_manifest_v1":
        print(f"❌ Invalid schema version: {manifest.get('schema_version')}")
        return False

    # Verify manifest hash
    recorded_hash = manifest.get("manifest_sha256")
    if not recorded_hash:
        print("❌ Manifest hash not found")
        return False

    # Reconstruct canonical JSON (excluding manifest_sha256 field)
    manifest_copy = dict(manifest)
    del manifest_copy["manifest_sha256"]
    canonical = json.dumps(manifest_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed_hash = sha256_bytes(canonical)

    if computed_hash != recorded_hash:
        print(f"❌ Manifest hash mismatch!")
        print(f"   Expected: {recorded_hash}")
        print(f"   Got:      {computed_hash}")
        return False

    print(f"✅ Manifest hash verified")
    print(f"   SHA256: {recorded_hash[:16]}...")
    print()

    # Verify each artifact
    print(f"Verifying {len(manifest.get('items', []))} artifacts...")
    print()

    all_ok = True
    missing_count = 0
    mismatch_count = 0

    for item in manifest.get("items", []):
        artifact_id = item.get("id", "unknown")
        artifact_path = item.get("path", "unknown")
        recorded_hash = item.get("sha256", "")

        path = Path(artifact_path)

        if not path.exists():
            print(f"❌ MISSING: {artifact_id}")
            print(f"   Path: {artifact_path}")
            missing_count += 1
            all_ok = False
        else:
            with open(path, "rb") as f:
                actual_bytes = f.read()
            actual_hash = sha256_bytes(actual_bytes)

            if actual_hash != recorded_hash:
                print(f"❌ MODIFIED: {artifact_id}")
                print(f"   Expected: {recorded_hash[:16]}...")
                print(f"   Got:      {actual_hash[:16]}...")
                mismatch_count += 1
                all_ok = False
            else:
                print(f"✅ {artifact_id}")

    print()
    print("=" * 60)

    if all_ok:
        print(f"✅ MANIFEST INTEGRITY VERIFIED")
        print(f"   {len(manifest.get('items', []))} artifacts checked")
        print(f"   All hashes match")
        return True
    else:
        print(f"❌ MANIFEST INTEGRITY FAILED")
        if missing_count:
            print(f"   Missing: {missing_count} artifacts")
        if mismatch_count:
            print(f"   Modified: {mismatch_count} artifacts")
        return False


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/verify_audit_manifest.py <manifest_path>")
        print()
        print("Example:")
        print("  python3 scripts/verify_audit_manifest.py receipts/oracle_town_audit_manifest.json")
        return 1

    manifest_path = sys.argv[1]

    if verify_manifest(manifest_path):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
