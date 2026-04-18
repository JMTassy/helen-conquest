# Oracle Town: Operational Reference Card

**Status:** Live and operational for Month 1 iteration
**Last Verified:** 2026-01-28 (all gates GREEN)

---

## One-Command Reference

```bash
# Daily (fast)
bash scripts/town-check.sh

# When writing governance claims
TOWN_EVIDENCE=1 bash scripts/town-check.sh

# Full verification (optional, heavier)
bash oracle_town/VERIFY_ALL.sh
```

---

## What Each Command Does

| Command | Time | Purpose | Use When |
|---------|------|---------|----------|
| `bash scripts/town-check.sh` | 65ms | Verify indices + syntax | Every commit |
| `TOWN_EVIDENCE=1 bash scripts/town-check.sh` | 100ms | Verify evidence report claims | Before submitting report |
| `bash oracle_town/VERIFY_ALL.sh` | 2-5s | Full governance verification | Touching core rules |
| `python3 scripts/extract-emulation-evidence.py` | 50ms | Manual evidence check | Debugging |

---

## The Two Modes

### Development Mode (Default)
```bash
bash scripts/town-check.sh
```
- Fast: checks documentation consistency only
- No report validation
- Safe for every commit loop
- **Output:** GREEN or RED

### Mayor Mode (Opt-In)
```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh
```
- Validates all evidence claims in ORACLE_TOWN_EMULATION_EVIDENCE.md
- Checks K3, K4, K5, K7 breakthroughs
- Catches drift, missing fields, changed structure
- **Output:** GREEN or RED with detailed evidence validation

---

## What Gets Validated in Mayor Mode

### K3: Quorum Enforcement
```
File: oracle_town/runs/runA_no_ship_missing_receipts/decision_record.json
Field: blocking_reasons
Check: Contains "missing classes ['LEGAL']"
Fails if: Field missing or content changed
```

### K4: Key Revocation
```
File: oracle_town/keys/public_keys.json
Field: keys[].status
Check: At least one key marked REVOKED with timestamp
Fails if: All revoked keys removed or status changed
```

### K5: Determinism
```
File: oracle_town/runs/runA_no_ship_missing_receipts/hashes.json
Field: decision_digest
Check: Digest is present and valid SHA256
Fails if: Digest missing or modified
```

### K7: Policy Pinning
```
File: oracle_town/runs/runA_no_ship_missing_receipts/policy.json
Fields: policy_id, quorum_rules, invariants
Check: All three fields present and populated
Fails if: Any field missing (note: hash may differ if regenerated)
```

### Reproducibility
```
File: oracle_town/runs/runA_no_ship_missing_receipts/decision_record.json
Field: decision_digest
Check: Matches expected value from hashes.json
Fails if: Digest changed
```

---

## Interpreting Output

### GREEN (both modes)
```
✅ GREEN — all gates passed
```
- All indices fresh
- All syntax valid
- (In Mayor mode) All evidence validated
- **Action:** Safe to commit

### RED (development mode)
```
ERROR: CLAUDE.md indices are stale (regeneration produced changes)
```
- Your edits changed documentation
- Indices need regeneration
- **Fix:**
  ```bash
  python3 scratchpad/generate_claude_index.py
  git add scratchpad/CLAUDE_MD_*.txt
  git commit -m "docs: regenerate CLAUDE.md indices"
  ```

### RED (Mayor mode)
```
❌ [K3 Quorum Breakthrough]
ERROR: MISSING field in decision_record: blocking_reasons
```
- Evidence claim cannot be validated
- Some artifact is missing or changed
- **Action:** Investigate and fix the artifact, then re-run validation

---

## Month 1 Iteration Pattern

```
Day 1: Propose governance (edit CLAUDE.md)
       → bash scripts/town-check.sh
       → If RED: regenerate indices
       → If GREEN: move to Day 2

Day 2: Write tests (add test_privacy_district.py)
       → bash oracle_town/VERIFY_ALL.sh
       → If RED: tests fail (expected)
       → Fix policy to make tests pass

Day 3-4: Iterate until tests GREEN
        → bash oracle_town/VERIFY_ALL.sh
        → Fix policy, test, repeat
        → When GREEN: governance locked in

After Day 4: Validate evidence (if making claims)
            → TOWN_EVIDENCE=1 bash scripts/town-check.sh
            → If GREEN: report is durable
            → If RED: claims need updating
```

---

## Expected Drift (Not an Error)

The system handles expected changes gracefully:

### Policy Hash Changes (Expected)
- **Why:** policy.json contains effective_date timestamp
- **When:** After `python3 oracle_town/core/policy.py --regenerate`
- **Validator Output:**
  ```
  ℹ Policy hash recorded: sha256:f5d4c1f28b132a1ff78fa32...
  ℹ Note: hash may differ if policy was regenerated (timestamps change)
  ```
