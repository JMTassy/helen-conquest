#!/usr/bin/env python3
import json, subprocess, hashlib, os, sys

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1<<20), b""):
            h.update(b)
    return h.hexdigest()

core = [
    "tools/ndjson_writer.py",
    "tools/validate_hash_chain.py",
    "tools/validate_turn_schema.py",
    "tools/test_meta_invariance.py",
    "tools/accept_payload_meta.sh",
    ".github/workflows/payload_meta.yml",
]

present = [p for p in core if os.path.exists(p)]
missing = [p for p in core if not os.path.exists(p)]
hashes = {p: sha256_file(p) for p in present}

def try_cmd(cmd):
    try:
        return sh(cmd + " 2>&1")
    except subprocess.CalledProcessError as e:
        return (e.output or "").strip() or f"[FAIL] {cmd}"

data = {
    "head_sha": sh("git rev-parse HEAD"),
    "python_version": sh("python3 -V"),
    "core_files_present": present,
    "core_files_missing": missing,
    "sha256": hashes,
    "acceptance_gate_stdout": try_cmd("bash tools/accept_payload_meta.sh town/ledger.ndjson"),
    "hash_chain_stdout": try_cmd("python3 tools/validate_hash_chain.py town/ledger.ndjson"),
    "schema_stdout": try_cmd("python3 tools/validate_turn_schema.py town/ledger.ndjson"),
    "meta_invariance_stdout": try_cmd("python3 tools/test_meta_invariance.py"),
}

out = "PROOF_BUNDLE_PAYLOAD_META.json"
with open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")

print(f"[OK] wrote {out}")
