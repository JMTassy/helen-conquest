# Critical Integrity Audit Fixes

**Audit By:** Expert governance reviewer
**Date:** 2026-01-30
**Priority:** Critical (governance consistency)

---

## Summary

Six structural issues identified that threaten repo integrity and governance consistency. All issues are actionable and have clear fixes. This document tracks status and resolution path.

---

## Issue 1: Index Files Governance State

**Status:** ✅ VERIFIED CLEAN

**Finding:** Indices were regenerated and staged AFTER the commit that modified CLAUDE.md

**Concern:** If indices are part of the governance chain (determinism verification, audit trail), then having them staged but not committed is a state inconsistency.

**Verification:**
```bash
git status → "On branch main, nothing to commit"
git diff --cached → empty (no staged files)
```

**Resolution:** ✅ CLEAN - Indices are already committed. No action needed.

**Lesson:** For governance systems, always verify `git status` shows no staged-but-uncommitted changes.

---

## Issue 2: K23 Enforcement Mechanism Missing

**Status:** 🚧 REQUIRES FIX

**Finding:** K23 (Mayor Purity) is defined as an invariant but lacks explicit enforcement mechanism.

**Problem:** Enforcement mechanism is critical for testability and audit. "Mayor is pure" means nothing if we don't specify HOW we enforce it.

**Current State:**
```
| K23 | Mayor Purity | mayor_rsm.py | Pure function only: (claim, evidence, policy) → receipt |
```

**Missing:** Clear enforcement method (static analysis or runtime sandbox)

**Fix Required:** Add one of these enforcement patterns:

### Option A: Static Import Boundary (Preferred - Testable in CI)
```python
# mayor_rsm.py MUST NOT import:
# - os, sys, subprocess, shutil
# - socket, requests, http.client
# - sqlite3, json.dumps (file I/O)
# - time, datetime (environmental state)
# - random (non-deterministic)

# ALLOWED imports:
# - copy (shallow copy)
# - typing (annotations only)
# - custom pure helper modules
```

**Test (CI Gate):**
```bash
#!/bin/bash
# test_mayor_purity_imports.py
FORBIDDEN_MODULES="os,subprocess,socket,requests,sqlite3,time,random"
for module in ${FORBIDDEN_MODULES//,/ }; do
  if grep -q "^import $module\|^from $module" mayor_rsm.py; then
    echo "FAIL: Mayor imports $module (K23 violation)"
    exit 1
  fi
done
echo "PASS: Mayor imports are pure"
```

### Option B: Runtime Sandbox (Execution-time verification)
```python
def test_mayor_purity():
    """Runtime verification: Mayor runs with NO I/O capability"""
    import restricted_exec

    # Attempt to call Mayor with restricted permissions
    # Should not be able to:
    # - Read/write files
    # - Make network calls
    # - Access environment variables
    # - Generate random numbers
    # - Call time.time()

    result = restricted_exec.run(mayor.ratify, claims, evidence, policy)
    assert result is not None  # Mayor executed successfully
```

**Recommendation:** Implement **Option A** (static analysis) as a CI gate:
- Easier to verify
- Deterministic
- Cannot be accidentally bypassed at runtime

**Action Required:**
1. Choose enforcement pattern (A or B)
2. Add to CLAUDE.md under K23 enforcement
3. Implement CI check (test or lint rule)

---

## Issue 3: K24 "Unreachable" Needs Deterministic Definition

**Status:** 🚧 REQUIRES FIX

**Finding:** K24 states "daemon unreachable → execution denied" but doesn't define what "unreachable" means.

**Problem:** Without deterministic definition, implementers will add retry logic, which gradually converts fail-closed to eventual-allow:

```python
# BAD: Silent retry-on-failure (violates K24)
def execute_with_kernel(claim):
    for attempt in range(3):  # Retries hide the failure
        try:
            receipt = kernel.ratify(claim)
            if receipt:
                return execute(claim)
        except ConnectionError:
            continue  # Keep retrying!

    # Falls through after retries...
    # Temptation: "Well, kernel was just slow, execute anyway"
    return execute(claim)  # BUG: fail-closed → eventual allow
```

**Current K24 Definition:**
```
K24 | Kernel Daemon Liveness | If unreachable → execution denied (fail-closed)
```

**Required:** Specify timeout/retry semantics

**Proposed K24 Hardening:**
```
K24 | Kernel Daemon Liveness |
     Execution denied if:
     - TCP connect fails (port not listening)
     - No response within T=250ms (single attempt)
     - Policy hash mismatch (daemon might be compromised)
     NO RETRIES. FAIL CLOSED.
     Rationale: Prevent retry-on-failure from converting fail-closed to eventual-allow
```

**Constraint to Add:**
```
**Daemon Liveness Hardening (K24):**
- Unreachable := TCP connect fails OR response timeout > 250ms
- Retry count := 0 (no retries; fail on first timeout)
- Fallback := execution DENIED (not deferred, not retried)
- Monitoring := Moltbot must alert if daemon unreachable for > 60s
```

**Action Required:**
1. Add timeout/retry semantics to K24 definition
2. Add constraint text specifying exact timeout value
3. Document monitoring requirement (alert on persistent unreachability)

---

## Issue 4: Commit Hash Reconciliation

**Status:** ✅ VERIFIED CLEAN

**Finding:** Transcript references commit ea363c4, but final `git log` shows 97b1b92 as latest.

**Verification:**
```bash
git log --oneline | head -5
# Output:
97b1b92 security: add critical kernel hardening (K23, K24) + Mayor purity statement
ea363c4 docs: Oracle Town as drop-in safety kernel for Moltbot/OpenClaw
311d64e docs: complete status — Oracle Town is now a jurisdiction
```

