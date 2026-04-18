# 🚀 BEGIN MONTH 1: Oracle Town Autonomous Iteration

**Date:** 2026-01-29
**Status:** ✅ READY TO BEGIN
**Your Next Steps:** Follow this guide to launch Month 1

---

## What You're About to Do

You're starting **Oracle Town's first autonomous month** where the system:
- ✅ **Validates itself** (no silent drift)
- ✅ **Shows itself visually** (ASCII town on every gate run)
- ✅ **Accepts external knowledge** (Bibliothèque)
- ✅ **Records immutable decisions** (deterministic ledger)
- ✅ **Demonstrates governance hardening** (soft → hard constraints via tests)

---

## 3-Minute Quick Start

### 1. Verify the System is Live

```bash
bash scripts/town-check.sh
```

**Expected output:**
- Gate status: `GREEN ✅`
- ASCII town visualization
- Last line: "continue iterating"

### 2. See ASCII Town with Full Evidence

```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh
```

**Expected output:**
- All gates pass
- Evidence validation: `5/5 ✅`
- ASCII shows: COURT OF EVIDENCE `extract-evidence ✅`

### 3. View the Map

```bash
cat TOWN_MAP.md
```

**What you'll see:**
- Mermaid diagrams (structure, workflow, gates, knowledge integration)
- Daily workflow from claim → decision → ledger
- Month 1 roadmap

---

## Your Month 1 Mission

### Week 1: Demonstrate Governance Hardening

**Goal:** Add Privacy District to handle GDPR claims

**Files to read:**
1. SCENARIO_NEW_DISTRICT.md (366 lines, day-by-day walkthrough)
2. Follow the 5-day scenario exactly

**What happens:**
1. Day 1: Define soft policy (PDF best-effort language)
2. Day 2: Write test (fails on soft language)
3. Day 3: Harden policy (deterministic rules)
4. Day 4: Test passes
5. Day 5: Record decision with proof

**Evidence generated:**
- Soft policy → Hard policy transformation
- Test failure → Pass log
- Decision record with policy hash
- Citation in MONTH_1_OBSERVATION_LOG.md

---

### Week 2: Integrate External Knowledge

**Goal:** Submit knowledge via Bibliothèque

**What you can submit:**
- Math proofs (K5 determinism theorems)
- Old code (legacy patterns)
- Research papers (governance references)
- Empirical data (benchmark results)
- Operational logs (incidents, post-mortems)
- Policy drafts (governance proposals)

**How to submit:**

```bash
# Example: Math proof
cat << 'EOF' | python3 scripts/bibliotheque_intake.py MATH_PROOF
Claim: K3 quorum prevents single-agent decisions
Proof: By definition, quorum requires min N distinct classes.
       Since N ≥ 2, single agent cannot satisfy quorum.
       Therefore, single agent cannot force decision.
       QED.
EOF
```

**What happens:**
- ✅ ACCEPTED
- Hashed (SHA256, K7 pinning)
- Integrated into oracle_town/memory/bibliotheque/
- Cited in next decision_record.json
- Available for replay testing (K5)

---

### Week 3: Track Emergence Patterns

**Goal:** Instrument E1, E4, E5 failure detectors

**Patterns to watch:**

| Pattern | Detector | When | Record |
|---------|----------|------|--------|
| **E1: Quorum Convergence** | class_count < min_quorum | Blocks decision | Marks as E1 in log |
| **E4: Revocation Cascade** | revoked_key used recently | Rejects attestation | Marks as E4 in log |
| **E5: Trust Network** | agent_id overused | Multiple roles | Marks as E5 in log |

**How to track:**
1. Run MONTH_1_OBSERVATION_LOG.md template
2. Record each E1, E4, E5 occurrence
3. Note what triggered it
4. What rule emerged?
5. Update policy if needed
6. Test enforces it

**Example entry:**
```
Week 3, Day 1: E1 Pattern
  Trigger: GDPR district missing LEGAL attestor (CI_RUNNER only)
  Detection: class_count = 1, min_quorum = 2 → E1 Convergence
  Rule emerged: "GDPR requires LEGAL + CI_RUNNER (2 distinct)"
  Test added: test_gdpr_quorum_enforcement.py
  Policy updated: quorum_rules[gdpr_consent_banner]
  Status: ✅ Enforced
```

---

### Week 4: Month 1 Summary

**Deliverables:**
1. MONTH_1_OBSERVATION_LOG.md (completed)
2. New governance rules (soft → hard)
3. Pattern detectors (E1, E4, E5)
4. Evidence still valid (no drift)
5. Knowledge base integrated (Bibliothèque)

**Verification:**
```bash
# Check evidence hasn't drifted
TOWN_EVIDENCE=1 bash scripts/town-check.sh

# Output should show:
# ✅ K3 Quorum Breakthrough
# ✅ K4 Revocation Breakthrough
# ✅ K5 Determinism Breakthrough
# ✅ K7 Policy Pinning Breakthrough
# ✅ Reproducibility Breakthrough
```

**Ready for Month 2:**
- ✅ Governance system operational
- ✅ Evidence non-drifting
- ✅ Patterns instrumented
- ✅ Knowledge base live
- ✅ Scalable to larger governance