- **Status:** ✓ OK, not a failure

### Decision Digest Stable (Not Expected to Drift)
- **Why:** Same claim + policy should produce identical decision
- **When:** Should be identical on every replay
- **Validator Output:**
  ```
  ✓ Verify with: python3 oracle_town/core/replay.py --run runA --iterations 10
  ```
- **Status:** ✗ If this changes, something is wrong

---

## Troubleshooting

### "Indices are stale"
```
ERROR: CLAUDE.md indices are stale (regeneration produced changes)
```
**Cause:** You edited CLAUDE.md but didn't regenerate indices
**Fix:**
```bash
python3 scratchpad/generate_claude_index.py
git add scratchpad/CLAUDE_MD_*.txt
bash scripts/town-check.sh  # Verify it's now GREEN
```

### "Evidence validation failed"
```
ERROR: Evidence validation failed
Some artifacts cited in ORACLE_TOWN_EMULATION_EVIDENCE.md are missing or changed.
```
**Cause:** Some breakthrough claim can't be validated
**Debug:**
```bash
python3 scripts/extract-emulation-evidence.py  # Run standalone to see which check failed
```
**Fix:** Update the artifact to match the claim, or update the claim to match the artifact

### "Python syntax error"
```
ERROR: Python syntax error detected
Run: python3 -m py_compile <file.py> for details
```
**Cause:** You created or edited a .py file with syntax error
**Fix:**
```bash
python3 -m py_compile oracle_town/core/new_file.py  # Shows exact error
# Fix the syntax error
bash scripts/town-check.sh  # Verify it's now GREEN
```

---

## Files You Interact With

| File | Purpose | Edit When | Run When |
|------|---------|-----------|----------|
| CLAUDE.md | Project documentation | Proposing new mechanism | Always before committing |
| SCENARIO_NEW_DISTRICT.md | Governance walkthrough | Learning how system works | Starting Month 1 |
| ORACLE_TOWN_EMULATION_EVIDENCE.md | Evidence-backed report | Making governance claims | Writing Mayor-grade docs |
| scripts/town-check.sh | Local gate | Never (it's stable) | Before every commit |
| scripts/extract-emulation-evidence.py | Evidence validator | Never (it's stable) | When validating claims |
| tests/test_*.py | Governance tests | When implementing policy | After implementing |
| oracle_town/runs/runA_*/decision_record.json | Decision artifacts | Never (auto-generated) | When validating evidence |

---

## Architecture at a Glance

```
Developer → Edit CLAUDE.md / tests / code
  ↓
bash scripts/town-check.sh (default)
  ├─ Regenerate indices
  ├─ Check for diffs
  ├─ Validate Python syntax
  └─ Exit 0 (GREEN) or 1 (RED)

If RED:
  ├─ Fix stale indices, OR
  ├─ Fix syntax error
  └─ Re-run gate

If GREEN:
  ├─ Normal commits: DONE
  └─ Mayor-grade claims: TOWN_EVIDENCE=1 bash scripts/town-check.sh
      ├─ Validate K3 (quorum)
      ├─ Validate K4 (revocation)
      ├─ Validate K5 (determinism)
      ├─ Validate K7 (policy)
      └─ Exit 0 (GREEN, claims durable) or 1 (RED, claims drifted)
```

---

## Key Principles

1. **Minimal by Default** — Daily loop is 65ms, no evidence overhead
2. **Friction on Demand** — Add evidence validation only when claiming governance
3. **Fail-Closed** — Missing evidence = RED, not assumed OK
4. **Honest Limits** — We say what we can't verify (cross-machine, formal proofs, etc.)
5. **Replayable** — Every claim has an exact command to reproduce it
6. **Audit Trail** — All decisions logged in decision_record.json + git

---

## Next Steps

**Right Now:**
```bash
bash scripts/town-check.sh
# If GREEN: ready to begin
# If RED: fix indices and retry
```

**In the Next Hour:**
1. Read SCENARIO_NEW_DISTRICT.md (30 min)
2. Understand the iteration pattern

**In the Next Day:**
1. Propose Privacy District (or custom mechanism)
2. Follow iteration loop: edit → gate → test → commit

**In the Next Month:**
1. Let test failures force governance clarity
2. Document what emerged vs was planned
3. Use MONTH_1_OBSERVATION_LOG.md to track patterns

---

## Support

For detailed explanations, see:
- EVIDENCE_SYSTEM_README.md — How evidence validation works
- SYSTEM_READY_FOR_AUTONOMY.md — How autonomy actually works
- MONTH_1_OBSERVATION_LOG.md — What to observe week-by-week

For quick reference, this file.

---

**Version:** 1.0 (2026-01-28)
**Status:** Live
**Next Review:** After Month 1 iteration