**Resolution:** ✅ CLEAN - Both commits exist on branch. This is the correct linear history.

**Lesson:** For governance audit, always provide full git log output showing complete commit chain.

---

## Issue 5: K23 Enforcement Method (Duplicate of Issue 2)

**Status:** 🚧 REQUIRES FIX (Same as Issue 2)

**Finding:** K23 lacks explicit test/verification mechanism

**Resolution:** See Issue 2 (static import analysis as CI gate)

---

## Issue 6: Invariant Table Duplication Check

**Status:** ✅ VERIFIED CLEAN

**Verification:**
```bash
rg -n "### Oracle Town Governance Invariants|### Safety Kernel Invariants" CLAUDE.md
# Output:
755:### Oracle Town Governance Invariants
770:### Safety Kernel Invariants (Moltbot/OpenClaw)
```

**Finding:** No duplication. Tables are properly separated.

---

## Summary of Actionable Fixes

### CRITICAL (Must Fix Before Production)

1. **K23 Enforcement Mechanism** (Issue 2)
   - Add static import check as CI gate
   - OR define runtime sandbox verification
   - Estimated effort: 30 minutes
   - Impact: Makes K23 testable and enforceable

2. **K24 Timeout/Retry Definition** (Issue 3)
   - Add deterministic "unreachable" definition
   - Specify timeout value (suggest: 250ms, no retries)
   - Add monitoring requirement (alert on persistent unreachability)
   - Estimated effort: 15 minutes
   - Impact: Prevents retry-on-failure attack

### NICE-TO-HAVE (Governance Hygiene)

3. **Enforcement Test Implementation** (Related to K23)
   - Write CI test for mayor import purity
   - Add to `tests/test_mayor_purity.py`
   - Run on every commit
   - Estimated effort: 45 minutes
   - Impact: Catches K23 violations in review

---

## Proposed Changes to CLAUDE.md

### 1. K23 Enhancement (Add enforcement)

**Current:**
```
| K23 | Mayor Purity | mayor_rsm.py | Pure function only: (claim, evidence, policy) → receipt |
```

**Proposed:**
```
| K23 | Mayor Purity | mayor_rsm.py | Pure function: (claim, evidence, policy) → receipt. Enforcement: Static import boundary (no os/subprocess/socket/requests) |
```

### 2. K24 Enhancement (Add timing semantics)

**Current:**
```
| K24 | Kernel Daemon Liveness | kernel_daemon.py | If unreachable → execution denied (fail-closed) |
```

**Proposed:**
```
| K24 | Kernel Daemon Liveness | kernel_daemon.py | Unreachable := TCP fail OR timeout > 250ms. Retry := 0. Default: DENY. Monitoring: alert if unreachable > 60s |
```

### 3. Add K24 Constraint (New subsection)

**Add under "Safety Kernel (Moltbot/OpenClaw)" constraints:**
```
- **Daemon Liveness Hardening (K24)**:
  - "Unreachable" defined as: TCP connect fails OR no response within 250ms
  - Retry policy: 0 retries (fail on first timeout)
  - Fallback: execution DENIED (not deferred, not retried)
  - Monitoring: Moltbot MUST alert if kernel daemon unreachable for > 60s
  - Rationale: Prevent retry-on-failure from converting fail-closed into eventual-allow
```

### 4. Add K23 Enforcement Test Specification

**Add under "Testing" section, new subsection:**
```
**Mayor Purity Tests (K23 enforcement):**
- Import boundary check: Mayor module imports no I/O modules
  - Forbidden: os, sys, subprocess, socket, requests, sqlite3, time, random
  - Allowed: typing, copy, custom pure helpers only
  - Run: Python linter rule in CI (`rg "^import (os|sys|subprocess)" mayor_rsm.py`)
- Runtime verification (optional):
  - Mayor executes with restricted file/network/env access
  - Implementation: Use restricted_exec or native Python sandbox
```

---

## Implementation Order

1. **First (5 min):** Read this document
2. **Second (15 min):** Add K24 timeout/retry definition to CLAUDE.md
3. **Third (15 min):** Add K23 enforcement method to CLAUDE.md
4. **Fourth (30 min):** Implement K23 CI test (`tests/test_mayor_purity.py`)
5. **Fifth (10 min):** Commit all changes
6. **Sixth (optional, 45 min):** Implement K24 monitoring alert

---

## Verification Checklist

After implementing fixes:

- [ ] K23 now explicitly specifies enforcement method
- [ ] K24 now specifies timeout/retry semantics
- [ ] K24 constraint section added to CLAUDE.md
- [ ] CI test exists for mayor import purity
- [ ] git status shows clean (no staged changes)
- [ ] All commits appear in git log
- [ ] scratchpad indices up-to-date

---

## Why This Matters

These six issues (identified by the audit) are exactly how governance systems degrade:

1. **Index state inconsistency** → Audit trail becomes untrusted
2. **Missing enforcement mechanisms** → Invariants become guidelines (and get violated)
3. **Vague definitions** (like "unreachable") → Implementers add "safe" workarounds that undermine the rule
4. **Commit history gaps** → Difficult to verify what actually shipped
5. **Unenforced invariants** → Can be accidentally violated in code review

This document and these fixes ensure Oracle Town's kernel specification stays governance-grade, not just well-documented.

---

**Status:** Ready for implementation
**Priority:** CRITICAL (blocks Phase 1 MVP)
**Time to Fix:** ~1 hour total
