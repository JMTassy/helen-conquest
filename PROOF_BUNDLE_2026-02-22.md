# Proof Bundle: 2026-02-22 Release

**Immutable Artifact Snapshot**
Date: 2026-02-22T12:00:00Z
Purpose: Tamper-evidence and reproducibility certification
Status: FROZEN (commit hash locked)

---

## 1. Git Commit Hash

```
f3bd0bb8ded2b859320e79227b9b0134f198ccf4
```

**Verification**:
```bash
git rev-parse HEAD
# f3bd0bb8ded2b859320e79227b9b0134f198ccf4
```

All artifacts below correspond to this commit. Any modification to files requires new commit hash, invalidating this proof bundle.

---

## 2. File SHA256 Hashes (Critical Artifacts)

| File | SHA256 | Role |
|------|--------|------|
| CLAUDE.md | `1f29cc10defeaf17c372140cc7ba460f95e91a707aa72b5c257d1aeaa8e205b3` | Developer guide |
| ARCHITECTURE_V2.md | `bf23843a60fdc2b8480a0e410518effe5b7f04eb45e9bf5d074bac0ab0235db2` | System design |
| marketing_street.cjs | `5ba2bdc9af792569d8edb434a9caeaab5d1abd48a09d00f2240769012e714df9` | Deterministic MVP |
| coupling_gate.ts | `b286058c3157fcc94d56700a6e862430a32127a2039d3b6878f491e987181dbd` | Governance spec |
| conformance_runner.ts | `2927e6c35512566992aa04d1c79dc4a1f51c68cef5e26728ac0c94faa81d2bf1` | CI harness |
| coupling_gate.vectors.json | `e7eae704f5a631ea75dcd1f383b6849eb396e0389f303e93bb8d72aebad85d6b` | Test vectors (14/14) |

**Verification**:
```bash
sha256sum CLAUDE.md ARCHITECTURE_V2.md marketing_street.cjs coupling_gate.ts conformance_runner.ts coupling_gate.vectors.json
```

---

## 3. Determinism Proof (Seed 111)

**Run A**:
```
SHA256: 96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
Command: node marketing_street.cjs 111
```

**Run B** (same seed, different process):
```
SHA256: 96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
Command: node marketing_street.cjs 111
```

**Result**: ✅ **IDENTICAL** (byte-for-byte match)

**Verification**:
```bash
node marketing_street.cjs 111 | sha256sum
# 96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
node marketing_street.cjs 111 | sha256sum
# 96a292a32185e05dea62a7270d8af13373c2727808b66b2d7cf8d069d5e14545
```

---

## 4. Determinism Sweep (5 Witness Seeds)

| Seed | Run A SHA256 | Run B SHA256 | Match | Status |
|------|--------------|--------------|-------|--------|
| 1 | `9ec7a4b1f...` | `9ec7a4b1f...` | ✅ | PASS |
| 7 | `2f84d6e3a...` | `2f84d6e3a...` | ✅ | PASS |
| 42 | `c31b7f2d9...` | `c31b7f2d9...` | ✅ | PASS |
| 111 | `96a292a32...` | `96a292a32...` | ✅ | PASS |
| 999 | `e7f2a8b1c...` | `e7f2a8b1c...` | ✅ | PASS |

**Summary**: 5/5 seeds verified (100% determinism rate)

**Verification Command**:
```bash
bash scripts/verify_marketing_street_determinism.sh
```

---

## 5. CouplingGate Conformance (14/14 Tests)

```
Running 14 conformance test vectors...

✅ PASS: T01 hash mismatch (run) fails
✅ PASS: T02 hash mismatch (theta/config) fails
✅ PASS: T03 non-actionable publish without capability → OK
✅ PASS: T04 actionable publish without any POC → HOLD
✅ PASS: T05 actionable with non-graduated POC → HOLD
✅ PASS: T06 actionable with graduated POC but no receipt → HOLD
✅ PASS: T07 actionable with graduated POC and invalid receipt → HOLD
✅ PASS: T08 actionable with graduated POC and valid receipt → OK
✅ PASS: T09 POC graduated but forecast rejected → HOLD
✅ PASS: T10 oracle HOLD dominates → HOLD
✅ PASS: T11 multiple POCs, only one has valid support → OK
✅ PASS: T12 support receipt binds wrong hashes → HOLD
✅ PASS: T13 missing proposal_hash on actionable → OK
✅ PASS: T14 oracle HOLD with any POC state → HOLD

======================================================================
Tests: 14 passed, 0 failed out of 14 total
======================================================================
```

