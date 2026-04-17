# Oracle Town — Technical Summary for Developers

## Quick Start

### Run the Sealed Constitution

```bash
# Verify constitution is locked
cat oracle_town/CONSTITUTION_HASH.txt

# Run TRI gate on a claim
python3 oracle_town/jobs/tri_gate.py \
  --claim oracle_town/state/acg/run_000003/claims/claim_001.json \
  --output /tmp/verdict.json \
  --policy-hash "sha256:policy_v1_2026_01" \
  --key-registry oracle_town/keys/test_public_keys.json \
  --evidence-dir artifacts/

# View result
cat /tmp/verdict.json | python3 -m json.tool
```

### Run All Observers

```bash
python3 oracle_town/observers/run_all_observers.py
```

---

## Architecture Overview

### Authorization Chain

```
Labor Layer (Claims)
        ↓
TRI Gate (Verification)
        ↓
Mayor (Signing)
        ↓
Ledger (Recording)
```

### Gates in Order (Irreversible)

```
1. Schema → validate fields
   ↓
2. P0 → evidence must exist, paths safe, hashes match
   ↓
3. K7 → policy hash must be pinned
   ↓
4. K0 → attestor must be registered
   ↓
5. P2 → no self-attestation, no ephemeral evidence
   ↓
6. P1 → no dynamic selectors
   ↓
VERDICT: ACCEPT or REJECT
```

**Critical**: If any gate fails, no later gate matters. Verdict is REJECT.

---

## Key Code Locations

### TRI Gate Implementation

**File**: `oracle_town/jobs/tri_gate.py`

**Critical Functions**:
- `run_tri_gate()` — Main entry point (lines 557-660)
- `verify_claim_schema()` — Gate 1
- `verify_evidence_realizability()` — Gate 2 (P0)
- `verify_k7_policy_pinning()` — Gate 3
- `verify_k0_authority()` — Gate 4
- `verify_k2_no_self_attestation_enhanced()` — Gate 5 (P2)
- `verify_k5_determinism_extended()` — Gate 6 (P1)
- `make_verdict()` — Verdict logic

**Helper Functions** (Pure, deterministic):
- `is_safe_relpath()` — Path safety (no absolute, no ..)
- `resolve_evidence_path()` — Realpath containment
- `sha256_file()` — Binary mode hashing
- `contains_reserved_keyword()` — Dynamic selector detection

### Constitution Verification

**File**: `oracle_town/CONSTITUTION_HASH.txt`

```
sha256:df9fb5da69dae59bfe8c0184018d65bc2cf2f578bc7adcc57f537d411a1ed07d
```

**Check**: If this changes, the constitution has drifted. Abort all runs.

### Test Registry

**File**: `oracle_town/keys/test_public_keys.json`

Contains 4 test attestors for validation (not production):
- `test-legal-001` (active)
- `test-legal-002` (active)
- `test-inactive-key` (inactive)
- Plus others as needed

---

## Reserved Keywords (P1 Gate)

```python
RESERVED_KEYWORDS = {
    "latest", "current", "today", "now", "auto", "dynamic",
    "HEAD", "main", "stable", "default", "production", "top", "best", "recommended",
    "yesterday", "tomorrow", "recent", "soon", "this week", "end of month", "Q1", "ASAP"
}
```

Any of these words in claim fields → P1 FAIL.

---

## Ephemeral Paths (P2 Gate)

```python
BANNED_EVIDENCE_PREFIXES = (
    "/tmp",
    "oracle_town/state",
    "oracle_town/run",
    ".cache",
    "run_",
    "state_"
)
```

Evidence from these paths → P2 FAIL.

---

## Verdict Logic

```python
if any(check.result == "FAIL" for check in all_checks):
    return TriVerdict.REJECT
elif any(check.result == "WARN" for check in all_checks):
    return TriVerdict.DEFER
else:
    return TriVerdict.ACCEPT
```

**No soft accepts. No thresholds. Binary only.**

---

## Testing

### Adversarial Claim Generator (ACG)

```bash
# Generate 50-claim balanced suite
python3 oracle_town/state/acg_generate.py \
  --seed 1337 \
  --n 50 \
  --run-id 000003 \
  --policy-hash "sha256:policy_v1_2026_01"

# Run through TRI
python3 oracle_town/state/acg_run_real_tri.py --run-id 000003
```

**Distribution** (10 claims per category):
- K1: Schema/evidence failures
- K0: Unregistered attestors
- K2: Self-attestation attempts
- K7: Policy mutation attempts
- K5: Determinism violations

**Expected Result**: 0 escapes, 100% gate coverage

### Replay Determinism

```bash
# Verify same claim always produces same verdict
python3 << 'EOF'
import hashlib
from pathlib import Path
from oracle_town.jobs.tri_gate import run_tri_gate

claim_file = Path("oracle_town/state/acg/run_000003/claims/claim_001.json")
hashes = []

for i in range(10):
    result_file = Path(f"/tmp/verdict_{i}.json")
    run_tri_gate(claim_file, result_file, "sha256:policy_v1_2026_01",
                 Path("oracle_town/keys/test_public_keys.json"), Path("."))

    with open(result_file, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
        hashes.append(h)

assert len(set(hashes)) == 1, f"Non-deterministic: {len(set(hashes))} different hashes"
print(f"✓ Determinism verified: all 10 runs produced {hashes[0][:16]}...")
EOF
```

