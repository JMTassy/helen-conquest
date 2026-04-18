# Month 1 Observation Log: What You'll Actually See

## Setup: What to Track

Before running the Privacy District scenario (or your own), set up these observation points:

### Metric 1: Gate Pass/Fail Ratio
```bash
# Count green gates vs red gates
git log --oneline | grep -E "gate failed|indices stale|syntax" | wc -l
# Expected: Most days = GREEN, occasional RED = normal iteration
```

### Metric 2: Documentation Growth
```bash
wc -l CLAUDE.md
# Track weekly. Expect: +5-15 lines/week when actively iterating
```

### Metric 3: Index Changes
```bash
git log --oneline -- scratchpad/CLAUDE_MD_*.txt | wc -l
# Track commits that touch indices
# Each one represents a governance decision documented
```

### Metric 4: Test Coverage Emergence
```bash
ls -1 tests/test_*.py | wc -l
# Track new test files. Each reveals a governance constraint
```

### Metric 5: Decision Coupling
```bash
git log --oneline | grep -E "K[0-9]|quorum|attestor|policy" | wc -l
# Track governance-language commits
# Indicator: system is forcing explicit decisions
```

---

## Week 1: The First Decision Cycle

### Day 1: Proposal + Documentation
```bash
# Edit CLAUDE.md with new district
bash scripts/town-check.sh
# Expected: RED (indices stale)

# Regenerate
python3 scratchpad/generate_claude_index.py
git add scratchpad/CLAUDE_MD_*.txt
git commit -m "docs: add Privacy District"

# Check gate
bash scripts/town-check.sh
# Expected: GREEN
```

**What you learn:** Documentation changes are the primary trigger for the gate.

### Day 2: Test Failure Forces Clarity
```bash
# Write first test
echo "def test_privacy_district(): ..." > tests/test_privacy.py
bash oracle_town/VERIFY_ALL.sh
# Expected: RED (no privacy rules implemented)
```

**Observation:** The system refuses incomplete governance.
You can't "plan to implement later." Tests fail immediately.

**Decision forced:** You must define Privacy District's K0–K9 before code passes.

### Day 3: K3 Quorum Implementation
```bash
# Implement quorum rule
python3 oracle_town/core/privacy_policy.py

bash oracle_town/VERIFY_ALL.sh
# Expected: RED (still missing something)
```

**What emerges:** The test reveals missing attestor classes in the key registry.

```
ERROR: Privacy District attestor 'DPO' not found in registry
```

**Decision forced:** You must register attestors before quorum works.

### Day 4: Operational Realism Enters
```bash
# Question: What if DPO is unavailable?
# Current: Quorum requires exactly 3 of 3
# Problem: One person on vacation = system fails closed

# Decision 1: Hard fail (K1 favor)
# Decision 2: Deputy attestor class (K0 delegation)
# Decision 3: Temporary CTO override (K0 separation violation)

# You choose: Deputy attestor class
# Add to policy: "deputy_dpo" class counts as DPO for quorum

bash oracle_town/VERIFY_ALL.sh
# Expected: GREEN (all tests pass)
```

**What this reveals:** Abstract governance (quorum = 3-of-3) breaks against reality (people are absent).

The system forces you to decide **which invariant wins**: fail-closed K1, or operational K0?

**You chose K0 (authority separation)** because the system wouldn't let K1 alone survive.

---

## Week 2: Cross-District Collision

### Day 8: Coupling Emerges in Tests
```bash
# You add a test:
def test_technical_and_privacy_agree():
    # Technical: "deploy new data pipeline"
    # Privacy: "needs consent first"
    # Both districts say NO_SHIP
    # Net: NO_SHIP (correct, fail-closed)

    # But then:
    # Technical approves (has evidence)
    # Privacy rejects (missing consent)
    # Net: BLOCKS deployment (good?)
    # or ALLOWS it (bad?)

result = mayor_rsm(claim, policy, briefcase, ledger)
# Test fails: unclear which district wins
```

**Decision forced:** Who wins when districts disagree?

**Options:**
- A) AND (both must approve) — most conservative, K1 maximized
- B) First veto (Privacy checks first) — governance hierarchy
- C) Consensus (must resolve disagreement) — collaborative, bureaucratic

**What system reveals:** This isn't a design question. It's a governance policy question.

You write it to CLAUDE.md:

```markdown
## District Authority (K0 Separation)

**Decision Rule:**
- Technical and Privacy have equal authority
- Conflicting decisions escalate to Town Hall
- Escalation requires unanimous Town Hall vote
- Default escalation vote: NO_SHIP (K1 fail-closed)
```

### Day 10: Determinism Test Finds Hidden Coupling
```bash
python3 oracle_town/core/replay.py  # Run 30 iterations

# Iteration 15:
# ERROR: Non-deterministic decision
# Scenario: Privacy + Technical both vote NO
# Run 1 result: NO_SHIP
# Run 15 result: ESCALATE_TO_TOWN_HALL (different!)
# Cause: Ledger order differs between runs
```

**System revelation:** Your decision rule is non-deterministic.

The problem: "escalate to Town Hall" without specifying **when** the escalation triggers.

**K5 violation detected by replay test.**

**Decision forced:** Rewrite as deterministic policy:

```python
def escalation_rule(technical_vote, privacy_vote):
    # ALWAYS escalate on disagreement
    # (not sometimes, not when convenient)
    if technical_vote != privacy_vote:
        return ESCALATE
    return technical_vote  # Both agree
```

