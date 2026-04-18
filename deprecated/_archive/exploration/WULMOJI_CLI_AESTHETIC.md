# WULmoji CLI Aesthetic for Foundry Town Skills

**Purpose:** Stimulate ADHD brain with colors, symbols, and faces
**Status:** Production aesthetic overlay
**Updated:** 2026-02-13

---

## Core Symbol Grammar

### VERBS (Action Types)

```
🧭 — Navigation / Discovery (foundry-new, dashboard)
🛑 — Stop / Gate / Enforce (phase-next, repeller-check)
👁️ — Observe / Check / Validate (claims-status, rhythm-check)
🏗️ — Build / Create / Scaffold (foundry-new, editorial-collapse)
🏴 — Flag / Mark / Alert (lego-check, rhythm-check warnings)
🎁 — Deliver / Ship / Complete (ship, hyperfocus-end)
🤝 — Coordinate / Submit (claim, skeptic-challenge)
📜 — Document / Log / Record (phase-next, artifact log)
⚔️ — Attack / Challenge / Red-team (skeptic-challenge)
🧨 — Explode / Break / Abort (repeller-check FAIL, abort decision)
🗣️ — Speak / Announce / Status (dashboard, claims-status)
🧵 — Thread / Connect / Link (claim dependencies)
```

### MODES (Execution Context)

```
⚡ — Active work (hyperfocus in progress)
🗺️ — Planning (foundry-new, dashboard)
❓ — Exploring (expansion phase, uncertain)
🎯 — Converging (drafting, finalizing)
⛓️ — Gated (waiting for phase transition or decision)
🧩 — Modular (lego-check, component validation)
➡️ — Forward (phase progression)
↩️ — Rewind / Revert (abort, restart)
```

### FLAGS (State Indicators)

```
🔒 — Locked / Terminal (artifact shipped)
🔥 — Hot / Critical / Burnout risk
⏸️ — Paused / Break / Hold
∅ — Empty / No results
⚫ — Blackout / Full stop (STATE=⚫, safety lock)
✖️ — Error / Fail (repeller-check FAIL)
⚠️ — Warning / Caution (burnout YELLOW/RED)
```

### RESOURCES (Personal State)

```
🥖 — Provisions / Energy / Time budget
💖 — Affection / Motivation / Heart
🛡️ — Stability / Coherence / Armor
```

---

## Skill Output Aesthetic (Per Skill)

### /foundry-new 🧭 🏗️

```
🧭 FOUNDRY RUN LAUNCHER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run: can-foundry-scale-to-100-agents
Objective: Explore governance scaling
Audience: engineers
Format: proposal
Timebox: 4h

🏗️ STRUCTURE CREATED:
  ✓ runs/can-foundry-scale-to-100-agents/
    ├─ MANIFEST.md (objective, constraints, 5-phase plan)
    ├─ CONTEXT.md (assumptions, dependencies)
    ├─ claims/ (pending.md, accepted.md, rejected.md, merged.md)
    ├─ drafts/ (v0.md, v1.md, v2.md stubs)
    ├─ logs/ (phase_transitions.md, decisions.md)
    └─ sources/ (bibliography.md, links.md)

📜 MANIFEST:
  Objective: Can Foundry scale to 100+ agents?
  Deliverable: Governance model for scaled systems
  Non-goals: Implementation code, performance metrics
  Constraints: 4h timebox, audience = engineers
  Definition of Done: 5+ accepted claims + draft v1

  Phases:
  ◷1 Explore (facts, outline, assumptions)
  ◷2 Outline (organize by structure)
  ◷3 Draft (prose from claims)
  ◷4 Verify (red-team, resolve contradictions)
  ◷5 Finalize (editorial collapse, deduplicate)
  ◷6 Ship (artifact freeze, archive)

🎯 READY FOR: /hyperfocus 90m --objective "Expand: sketch 3 scaling architectures"

═══════════════════════════════════════════════════════════════════════════════
```

### /claim 🤝 🧵

```
🤝 CLAIM SUBMISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Type: fact
Statement: Foundry supports 6 atomic roles (no role creep)
Support: CLAUDE.md: LEGO1 definition
Confidence: high
Dependencies: [none]
Falsifier: If any agent can do 2+ roles → FALSE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ CLAIM SUBMITTED
ID: F-001
Status: pending → awaiting Foreman curation
Owner: you
Timestamp: 2026-02-13T14:30:00Z

🧵 This claim is now in claims/pending.md
   Can be challenged with /skeptic-challenge F-001
   Can be accepted, rejected, or merged

═══════════════════════════════════════════════════════════════════════════════
```

