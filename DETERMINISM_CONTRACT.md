# Determinism Contract

**Marketing Street Deterministic Execution Guarantee**

Last Updated: 2026-02-22
Status: FROZEN (enforced by CI gates)

---

## 1. Core Promise

Same input (seed + configuration) → Byte-identical output (JSON + SHA256)

This is not aspirational. This is enforced by two automated CI gates:
1. **Preflight check** — scans for forbidden patterns (grep-based)
2. **Determinism verification** — runs seed twice, compares SHA256

---

## 2. Forbidden Patterns (Strictly)

These patterns break determinism and are **never allowed** in the deterministic execution path:

- `Date.now()` — millisecond wall-clock time (varies per run)
- `new Date()` — date object creation (depends on system time)
- `toISOString()` — ISO 8601 formatting (includes current time)
- `Math.random()` — unseeded randomness
- `crypto.randomUUID()` — generates random UUIDs
- `process.hrtime()` — high-resolution timer (platform-specific)
- `performance.now()` — performance API timing (varies per run)
- `crypto.randomBytes()` — random byte generation
- Object key iteration without sorting — sets/maps are unordered; iterate order varies

### Exception Rule

If you must use a forbidden pattern (e.g., for logging-only output that doesn't affect JSON export), mark it explicitly:

```javascript
const timestamp = new Date().toISOString(); // NONDETERMINISTIC_OK: logging-only, not exported
```

The CI preflight gate will allow this and skip the check.

---

## 3. Required Patterns (Always)

- **Seeded RNG only**: `Math.sin(seed + offset) * 10000` or equivalent deterministic derivative
- **Run ID as pure function**: `run_id = sha256(prefix + seed + version_hash)`, never include timestamps
- **No generated_at field** (unless derived purely from seed, e.g., `"SEED_TIME:"+seed`)
- **Canonical JSON**: Sort all object keys lexicographically before hashing
- **Stable iteration**: If iterating over sets/maps, sort keys first

---

## 4. Enforcement: Two CI Gates

### Gate 1: Preflight Grep Check

**Script**: `scripts/preflight_nondeterminism_check.sh`

**Trigger**: On every commit to `marketing_street.cjs` or related scripts

**Action**:
```bash
grep -R -E "Date\.now\(|new Date\(|toISOString\(|Math\.random\(|randomUUID\(" marketing_street.cjs scripts/
```

**Pass/Fail**:
- ✅ PASS — No forbidden patterns found (or all allowlisted with `NONDETERMINISTIC_OK`)
- ❌ FAIL — Forbidden pattern detected without allowlist → CI block

### Gate 2: Determinism Verification

**Script**: `scripts/verify_marketing_street_determinism.sh`

**Trigger**: After preflight passes

**Action**:
- For seeds [1, 7, 42, 111, 999]:
  - Run `node marketing_street.cjs SEED` twice
  - Compare SHA256 of outputs
  - Fail fast on first mismatch

**Output**:
```
Seed 1:   PASS (hash=abc123...)
Seed 7:   PASS (hash=def456...)
Seed 42:  PASS (hash=ghi789...)
Seed 111: PASS (hash=jkl012...)
Seed 999: PASS (hash=mno345...)
✅ DETERMINISM VERIFIED (5/5 seeds)
```

**Failure case**:
```
Seed 42: FAIL (hash mismatch)
  Run A: abc123
  Run B: def456
  Diff:
    < "generated_at": "2026-02-22T10:15:23.456Z"
    > "generated_at": "2026-02-22T10:15:24.789Z"
❌ DETERMINISM VERIFICATION FAILED (1/5 seeds)
```

---

## 5. JSON Canonicalization Rule

Before hashing or storing outputs:

1. **Recursively sort all object keys** alphabetically
2. **Preserve array order** (arrays determined by seed, not iteration)
3. **No locale-specific formatting** (avoid `toLocaleString()`, currency symbols)
4. **No float approximation** (use `toFixed()` or store as string if needed)

Example (before → after canonicalization):

```javascript
// BEFORE (unordered)
{
  "metadata": {...},
  "agents": [...],
  "run_id": "...",
}

// AFTER (canonical)
{
  "agents": [...],
  "metadata": {...},
  "run_id": "...",
}
```

Then:
```javascript
const canonical = JSON.stringify(output, Object.keys(output).sort());
const sha256 = crypto.createHash('sha256').update(canonical).digest('hex');
```

---

## 6. Proof Bundle Immutability

Every release must include a **immutable proof artifact** with:

1. **Git commit hash** (`git rev-parse HEAD`)
2. **File SHAs**:
   ```
   CLAUDE.md: abc123def456...
   ARCHITECTURE_V2.md: ghi789jkl012...
   marketing_street.cjs: mno345pqr678...
   coupling_gate.ts: stu901vwx234...
   conformance_runner.ts: yza567bcd890...
   coupling_gate.vectors.json: efg123hij456...
   ```
3. **Determinism sweep output** (5 seeds, 5/5 pass)
4. **Conformance tests** (CouplingGate 14/14 pass)
5. **Seed 111 canonical SHA**

This artifact is stored as `PROOF_BUNDLE_[DATE].json` and committed to git. **No rollback permitted without full re-verification.**

---

## 7. Regression Prevention Checklist

Before committing any change to `marketing_street.cjs`:

- [ ] Ran `scripts/preflight_nondeterminism_check.sh` — PASS
- [ ] Ran `scripts/verify_marketing_street_determinism.sh` — PASS (5/5 seeds)
- [ ] Canonicalized JSON before export (sorted keys)
- [ ] No `Date.now()`, `Math.random()`, or unseeded randomness
- [ ] Run IDs and generated_at fields are pure functions of seed
- [ ] Git status clean (`git status`)
- [ ] Commit message includes reference to determinism gates

---

## 8. What "Determinism" Means (Precisely)

**Definition**: For any two executions with identical inputs (seed, config, args), the byte-for-byte SHA256 of the output is identical.

**Not a vibe.** Measurable. Verifiable. Reproducible.

**This applies to:**
- Consensus (agent agreement flows)
- Ordering (decision sequence)
- Probability (seeded RNG outcomes)
- Timing (never wall-clock; only logical tick count)

**This does NOT apply to:**
- Console logs (stderr, not part of output)
- Performance metrics (execution time varies)
- Comments or documentation (not part of determinism)

---

## 9. History of Violations (For Learning)

This section documents past determinism regressions and fixes:

### 2026-02-22: Timestamp Nondeterminism (FIXED)

**Pattern**: `new Date().toISOString()` and `Date.now()`

**Impact**: Seed 111 ran twice with different hashes (identified via mechanical verification)

**Root Cause**: `generated_at` field and `golden_run_id` included millisecond timestamps

**Fix**: Removed all timestamp logic; run_id is now pure function of seed

**Detection Method**: SHA256 comparison of dual runs

**Lesson**: Even "innocent" fields (metadata, ID generation) can hide nondeterminism. Always canonicalize before hashing.

---

## 10. CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Preflight Nondeterminism Check
  run: bash scripts/preflight_nondeterminism_check.sh

- name: Determinism Verification Gate
  run: bash scripts/verify_marketing_street_determinism.sh

- name: CouplingGate Conformance
  run: npx tsx conformance_runner.ts coupling_gate.vectors.json
```

**Failure blocks merge.**

---

## 11. Future Extensions

Once determinism is locked:

- [ ] Add canonical JSON encoder (recursive key sorting + float normalization)
- [ ] Add immutable proof bundle generator
- [ ] Add determinism trace (log seed + RNG calls for debugging)
- [ ] Extend to other deterministic systems (CONQUEST, Street 1)
- [ ] Formalize "replay guarantee" (prove any seed → same output via cryptographic audit trail)

---

**Signed**: Determinism Contract FROZEN 2026-02-22
**Authority**: CI gates (automated, non-negotiable)
**Termination**: Only via amendment process (requires explicit K-τ gate + conformance re-test)
