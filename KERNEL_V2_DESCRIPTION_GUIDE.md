# KERNEL_V2 — Description Guide (Audience-Based)

**How to pitch KERNEL_V2 depending on who's listening**

---

## Rule: Choose Your Frame Based on Audience

| Audience | Frame | Lead With | Example Use |
|---|---|---|---|
| **Builders/Architects** | Technical | Rules + structure | "Show me the constitutional rules and how superteams map to them" |
| **Users/Stakeholders** | Functional | What it produces | "We run a subject through 5 phases and get a decision memo in 5 hours" |
| **Systems Thinkers** | Philosophical | Atomic units scaling | "One agent does one thing atomically. Stack into teams. Stack into districts. The kernel replicates." |
| **You (self-reflection)** | Implementation | What changed | "Execution deleted. Creative activated. 5 rules rewritten for precision." |

---

## Frame 1: TECHNICAL (For Architects/Builders)

### Elevator Pitch (30 seconds)
"KERNEL_V2 is a constitutional framework for multi-agent systems. Five immutable rules constrain four superteams. Each superteam's power flows directly from a rule — no power exists without a rule source. It's self-enforcing through the 5-phase pipeline."

### Full Pitch (2 minutes)

KERNEL_V2 solves a critical problem: in multi-agent systems, authority gets murky. Who decides? Who can override whom? When does a role exceed its bounds?

**The answer: constitutional rules.**

We have 5 rules (not 20, not 100):
1. **Single Finalization Point** — One role finalizes. Declared upfront.
2. **Record Before Transition** — Log before advancing (not after).
3. **No Self-Edit** — Proposer ≠ validator. Always.
4. **Coordinator is Process-Only** — Foreman manages flow, not content.
5. **Fail-Closed + Mandatory Termination** — Missing evidence rejected. Silence invalid.