### /claims-status 👁️ 🗣️

```
👁️ CLAIM MARKET STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run: can-foundry-scale-to-100-agents
Generated: 2026-02-13T14:35:00Z

Totals: 🔴 5 pending | 🟢 0 accepted | 🔵 0 rejected | 🟣 0 merged

┌────┬────────┬──────────┬─────────┬──────┬─────────────────┐
│ ID │ Type   │ Owner    │ Status  │ Conf │ Statement       │
├────┼────────┼──────────┼─────────┼──────┼─────────────────┤
│ F1 │ fact   │ you      │pending  │ high │ 6 atomic roles  │
│ L1 │ lemma  │ you      │ pending │ med  │ Roles enable    │
│ C1 │ conj   │ you      │ pending │ med  │ Need K-gates    │
│ D1 │ design │ you      │ pending │ med  │ Districts scale │
│ R1 │ risk   │ you      │ pending │ high │ Ledgers sync    │
└────┴────────┴──────────┴─────────┴──────┴─────────────────┘

🏴 TOP 3 BLOCKERS (pending claims that block progress):
  1️⃣  C1 (conjecture): "K-gates required" — needs evidence
  2️⃣  D1 (design): "Districts scale" — needs validation
  3️⃣  R1 (risk): "Ledgers sync" — needs mitigation plan

🎯 NEXT ACTION:
  → Skeptic-challenge the 3 blockers
  → Then transition to Outline phase
  → Then Foreman curates all claims

═══════════════════════════════════════════════════════════════════════════════
```

### /phase-next 🛑 📜 ➡️

```
🛑 PHASE TRANSITION GATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FROM: Explore
TO:   Outline
Reason: Starter claims submitted; outline sketch ready
Carryovers: [F1, L1, C1, D1, R1]

🔍 EXIT CHECKLIST (Explore):
  ✓ ≥10 claims submitted (5 submitted)
  ✓ Outline sketch exists (governance scaling architecture)
  ✓ Assumptions labeled ([ASSUMPTION] tags added)
  ✓ Gaps identified (K-gate validation gap, ledger sync gap)

═══════════════════════════════════════════════════════════════════════════════

✅ PHASE TRANSITION APPROVED
Timestamp: 2026-02-13T14:40:00Z
Carryovers: 5 claims → flow to Outline phase

📜 LOG ENTRY:
  Phase: Explore → Outline
  Status: ✅ COMPLETE
  Exit checklist: PASS
  Carryovers: [F1, L1, C1, D1, R1]
  Archived: v0_fragments.md (raw notes)

🔗 ENTRY CHECKLIST (Outline):
  ☐ Claims organized by section
  ☐ Structure is linear
  ☐ Transitions identified
  ☐ No gaps >1 paragraph

═══════════════════════════════════════════════════════════════════════════════

🎯 NEXT: /skeptic-challenge to red-team blockers → then continue
```

### /skeptic-challenge ⚔️ 🏴

```
⚔️ RED TEAM ATTACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target: C1 (Conjecture: "Scaling to 100+ agents requires K-gates")
Context: Edge case — what if agents collude to bypass K-gates?

🎯 FAILURE ANALYSIS:

Failure Mode: Colluding agents can forge signatures if K-gates lack entropy source
Missing Assumption: Assumes K-gates have cryptographic strength
Counterexample: 5 agents each propose a fake claim; majority votes it through
Severity: 🔴 4/5 (high impact)
Minimal Fix: Add HMAC-SHA256 per agent + randomized nonce

───────────────────────────────────────

Alternative Attack Angle:

Failure Mode: Single agent can modify claim after acceptance (timing window)
Missing Assumption: Assumes immutable ledger (but not stated)
Counterexample: Agent submits claim C1 at T1, later modifies at T5 (pre-ship)
Severity: 🟡 3/5 (medium impact)
Minimal Fix: Seal ledger entries at acceptance, not at ship

═══════════════════════════════════════════════════════════════════════════════

✅ CRITIQUE SUBMITTED
ID: CRIT-001
Target: C1
Status: pending → awaiting response
Owner: Skeptic
Timestamp: 2026-02-13T14:45:00Z

🤝 Next: Researcher responds with evidence or author revises C1

═══════════════════════════════════════════════════════════════════════════════
```

