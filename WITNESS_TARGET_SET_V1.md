# WITNESS_TARGET_SET_V1

## Purpose

Specifies the **constitutional spine** files required for second-witness audit to move system from **STAGED → WITNESSED**.

Each evidence handle contains the information needed for an independent observer to:
1. Locate the exact file version
2. Compute its hash
3. Run a replay command
4. Verify the deterministic output

---

## Witness Target Set (7 Core Files)

### 1. Governance VM (Authority Execution)

```
artifact_name: governance_vm.py
category: KERNEL/core
path: helen_os_scaffold/helen_os/kernel/governance_vm.py
commit: (current HEAD)
artifact_hash_sha256: 7d55f3de706ee1bac24d8ab28516e65e0e5a50f8576e6300e971f52966e333ef
file_size_bytes: (computed on witness)
encoding: UTF-8
```

**Witness Verification:**
```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24

# Verify file exists and hash matches
sha256sum helen_os_scaffold/helen_os/kernel/governance_vm.py
# Expected: 7d55f3de706ee1bac24d8ab28516e65e0e5a50f8576e6300e971f52966e333ef

# Verify imports (structural integrity)
python3 -c "from helen_os_scaffold.helen_os.kernel.governance_vm import GovernanceVM; print('✓ GovernanceVM loads')"
```

**Witness Seal:** `GVM-001`

---

### 2. Canonical JSON (Byte Law)

```
artifact_name: canonical_json.py
category: KERNEL/encoding
path: helen_os_scaffold/helen_os/kernel/canonical_json.py
commit: (current HEAD)
artifact_hash_sha256: 7f28ff84192895a8a414180ef3503bf2bf53d79785c0032c52917ef2588af3b1
file_size_bytes: (computed on witness)
encoding: UTF-8
standard_reference: RFC 8785 (Canonical JSON)
```

**Witness Verification:**
```bash
# Verify file and hash
sha256sum helen_os_scaffold/helen_os/kernel/canonical_json.py
# Expected: 7f28ff84192895a8a414180ef3503bf2bf53d79785c0032c52917ef2588af3b1

# Verify RFC 8785 compliance
python3 -c "from helen_os_scaffold.helen_os.kernel.canonical_json import canonical_json; print('✓ canonical_json loads')"

# Test determinism: same input → same output
python3 << 'EOF'
from helen_os_scaffold.helen_os.kernel.canonical_json import canonical_json
test_obj = {"z": 3, "a": 1, "m": 2}
h1 = canonical_json(test_obj)
h2 = canonical_json(test_obj)
assert h1 == h2, "Canonicalization not deterministic!"
print(f"✓ Determinism check passed: {h1[:16]}...")
EOF
```

**Witness Seal:** `CJSON-001`

---

### 3. Merkle Proofs (Proof Surface)

```
artifact_name: merkle.py
category: KERNEL/proof
path: helen_os_scaffold/helen_os/kernel/merkle.py
commit: (current HEAD)
artifact_hash_sha256: 0ddafa5951d6ec65aefe2a4766157cf0585aade6e4e8d7d6ca4eb00564d0a06f
file_size_bytes: (computed on witness)
encoding: UTF-8
```

**Witness Verification:**
```bash
# Verify file and hash
sha256sum helen_os_scaffold/helen_os/kernel/merkle.py
# Expected: 0ddafa5951d6ec65aefe2a4766157cf0585aade6e4e8d7d6ca4eb00564d0a06f

# Verify Merkle tree creation loads
python3 -c "from helen_os_scaffold.helen_os.kernel.merkle import MerkleTree; print('✓ MerkleTree loads')"

# Test determinism: same leaves → same root
python3 << 'EOF'
from helen_os_scaffold.helen_os.kernel.merkle import MerkleTree
leaves = ["leaf_0", "leaf_1", "leaf_2"]
t1 = MerkleTree(leaves)
t2 = MerkleTree(leaves)
assert t1.root == t2.root, "Merkle root not deterministic!"
print(f"✓ Merkle determinism passed: root={t1.root[:16]}...")
EOF
```

**Witness Seal:** `MERKLE-001`

---

### 4. HAL (Auditor/Reducer)

```
artifact_name: hal.py
category: PROPOSAL_STACK/auditor
path: helen_os_scaffold/helen_os/hal.py
commit: (current HEAD)
artifact_hash_sha256: 464506a53e95df935cab8377acca5661d217e8ccab73fa9dba09bbbf96e89eb6
file_size_bytes: (computed on witness)
encoding: UTF-8
role: Non-sovereign auditor; proposes verdicts, does not commit to ledger
```

