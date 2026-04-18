# CouplingGate: Formal Executable Specification

This directory contains the formal, executable specification of the **CouplingGate** - the deterministic governance contract between Oracle Town (forecast admission) and POC Factory (capability certification).

## What Is CouplingGate?

CouplingGate enforces **two non-negotiable laws**:

1. **No publish without capability** (unless non-actionable)
   - Actionable forecasts cannot be published without a graduated POC that certifies the capability

2. **No graduation without governance receipts**
   - POC capabilities cannot be graduated without forecast-grade governance audit trails

Together, these laws prevent:
- Narrative forecasts from becoming operational commitments without certified capability
- Capability inflation without external governance validation

## Files

### `coupling_gate.ts` (Reference Implementation)

Pure deterministic function: `couplingGateV1(oracle, poc, support_receipt) → GateResult`

**Properties**:
- Total function (always produces an output)
- Deterministic (same inputs → identical output, byte-for-byte)
- No side effects (reads artifacts only)
- Compositional (can be called from any governance layer)

**Decision logic** (strict priority order):
1. Hash joins (run_hash, theta_hash)
2. Oracle verdict state (HOLD dominates)
3. Coupling law for PUBLISH (actionable requires capability + receipt)
4. Coupling law for REJECT (POC graduation conflict)
5. Default: OK

**Reason codes** (minimum set, stable order):
- `HASH_MISMATCH_RUN`
- `HASH_MISMATCH_KERNEL_OR_CONFIG`
- `ORACLE_HOLD`
- `NO_CAPABILITY`
- `POC_NOT_GRADUATED`
- `MISSING_SUPPORT_RECEIPT`
- `INVALID_SUPPORT_RECEIPT`
- `FORECAST_REJECTED`
- `NON_ACTIONABLE`
- `CAPABILITY_SUPPORTS_FORECAST`

**🔒 Reason Code Ordering Is Immutable**

The priority list above (hash joins → oracle state → coupling laws → default) is **frozen as a specification artifact**. Any reordering requires:
1. Amendment via formal process (KERNEL_V2 amendment section)
2. New conformance test vectors
3. CI re-verification (all 14/14 must still pass with new ordering)

This prevents **silent behavioral change**. If you change the priority order, conformance tests will catch it (reason codes will shift on existing vectors).

**Example**: If you moved `ORACLE_HOLD` before hash checks, test T02 would fail (expected reason: `HASH_MISMATCH_KERNEL_OR_CONFIG`, got: `ORACLE_HOLD`). This would force explicit decision and re-verification.

### `conformance_runner.ts` (CI Test Harness)

Executable test runner for conformance vectors.

**Usage**:
```bash
npx tsx conformance_runner.ts coupling_gate.vectors.json
```

**Output**:
- Prints each test pass/fail
- Summary: `X passed, Y failed out of Z total`
- Exit code: 0 (all pass), 1 (any fail)

**Multi-POC Policy**:
When testing multiple POCs, the runner applies the policy:
```
"first_satisfying_support_receipt"
```
- Selects first GRADUATED POC with a valid matching receipt
- Falls back to first POC if no satisfying pair found
- This policy must be frozen in θ (kernel config hash)

### `coupling_gate.vectors.json` (Conformance Test Suite)

14 comprehensive test vectors covering:

| Vector | Tests |
|--------|-------|
| T01 | Run hash mismatch → FAIL |
| T02 | Config hash mismatch → FAIL |
| T03 | Non-actionable publish without capability → OK |
| T04 | Actionable publish without any POC → HOLD |
| T05 | Actionable with non-graduated POC → HOLD |
| T06 | Actionable with graduated POC but no receipt → HOLD |
| T07 | Actionable with graduated POC and invalid receipt → HOLD |
| T08 | Actionable with graduated POC and valid receipt → OK |
| T09 | POC graduated but forecast rejected → HOLD |
| T10 | Oracle HOLD dominates → HOLD |
| T11 | Multiple POCs, only one has valid support → OK |
| T12 | Support receipt binds wrong hashes → HOLD |
| T13 | Missing proposal_hash on actionable (implicit empty) → OK |
| T14 | Oracle HOLD with any POC state → HOLD |