### /editorial-collapse 🏗️ 🎯

```
🏗️ EDITORIAL COLLAPSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Merging:
  drafts/v0.md (raw fragments)
  drafts/v1.md (convergent prose)

Target: 40% reduction
Tone: formal, authoritative
Notation: consistent throughout

═══════════════════════════════════════════════════════════════════════════════

📊 ANALYSIS:

Original (v1.md):
  Word count: 4,200
  Sections: 8
  Duplicates found: 2 (governance model repeated in intro + section 2)
  Contradictions: 1 (timeline: 8 weeks vs. 12 weeks)
  Tone drift: Yes (informal in section 4)

🎯 COLLAPSE PLAN:
  Cut #1: Intro example (300 words) → too context-heavy
  Cut #2: Historical background (600 words) → not needed for execs
  Cut #3: Alternative frameworks discussion (350 words) → weakens recommendation
  Merge #1: Two timeline claims → split difference (10 weeks)
  Tone harmonize: Formal throughout (remove "super important", casual language)

═══════════════════════════════════════════════════════════════════════════════

✅ EDITORIAL COLLAPSE COMPLETE

Final (v2.md):
  Word count: 2,520
  Reduction: 40% (1,680 words cut)
  Status: ✅ COHERENT (no duplicates, no contradictions)
  Tone: ✅ CONSISTENT (formal throughout)
  Gaps: 2 marked as [TODO: expand with example]

📜 DECISION LOG (logs/decisions.md):
  [#1] Removed intro example (too much context)
  [#2] Removed historical background (not executive-relevant)
  [#3] Merged timelines (8w + 12w = 10w compromise)
  [#4] Unified tone (removed casual language)
  [#5] Reordered sections (pyramid structure: context → problem → solution)

═══════════════════════════════════════════════════════════════════════════════

🎯 READY FOR: /ship drafts/v2.md --impact "Governance model for scaling"
```

### /ship 🎁 🔒

```
🎁 ARTIFACT SHIPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Artifact: drafts/v2.md
Impact: Governance model validated for 100+ agent scaling
Next Steps: Prototype in CONQUEST world model; test K-gate enforcement

═══════════════════════════════════════════════════════════════════════════════

📜 SHIPPING LOG:

Changes from last version:
  - Word count: 4,200 → 2,520 (40% reduction)
  - Sections reorganized (8 → 6, better flow)
  - Tone harmonized (formal throughout)
  - 2 duplicates removed
  - 1 contradiction resolved (timeline compromise)

🔓 Open Loops:
  ❌ K-gate implementation details (TODO: next run)
  ❌ Performance benchmarks (TODO: measurement phase)
  ⚠️  Ledger synchronization (flagged for next iteration)

🔒 ARCHIVE CREATED:
  archive/can-foundry-scale-to-100-agents_2026-02-13_1450.md
  (immutable snapshot with metadata)

═══════════════════════════════════════════════════════════════════════════════

✅ ARTIFACT SHIPPED
Status: 🔒 LOCKED (immutable)
Timestamp: 2026-02-13T14:50:00Z

📋 MANIFEST UPDATED:
  Phase: ◷6 Ship
  Status: ✅ DELIVERED
  Artifact: archive/can-foundry-scale-to-100-agents_2026-02-13_1450.md
  Impact: Governance model validated for 100+ agent scaling
  Next: Prototype in CONQUEST world model

  Run is now TERMINAL (no further work without restart)

═══════════════════════════════════════════════════════════════════════════════
```

### /hyperfocus ⚡ 🎯

```
⚡ HYPERFOCUS SESSION START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Duration: 90 minutes
Objective: Expand — sketch 3 scaling architectures
Discipline: Lateral exploration (raw ideas, no editing)
Run: can-foundry-scale-to-100-agents

Timer: ◷ 0:00 / 90:00 [▶ RUNNING]

🎯 SESSION RULES:
  ✓ Submit one claim per idea (don't overthink)
  ✓ Label [ASSUMPTION] tags (mark uncertainty)
  ✓ No editing, no organizing (raw only)
  ✓ Silence notifications (focus)
  ✓ Produce claims, not prose

✗ DO NOT:
  ✗ Context-switch (no email, no Slack)
  ✗ Revise (first draft only)
  ✗ Zoom out (stay on objective)

═══════════════════════════════════════════════════════════════════════════════

⏰ MIDPOINT BREAK TIMER: ◷ 45:00

At 45m, you'll see:
  ⏸️  BREAK TIME (10 minutes)
     Claims so far: [N]
     Words produced: [N]
     Pace: [words/min]
     Energy check: (restore? continue?)

═══════════════════════════════════════════════════════════════════════════════
```