---

## Observers

### Refusal Rate

```bash
python3 oracle_town/observers/observer_refusal_rate.py
```

Output: Daily/weekly rejection percentages, per-gate contribution

### Gate Firing

```bash
python3 oracle_town/observers/observer_gate_firing.py
```

Output: Gate firing frequency, entropy, co-firing patterns

### Determinism

```bash
python3 oracle_town/observers/observer_determinism.py --sample-size 10
```

Output: Claim replay results, K5 verification

---

## Ledger Structure

```
oracle_town/ledger/
└── YYYY/MM/claim_id/
    ├── claim.json              ← Original claim
    ├── tri_verdict.json        ← Unsigned verdict
    └── mayor_receipt.json      ← Signed receipt
```

**Immutability**: Append-only. All entries have claim_id → verdict → receipt chain.

---

## Claim Schema (Required Fields)

```json
{
  "claim": {
    "id": "unique_claim_id",
    "timestamp": "2026-01-31T10:00:00Z",
    "target": "oracle_town/jobs/obs_scan.py",
    "claim_type": "code_change",
    "proposed_diffs": [{"path": "...", "operation": "modify", "hash_before": "...", "hash_after": "..."}],
    "evidence_pointers": [{"type": "test_result", "path": "artifacts/...", "hash": "sha256:...", "description": "..."}],
    "acceptance_criteria": ["criterion1", "criterion2"],
    "expected_outcomes": ["outcome1"],
    "policy_pack_hash": "sha256:policy_v1_2026_01",
    "generated_by": "attestor-legal-001",
    "intent": "Human-readable description"
  }
}
```

**Missing any field** → Schema FAIL → immediate REJECT

---

## Development Guidelines

### Adding a New Gate

1. **Create gate function** (pure, deterministic)
   ```python
   def verify_k_new_gate(claim: dict) -> list[Check]:
       checks = []
       # Logic here (no I/O, no randomness)
       return checks
   ```

2. **Insert in correct position** (maintain immutable order)
   ```python
   # In run_tri_gate():
   all_checks.extend(verify_k_new_gate(claim))
   ```

3. **Test determinism** (200 iterations must produce same output)
   ```bash
   python3 oracle_town/core/replay.py --iterations 200
   ```

4. **Do NOT soften earlier gates** (architecture is fail-fast, not negotiable)

### Modifying TRI Gate

**WARNING**: Changes to gate logic are architectural decisions. They require:
1. Full determinism verification (200-iteration replay)
2. Revalidation against all 50-claim suite
3. Constitutional review (gates cannot be softened)

---

## Common Patterns

### Path Safety (P0)

```python
# Bad: String comparison
if "/tmp" not in path_string:
    accept()

# Good: Canonical path with containment check
resolved = (EVIDENCE_ROOT / path_string).resolve()
resolved.relative_to(EVIDENCE_ROOT)  # Raises ValueError if outside
```

### Hashing (D2)

```python
# Bad: Text mode (platform-dependent line endings)
with open(file_path, "r") as f:
    hash = hashlib.sha256(f.read().encode()).hexdigest()

# Good: Binary mode (deterministic)
with open(file_path, "rb") as f:
    hash = hashlib.sha256(f.read()).hexdigest()
```

### Dynamic Selectors (P1)

```python
# Bad: Function that uses implicit time
def get_latest():
    return results[-1]  # Changes based on when run

# Good: Explicit frozen selection
def get_frozen_result(result_index: int):
    return results[result_index]  # Deterministic
```

---

## Performance Notes

- **Schema validation**: O(n) where n = field count (~10)
- **P0 hashing**: O(file_size), streamed in 1MB chunks
- **Gate execution**: Pure functions, no I/O beyond evidence check
- **Typical verdict time**: < 100ms per claim

No optimization needed. Authority is cheap once legitimacy is established.

---

## Debugging Checklist

If a claim is unexpectedly rejected:

1. **Check schema** (`expected_outcomes` missing?)
2. **Check evidence** (file exists? hash matches? path safe?)
3. **Check K7** (policy hash matches pinned?)
4. **Check K0** (attestor in registry? not revoked?)
5. **Check P2** (self-ref? ephemeral path?)
6. **Check P1** (reserved keywords?)

Each check corresponds to a gate in order. Fix the earliest failure.

---

## References

- `oracle_town/CONSTITUTION.json` — Constitutional specification
- `oracle_town/jobs/tri_gate.py` — Gate implementation
- `oracle_town/state/GATE_COVERAGE_MATRIX.md` — Test results
- `oracle_town/SEALED_JURISDICTION_COMPLETE.md` — Overview

---

**Status**: Ready for deployment and extension.