Now replay test passes (K5 determinism).

---

## Week 3: The Ledger Reveals Patterns

### Day 15: Observability Question
```bash
# Query decisions made so far:
grep -r "Privacy.*approved" oracle_town/runs/

# Results show:
# - Privacy blocks 3 decisions
# - Technical blocks 1 decision
# - Escalations: 0
```

**Observation:** Privacy is conservative (blocks more often).

**Question emerges:** Is this K0 authority separation, or K1 fail-closed too aggressive?

**Decision:** Audit quorum requirements.

```markdown
## Privacy District Attestation Analysis

**Current:** 2-of-3 required
- DPO blocks when conservative
- Compliance blocks when unclear
- SecOps blocks when risky

**Result:** 60% of decisions hit Privacy gate

**Decision:** Adjust to 2-of-3 with "confidence threshold"
- Simple decisions (low risk): 1-of-3 DPO only
- Complex decisions (GDPR impact): 2-of-3 required
```

**New governance rule written to CLAUDE.md.**

---

## Week 4: The System Stabilizes

### Day 20: Determinism Lock-In
```bash
bash scripts/town-check.sh
✅ GREEN (indices stable)

bash oracle_town/VERIFY_ALL.sh
✅ ALL TESTS PASS (including 30 determinism iterations)
```

**What you've learned:**
- Privacy District is no longer aspirational, it's operational
- All decisions are testable, deterministic, and logged
- District authority is explicit in code

### Day 25: New Insight — Delegation Patterns
```bash
# Query ledger:
git log --oneline -- oracle_town/runs/ | head -20

# Shows pattern:
# Many decisions: "deputy_dpo approves" (vacation coverage works)
# Some decisions: "escalate to town_hall" (unresolved conflicts)
# Few decisions: "ship" (full consensus)
```

**Emergent insight:** Deputy attestors work. Escalation is rare. Most decisions have privacy consideration.

**New decision:** "Establish deputy rotation schedule" (K0 governance)

### Day 28: System Observability Question
```bash
# User asks: "Can we query 'which decisions failed privacy gate'?"
# Current: Must grep through ledger manually
# Better: Add metadata to decision_record schema

# New schema requirement:
decision_record = {
    ...
    "districts": {
        "privacy": {
            "status": "approved|rejected|escalated",
            "reason": "...",
            "quorum": "2-of-3"
        }
    }
}
```

**System forces:** Observability becomes a K9 (replay) requirement.

---

## The Emergent Pattern You'll See

| Week | Focus | Gate Red | Gate Green | Commits | Insight |
|------|-------|----------|-----------|---------|---------|
| 1 | Proposal → Implementation | 3x | 4x | 7 | Documentation drives governance |
| 2 | Cross-district collision | 2x | 5x | 6 | Authority conflicts emerge in tests |
| 3 | Determinism lock-in | 1x | 6x | 5 | Non-deterministic policy caught by K5 |
| 4 | Stabilization | 0x | 7x | 4 | Observability becomes necessity |

---

## What You'll Commit Each Day

### Day 1–4 (Proposal Phase)
```
docs: add Privacy District to CLAUDE.md
docs: regenerate indices
test: add privacy district E2E test
feat: implement privacy quorum (K3)
feat: implement privacy fail-closed (K1)
docs: clarify privacy evidence requirements (K5)
```

### Day 5–10 (Collision Phase)
```
test: add tech + privacy conflict scenario
feat: add escalation rule for district disagreement
docs: clarify K0 authority separation (Privacy vs Technical)
fix: privacy + technical deadlock via escalation
test: validate escalation determinism
```

### Day 11–20 (Stability Phase)
```
test: 30-iteration determinism pass
docs: audit privacy decision patterns (observability)
feat: adjust privacy quorum based on decision complexity
docs: establish deputy dpo rotation schedule
feat: add decision metadata for observability
test: validate K9 replay with deputy attestors
```

### Day 21–28 (Observability Phase)
```
feat: enhance decision_record schema (districts metadata)
test: query privacy decisions by status
docs: Privacy District month 1 retrospective
docs: regenerate indices (final size)
```

---

## Real Metrics You'll Observe

At the end of Month 1:

```
CLAUDE.md size:     800 lines (+50 lines from new district)
Test files:         +2 new (privacy-specific tests)
Commits:            ~28 (avg 1/day, ~1 gate red per week)
Determinism passes: 30/30 iterations (K5 ✅)
District tests:     12 tests, 11 passing, 1 integration (cross-district)
Governance rules:   6 explicit (K0-K9 each tested)
```

---

## The Key Realization After Month 1

You won't feel like you "designed" the Privacy District.

**It will feel like the Privacy District designed itself**, through the system's insistence on:
- Testability (K0–K9 constraints)
- Determinism (K5 replay)
- Auditability (K9 observability)
- Fail-closed defaults (K1)

**The gate system didn't create the district. It forced the district to be real.**

That's the emergent property: **governance becomes concrete, not aspirational.**

After month 1, you'll have:
- ✅ A real Privacy District (tested, deterministic, observable)
- ✅ Explicit authority separation (K0)
- ✅ Quorum rules (K3)
- ✅ Fail-closed defaults (K1)
- ✅ Operational procedures (deputy rotation)
- ✅ Cross-district protocols (escalation)

And it all emerged from the system's refusal to accept vague governance.