### /rhythm-check 👁️ ⚠️

```
👁️ RHYTHM CHECK (Anti-Burnout Monitor)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Last 24 hours:

Hyperfocus Sessions: 2
  ⚡ Session 1: 90m (10:00-11:30) — Expand
  ⚡ Session 2: 45m (14:00-14:45) — Select

Total Active Time: 2h 15m
Breaks Taken: 1 (at 45m mark of Session 1)

───────────────────────────────────────

🟢 BURNOUT RISK: LOW ✅

  Baseline: <4h/day, regular breaks, balanced session types
  Your pattern: 2.25h/day, breaks observed, variety present

  ✓ Total hyperfocus <4 hours
  ✓ Break observed (every 45m)
  ✓ Session variety (expand + select)
  ✓ No late-night work

═══════════════════════════════════════════════════════════════════════════════

🎯 PERSONAL STATE:

🥖 Energy: 7/10 (good provisioning)
💖 Motivation: 5.0/10 (stable, engaged)
🛡️ Stability: 6.0/10 (coherent, no major blockers)
⚠️ Risk Level: 1/10 (very low)

───────────────────────────────────────

✅ RHYTHM IS HEALTHY. CONTINUE AT CURRENT PACE.

Recommendations:
  1️⃣  Next hyperfocus: 90m (expand → select cycle works)
  2️⃣  Optional break: 15m walk/hydrate
  3️⃣  Stay on current topic (momentum is good)

═══════════════════════════════════════════════════════════════════════════════
```

### /dashboard 🗺️ 🗣️

```
🗺️ FOUNDRY TOWN DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACTIVE RUNS
┌───────────────────────┬─────────┬──────────┬─────────────────┐
│ Run                   │ Phase   │ Claims   │ Next Action     │
├───────────────────────┼─────────┼──────────┼─────────────────┤
│ can-foundry-scale     │ ◷3 Drft │ 15 acc   │ Finish v1.md    │
│ governance-tiers      │ ◷2 Otln │ 8 pend   │ Organize claims │
│ zeta-proof-matrix     │ ◷4 Vrfy │ 12 acc   │ Challenge R-5   │
└───────────────────────┴─────────┴──────────┴─────────────────┘

───────────────────────────────────────

🎭 YOUR STATE (Now: 2026-02-13 14:55):

🥖 Energy: 7/10 (provisioning good)
💖 Motivation: 5.0/10 (stable, on task)
🛡️ Stability: 6.0/10 (coherent, no blockers)

⏰ Timestamps:
   Last hyperfocus: 45m ago (select phase)
   Last break: 50m ago (good)
   Last ship: 5m ago (🎁 just delivered!)

🟢 Burnout Risk: LOW (continue at pace)

═══════════════════════════════════════════════════════════════════════════════

🎯 IMMEDIATE NEXT (Pick One):

[ ] A️⃣  can-foundry-scale: Finish v1.md prose (30m) → then editorial-collapse
[ ] B️⃣  governance-tiers: Organize 8 pending claims (20m) → then phase-next outline
[ ] C️⃣  zeta-proof: Challenge R-5 with edge case (15m) → then /skeptic-challenge
[ ] D️⃣  Personal: Take 15m break (walk, hydrate, reset)
[ ] E️⃣  Admin: Clean up deferred claims from old runs

═══════════════════════════════════════════════════════════════════════════════

💡 STRATEGIC CONTEXT:

You've shipped 1 artifact today (governance scaling model).
3 runs are active in parallel.
Rhythm is healthy; continue with current 2-session/day pattern.

Next milestone: Ship zeta-proof-matrix by EOW (3 days).

═══════════════════════════════════════════════════════════════════════════════
```

### /lego-check 🧩 🏴

