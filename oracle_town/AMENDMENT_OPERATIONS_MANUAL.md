# Amendment Operations Manual

**Effective Date:** January 31, 2026
**Doctrine Version:** 1.0 (and forward)
**Status:** OPERATIONAL

---

## Quick Start: How to Propose an Amendment

1. **Observe for 90 days** — Collect evidence of doctrine drift or gap
2. **Gather NPC claims** — Get ≥2 independent observers noticing same pattern
3. **Find counterexample** — Show a real case where current doctrine failed
4. **Fill template** — Use `AMENDMENT_A_TEMPLATE.md` to structure proposal
5. **Pass Gate B** — Answer "Why is inaction more dangerous than change?"
6. **Vote at Gate C** — Ratify, conditionally accept, or reject amendment
7. **Lock it** — Amendment becomes immutable, new doctrine version created

**Entire process:** 90+ days (observation window is non-negotiable)

---

## The Three Amendment Gates

### Gate A: Evidence (Non-Negotiable)

**What You Must Provide:**
- ≥2 independent NPC claims (different observers noticed same problem)
- ≥90 days of continuous observation (not "we thought about this for a week")
- ≥1 concrete counterexample (a real decision that proved doctrine inadequate)

**What This Prevents:**
- Emotional amendments ("I'm frustrated with rejections")
- Reactive amendments ("I failed one decision, change the rules")
- Self-interested amendments ("I want this specific decision to have passed")

**Evidence Must:**
- Date-stamped NPC observations (not retroactive)
- Show quantitative pattern (not anecdote)
- Include failed case with documented outcome
- Cover exactly 90+ day window

**You Cannot Pass Gate A By:**
- Saying "I believe we need this" (requires NPC claims)
- Pointing to one failure (requires ≥90 days pattern)
- Using only theoretical arguments (requires actual observed evidence)

**Passing Gate A means:**
Evidence is sufficient. Doctrine has a real gap. Proceed to Gate B.

---

### Gate B: Conservatism (The Safety Test)

**What You Must Answer:**
> Why is inaction more dangerous than change?

**Default position:** Keep current doctrine. You must prove amendment is necessary.

**Test Structure:**
1. Quantify cost of inaction
2. Quantify risk of amendment
3. Compare them
4. Decide which is worse

**What This Prevents:**
- "Optimizing" doctrine every quarter
- "We thought of a better way" amendments (no cost-benefit)
- "All these NPC observations support this, so why not?" (burden on amendment)

**Cost of Inaction Example:**
"If we don't tighten CLASS_II evidence, we'll continue accepting ~4 weak-evidence bets/month at 50% failure rate = $200k/month in preventable losses."

**Risk of Amendment Example:**
"If we tighten CLASS_II evidence, we might reject some borderline-good submissions, but we can mitigate this by monitoring rejection rates and reverting if it exceeds 70%."

**You Cannot Pass Gate B By:**
- Saying "evidence is sufficient" (Gate A already checked this)
- Claiming "it's obviously better" (must quantify)
- Assuming inaction is safer (burden is on you to prove it)

**Passing Gate B means:**
The case for change is stronger than the case for stability. Proceed to Gate C.

---

### Gate C: Ratification (Your Binding Vote)

**What You Must Do:**
Cast a vote: RATIFY, CONDITIONALLY ACCEPT, or REJECT

**Your options:**

**1. RATIFY**
- Amendment becomes new doctrine version
- Old doctrine pinned to all past claims (no retroactive harm)
- New doctrine effective immediately for new claims
- This is permanent (no undo button)

**2. CONDITIONALLY ACCEPT**
- New rules apply only to future submissions
- Old submissions remain under old doctrine
- Sunset date: you specify when this conditional version expires
- Example: "Apply to all CLASS_II submitted after July 1, 2026, until December 31, 2026"

**3. REJECT**
- Amendment is not adopted
- Cannot re-propose same amendment for 180 days
- Current doctrine remains in effect
- Reasons for rejection recorded (for your future self)

**What This Prevents:**
- Passive amendments (no explicit vote)
- Ambiguous votes ("this seems right")
- Unsigned decisions (your vote is logged, timestamped, irreversible)

**Voting happens when:**
- Gate A has PASSED (evidence is sufficient)
- Gate B has PASSED (inaction is more dangerous than change)
- Only then can you vote

**Your vote is:**
- Logged with date, time, and amendment hash
- Immutable (cannot be changed, amended, or deleted)
- Part of permanent amendment record
- Foundation for future amendments referencing this one

**Passing Gate C means:**
Amendment is complete. Doctrine has evolved. New version recorded.

---

