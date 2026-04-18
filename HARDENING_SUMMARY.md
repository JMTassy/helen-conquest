# Hardening Summary: Determinism & Governance Regression Prevention

Date: 2026-02-22
Status: All hardening moves implemented and operational

---

## Overview

Five strategic hardening moves implemented to prevent regression of the timestamp nondeterminism bug and to freeze governance specifications immutably.

**Key Principle**: Automation + CI gates prevent manual vigilance from failing.

---

## 1. Determinism Contract (Frozen Specification)

**File**: `DETERMINISM_CONTRACT.md`

**What it does**:
- Defines what "determinism" means (precisely, not vaguely)
- Lists forbidden patterns (Date.now, Math.random, etc.)
- Requires "NONDETERMINISTIC_OK" allowlist for exceptions
- Documents the timestamp bug discovery
- Provides regression prevention checklist

**Why it matters**:
- Creates shared understanding of determinism rules
- Establishes exception protocol (prevents accidental slip-through)
- Documents lessons learned (timestamp bug)

**Authority**: Non-binding document + CI gates enforce it

---

## 2. Preflight Nondeterminism Gate (Grep-based)

**File**: `scripts/preflight_nondeterminism_check.sh`

**What it does**:
```bash
grep -R -E "Date\.now\(|new Date\(|toISOString\(|Math\.random\(|randomUUID\(" marketing_street.cjs scripts/
```

**Trigger**: On every commit to deterministic scripts

**Output**:
- ✅ PASS — No forbidden patterns (or all allowlisted)
- ❌ FAIL — Forbidden pattern detected → CI blocks merge

**Why it matters**:
- Catches Date.now(), Math.random(), etc. before they run
- Fast, cheap gate (grep is microseconds)
- Prevents the exact bug that broke determinism in February

**False positives handled**: `// NONDETERMINISTIC_OK: reason` allowlists exceptions

---

## 3. Determinism Verification Gate (Hash-based)

**File**: `scripts/verify_marketing_street_determinism.sh`

**What it does**:
1. For each seed in [1, 7, 42, 111, 999]:
   - Run `node marketing_street.cjs SEED` twice
   - Compute SHA256 of each output
   - Compare hashes (must be byte-identical)
   - Fail fast on first mismatch

**Trigger**: After preflight passes

**Output**:
```
Testing seed=111... PASS (hash=96a292a32...)
Testing seed=999... FAIL (hash mismatch)
  Run A: abc123...
  Run B: def456...
  Diff:
    < "generated_at": "2026-02-22T10:15:23.456Z"
    > "generated_at": "2026-02-22T10:15:24.789Z"
❌ DETERMINISM VERIFICATION FAILED (4/5 seeds)
```

**Why it matters**:
- Detects hidden nondeterminism that grep misses (object key ordering, locale formatting, etc.)
- Runs before tests, so catches regression early
- 5-seed sweep covers diverse code paths

---

## 4. CouplingGate Reason Ordering Immutability

**File**: `COUPLING_GATE_README.md` (new section added)

**What it does**:
- Freezes the reason code priority order as a specification
- Adds conformance test assertion: must match exact reasons
- Documents that any reordering requires amendment process

**Example of enforcement**:
```
Current ordering (frozen):
1. Hash joins (run_hash, theta_hash)
2. Oracle verdict state
3. Coupling law for PUBLISH
4. Coupling law for REJECT
5. Default: OK

If someone reorders to:
1. Oracle verdict state (moved up)
2. Hash joins (moved down)
...

Then test T02 (hash mismatch) would fail with:
  Expected: HASH_MISMATCH_KERNEL_OR_CONFIG
  Got: ORACLE_HOLD
  → CI blocks merge
```

**Why it matters**:
- Prevents silent behavioral change in governance logic
- Makes governance transparent (ordering is explicit, not hidden)
- Conformance tests catch any violation

---

## 5. Immutable Proof Bundle

**File**: `PROOF_BUNDLE_2026-02-22.md`