These rules shape four superteams:
- **Production** (Editor's unilateral cut)
- **Knowledge** (Researcher's source authority)
- **Creative** (Lateral Pattern + Rhythm Tracker, K5 exempt)
- **Governance** (frozen reference)

Every superteam power traces back to a rule. If you can't trace it, the power is invalid.

**Architecture benefit:** When conflicts arise, you check which rule was violated. No human judgment needed. The rules decide.

### For Technical Discussion
- Reference: `KERNEL_V2.md` Sections 2-4 (rules, K-gates, power declarations)
- Visual: Section 7 (authority flow diagram)
- Test: `KERNEL_V2_TEST_MONETIZATION.md` (proof that all 8 rules enforced in production)

### Technical Q&A Prep
- "Why 5 rules?" — Minimal set that covers all observed violations in prior system
- "What if a rule is violated?" — Run audit, isolate violation, file amendment (Section 9)
- "Can I add a 6th rule?" — Only after evidence gate + conservatism gate (Section 9 amendment process)

---

## Frame 2: FUNCTIONAL (For Users/Stakeholders)

### Elevator Pitch (30 seconds)
"KERNEL_V2 is a decision system. You give us a question, we run it through five phases (exploration, tension, drafting, editorial collapse, termination), and you get a memo with three findings in 5 hours. No endless chat. Clear ownership. Final decision logged."

### Full Pitch (2 minutes)

Here's the problem we solve: disagreement. When multiple perspectives exist, how do you move forward?

**Most systems fail because they optimize for consensus.** Wrong goal. Consensus means slow, watered-down, nobody's satisfied.

**KERNEL_V2 optimizes for decision.**

Here's how it works:

**Phase 1 (Exploration):** We gather evidence from all sides. Researcher finds facts. Skeptic finds contradictions. Lateral thinker finds unexpected connections. No filtering.

**Phase 2 (Tension):** Skeptic attacks everything. Forces clarification. This is where bad ideas die.

**Phase 3 (Drafting):** We convert accepted ideas into prose. Write the memo.

**Phase 4 (Editorial Collapse):** Editor reads the draft. Makes unilateral cuts (30-50%). Decides.

**Phase 5 (Termination):** Editor declares: artifact ready or abort. No silence. No "still working on it."

**Result:** A memo that's been stress-tested, challenged, and decided. You know the reasoning. You know what was cut and why.

**Time commitment:** 5 hours total. Not weeks. Not months.

### For Stakeholder Discussion
- Reference: `CREATIVE_DEPLOYMENT.md` (shows how each role contributes)
- Example: `KERNEL_V2_TEST_MONETIZATION.md` (real memo output on real question)
- Timeline: "FOUNDRY District: 5-phase pipeline, 5.25 hours per run"

### Stakeholder Q&A Prep
- "Who makes the final decision?" — The Editor, after phases 1-3 inform them. Editor is accountable.
- "What if I disagree with the Editor's cut?" — You can, but the artifact shipped. Amendment requires evidence + new run.
- "Can we run multiple subjects in parallel?" — Yes, using different superteams at the same time. Claim Market coordinates.

---

## Frame 3: PHILOSOPHICAL (For Systems Thinkers)

### Elevator Pitch (30 seconds)
"KERNEL_V2 is an atomic intelligence model. Smallest unit: a role (one person, one task). Combine roles → superteams. Combine superteams → districts. The kernel replicates infinitely without redesign. Self-enforcing rules eliminate the need for central authority."

### Full Pitch (3 minutes)

The idea is **atomicity**.

Most multi-agent systems fail because authority is distributed but not clear. Everyone has a little power. Nobody is accountable.

**KERNEL_V2 inverts this.** Every role is atomic:
- One job
- Clear limits
- Clear powers
- Testable in 2 sentences

**Example:** Lateral Pattern's 2-sentence test: "Identifies unexpected relationships between claims. Does not explain why they matter, propose what to do, or validate whether they are true."

That's atomic. You can test it. You can enforce it. You can replace the person and the role stays the same.

**Then scale:**

2-6 atomic roles → **superteam** (one domain, one unique power)

2-5 superteams → **district** (one rhythm, one output type)

Multiple districts → **kernel** (replicates infinitely)

**Why it works:**

Constitutional rules enforce themselves. No central authority needed. A role either violates Rule 3 (self-edit) or it doesn't. No judgment call. The rule decides.

**Scalability:**

Want to add a new superteam? Test it against the 5 rules. Want to fork to a new domain? Clone a district. The kernel doesn't change. Only the content changes.

**This is why KERNEL_V2 is stable.** Not because it's perfect. But because violations are detectable, repairable, and don't require kernel redesign.

### For Systems-Thinking Discussion
- Reference: `CLAUDE.md` (LEGO hierarchy section — shows the stacking principle)
- Reference: `KERNEL_V2.md` Section 7 (authority flow diagram)
- Comparison: Oracle Town (governance kernel, frozen) vs. Foundry Town (production system, active) vs. KERNEL_V2 (integrated)

### Philosophical Q&A Prep
- "Is this deterministic?" — No. K5 exemption for Creative allows non-determinism. The kernel enforces what it can, allows chaos where it helps.
- "What happens when rules conflict?" — Use the amendment process (Section 9). Evidence gate prevents frivolous changes.
- "Can the kernel break?" — Yes. When a violation slips through undetected. The fix: audit, evidence gate, amend. The kernel learns.

---

## Frame 4: IMPLEMENTATION (Self-Reflection / What Changed)

### What Changed from V1 (in CLAUDE.md)

| Aspect | V1 (CLAUDE.md) | V2 (KERNEL_V2.md) | Why |
|---|---|---|---|
| **Rule Precision** | Abstract statements | 2-sentence tests + pass/fail | Testable rules > aspirational rules |
| **Execution superteam** | Active (3 violations) | DELETED (absorbed) | Eliminated duplication and authority conflicts |
| **Creative superteam** | Blocked (no charters) | ACTIVE (fully chartered) | Lateral Pattern + Rhythm Tracker now formal |
| **K5 in Creative** | Treated as constraint | Explicit exemption | Lateral thinking is non-deterministic by design |
| **Rule 4 framing** | "Foreman has zero authority" | "Foreman has process-only authority" | Clarifies what Foreman CAN do, not just restrictions |
| **Rule 5 depth** | Fail-closed only | Fail-closed + mandatory termination | Closes the endless-revision gap |
| **Authority flow** | Implied | Explicit diagram (Section 7) | Every power traces to a rule |

### What's Stable (Unchanged)

- CLAUDE.md operational baseline → untouched
- Oracle Town governance kernel → frozen reference
- LEGO hierarchy (LEGO1-4) → foundational
- 5-phase pipeline → same phases, sharper definitions

### What's New

- Rhythm Tracker (renamed from "Music Rhythm" for clarity)
- CREATIVE_DEPLOYMENT.md (ready-to-use guide)
- SOUL.md (agent operating rules)
- Amendment process in Section 9

---

## Routing Guide (Use This to Pick Your Frame)

### You're explaining to...

**An architect or someone building on KERNEL_V2:**
→ Use Frame 1 (Technical)
- Start with the 5 rules
- Show the power declarations
- Reference the authority flow diagram
- Discuss amendment process

**A stakeholder or decision-maker:**
→ Use Frame 2 (Functional)
- Start with "what does it produce?"
- Show the 5-phase pipeline
- Reference a concrete memo example
- Discuss timeline and decision ownership

**A systems designer or theorist:**
→ Use Frame 3 (Philosophical)
- Start with "atomic units"
- Show LEGO hierarchy
- Discuss scalability and self-enforcement
- Reference the kernel principle

**Yourself, in retrospective or review:**
→ Use Frame 4 (Implementation)
- Compare V1 → V2 changes
- Identify what's stable vs. what's new
- Plan next steps toward V3

---

## The Full Context Pitch (If Someone Asks for Everything)

**Time:** 5 minutes
**Structure:**
1. Start with Frame 2 (Functional) — "here's what we do"
2. Pivot to Frame 1 (Technical) — "here's how it works"
3. End with Frame 3 (Philosophical) — "here's why it scales"

**Script:**
> "KERNEL_V2 is a decision system. You give us a question, we run it through five phases and get a memo with final decisions logged. No endless chat. Clear ownership.
>
> It works through five constitutional rules. Each superteam's power flows directly from a rule — if you can't trace the power to a rule, it's invalid. This keeps authority clear.
>
> Why does this matter? Because it scales. Each role is atomic — one job, one clear limit, one clear power. Combine roles into superteams. Combine superteams into districts. The kernel replicates infinitely without redesign. Self-enforcing rules eliminate the need for a central authority."

---

## Files to Reference by Frame

| Frame | Primary File | Secondary | Tertiary |
|---|---|---|---|
| Technical | KERNEL_V2.md (Sections 2-4) | KERNEL_V2.md (Section 7) | KERNEL_V2_TEST_MONETIZATION.md |
| Functional | CREATIVE_DEPLOYMENT.md | KERNEL_V2_TEST_MONETIZATION.md | KERNEL_V2.md (Section 8: Districts) |
| Philosophical | CLAUDE.md (LEGO hierarchy) | KERNEL_V2.md (Section 4: Power declarations) | KERNEL_V2.md (Section 7: Authority flow) |
| Implementation | This file (Frame 4) | KERNEL_V2.md (Section 9: Amendment process) | MEMORY.md (V2 changes logged) |

---

**Use this guide to explain KERNEL_V2. Pick the frame. Land the pitch.**