## Amendment Ledger: Complete Record

Every amendment creates immutable ledger entries:

```
oracle_town/ledger/amendments/2026/
├── A-2026-06-001_ratified.json
│   ├── amendment_id
│   ├── doctrine_version_from/to
│   ├── gate_a_evidence (NPC claims + dates)
│   ├── gate_b_conservatism (cost analysis)
│   ├── gate_c_ratification_vote (timestamped)
│   └── new_doctrine_hash
├── A-2026-06-002_rejected.json
│   ├── amendment_id
│   ├── gate_a_result (PASS)
│   ├── gate_b_result (PASS)
│   ├── gate_c_decision (REJECT)
│   └── rejection_reason
└── A-2026-07-001_pending.json
    ├── amendment_id
    ├── observation_start/end
    ├── gate_a_status (collecting)
    └── evidence_collected_so_far
```

**Properties:**
- Append-only (no deletion, no editing)
- Date-organized (amendments searchable by year/month)
- Complete audit trail (what changed, when, why, by whose vote)
- Doctrine evolution is fully transparent

---

## Amendment Workflow

### Phase 1: Observation (Weeks 1-12)

**What You Do:**
- Observe verdicts and outcomes
- Let NPCs make claims independently
- Document failures and patterns

**No action needed.** Let data accumulate.

**End condition:** 90+ days have passed AND ≥2 NPCs made claims AND ≥1 counterexample exists

---

### Phase 2: Proposal (Week 13)

**What You Do:**
1. Review NPC claims (do they match your observation?)
2. Select counterexample (real case where doctrine failed)
3. Fill AMENDMENT_A_TEMPLATE.md
4. Document evidence in Gate A section
5. Save as `oracle_town/AMENDMENT_A_[TITLE].md`

**Time required:** 2-3 hours to write proposal

**End condition:** Amendment template is complete, all three gates are documented

---

### Phase 3: Conservatism Test (1-2 hours)

**What You Do:**
1. Fill Gate B section: Cost of inaction
2. Fill Gate B section: Risk of amendment
3. Make decision: Inaction more dangerous? Yes or no?
4. Explain your reasoning

**This is the hardest part.** Don't rush. Quantify costs if possible.

**End condition:** Gate B analysis is complete and reasonable

---

### Phase 4: Ratification (15 minutes)

