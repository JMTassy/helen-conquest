# Scenario: Add a New Oracle Town District

## The Proposal

> "We need a **Privacy District** to handle GDPR, data retention, and consent management in all decisions. Right now privacy is scattered across Legal and Technical. We need a dedicated authority."

## Step 1: Gate Interaction (First Commit)

### What the User Does
```bash
# Edit CLAUDE.md to document the new district
cat >> CLAUDE.md << 'EOF'

    - ### Privacy & Compliance District
      Lines TBD | Anchor: #privacy-compliance-district

EOF

git add CLAUDE.md
bash scripts/town-check.sh
```

### What the Gate Reveals
```
[town-check] gate 1: doc indices
ERROR: CLAUDE.md indices are stale (regeneration produced changes)

Fix:
  1. Run: python3 scratchpad/generate_claude_index.py
  2. Review changes: git diff --stat -- scratchpad/CLAUDE_MD_*.txt
  3. Commit: git add scratchpad/CLAUDE_MD_*.txt && git commit ...
```

### Decision Surface #1: "Where Does This Live?"
The gate forces the first decision: **the documentation must be accurate before code exists**.

**What emerges:**
- User must commit CLAUDE.md changes + regenerated indices together
- This creates a **governance paper trail**: "on [date], Privacy District proposed in CLAUDE.md"
- The indices show exactly what changed: `git diff scratchpad/CLAUDE_MD_*.txt`

```
+    - ### Privacy & Compliance District
+      Lines 750–765 | Anchor: #privacy-compliance-district
```

**Decision recorded in git:**
```
commit abc123
docs: add Privacy & Compliance District to CLAUDE.md

This district handles GDPR, data retention, and consent management.
```

---

## Step 2: Governance Emergence (What Becomes Necessary)

Once the documentation is committed, the system reveals what's actually missing:

### Question 1: "What does a District look like?"
User runs `bash oracle_town/VERIFY_ALL.sh` and discovers:
- The test suite expects districts to implement K0–K9 invariants
- Privacy District must define a mayor RSM function (pure predicate)
- Attestors must be defined in the key registry

**System decision point:** Before code exists, we need to answer:
- Who are the Privacy District's attestors? (K0 Authority)
- What evidence does Privacy District require? (K3 Quorum)
- What's the fail-closed default for privacy decisions? (K1)

### Question 2: "How does Privacy interact with Legal and Technical?"
The indices show section sizes:

```
• Legal & Compliance: 45 lines
• Technical & Security: 52 lines
• Privacy & Compliance: 8 lines (newly added, incomplete)
```

**System revelation:** By making it a first-class section in the index, the system shows:
- Privacy is now **co-equal** with Legal/Technical, not subordinate
- This is a governance decision, not implementation detail
- The size gap (8 vs 45 lines) means the Privacy District is under-specified

**What gets written to CLAUDE.md:**
```markdown
### Privacy & Compliance District

**Authority** (K0): Data Privacy Officer + Compliance Lead + Security Ops
(Must be distinct from Legal attestor to prevent self-attestation — K2)

**Fail-Closed** (K1): Default is REJECT consent changes, REJECT data access
(Blocks all privacy-impacting decisions unless explicitly approved)

**Quorum** (K3): Requires 2-of-3 attestors (DPO, Compliance, SecOps)
(Prevents single point of failure in privacy gate)

**Evidence Requirements**:
- Privacy impact assessment (mandatory for any data-touching decision)
- Retention policy reference
- Consent proof (if user data involved)
- GDPR compliance audit trail
```

---

## Step 3: Testing Forces Clarity (The Gate Validates)

User creates the first Privacy District decision test:

```python
# tests/test_privacy_district.py
def test_privacy_rejects_consent_without_evidence():
    claim = {
        "action": "collect_email_for_marketing",
        "user_id": "user_123"
    }

    # No privacy evidence attached
    result = mayor_rsm(claim, policy, briefcase, ledger)

    assert result == "NO_SHIP"  # Must fail closed
```

Running `bash scripts/town-check.sh`:

```
✓ Indices are current
✓ Python syntax valid
✅ GREEN — all gates passed
```

Then `bash oracle_town/VERIFY_ALL.sh`:

```
[Test Suite: Privacy District] FAIL

ERROR: Privacy District quorum check not implemented
  - Mayor RSM doesn't recognize privacy attestors
  - Key registry missing Privacy District keys
  - Policy file has no privacy rules
```

**Decision emergence:**
- The system forces implementation of K0, K3, K5 before any decision can pass
- Incomplete governance = test failure (non-negotiable)

---

## Step 4: Code Implementation Surfaces Policy Decisions

User creates `oracle_town/core/privacy_policy.py`:

```python
def privacy_quorum_rule(policy, attestations):
    """
    Privacy decisions require 2-of-3 attestors:
    - Data Privacy Officer
    - Compliance Lead
    - Security Operations
    """
    privacy_attestors = [
        a for a in attestations
        if a['class'] in ['DPO', 'COMPLIANCE', 'SECOPS']
    ]

    distinct_classes = set(a['class'] for a in privacy_attestors)
    return len(distinct_classes) >= 2  # K3: quorum by class
```

**New decision surface:** K3 Quorum-by-Class

The system surfaces a governance question the user hadn't explicitly asked:

> "If we require 2-of-3, what happens when DPO is on vacation?"

**Options that emerge:**
- A) Hard fail (K1 fail-closed) — safest but operationally rigid
- B) Allow deputy attestor — requires governance of delegation
- C) Temporary override by CTO + Compliance — requires explicit policy

**The system forces a choice**, because the test won't pass without deciding.

---

## Step 5: Determinism Testing Reveals Hidden Coupling

User runs the determinism gate (part of `VERIFY_ALL.sh`):