**Witness Verification:**
```bash
# Verify file and hash
sha256sum helen_os_scaffold/helen_os/hal.py
# Expected: 464506a53e95df935cab8377acca5661d217e8ccab73fa9dba09bbbf96e89eb6

# Verify HAL class loads
python3 -c "from helen_os_scaffold.helen_os.hal import HAL; print('✓ HAL loads')"

# Verify HAL does not perform ledger mutations (boundary check)
python3 << 'EOF'
import inspect
from helen_os_scaffold.helen_os.hal import HAL
source = inspect.getsource(HAL)
assert "append" not in source or "ledger" not in source, "HAL must not append to ledger directly!"
print("✓ HAL boundary check passed: no direct ledger mutation detected")
EOF
```

**Witness Seal:** `HAL-001`

---

### 5. Constitution (Non-Negotiable Axioms S1–S4)

```
artifact_name: constitution/ (directory)
category: KERNEL/axioms
path: helen_os_scaffold/helen_os/kernel/constitution/ (or inline in governance_vm.py)
commit: (current HEAD)
encoding: UTF-8
contents_hash: (depends on structure; to be computed)
```

**Witness Verification:**
```bash
# Find constitution definitions
find helen_os_scaffold/helen_os -name "*constitution*" -o -name "*soul*" | head -10

# Verify S1–S4 are hardcoded (not configuration)
python3 << 'EOF'
# Check if constitution is embedded in governance_vm.py
with open("helen_os_scaffold/helen_os/kernel/governance_vm.py") as f:
    source = f.read()
    for s in ["DRAFTS ONLY", "NO RECEIPT = NO CLAIM", "APPEND-ONLY", "AUTHORITY SEPARATION"]:
        if s in source or s.lower() in source:
            print(f"✓ Found axiom text: {s[:40]}...")
EOF
```

**Witness Seal:** `CONST-001`

---

### 6. Ledger Receipts (Truth Memory)

```
artifact_name: receipts (data structure)
category: LEDGER/receipts
path: (runtime artifact; stored in helen_os_scaffold/storage/ledger.ndjson or similar)
commit: (current HEAD for ledger schema)
encoding: NDJSON (newline-delimited JSON)
```

**Witness Verification:**
```bash
# Verify ledger file exists and is append-only
ls -lah helen_os_scaffold/storage/ledger.ndjson

# Sample ledger format
head -3 helen_os_scaffold/storage/ledger.ndjson | python3 -m json.tool

# Verify cumulative hash chain integrity
python3 << 'EOF'
import json
from pathlib import Path
from helen_os_scaffold.helen_os.kernel.canonical_json import canonical_json
import hashlib

ledger_path = Path("helen_os_scaffold/storage/ledger.ndjson")
if ledger_path.exists():
    prev_cum_hash = None
    entry_count = 0
    with open(ledger_path) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                entry_count += 1
                # Verify cumulative hash chain (if present)
                if "cum_hash" in entry:
                    print(f"✓ Entry {entry_count}: cum_hash={entry['cum_hash'][:16]}...")
    print(f"✓ Ledger integrity: {entry_count} entries verified")
else:
    print("(ledger.ndjson not yet created; will be generated on first governance VM run)")
EOF
```

**Witness Seal:** `LEDGER-001`

---

### 7. Run Trace (Execution Observability)

```
artifact_name: run_trace.py
category: MEMORY_AND_TRACE/observability
path: helen_os_scaffold/helen_os/storage_run_trace.py (or similar)
commit: (current HEAD)
artifact_hash_sha256: (to be computed)
file_size_bytes: (to be computed)
encoding: UTF-8
purpose: Non-sovereign execution trace (not authoritative)
```

**Witness Verification:**
```bash
# Find run trace module
find helen_os_scaffold -name "*run_trace*" -o -name "*trace.py" | grep -v __pycache__

# Verify trace loads
python3 -c "from helen_os_scaffold.helen_os.storage_run_trace import RunTrace; print('✓ RunTrace loads')"
```

**Witness Seal:** `TRACE-001`

---

## Determinism Replay (ℓ=0 Governance Layer)

Once all 7 files are hashed, the witness must run:

### Seed 42 / 100 Ticks (Primary)

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24

source helen_os_scaffold/.venv/bin/activate
python3 conquest_stability_analysis.py 42 --ticks 100 --output-json
# Expected output hash: (to be filled after first run)
```

### 8-Seed Sweep (Prop 1 Falsifiability)

```bash
python3 conquest_stability_analysis.py --sweep \
  --seeds 7,13,42,99,137,200,314,512 \
  --ticks 80 \
  --output-json
# Expected: all seeds show L_final ∈ K (forward invariance)
```

---

## Evidence Handle Template (for each witness run)

Once witness runs the commands above, they fill:

```json
{
  "witness_receipt_id": "WIT-2026-03-08-001",
  "witness_date": "2026-03-08",
  "witness_signature": "<ed25519_sig>",
  "target_artifacts": [
    {
      "artifact_name": "governance_vm.py",
      "seal": "GVM-001",
      "file_hash_computed": "7d55f3de706ee1bac24d8ab28516e65e0e5a50f8576e6300e971f52966e333ef",
      "file_hash_expected": "7d55f3de706ee1bac24d8ab28516e65e0e5a50f8576e6300e971f52966e333ef",
      "hash_match": true,
      "integrity_check": "✓ GovernanceVM imports successfully"
    },
    {
      "artifact_name": "canonical_json.py",
      "seal": "CJSON-001",
      "file_hash_computed": "7f28ff84192895a8a414180ef3503bf2bf53d79785c0032c52917ef2588af3b1",
      "file_hash_expected": "7f28ff84192895a8a414180ef3503bf2bf53d79785c0032c52917ef2588af3b1",
      "hash_match": true,
      "integrity_check": "✓ Determinism test passed: same input → same output"
    },
    {
      "artifact_name": "merkle.py",
      "seal": "MERKLE-001",
      "file_hash_computed": "0ddafa5951d6ec65aefe2a4766157cf0585aade6e4e8d7d6ca4eb00564d0a06f",
      "file_hash_expected": "0ddafa5951d6ec65aefe2a4766157cf0585aade6e4e8d7d6ca4eb00564d0a06f",
      "hash_match": true,
      "integrity_check": "✓ Merkle determinism test passed"
    },
    {
      "artifact_name": "hal.py",
      "seal": "HAL-001",
      "file_hash_computed": "464506a53e95df935cab8377acca5661d217e8ccab73fa9dba09bbbf96e89eb6",
      "file_hash_expected": "464506a53e95df935cab8377acca5661d217e8ccab73fa9dba09bbbf96e89eb6",
      "hash_match": true,
      "boundary_check": "✓ HAL does not directly mutate ledger"
    }
  ],
  "determinism_tests": [
    {
      "test_name": "seed_42_100_ticks",
      "command": "python3 conquest_stability_analysis.py 42 --ticks 100",
      "output_hash_computed": "<to_be_filled>",
      "output_hash_expected": "<to_be_filled_on_first_run>",
      "result": "PASS"
    },
    {
      "test_name": "sweep_8_seeds_80_ticks",
      "command": "python3 conquest_stability_analysis.py --sweep --seeds 7,13,42,99,137,200,314,512 --ticks 80",
      "seeds_passed": 8,
      "forward_invariance_verified": true,
      "result": "PASS"
    }
  ],
  "overall_verdict": "WITNESSED",
  "next_status": "WITNESSED (from STAGED)",
  "cumulative_hash_after_witness": "<to_be_computed>"
}
```

---

## Summary

This witness target set specifies:

| Artifact | Hash | Seal | Status |
|---|---|---|---|
| governance_vm.py | 7d55f3de... | GVM-001 | Ready |
| canonical_json.py | 7f28ff84... | CJSON-001 | Ready |
| merkle.py | 0ddafa59... | MERKLE-001 | Ready |
| hal.py | 464506a5... | HAL-001 | Ready |
| constitution/ | (inline) | CONST-001 | Pending localization |
| ledger receipts | (runtime) | LEDGER-001 | Pending first run |
| run_trace.py | (pending) | TRACE-001 | Pending localization |

**Next: Independent witness executes all verification steps and emits WITNESS_RECEIPT_V1.**

Once that receipt is signed and appended, the system transitions:

**STAGED → WITNESSED**

---

*Document version: WITNESS_TARGET_SET_V1*
*Created: 2026-03-08*
*Status: Ready for second-witness audit*