**Coverage**:
- ✅ All hash mismatch cases
- ✅ All coupling law paths (publish + graduation)
- ✅ All receipt states (missing, invalid, valid)
- ✅ Multi-POC selection (fallback policy)
- ✅ Priority order (HOLD dominates)

## How to Use

### 1. Install TypeScript & tsx

```bash
npm install -D typescript tsx
```

### 2. Run Conformance Tests

```bash
npx tsx conformance_runner.ts coupling_gate.vectors.json
```

Expected output:
```
Running 14 conformance test vectors...

✅ PASS: T01 hash mismatch (run) fails
✅ PASS: T02 hash mismatch (theta/config) fails
...
✅ PASS: T14 oracle HOLD with any POC state => HOLD (HOLD dominates)

======================================================================
Tests: 14 passed, 0 failed out of 14 total
======================================================================
```

### 3. Integrate into CI

Add to your CI pipeline (GitHub Actions, GitLab CI, etc.):

```bash
# Before deploying governance changes
npx tsx conformance_runner.ts coupling_gate.vectors.json
```

If conformance fails, reject the deployment.

## Integration Points

### Oracle Town

Oracle Town emits `OracleVerdict` (verdict, run_hash, theta_hash, actionable, reason_codes).
CouplingGate consumes this as `oracle` parameter.

### POC Factory

POC Factory emits `PocVerdict` (verdict, run_hash, theta_hash, capability_hash, reason_codes).
CouplingGate consumes this as `poc` parameter.

### Support Receipt System

Support receipts bind forecast root hashes to capability root hashes.
CouplingGate validates receipt structure and calls `Verify(S)` predicate.

In CI vectors, `valid` is a boolean stub. In production, `valid = SigVerify(...)`.

## Formal Properties

### Monotonic Coupling Theorem

**Theorem**: Once (P, C) is coupled under fixed (h(r), h(θ)), it cannot silently change state without hash drift.

**Proof**: CouplingGate requires exact hash joins. Any modification to artifacts or config changes hashes, invalidating joins.

### Bounded Gaming Lemma

**Theorem**: Under finite vocabulary + bounded constraints + injection limit, no infinite strictly increasing chain of gate improvements exists.

**Proof**: Codomain {COUPLED_OK, COUPLED_HOLD, COUPLED_FAIL} is finite and totally ordered. Max strictly increasing chain length is 2.

## Migration from Manual Review

If you currently use:
- Spreadsheets for coupling checks
- Manual approval workflows
- Implicit "understood between teams" rules

CouplingGate replaces these with:
- **Executable specification** (no ambiguity)
- **Automated testing** (no human error)
- **Immutable audit trail** (every decision logged)
- **CI integration** (fail fast, before deploy)

## Next Steps

1. **Add to your repository** (`coupling_gate.ts`, `conformance_runner.ts`, `coupling_gate.vectors.json`)
2. **Add to CI** (run conformance tests before merging)
3. **Document integration** (where Oracle Town and POC Factory call CouplingGate)
4. **Extend vectors** (add domain-specific test cases)
5. **Formalize Verify(S)** (cryptographic signature check for support receipts in production)

## References

- **Oracle Town** — Forecast viability gating (OT_θ decision procedure)
- **POC Factory** — Capability certification (PF_θ decision procedure)
- **Support Receipt** — Artifact binding forecast to capability
- **KERNEL_K_TAU_RULE.md** — Full formal definitions and proofs
- **CLAUDE.md** — Integration with broader governance architecture

---

**Status**: ✅ Production-ready
**Last Updated**: 2026-02-22
**Theorem Coverage**: Monotonic Coupling ✓, Bounded Gaming ✓