---

## The Three Commands You'll Use Every Day

### Command 1: Daily Gate (65ms)

```bash
bash scripts/town-check.sh
```

- Checks: indices fresh + syntax valid
- Shows: ASCII town (live status)
- Use: Every iteration before commit
- Displays: Current decision, policy hash, digest

### Command 2: Report Validation (100ms)

```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh
```

- Checks: All gates + 5/5 evidence breakthroughs
- Shows: ASCII town with evidence validation
- Use: Before submitting report or claiming governance
- Validates: K3, K4, K5, K7, reproducibility

### Command 3: Submit Knowledge

```bash
cat file | python3 scripts/bibliotheque_intake.py <TYPE>
```

- Types: MATH_PROOF, CODE_ARCHIVE, RESEARCH, DATA, OPERATIONAL, POLICY
- Output: ✅ ACCEPTED or ⚠️ WARN/ERROR
- File created: oracle_town/memory/bibliotheque/{type}/{id}/
- Integrated: Into next decision_record.json with hash pinning

---

## ASCII Town Explained

Every time you run `bash scripts/town-check.sh`, you see:

```
ORACLE TOWN  (local)                                2026-01-29 HH:MM:SS
══════════════════════════════════════════════════════════════════════

            🧱 CITY WALL (Fail-Closed K1)
        ┌────────────────────────────────┐
        │  TOWN GATE: town-check.sh      │
        │  STATUS:  GREEN ✅              │  ← Current gate status
        └──────────────┬─────────────────┘
```

**What each section means:**

| Section | Shows | Meaning |
|---------|-------|---------|
| **DOCS DISTRICT** | `generator.py ✅` | Indices current |
| | `CLAUDE.md ✅` | Documentation fresh |
| **GOVERNANCE DISTRICT** | `policy.json ✅` | Policy loaded |
| | `K3 quorum active ✅` | Quorum rule enforced |
| **COURT OF EVIDENCE** | `extract-evidence ✅` | Evidence validated (when enabled) |
| | `evidence_status: 5/5 ✅` | All 5 breakthroughs pass |
| **DECISION LEDGER** | `run: runC_ship_quorum_valid` | Latest run |
| | `decision: SHIP` | Last decision |
| | `policy_hash: sha256:...` | Policy version |
| | `decision_digest: sha256:...` | Determinism marker |

**If any ❌ appears:**
- Red means that component failed validation
- Run `TOWN_EVIDENCE=1 bash scripts/town-check.sh` for details
- Check SYSTEM_READINESS_CHECKLIST.md for troubleshooting

---

## File Organization

### Read First (Quick Orientation)

- **QUICK_START_AUTONOMOUS.md** (159 lines) — 5-minute overview
- **THIS FILE** (BEGIN_MONTH_1.md) — Your launch guide
- **TOWN_MAP.md** — Visual navigation (Mermaid diagrams)

### For Month 1 Work

- **SCENARIO_NEW_DISTRICT.md** (366 lines) — Day-by-day walkthrough
- **MONTH_1_OBSERVATION_LOG.md** (373 lines) — Metrics template (fill as you go)

### Reference & Evidence

- **AUTONOMOUS_MODE_ACTIVATED.md** (282 lines) — System state
- **ORACLE_TOWN_EMULATION_EVIDENCE.md** (359 lines) — 5 breakthroughs (the proof)
- **SYSTEM_READINESS_CHECKLIST.md** (285 lines) — Full verification

### Knowledge Base

- **oracle_town/memory/BIBLIOTHEQUE_INTAKE.md** (320+ lines) — Protocol
- **scripts/bibliotheque_intake.py** (250 lines) — Ingestion validator

### Gates & Automation

- **scripts/town-check.sh** — Daily gate (regenerated with this session)
- **scripts/generate_town_ascii.py** — ASCII town generator (new)
- **TOWN_ASCII.generated.txt** — Live town status (auto-updated)

---

## System Guarantees (Cannot Be Broken)