```bash
for i in {1..30}; do
    python3 scratchpad/generate_claude_index.py
    if ! git diff --quiet scratchpad/CLAUDE_MD_*.txt; then
        echo "FAIL: Non-deterministic at iteration $i"
        exit 1
    fi
done

✅ All 30 iterations produced identical indices
```

But then they find a **hidden decision point:**

In CLAUDE.md, they wrote:

```markdown
**Evidence Requirements**:
- Privacy impact assessment (mandatory...)
- Retention policy reference
- Consent proof (if user data involved) ← CONDITIONAL
```

**System revelation:** This "if" statement is non-deterministic policy language.

The gate doesn't reject it (it's just documentation), but it reveals:
> "Your governance has a soft rule. The word 'if' means developers will interpret this differently."

**Decision forced:** Rewrite as K5-compliant (deterministic):

```markdown
**Evidence Requirements**:
- Privacy impact assessment (mandatory for all)
- Retention policy reference (mandatory for all)
- Consent proof (mandatory if action == 'collect_personal_data')
- Audit trail (mandatory for all)
```

Now the policy is **testable and K5-compliant**.

---

## Step 6: The Emergent Governance Structure

After the gate validates, the system reveals what Privacy District actually **is**:

```
Commit sequence in git log:

1. docs: add Privacy District to CLAUDE.md
2. docs: regenerate indices (gate forced)
3. test: add privacy district determinism tests
4. feat: implement privacy quorum rule (K3)
5. feat: implement privacy fail-closed default (K1)
6. docs: clarify evidence requirements (K5 determinism)
7. test: validate privacy district E2E
```

**What emerged:**
- Privacy District is not just documentation — it's a **governance authority**
- It has explicit quorum rules (K3)
- It has deterministic decision criteria (K5)
- It must pass replay tests (K9)
- Decisions are cryptographically signed (K0)

### The Key Insight the System Revealed

> **The Mayor gate and index regeneration don't just check syntax. They force governance to be explicit.**

When Privacy District couldn't be "vague" or "conditional," the team had to:
1. Define quorum explicitly
2. Choose between hard-fail and delegation
3. Write testable policy
4. Create deterministic evidence rules
5. Document attestor responsibilities

---

## Step 7: One Month Later — What Changed

If you run `git log --oneline | head -20` after a month of Privacy District work:

```
abc999  docs: privacy district quorum reduced to 2-of-3 (not 3-of-3)
abc888  feat: add deputy dpo attestor class for vacation coverage
abc777  test: privacy decision replay validates determinism
abc666  docs: clarify consent evidence requires user signature
abc555  fix: privacy decision shouldn't block technical changes (K0 separation)
abc444  feat: privacy district now observable via ledger
abc333  test: add 50-decision privacy E2E scenario
abc222  docs: privacy district added to CLAUDE.md
abc111  docs: regenerate indices
```

**Emergent properties visible in git:**

1. **Clarity through iteration:** Early version had "2-of-3 or 3-of-3?" — now explicit.
2. **Operational reality:** "deputy dpo attestor class" emerged because quorum didn't account for human absence.
3. **Cross-district learning:** "shouldn't block technical changes" reveals coupling between Privacy and Technical districts.
4. **Observability:** "observable via ledger" means Privacy decisions are now auditable and queryable.

---

## Key Insights from This Scenario

### What the Gate System Revealed:

| Discovery | How System Surfaced It |
|-----------|----------------------|
| Privacy must be first-class, not scattered | Index size comparison (Privacy vs Legal) |
| Quorum rules must be explicit | Test failure until K3 policy written |
| Soft language is non-deterministic | K5 determinism gate rejected "if" conditions |
| Delegation needs governance | Test coverage gap when DPO unavailable |
| Privacy couples to Technical | Cross-district test failures revealed dependency |
| Decisions must be observable | Ledger structure questioned in design |

### What Didn't Need to Be Decided Upfront:

❌ "Will Privacy District be authority-based or advisory?" — **Emerges from K0 test**
❌ "What's the quorum?" — **Emerges from quorum-by-class requirement**
❌ "How do we handle attestor absence?" — **Emerges from operational pressure**
❌ "What evidence matters?" — **Emerges from K5 determinism requirement**

### The System's Governance Power:

The gate system **refuses soft governance**. Every decision must eventually become:
- Testable (can be automated)
- Deterministic (same inputs → same results)
- Auditable (decisions appear in ledger)
- Replayable (anyone can verify the decision)

This is why the Privacy District evolved the way it did — not by debate, but by the system's refusal to accept vague policy.

---

## What You'd See in Real Time

```bash
# Day 1: Propose district
bash scripts/town-check.sh
✅ GREEN (indices updated)

# Day 2: Write tests
bash oracle_town/VERIFY_ALL.sh
❌ FAIL (privacy rules not implemented)

# Day 3: Implement K0/K3/K5
bash oracle_town/VERIFY_ALL.sh
❌ FAIL (missing deputy attestor class)

# Day 4: Add operational realism
bash oracle_town/VERIFY_ALL.sh
✅ GREEN (30 determinism iterations pass)

# Day 5: Cross-district check
bash oracle_town/VERIFY_ALL.sh
❌ FAIL (privacy blocks technical changes, violates K0)

# Day 6: Decouple districts
bash oracle_town/VERIFY_ALL.sh
✅ GREEN

# Commit: All governance decisions forced by the system
```

---

## The Emergent Lesson

**The system doesn't ask "what's your policy?"**
**It asks "can you prove it?" — and refuses lies.**

Privacy District wasn't designed via discussion.
It emerged from the system's insistence on K0–K9 compliance.

That's the power of a governance gate: it turns soft decisions into hard constraints, and hard constraints into operational reality.