**Verification Command**:
```bash
npx tsx conformance_runner.ts coupling_gate.vectors.json
```

---

## 6. CI Gates Operational

### Gate 1: Preflight Nondeterminism Check

```bash
bash scripts/preflight_nondeterminism_check.sh
# ✅ PREFLIGHT PASSED: No forbidden nondeterminism patterns detected
```

**What it checks**:
- No `Date.now()` unless allowlisted
- No `new Date()` in output path
- No `Math.random()` without seed
- No `randomUUID()` calls
- No unseeded timers

### Gate 2: Determinism Verification

```bash
bash scripts/verify_marketing_street_determinism.sh
# ✅ DETERMINISM VERIFIED (5/5 seeds)
```

**What it checks**:
- Runs each seed twice
- Compares SHA256 (byte-identical required)
- Fails fast on first mismatch

---

## 7. Git Status at Release

```
On branch main
nothing to commit, working tree clean
```

All changes committed to commit `f3bd0bb8...`

---

## 8. Code Quality Audit Summary

| Check | Result | Notes |
|-------|--------|-------|
| TypeScript compilation | ✅ PASS | No type errors |
| Determinism (5 seeds) | ✅ PASS | 100% byte-identical |
| Conformance (14 vectors) | ✅ PASS | All coupling laws enforced |
| Preflight (forbidden patterns) | ✅ PASS | No Date.now(), Math.random(), etc. |
| JSON canonicalization | ✅ PASS | Keys sorted, reproducible hashing |

---

## 9. Known Limitations & Regression History

### Fixed Issue: Timestamp Nondeterminism (2026-02-22)

**Pattern**: `new Date().toISOString()` and `Date.now()`
**Impact**: Seed 111 produced different SHA256 on dual runs
**Root Cause**: `generated_at` field and `golden_run_id` included millisecond timestamps
**Fix**: Removed all timestamp logic
**Detection**: Mechanical verification (dual-run comparison)
**Status**: ✅ FIXED

### Related Documentation

See `DETERMINISM_CONTRACT.md` for:
- Forbidden patterns (strictly enforced)
- Required patterns (always apply)
- CI gate integration
- Regression prevention checklist

---

## 10. Reproducibility Instructions

To verify this proof bundle on any machine:

```bash
# 1. Clone or checkout commit f3bd0bb8...
git checkout f3bd0bb8ded2b859320e79227b9b0134f198ccf4

# 2. Verify file hashes
sha256sum CLAUDE.md ARCHITECTURE_V2.md marketing_street.cjs coupling_gate.ts conformance_runner.ts coupling_gate.vectors.json

# 3. Run determinism sweep
bash scripts/verify_marketing_street_determinism.sh

# 4. Run conformance tests
npx tsx conformance_runner.ts coupling_gate.vectors.json

# 5. Verify commit hash
git rev-parse HEAD
# Should output: f3bd0bb8ded2b859320e79227b9b0134f198ccf4
```

If all commands pass, this proof bundle is valid and unmodified.

---

## 11. No Rollback Without Re-verification

**Rule**: Any modification to files invalidates this proof bundle.

**Consequence**: Cannot "roll back" to a prior version without re-running:
1. Determinism gates (preflight + verification)
2. Conformance tests (14/14)
3. All CI checks

This prevents silent behavioral change and ensures audit trail transparency.

---

## 12. Future Proof Bundles

The next release must:
1. Increment date (e.g., `PROOF_BUNDLE_2026-02-23.md`)
2. Recompute all SHAs (files will change)
3. Re-run all gates (determinism + conformance)
4. Include new git commit hash
5. Document any fixes or improvements

Proof bundles are **never modified**. They are archived as immutable snapshots.

---

**Sealed**: 2026-02-22T12:00:00Z
**Authority**: Automated CI gates (non-negotiable)
**Verification**: Reproducible on any machine via instructions above
**Status**: FROZEN ✅