**What it contains**:
1. Git commit hash (`f3bd0bb8...`)
2. File SHA256s (all 6 critical artifacts)
3. Determinism proof (seed 111, dual runs)
4. Determinism sweep (5 seeds, all passing)
5. CouplingGate conformance (14/14 tests)
6. CI gate operational status
7. Known limitations & regression history
8. Reproducibility instructions

**Why it matters**:
- **Tamper-evident**: Any file change invalidates proof
- **Reproducible**: Anyone can verify on any machine
- **Permanent record**: Archived, never modified
- **Immutable**: New releases create new bundles, old ones stay locked

**Example verification**:
```bash
# Verify file hasn't changed
sha256sum CLAUDE.md
# Expected: 1f29cc10defeaf17c372140cc7ba460f95e91a707aa72b5c257d1aeaa8e205b3
# Actual:   1f29cc10defeaf17c372140cc7ba460f95e91a707aa72b5c257d1aeaa8e205b3
# ✅ MATCH

# Verify determinism still holds
node marketing_street.cjs 111 | sha256sum
# Expected: 96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
# Actual:   96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
# ✅ MATCH
```

---

## 6. CI/CD Integration

**File**: `.github/workflows/determinism-gates.yml`

**What it does**:
1. Trigger on commits to deterministic files
2. Run preflight check (grep for forbidden patterns)
3. Run determinism verification (5 seeds)
4. Run CouplingGate conformance (14/14)
5. On main merge: generate new proof bundle
6. On failure: block merge with regression alert

**Gates in order**:
```
Preflight (grep)
  ↓ (if passes)
Determinism (5 seeds)
  ↓ (if passes)
Conformance (14 tests)
  ↓ (if passes)
Merge allowed
  ↓ (on main)
Proof bundle generated + committed
```

**Failure behavior**:
- Preflight fails → blocks at "no forbidden patterns"
- Determinism fails → blocks at "hash mismatch"
- Conformance fails → blocks at "test vector mismatch"
- No merging past first failure

---

## Complete Hardening Stack

```
DETERMINISM_CONTRACT.md (specification)
  ↓
scripts/preflight_nondeterminism_check.sh (fast gate, grep-based)
  ↓
scripts/verify_marketing_street_determinism.sh (deep gate, hash-based)
  ↓
COUPLING_GATE_README.md (frozen reason ordering)
  ↓
coupling_gate.vectors.json (14 test cases)
  ↓
conformance_runner.ts (CI test harness)
  ↓
PROOF_BUNDLE_2026-02-22.md (immutable snapshot)
  ↓
.github/workflows/determinism-gates.yml (CI/CD orchestration)
```

---

## What Gets Prevented

| Regression Type | Prevention Gate | Detection Method |
|---|---|---|
| `Date.now()` sneaks back in | Preflight + Determinism | Grep + hash comparison |
| `Math.random()` without seed | Preflight | Grep pattern match |
| `Object.keys()` unordered iteration | Determinism | Hash mismatch (unstable JSON order) |
| Locale-dependent formatting | Determinism | Hash mismatch (different string output) |
| CouplingGate reason reordering | Conformance | Test vector mismatch (unexpected reason) |
| Silent config change | Proof bundle hash | File SHA256 mismatch |
| Governance authority drift | Proof bundle + Conformance | Reason code reordering caught |

---

## Operational Integration

### Before Every Commit

```bash
# Local check (before pushing)
bash scripts/preflight_nondeterminism_check.sh
bash scripts/verify_marketing_street_determinism.sh
npx tsx conformance_runner.ts coupling_gate.vectors.json
```

### On GitHub (automatic)

```yaml
- On push to main: run all 3 gates
- If any fail: block merge, send alert
- If all pass: generate proof bundle, commit to main
- Proof bundle is permanent (never edited, only new dates)
```

### On Release

```bash
# Archive proof bundle with version
cp PROOF_BUNDLE_2026-02-22.md releases/proof-bundles/v1.0.0-proof-2026-02-22.md

# Include in release notes:
# - Commit hash
# - All file SHAs
# - Determinism proof (seed 111)
# - Conformance results (14/14)
```