These are **hardened** (you can't remove them, bypass them, or weaken them):

| Invariant | Guarantee |
|-----------|-----------|
| **K0** | Only registered attestors can sign decisions |
| **K1** | Default is NO_SHIP (burden of proof) |
| **K2** | agent_id ≠ attestor_id always |
| **K3** | Min N distinct attestor classes required |
| **K4** | Revoked keys never accepted |
| **K5** | Same input → same output (30x verified) |
| **K7** | Policy immutable via hash |
| **K9** | All decisions reproducible & auditable |

---

## Scenario: Your First Day

### 9 AM: Start the day

```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
bash scripts/town-check.sh
```

✅ Town shows GREEN, decision SHIP

### 10 AM: Read SCENARIO_NEW_DISTRICT.md

- Day 1 walkthrough (Privacy District addition)
- Day 1 Step 1: Define soft policy
- Create oracle_town/districts/privacy/policy_draft.md

### 11 AM: Day 1 work (follow scenario exactly)

- Soft policy written (mentions "usually", "probably", "if needed")
- Policy validator checks: ⚠️ WARN (soft language detected)

### 2 PM: Commit work

```bash
git add oracle_town/districts/privacy/policy_draft.md
git commit -m "docs: Privacy District soft policy draft (needs hardening)"
bash scripts/town-check.sh  # Gate still GREEN (indices fresh)
```

### 3 PM: Town shows updated ASCII

- Gate: GREEN ✅
- Policy: soft language 3 phrases detected
- Note in MONTH_1_OBSERVATION_LOG.md

### Next morning: Day 2 work begins

Follow SCENARIO_NEW_DISTRICT.md Day 2 (write test that fails on soft language)

---

## Knowledge You Can Submit Right Now

### Example 1: Math Proof (K5 Determinism)

```bash
cat << 'PROOF' | python3 scripts/bibliotheque_intake.py MATH_PROOF
Claim: K5 determinism is preserved under policy updates
Proof:
  - Policy updates change rules, not digest algorithm
  - Digest algorithm: SHA256(decision_input)
  - Same input → same output regardless of policy version
  - Therefore K5 holds across policy updates
  QED.
PROOF
```

### Example 2: Old Code (Pattern Extraction)

```bash
# If you have legacy governance code, submit it:
cat legacy_quorum_check.py | python3 scripts/bibliotheque_intake.py CODE_ARCHIVE
# Output: Parses functions, detects patterns, marks for integration
```

### Example 3: Operational Log (Incident)

```bash
cat << 'LOG' | python3 scripts/bibliotheque_intake.py OPERATIONAL
2026-01-20: Incident: Invalid attestation from key-2025-12-legal-old
Time: 15:23:04 UTC
Failure: Key was revoked 2026-01-15 but still in registry
Impact: Decision delayed (K4 revocation cascade pattern)
Resolution: Removed from registry, K4 detector updated
Pattern: E4 (Revocation Cascade)
LOG
```

---

## Success Looks Like

**At end of Week 1:**
```
✅ Privacy District added
✅ Soft policy → hard policy transformation visible
✅ Tests show soft → hard progression
✅ MONTH_1_OBSERVATION_LOG entries recorded
✅ Gate still GREEN
✅ Evidence still validates (5/5)
```

**At end of Week 2:**
```
✅ 3+ knowledge submissions to Bibliothèque
✅ All submissions marked ACCEPTED ✅
✅ oracle_town/memory/bibliotheque/ populated
✅ Citations in decision records
✅ Determinism verified (K5)
```

**At end of Week 3:**
```
✅ E1 patterns detected and recorded
✅ E4 patterns detected and recorded
✅ E5 patterns detected and recorded
✅ New rules created from patterns
✅ Tests enforce new rules
✅ ASCII town shows active governance
```

**At end of Month 1:**
```
✅ MONTH_1_OBSERVATION_LOG complete
✅ Evidence non-drifting (still 5/5)
✅ 5+ governance rules added
✅ 3+ patterns instrumented
✅ Knowledge base operational
✅ Ready for Month 2 scaling
```

---

## Launch Checklist

- [ ] Read QUICK_START_AUTONOMOUS.md (5 min)
- [ ] Read THIS FILE: BEGIN_MONTH_1.md (10 min)
- [ ] Run `bash scripts/town-check.sh` (see ASCII town GREEN)
- [ ] Run `TOWN_EVIDENCE=1 bash scripts/town-check.sh` (see 5/5 evidence)
- [ ] Open SCENARIO_NEW_DISTRICT.md
- [ ] Create oracle_town/districts/privacy/ directory
- [ ] Start Day 1: Define soft policy

---

## You Are Ready

✅ System operational
✅ Gates green
✅ ASCII town running
✅ Evidence validated (5/5)
✅ Knowledge base live
✅ Scenario ready
✅ First week mapped out

**Begin Month 1 whenever you're ready.**

---

## Quick Reference: Files You'll Touch

| File | Purpose | Frequency |
|------|---------|-----------|
| SCENARIO_NEW_DISTRICT.md | Follow daily (5 days Week 1) | Daily Week 1 |
| MONTH_1_OBSERVATION_LOG.md | Record metrics + patterns | Daily |
| oracle_town/districts/privacy/policy_draft.md | Soft → hard policy | Days 1-4 |
| test_privacy_*.py | Tests (failing → passing) | Days 2-4 |
| scripts/town-check.sh | Verify gate still green | After each commit |
| oracle_town/memory/bibliotheque/ | Knowledge submissions | Weeks 2-4 |

---

## Questions?

If you get stuck:

1. **Gate turns RED:** Check SYSTEM_READINESS_CHECKLIST.md troubleshooting
2. **Evidence fails:** Run `python3 scripts/extract-emulation-evidence.py` for details
3. **Unsure about Day N:** Reread SCENARIO_NEW_DISTRICT.md Day N section
4. **Need to submit knowledge:** See examples above, or read BIBLIOTHEQUE_INTAKE.md

---

**🚀 Ready? Begin Month 1!**

```bash
bash scripts/town-check.sh
# Shows: GREEN ✅
# ASCII: Live town visualization
# Next: Follow SCENARIO_NEW_DISTRICT.md Day 1
```