```
🧩 ATOMICITY VALIDATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component: role
Description: Writer and Skeptic combined: writes prose AND challenges claims

Analysis:
  Responsibilities identified: 2 ❌ (should be 1)
  1. "Writes prose from accepted claims"
  2. "Challenges claims and finds logical holes"

🔴 FAIL: NOT ATOMIC

Reason: Two conflicting mindsets (accept vs. attack) cannot coexist in single agent.
  ✗ Authority blending detected (editing prose + critiquing prose)
  ✗ Scope creep (exceeds single responsibility)
  ✗ Overlap with Skeptic role (direct conflict)
  ✗ Overlap with Writer role (direct conflict)

🏴 RECOMMENDATION: SPLIT INTO 3 ROLES

  Role A: Writer (atomic)
    ✓ Responsibility: Draft prose from accepted claims
    ✓ Powers: propose, draft, suggest transitions
    ✓ Limits: cannot decide structure, cannot challenge

  Role B: Skeptic (atomic)
    ✓ Responsibility: Attack claims and find logical holes
    ✓ Powers: propose critiques, surface assumptions, flag contradictions
    ✓ Limits: cannot write prose, cannot approve claims

  Role C: Synthesizer (atomic)
    ✓ Responsibility: Merge overlapping claims
    ✓ Powers: consolidate, deduplicate, normalize language
    ✓ Limits: cannot invent, cannot rewrite for style

═══════════════════════════════════════════════════════════════════════════════

✖️ VERDICT: DO NOT IMPLEMENT as combined role

✅ NEXT: Use the 3-role split above; run /lego-check on each individually

═══════════════════════════════════════════════════════════════════════════════
```

### /repeller-check 🛑 ✖️

```
🛑 REPELLER CHECK (Kill-Switch Validator)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target: runs/can-foundry-scale/drafts/v2.md
Custom Test: [none provided]

🔍 VALIDATION:

1. Internal Contradictions: ✓ PASS
   (Timeline: 10 weeks, consistent throughout)

2. Falsifiers Addressed: ✓ PASS
   (All assumptions from CONTEXT.md are either stated or footnoted)

3. Gaps: ✓ PASS
   (Marked as [TODO: expand with K-gate example])

4. Tone Consistency: ✓ PASS
   (Formal, authoritative throughout)

5. Reality-Check: ✓ PASS
   (Governance model is grounded in CLAUDE.md + CONQUEST precedents)

═══════════════════════════════════════════════════════════════════════════════

✅ REPELLER CHECK: PASS

Artifact is safe to ship.
No blocking issues detected.
Ready for /ship → archive → closure.

═══════════════════════════════════════════════════════════════════════════════
```

---

## Color Legend (For CLI Output)

```
🟢 GREEN   — All good, continue, pass
🟡 YELLOW  — Caution, monitor, warning
🔴 RED     — Critical, stop, burnout risk
🔵 BLUE    — Info, status, informational
🟣 PURPLE  — Phase/state-related, transitions
```

---

## Actor State Display (Optional, for multi-agent tracking)

```
🎭 MULTI-AGENT STATE (if tracking parallel workers)

⚜ Scribe-Heart (Lux):
   🥖 7/10 | 💖 5.0/10 | 🛡️ 6.0/10 | ⚠️ 1/10

🜍 Water (Key):
   🥖 7/10 | 💖 4.8/10 | 🛡️ 6.0/10 | ⚠️ 1/10

⚔ Fire (Breaker):
   🥖 7/10 | 💖 4.2/10 | 🛡️ 6.0/10 | ⚠️ 2/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Alert: Breaker's motivation (💖 4.2) is dropping.
   Recommendation: Assign lighter tasks; take break in 20m.
```

---

## Summary: WULmoji Makes Skills Feel Alive

**Instead of:**
```
Phase transition: explore → outline. Ready.
```

**You see:**
```
🛑 PHASE TRANSITION GATE
FROM: Explore → TO: Outline ➡️
✅ EXIT CHECKLIST PASS
📜 LOG ENTRY: [timestamp]
🎯 NEXT: Organize claims by section
```

---

**Status:** WULmoji aesthetic integrated across all 12 skills
**Effect:** Visual stimulation + symbol grammar reduces cognitive load
**Next:** Use `/foundry-new` with this aesthetic in your next run!

---

## Quick Aesthetic Copy-Paste Templates

For quick CLI output, copy these headers:

```
🧭 NAVIGATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👁️ OBSERVE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛑 GATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚔️ ATTACK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 DELIVER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ SUCCESS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✖️ FAIL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**Created:** 2026-02-13
**Status:** Ready for integration
**Next:** Apply to all skill output in live Foundry runs!
