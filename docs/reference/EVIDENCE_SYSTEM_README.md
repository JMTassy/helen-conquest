# Oracle Town Evidence System: Local Verification Layer

## What This Is

A **self-verifying evidence system** that prevents the breakthrough report (ORACLE_TOWN_EMULATION_EVIDENCE.md) from drifting as the codebase evolves.

The system consists of three components:

1. **Evidence Report** (ORACLE_TOWN_EMULATION_EVIDENCE.md) — 5 breakthroughs grounded in actual artifacts
2. **Evidence Extractor** (scripts/extract-emulation-evidence.py) — Machine validator
3. **Optional Gate** (scripts/town-check.sh with TOWN_EVIDENCE=1) — Integrates validation into the iteration loop

## Why It Matters

Evidence reports can become stale two ways:

**Type A: Silent Drift**
Someone regenerates policy.json (timestamp changes), and the report's policy hash no longer matches. The claim "policy is immutable" is now false, but nobody notices.

**Type B: Accidental Corruption**
Someone manually edits decision_record.json and removes the blocking_reasons field. The K3 (quorum) breakthrough is no longer valid, but the report still exists unchanged.

This system catches both by making evidence validation **automatic and deterministic**.

## How to Use

### Daily Development (Fast)
```bash
bash scripts/town-check.sh
```
- Runs: doc indices + Python syntax (65ms)
- Output: GREEN or RED
- Suitable for every commit loop

### Evidence Validation (Opt-In)
```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh
```
- Runs: indices + syntax + evidence extraction (100ms total)
- Validates 5 breakthrough claims
- Suitable for before submitting report for review

### Standalone Evidence Check
```bash
python3 scripts/extract-emulation-evidence.py
```
- Runs: evidence validation only
- Output: detailed breakdown of each breakthrough
- Suitable for debugging / understanding what's being validated

## What Gets Validated

### Breakthrough #1: K3 Quorum (Automatic Enforcement)
- ✓ decision_record.json has a blocking_reasons field
- ✓ Blocking reason mentions "missing classes ['LEGAL']"
- ✓ Decision is "NO_SHIP"
- Detects: if quorum rule is removed or decision changes

### Breakthrough #2: K4 Revocation (Key Status)
- ✓ public_keys.json has at least one REVOKED key
- ✓ Revoked key has a revocation date
- ✓ Active keys still exist in registry
- Detects: if key status is silently changed or registry corrupted

### Breakthrough #3: K5 Determinism (Decision Digest)
- ✓ hashes.json contains a decision_digest
- ✓ decision_record.json records the same digest
- ✓ Format is valid SHA256
- Detects: if decision digest is lost or altered

### Breakthrough #4: K7 Policy Pinning (Structure)
- ✓ policy.json has policy_id, quorum_rules, invariants fields
- ✓ hashes.json records a policy_hash
- ✓ Structure remains valid even if timestamps change
- Detects: if policy structure is gutted or mandatory fields removed

### Breakthrough #5: Determinism Tracking
- ✓ decision_digest is present in record
- ✓ Points to correct replay verification command
- Detects: if decision tracking is removed

## Expected Drift (Not an Error)

The system is **honest about expected changes**:

- **Policy hash will change** if policy.json is regenerated (timestamps are regenerated)
  - The validator notes this: "hash may differ if policy was regenerated"
  - Validates **structure** instead (policy_id, quorum_rules, invariants)

- **Ledger digest may change** if new attestations are added
  - The validator doesn't currently check ledger content (only existence)
  - Adding new runs/evidence is expected

- **Decision digest is stable** (same run should always produce same digest)
  - The validator checks this strictly
  - If it changes unexpectedly, that's a real problem

## Exit Codes

```
0 = all evidence present and valid
1 = evidence missing or validation failed
```

Suitable for CI/CD pipelines or pre-commit hooks (optional).

## Example: Detecting Drift

Scenario: Someone accidentally runs a script that deletes the blocking_reasons field from decision_record.json

Before fix:
```bash
$ TOWN_EVIDENCE=1 bash scripts/town-check.sh
...
❌ [K3 Quorum Breakthrough]
ERROR: MISSING field in decision_record: blocking_reasons
...
❌ SOME EVIDENCE VALIDATION FAILED
```

After restoring:
```bash
$ TOWN_EVIDENCE=1 bash scripts/town-check.sh
...
✓ Blocking reason: Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']
...
✅ ALL EVIDENCE VALIDATED (5/5 checks passed)
```

## Architecture

```
Developer edits CLAUDE.md or code
          ↓
   bash scripts/town-check.sh (default)
          ↓
   ✓ Indices fresh
   ✓ Python syntax valid
          ↓
   Ready to commit (fast loop, 65ms)

---optional evidence check---

   TOWN_EVIDENCE=1 bash scripts/town-check.sh
          ↓
   [calls] python3 scripts/extract-emulation-evidence.py
          ↓
   ✓ K3 breakthrough validated
   ✓ K4 breakthrough validated
   ✓ K5 breakthrough validated
   ✓ K7 breakthrough validated
   ✓ Determinism tracked
          ↓
   Report claims are verified
```

## Limitations (Honestly Stated)

The system does **not** provide:

- ❌ Cross-machine replay (this machine only)
- ❌ Formal proofs (only structural validation)
- ❌ Version control of schemas (expects stable structure)
- ❌ Cryptographic verification of signatures (only checks fields exist)
- ❌ Automatic CI/CD integration (gate is optional, local-only)

These would require additional layers (not minimal).

## Future Extensions

If evidence grows, natural additions:

1. **Multiple runs**: Add validators for runB, runC (copy-paste 3 new functions)
2. **Hash tracking**: Store expected hashes separately, handle drift gracefully
3. **Schema validation**: Use jsonschema to verify artifact structure
4. **Determinism tracking**: Auto-verify digest hasn't changed across runs
5. **Git hooks**: Pre-commit integration (optional)

None are needed for initial Month 1 iteration.

## Files

| File | Lines | Purpose |
|------|-------|---------|
| ORACLE_TOWN_EMULATION_EVIDENCE.md | 359 | Evidence-backed report (5 breakthroughs) |
| scripts/extract-emulation-evidence.py | 200 | Machine validator (K3, K4, K5, K7 checks) |
| scripts/town-check.sh | 105 | Gate with optional TOWN_EVIDENCE flag |

## Status

✅ **Complete and committed**

- All gates GREEN (indices, syntax, evidence)
- Ready for Month 1 iteration
- No external dependencies
- Backward compatible (default behavior unchanged)

## Next Step

Begin Month 1 autonomous governance iteration:

```bash
# Verify gates are green
bash scripts/town-check.sh

# Validate evidence report
TOWN_EVIDENCE=1 bash scripts/town-check.sh

# Follow SCENARIO_NEW_DISTRICT.md to propose your first governance mechanism
# System will force soft policy → hard constraints through test failures
```

---

**Design Principle:** Evidence reports should not silently become false. This system makes them locally verifiable and prevents drift through deterministic, automated checks.