**What You Do:**
1. Read entire amendment document
2. Check: Is Gate A evidence sufficient? (≥2 NPCs, ≥90 days, ≥1 counterexample)
3. Check: Is Gate B conservatism test passed?
4. Make final vote: RATIFY / CONDITIONALLY ACCEPT / REJECT
5. Write ratification statement (your own words, why you're voting this way)
6. Record timestamp
7. Lock document (no further edits)

**End condition:** Your vote is cast and timestamped

---

### Phase 5: Ledger Entry (10 minutes)

**What You Do:**
1. Compute SHA-256 hash of amendment document
2. Create ledger entry: `oracle_town/ledger/amendments/2026/A-[ID]_[STATUS].json`
3. Record:
   - Amendment ID
   - Doctrine versions (from/to)
   - Gate results (A, B, C)
   - Your vote and timestamp
   - New doctrine hash (if ratified)
4. Append to ledger

**End condition:** Amendment is locked, ledger entry exists, new doctrine hash computed (if ratified)

---

### Phase 6: If Ratified — Create New Doctrine Version

**What Happens:**
1. Old DOCTRINE_V1.0 remains in place (pinned to all past claims)
2. New DOCTRINE_V1.1 is created with updated text
3. New doctrine file: `oracle_town/DOCTRINE_V1_1.md` (copy of 1.0, with edits)
4. Compute new hash: `sha256 oracle_town/DOCTRINE_V1_1.md`
5. Update policy pinning: New claims use new hash
6. Old claims continue using old hash

**Property:** No retroactive reinterpretation. Past decisions remain valid under doctrine they were made under.

---

## Example: Full Amendment Lifecycle

**Timeline:**

```
March 30, 2026 — Observation begins (Day 0)
  └─ PatternDetector notices CLASS_II weakness starting
  └─ AccuracyWatcher begins tracking failure rates

May 15, 2026 — NPC Claim #1 (Day 46)
  └─ AccuracyWatcher: "50% failure rate on weak-evidence CLASS_II"

May 20, 2026 — Concrete counterexample (Day 51)
  └─ Vendor partnership claim fails, $50k loss, weak evidence

June 10, 2026 — NPC Claim #2 (Day 72)
  └─ PatternDetector: "Evidence quality declining, acceptance rate rising"

June 28, 2026 — Observation complete (Day 90)
  └─ All three requirements met: 2 NPCs + 90 days + 1 counterexample

June 30, 2026 — Amendment proposal (Day 92)
  └─ Fill AMENDMENT_A_TEMPLATE.md
  └─ Document all evidence from Gate A

June 30, 2026 — Gate B analysis (Day 92, same day)
  └─ Cost of inaction: $200k/month in weak-evidence failures
  └─ Cost of amendment: Modest rejection rate increase
  └─ Decision: Inaction is more dangerous

June 30, 2026 — Ratification vote (Day 92, afternoon)
  └─ Decision: RATIFY
  └─ Timestamp: 2026-06-30T09:15:00Z

June 30, 2026 — Ledger entry (Day 92, evening)
  └─ Amendment locked
  └─ DOCTRINE_V1.1 hash computed
  └─ Policy pinning updated

July 1, 2026 — New doctrine effective (Day 93)
  └─ All new submissions use DOCTRINE_V1.1
  └─ CLASS_II evidence threshold raised
  └─ Old DOCTRINE_V1.0 pinned to May/June decisions
```

**Total elapsed time:** 92 days (90-day observation + 2 days for writing and voting)

---

## Amendment Rejection: What Happens If You Vote REJECT?

**Your vote:** REJECT
**Effect:** Amendment is not adopted
**Consequence:** Current doctrine remains unchanged
**Lockout:** Cannot re-propose same amendment for 180 days

### Documenting the Rejection

When you REJECT an amendment, record:

```json
{
  "amendment_id": "A-2026-06-001",
  "proposed_change": "Tighten CLASS_II evidence threshold",
  "gate_a_result": "PASS",
  "gate_b_result": "PASS",
  "gate_c_vote": "REJECT",
  "rejection_reason": "Conservatism test shows risk of over-rejection exceeds benefit of tightening. Recommend monitoring CLASS_II rejection rates for next 6 months and re-proposing if trend worsens.",
  "cannot_resubmit_until": "2026-12-30T09:15:00Z"
}
```

### Why Rejection Is Valid

Rejection is not a failure. It's a statement: "Current doctrine is appropriate despite the evidence."

**Valid reasons for rejection:**
- "Benefits don't outweigh risks"
- "Evidence is insufficient despite NPCs"
- "Amendment would create worse problems"
- "Timing is wrong (wait for more data)"
- "Better to handle via individual CLASS_III overrides"

**Invalid reasons for rejection:**
- "I don't feel like changing things"
- "It's hard to implement"
- "I'm tired of reviewing"

The 180-day lockout prevents rejection from meaning "never reconsidered." It means "wait 6 months and try again with fresh evidence."

---

## Amendment Conditional Acceptance: Gradual Doctrine Change

**Your vote:** CONDITIONALLY ACCEPT
**Effect:** New rules apply to future submissions only
**Scope:** "All CLASS_II submissions after [DATE]"
**Sunset:** Conditional version expires on [DATE]

### When to Use Conditional Acceptance

Use this if:
- Evidence supports change but you want a trial period
- You want to measure impact before full adoption
- New threshold should apply only to new submissions, not retroactively
- You're skeptical but willing to test

### Example: Conditional CLASS_II Tightening

```json
{
  "amendment_id": "A-2026-06-001",
  "gate_c_vote": "CONDITIONALLY_ACCEPT",
  "conditional_scope": "All CLASS_II submissions with timestamp >= 2026-07-01T00:00:00Z",
  "sunset_date": "2026-12-31T23:59:59Z",
  "conditional_doctrine": "DOCTRINE_V1.1_TRIAL",
  "measurement_plan": "Monitor CLASS_II rejection rate weekly. If sustained >70%, revert to V1.0"
}
```

### Measurement After Trial Period

At sunset date, you decide:
- **ADOPT:** Conditional version becomes permanent (convert to RATIFY)
- **REVERT:** Conditional version expires, old doctrine resumes
- **MODIFY:** Data suggests different threshold, propose new amendment

---

## Amendment History: Reading the Record

To understand doctrine evolution, read amendment ledger:

```bash
ls -la oracle_town/ledger/amendments/2026/
```

Shows:
- A-2026-06-001_ratified.json (evidence tightening, passed)
- A-2026-06-002_rejected.json (acceptance rate change, failed Gate B)
- A-2026-07-001_pending.json (still collecting evidence)

To trace doctrine evolution:
1. Start with DOCTRINE_V1.0 (baseline, January 31, 2026)
2. Read A-2026-06-001 (what changed, who approved, when)
3. Read DOCTRINE_V1.1 (new text, effective July 1)
4. Repeat for each future amendment

**Key property:** Amendment record is complete and transparent. Future-you can understand why doctrine evolved.

---

## Amendment Immutability: Why Amendments Cannot Change

Once an amendment is RATIFIED, it is immutable:

❌ **Cannot edit amendment document** (locked after vote)
❌ **Cannot change the vote** (timestamp + irreversible)
❌ **Cannot delete an amendment** (ledger is append-only)
❌ **Cannot hide an amendment** (all versions auditable)
❌ **Cannot claim "we always meant something else"** (amendment document is frozen)

✓ **Can propose new amendment** (referencing old amendment)
✓ **Can revert amendment's changes** (via new amendment going opposite direction)
✓ **Can document lessons learned** (in future amendment rationale)

**Example:** If A-2026-06-001 tightens CLASS_II evidence and later you want to loosen it again, you:
1. Propose A-2027-03-001 (relaxing CLASS_II evidence)
2. Provide evidence it was too strict
3. Pass conservatism test
4. Ratify new amendment
5. Create DOCTRINE_V1.2 with loosened threshold

The original A-2026-06-001 remains in the ledger forever, showing what changed and why. No rewriting history.

---

## Amendment Anti-Patterns: What Not To Do

### ❌ Amendment Ping-Pong
**Problem:** Proposing opposite amendments (tighten, then loosen, then tighten again)
**Prevention:** Evidence gate requires 90-day observation. If evidence conflicts, wait longer.
**Good pattern:** Propose conservative first amendment, measure impact, refine if needed.

### ❌ Pre-dated Evidence
**Problem:** Claiming "we noticed this for 90 days" when observation only started 30 days ago
**Prevention:** NPC claims must be timestamped with observation dates. Ledger shows exact timeline.
**Enforcement:** Gate A explicitly checks observation_start_date.

### ❌ Retroactive Doctrine Changes
**Problem:** "We tightened CLASS_II evidence, and this old decision should have failed under new rules"
**Prevention:** Old claims pinned to doctrine version at creation time. DOCTRINE_V1.0 decisions remain valid under V1.0.
**Enforcement:** Ledger entries include policy_hash_at_creation.

### ❌ Self-Interested Amendments
**Problem:** "This amendment benefits my specific decision, so it's a good change"
**Prevention:** Gate B conservatism test is not about your decision. It's about systemic benefit.
**Enforcement:** Reject amendments that cherry-pick one case.

### ❌ Vague Ratification
**Problem:** "I vote RATIFY because it seems right"
**Prevention:** Ratification statement must explain your reasoning (at least 3-4 sentences).
**Enforcement:** Ledger includes ratification_statement. Vague statements stand as record of unclear thinking.

---

## Amendment Frequency: How Often Should Doctrine Change?

**Not prescriptive.** Frequency depends on:
- How often gaps appear in doctrine
- How much data NPCs collect
- How conservative you are at Gate B

**Healthy frequency:**
- 1-2 amendments per year (steady evolution)
- 1-2 rejected amendments per year (sometimes inaction is right)
- Long gaps between amendments (doctrine is stable, not reactive)

**Red flags:**
- >4 amendments in one year (doctrine is unstable or reactive)
- 0 amendments in 3 years (doctrine never tested against reality)
- Amendments ping-ponging (evidence gathering is poor)

---

## Amendment Templates and Tools

**Template:** `AMENDMENT_A_TEMPLATE.md`
- Blank form ready to fill
- All three gates included
- Instructions for each section

**Example:** `AMENDMENT_A_EXAMPLE_EVIDENCE_THRESHOLD.md`
- Shows real amendment structure
- Demonstrates evidence gathering
- Illustrates conservatism analysis

**Ledger format:** `oracle_town/ledger/amendments/YYYY/A-[ID]_[STATUS].json`
- Immutable record of all amendments
- Searchable by date and status
- Complete audit trail

---

## Next Amendment: When To Propose

**Propose an amendment when:**
- ≥2 NPCs independently noticed same gap (not before)
- ≥90 days of observation have passed (not faster)
- ≥1 concrete case failed due to doctrine gap (not theoretical)
- You've quantified cost of inaction (not vague)
- You've considered risks of change (not naive)

**Do not propose an amendment when:**
- One decision failed (wait for pattern)
- You're frustrated (wait for cooling off)
- Evidence is sparse (wait for NPCs to confirm)
- You haven't done conservatism analysis (do the work first)

---

**Amendment Operations Manual — Effective January 31, 2026**
**Status:** OPERATIONAL AND IMMUTABLE
**Questions?** Refer to AMENDMENT_A_TEMPLATE.md for details