---

## Regression Scenarios (Hypothetical)

### Scenario 1: Accidental `Date.now()`

**Developer**: "I'll add a timestamp to the run ID for debugging"
```javascript
golden_run_id: `MARKET-${seed}-${Date.now()}`
```

**What happens**:
1. Push to branch → CI runs preflight
2. Grep finds `Date.now()` → ❌ FAIL
3. Merge blocked
4. Message: "Forbidden pattern: Date.now()"

**Developer fixes**: Removes timestamp, uses seed-derived value
```javascript
golden_run_id: `MARKET-${seed}`
```

**Result**: ✅ CI passes, merge allowed

### Scenario 2: Reordered CouplingGate Reasons

**Developer**: "Let me move hash checks after oracle state for clarity"

```typescript
// BEFORE (frozen):
if (hashMismatch) return FAIL;
if (oracleHold) return HOLD;

// AFTER (new order):
if (oracleHold) return HOLD;
if (hashMismatch) return FAIL;
```

**What happens**:
1. Push to branch → CI runs conformance tests
2. Test T02 (expects `HASH_MISMATCH_KERNEL_OR_CONFIG` on hash mismatch)
3. But gets `ORACLE_HOLD` (oracle state checked first now)
4. ❌ TEST FAILURE: "Expected HASH_MISMATCH_KERNEL_OR_CONFIG, got ORACLE_HOLD"
5. Merge blocked

**Developer decision**:
- Option A: Revert to original order (fast, safe)
- Option B: Update test vectors + amendment process (explicit, slow)

**Result**: Governance change is visible, intentional, documented

### Scenario 3: Silent Object Key Ordering Change

**Developer**: Refactors JSON building (accidentally breaks key ordering)

```javascript
// BEFORE (canonical):
const output = JSON.stringify({
  agents: [...],
  metadata: {...},
  run_id: "...",
}, null, 2);

// AFTER (unordered):
const output = {};
output.run_id = "...";
output.metadata = {...};
output.agents = [...];
```

**What happens**:
1. Preflight passes (no Date.now, etc.)
2. Run seed 111 twice
3. Hash A: `96a292a32...`
4. Hash B: `e7f2a8b1c...` (keys in different order, different JSON)
5. ❌ DETERMINISM FAILURE: "Hash mismatch on seed 111"
6. Merge blocked

**Developer fixes**: Canonicalizes output (sorts keys)
```javascript
const canonical_json = JSON.stringify(output, Object.keys(output).sort());
```

**Result**: ✅ Hashes match, merge allowed

---

## Future Extensions

Once this hardening is proven stable (10+ releases without regression):

1. **Extend to CONQUEST** — Add same gates to game simulation
2. **Extend to Street 1** — Determinism verification for NPC server
3. **Canonical JSON library** — Reusable canonicalizer across all systems
4. **Immutable proof chain** — Link proof bundles via git tags (cryptographic seal)
5. **Automated amendment process** — Conformance test failure → propose amendment automatically

---

## Summary: What Changed

| What | Before | After | Authority |
|------|--------|-------|-----------|
| Nondeterminism prevention | Manual vigilance (error-prone) | Automated CI gates | CI blocks merges |
| Forbidden patterns | Suggested best practice | Grep-enforced (allowlist model) | Preflight gate |
| Determinism verification | "Looks good to me" | Dual-run hash comparison | Determinism gate |
| Governance ordering | Implementation detail | Immutable specification | Conformance tests |
| Proof of safety | Claims ("it's deterministic") | Tamper-evident bundle | Proof bundle hashes |
| Regression response | "Oops, let me fix it" | "CI blocked this, here's why" | Automated + human readable |

---

## Key Insight

**Regression prevention is not about willpower. It's about making regression impossible.**

These gates don't ask developers to remember the rules. They enforce the rules automatically. By the time human judgment is involved ("should I commit this?"), the machine has already validated determinism and governance compliance.

---

**Frozen**: 2026-02-22
**Status**: ✅ All hardening moves operational
**Next review**: When regression detected or 10 releases pass without incident
