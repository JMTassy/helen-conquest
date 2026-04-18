# Foundry Town: Complete Skills Library

**Status:** Production-ready, 12 core skills
**Architecture:** 3 tiers (Prompt-only, Repo-integrated, Scripted)
**Updated:** 2026-02-13

---

## Overview: The 12 Core Skills

| # | Skill | Tier | Purpose | Criticality |
|---|-------|------|---------|-------------|
| 01 | `/foundry-new` | B | Run scaffolder | CRITICAL (entry point) |
| 02 | `/claim` | B | Submit atomic idea | CRITICAL (coordination) |
| 03 | `/claims-status` | B | Pipeline dashboard | CRITICAL (visibility) |
| 04 | `/phase-next` | B | Phase gate + logging | CRITICAL (enforcement) |
| 05 | `/skeptic-challenge` | B | Red team attack | MANDATORY (tension) |
| 06 | `/editorial-collapse` | B | Merge + deduplicate | CRITICAL (convergence) |
| 07 | `/ship` | B | Artifact freeze + archive | CRITICAL (termination) |
| 08 | `/lego-check` | B | Atomicity validator | VALIDATION |
| 09 | `/hyperfocus` | B | Timebox sprint | OPERATIONAL |
| 10 | `/rhythm-check` | B | Anti-burnout monitor | HEALTH |
| 11 | `/dashboard` | B | State snapshot | OPERATIONAL |
| 12 | `/repeller-check` | B | Kill-switch validator | SAFETY |

---

## Directory Structure

```
your-project/
├── runs/
│   └── <run_name>/
│       ├── MANIFEST.md           # Objective, constraints, definition of done
│       ├── CONTEXT.md            # Assumptions, dependencies
│       ├── claims/
│       │   ├── pending.md        # [Inbox]
│       │   ├── accepted.md       # [Curated]
│       │   ├── rejected.md       # [Audit trail]
│       │   └── merged.md         # [Synthesis]
│       ├── drafts/
│       │   ├── v0.md             # [Raw outline]
│       │   ├── v1.md             # [Convergent prose]
│       │   └── v2.md             # [Final edited]
│       ├── logs/
│       │   ├── decisions.md      # [Editorial calls]
│       │   ├── phase_transitions.md
│       │   ├── experiments.md
│       │   └── artifacts.md      # [Shipped]
│       └── sources/
│           ├── bibliography.md
│           └── links.md
│
├── skills/
│   ├── 01-foundry-new.skill.md
│   ├── 02-claim.skill.md
│   ├── 03-claims-status.skill.md
│   ├── 04-phase-next.skill.md
│   ├── 05-skeptic-challenge.skill.md
│   ├── 06-editorial-collapse.skill.md
│   ├── 07-ship.skill.md
│   ├── 08-lego-check.skill.md
│   ├── 09-hyperfocus.skill.md
│   ├── 10-rhythm-check.skill.md
│   ├── 11-dashboard.skill.md
│   └── 12-repeller-check.skill.md
│
├── templates/
│   ├── MANIFEST.md.template
│   ├── CONTEXT.md.template
│   ├── claim-schema.yaml
│   ├── critique-schema.yaml
│   └── phase-checklist.md
│
└── _DASHBOARD.md                # Current state snapshot
```

---

## Skill Definitions (Full)

### SKILL 01: /foundry-new

**Purpose:** Create a run skeleton with scope contract.

**Tier:** B (Repo-integrated)

**Inputs:**
- `run_name` — Identifier (sanitized)
- `objective` — 1-sentence goal
- `audience` — Target (executives, engineers, team)
- `artifact_type` — memo, doc, guide, proposal, code
- `timebox` — Duration (45m, 90m, 2h, etc.)

**Outputs:**
```
runs/<run_name>/
├── MANIFEST.md        [Objective, constraints, definition of done]
├── CONTEXT.md         [Assumptions, dependencies]
├── claims/
│   ├── pending.md
│   ├── accepted.md
│   ├── rejected.md
│   └── merged.md
├── drafts/
│   ├── v0.md          [Outline sketch]
│   ├── v1.md
│   └── v2.md
├── logs/
│   ├── phase_transitions.md
│   ├── decisions.md
│   ├── experiments.md
│   └── artifacts.md
└── sources/
    ├── bibliography.md
    └── links.md
```

**Acceptance Criteria:**
- ✅ All folders exist
- ✅ MANIFEST.md has Objective, Deliverable, Non-goals, Constraints, Definition of Done
- ✅ CONTEXT.md lists assumptions + dependencies
- ✅ Phase 0 logged in phase_transitions.md

**Procedure:**
1. Sanitize `run_name` (lowercase, hyphens, no spaces)
2. Create folder tree
3. Generate MANIFEST.md with template
4. Generate CONTEXT.md with template
5. Create empty claim files with headers
6. Create empty draft files with headers
7. Log Phase 0 (Init) with timestamp
8. Return: run path + next action prompt

**Prompt Template:**
```
Create a Foundry run named "<run_name>".

Objective: <objective>
Audience: <audience>
Artifact Type: <artifact_type>
Timebox: <timebox>

Generate:
1. MANIFEST.md with:
   - Objective (1 sentence)
   - Deliverable (what ships)
   - Non-goals (what's explicitly out)
   - Constraints (scope, tone, length)
   - Definition of Done (success criteria)
   - 5-phase plan with exit conditions

2. CONTEXT.md with:
   - Assumptions (what we take as given)
   - Dependencies (what this requires)
   - Known risks (what could derail)
   - Decision points (where we need to choose)

3. Stub outlines for drafts/v0.md and claims/pending.md

Output the full run structure.
```

---

### SKILL 02: /claim

**Purpose:** Submit an atomic claim with evidence status.

**Tier:** B (Repo-integrated)

**Inputs:**
- `type` — fact, lemma, conjecture, design, risk
- `statement` — The claim (1-2 sentences)
- `support` — Evidence, reference, or reasoning
- `confidence` — low, medium, high
- `dependencies` — Other claims this relies on (optional)

**Outputs:**
```yaml
ID: C-###
Type: fact|lemma|conjecture|design|risk
Statement: "..."
Support: [links/notes]
Confidence: low|med|high
Dependencies: [C-...]
Falsifier: "What would disprove it?"
Status: pending
Owner: <you>
Date: [ISO 8601]
```

**Acceptance Criteria:**
- ✅ Claim has unique ID
- ✅ Statement is falsifiable (not circular)
- ✅ Falsifier is explicit (what would kill it)
- ✅ Appended to claims/pending.md

**Procedure:**
1. Generate next claim ID (auto-increment)
2. Parse claim type (validate)
3. Check statement is <200 words
4. Validate falsifier is present + meaningful
5. Append to claims/pending.md with timestamp
6. Return: claim ID + status

**Prompt Template:**
```
Submit this claim:

Type: <type>
Statement: <statement>
Support: <support>
Confidence: <confidence>
Dependencies: <dependencies>

Falsifier (what would disprove it?): [REQUIRED]

Append to claims/pending.md with auto-incremented ID.
Show me the formatted YAML.
```

---

### SKILL 03: /claims-status

**Purpose:** Show pipeline health + blockers.

**Tier:** B (Repo-integrated)

**Inputs:**
- `filter_type` (optional) — fact, lemma, conjecture, design, risk
- `filter_status` (optional) — pending, accepted, rejected, merged
- `filter_owner` (optional) — Your name or agent

**Outputs:**
```
CLAIM MARKET STATUS
Total: [N] pending | [N] accepted | [N] rejected | [N] merged

Table:
ID  | Type      | Owner       | Status   | Conf. | Statement
----|-----------|-------------|----------|-------|----------
C-1 | fact      | Researcher  | accepted | high  | ...
C-2 | critique  | Skeptic     | pending  | med   | ...

Top 3 Blockers:
[Pending claims that other work depends on]

Next Action: [What to do now]
```

**Acceptance Criteria:**
- ✅ Table shows all claims aggregated
- ✅ Blockers are identified (dependencies unresolved)
- ✅ Next action is <15 min task

**Procedure:**
1. Read all claim files (pending, accepted, rejected, merged)
2. Aggregate by status + type
3. Build table (5 columns min)
4. Identify blockers (high-confidence pending claims others depend on)
5. Suggest next action based on current phase

**Prompt Template:**
```
Show me claim market status for runs/<run_name>/.

Aggregate:
- Total pending, accepted, rejected, merged
- Table: ID | Type | Owner | Status | Confidence | Statement
- Top 3 blockers (pending claims that block progress)
- Next action (what to work on now)

Apply filters if provided: [filters]
```

---

### SKILL 04: /phase-next

**Purpose:** Move between phases with explicit reason + logging.

**Tier:** B (Repo-integrated)

**Phases:**
1. Explore — Divergent: gather facts, sketch outline, surface assumptions
2. Outline — Organize claims into structure
3. Draft — Convergent: prose from accepted claims
4. Verify — Red team, test assumptions, resolve contradictions
5. Finalize — Editorial collapse, deduplicate, cut
6. Ship — Freeze artifact, archive, declare done

**Inputs:**
- `from_phase` — Current phase
- `to_phase` — Next phase
- `reason` — Why we're moving
- `carryovers` — Claims/artifacts to carry forward

**Outputs:**
```
Phase Transition Logged:
FROM: <from_phase>
TO: <to_phase>
Reason: <reason>
Carryovers: [list]
Timestamp: [ISO 8601]
Exit Checklist: [Phase-specific checklist, completed]
Entry Checklist: [Phase-specific checklist, ready]
```

**Acceptance Criteria:**
- ✅ Previous phase exit checklist is done
- ✅ Reason is explicit (not vague)
- ✅ Carryovers are listed
- ✅ Logged to logs/phase_transitions.md
- ✅ MANIFEST.md updated with phase status

**Procedure:**
1. Check previous phase exit checklist (pass/fail)
2. List carryovers (approved claims, drafts, logs)
3. Log transition with reason + timestamp
4. Update MANIFEST.md phase status
5. Load new phase entry checklist
6. Return: confirmation + next actions

**Phase Checklists:**

**Explore (Exit):**
- [ ] ≥10 claims submitted
- [ ] Outline sketch exists
- [ ] Assumptions labeled
- [ ] Gaps identified

**Outline (Exit):**
- [ ] Claims organized by section
- [ ] Structure is linear
- [ ] Transitions identified
- [ ] No gaps >1 paragraph

**Draft (Exit):**
- [ ] Prose written from accepted claims
- [ ] Gaps marked explicitly
- [ ] Transitions are smooth
- [ ] Tone is consistent

**Verify (Exit):**
- [ ] Skeptic has challenged major claims
- [ ] Contradictions are logged
- [ ] False claims are marked
- [ ] Ready for editorial decision

**Finalize (Exit):**
- [ ] Duplicates removed
- [ ] Contradictions resolved
- [ ] Tone harmonized
- [ ] Gaps filled or explicitly listed

**Ship (Exit):**
- [ ] Artifact is immutable snapshot
- [ ] Impact statement is explicit
- [ ] Next steps are clear
- [ ] Archive entry exists

**Prompt Template:**
```
Transition from <from_phase> to <to_phase>.

Reason: <reason>
Carryovers: <carryovers>

Check:
1. Is <from_phase> exit checklist done?
2. Are carryovers legitimate?
3. Log to logs/phase_transitions.md
4. Update MANIFEST.md
5. Show entry checklist for <to_phase>
```

---

### SKILL 05: /skeptic-challenge

**Purpose:** Attack a claim or section with brutal honesty.

**Tier:** B (Repo-integrated)

**Inputs:**
- `target` — Claim ID (C-001) or section (drafts/v1.md#section-name)
- `context` — Optional framing ("edge case", "worst case", etc.)

**Outputs:**
```
Critique (appended to claims/pending.md or logs/decisions.md):
Target: <claim_id or section>
Failure Mode: <what goes wrong>
Missing Assumption: <hidden premise>
Counterexample: <case that breaks it>
Severity: 1-5 (1=minor, 5=fatal)
Minimal Fix: <simplest way to repair>
```

**Acceptance Criteria:**
- ✅ Attack is specific (not vague)
- ✅ Counterexample is concrete (not hypothetical)
- ✅ Minimal fix is stated
- ✅ Severity is rated 1-5
- ✅ Logged to claims/pending.md as critique

**Procedure:**
1. Locate target claim or section
2. Identify failure modes (logical, empirical, scope)
3. Surface missing assumptions
4. Propose counterexample
5. Rate severity 1-5
6. Suggest minimal fix
7. Append critique claim to pending.md

**Prompt Template:**
```
Red-team this target:

Target: <claim_id or section>
Context: <context if any>

For each failure mode, provide:
- Failure Mode: [What breaks?]
- Missing Assumption: [What's unstated?]
- Counterexample: [Concrete case that fails]
- Severity: [1-5]
- Minimal Fix: [Simplest repair]

Output as critique claim (append to claims/pending.md).
```

---

### SKILL 06: /editorial-collapse

**Purpose:** Merge multiple drafts into one canonical, deduplicated version.

**Tier:** B (Repo-integrated)

**Inputs:**
- `drafts` — List of draft files (v0.md, v1.md, etc.)
- `target_reduction` — % to cut (30%, 40%, 50%)
- `tone` — formal, casual, technical, narrative
- `notation_rules` — Consistency requirements (optional)

**Outputs:**
```
drafts/v2.md (final canonical version)
logs/decisions.md (detailed editorial log)
- [Cut #1: what was removed, why]
- [Contradiction #1: how it was resolved]
- [Tone harmonizations]
```

**Acceptance Criteria:**
- ✅ One canonical version (no duplicates)
- ✅ Notation is consistent
- ✅ Gaps are marked or filled
- ✅ Target reduction achieved (±5%)
- ✅ All cuts are logged with rationale
- ✅ Contradictions are resolved unilaterally

**Procedure:**
1. Read all drafts
2. Identify duplicated sections (deduplicate)
3. Find contradictions (log + resolve unilaterally)
4. Identify lowest-value content (candidates for cutting)
5. Cut to target reduction %
6. Harmonize tone + notation
7. Write logs/decisions.md entry
8. Output drafts/v2.md

**Prompt Template:**
```
Merge these drafts into one canonical version:

Drafts: <files>
Target Reduction: <target_reduction>%
Tone: <tone>
Notation Rules: <rules if any>

Steps:
1. Identify duplicated sections (remove)
2. Find contradictions (log + resolve unilaterally)
3. Select lowest-value content for cutting
4. Cut to target
5. Harmonize tone + notation
6. Produce v2.md + decisions.md entry

Show the merged version + decision log.
```

---

### SKILL 07: /ship

**Purpose:** Freeze an artifact with metadata + archive.

**Tier:** B (Repo-integrated)

**Inputs:**
- `artifact` — File to ship (drafts/v2.md)
- `impact` — 1-sentence impact statement
- `next_steps` — What this unlocks

**Outputs:**
```
logs/artifacts.md entry:
Artifact: <name>
Version: <version>
Timestamp: [ISO 8601]
Impact: <impact>
Next Steps: <next>
Changes from Last: [diff summary]
Open Loops: [unresolved items]
Archive: [immutable copy path]
Status: ✅ SHIPPED

runs/<run_name>/ marked as TERMINAL (no more work)
```

**Acceptance Criteria:**
- ✅ Artifact is immutable (snapshot)
- ✅ Archive entry created
- ✅ MANIFEST.md shows SHIPPED status
- ✅ Impact and next steps are explicit
- ✅ No reversions allowed

**Procedure:**
1. Create immutable copy (archive/)
2. Generate diff from last version
3. List open loops (unresolved items)
4. Log to logs/artifacts.md
5. Update MANIFEST.md with SHIPPED status
6. Mark run as terminal

**Prompt Template:**
```
Ship this artifact:

Artifact: <artifact>
Impact: <impact>
Next Steps: <next_steps>

Steps:
1. Summarize changes from last version
2. List open loops (unresolved items)
3. Create immutable snapshot
4. Log to logs/artifacts.md
5. Update MANIFEST.md with SHIPPED status
6. Show archive reference + completion confirmation
```

---

### SKILL 08: /lego-check

**Purpose:** Validate atomicity — one component = one responsibility.

**Tier:** B (Repo-integrated)

**Inputs:**
- `component_type` — role, superteam, district, kernel
- `description` — What it does
- `responsibilities` (optional) — List
- `powers` (optional) — List
- `limits` (optional) — List

**Outputs:**
```
✅ PASS or ❌ FAIL

If PASS:
- Single responsibility identified
- Powers are contained
- Limits are enforced
- No overlap with other components

If FAIL:
- Multiple responsibilities detected
- Authority blending found
- Proposed rewrite (minimal)
```

**Acceptance Criteria:**
- ✅ Component has ONE clear responsibility
- ✅ Powers support that responsibility only
- ✅ Limits prevent scope creep
- ✅ No authority blending with other components

**Procedure:**
1. Parse component description
2. Identify responsibilities (count)
3. Check powers align with responsibility
4. Verify limits are sufficient
5. Scan for overlap with known components
6. If >1 responsibility → suggest decomposition
7. Return PASS/FAIL + explanation

**Prompt Template:**
```
Validate atomicity for this component:

Type: <type>
Description: <description>
Responsibilities: <responsibilities if provided>
Powers: <powers if provided>
Limits: <limits if provided>

Check:
1. How many distinct responsibilities?
2. Do powers align with responsibility?
3. Are limits sufficient to prevent scope creep?
4. Any overlap with existing components?

Output: PASS/FAIL + explanation.
If FAIL, suggest minimal rewrite.
```

---

### SKILL 09: /hyperfocus

**Purpose:** Bounded sprint with no context-switching.

**Tier:** B (Repo-integrated)

**Inputs:**
- `duration` — 45m, 90m, 2h, 4h
- `objective` — Single deliverable
- `stop_condition` — When to end (time, deliverable, or threshold)

**Outputs:**
```
logs/experiments.md entry:
Sprint: <name>
Duration: <duration>
Objective: <objective>
Start: [ISO 8601]
End: [ISO 8601]
Claims Submitted: [N]
Words Produced: [N]
Output Artifacts: [list]
Status: ✅ COMPLETE or ❌ ABORT
Notes: [what happened]
```

**Acceptance Criteria:**
- ✅ Single objective (no scope drift)
- ✅ Duration respected (timebox enforced)
- ✅ Artifacts produced (not just effort)
- ✅ Explicit outcome (complete or abort)

**Procedure:**
1. Set timer for duration
2. Log sprint start with objective
3. Track claims submitted + words produced
4. Check at 50% mark (midpoint break recommended)
5. At timer end, log completion
6. If objective not met, explicit abort + reason
7. Update logs/experiments.md

**Prompt Template:**
```
Start hyperfocus sprint:

Duration: <duration>
Objective: <objective>
Stop Condition: <stop_condition>

Log start, set timer, produce only toward objective.
At end: log completion + artifact list.
If objective fails: explicit abort + reason.
```

---

### SKILL 10: /rhythm-check

**Purpose:** Anti-burnout monitor + throughput tracking.

**Tier:** B (Repo-integrated)

**Inputs:**
- None (or "today", "week", "month")

**Outputs:**
```
Rhythm Status:
- Last hyperfocus: [when] [duration]
- Last break: [when]
- Last ship: [when]
- Burnout risk: GREEN / YELLOW / RED

Pattern:
[N] sessions in [timeframe]
Total active: [hours]
Breaks taken: [N]

Recommendations:
1. [Next micro-task ≤15 min]
2. [If RED: stop now, break]
3. [If all green: continue]
```

**Acceptance Criteria:**
- ✅ Always returns one next action
- ✅ Flags are based on data (not opinion)
- ✅ Recommendations are <15 min tasks

**Procedure:**
1. Query logs/experiments.md for hyperfocus sessions
2. Count total active time (today/week)
3. Check break frequency
4. Query logs/artifacts.md for last ship
5. Compare to baselines:
   - Healthy: <4h/day, 2-3 sessions/week, breaks every 45m
   - YELLOW: 4-6h/day or 3-4 sessions/week or irregular breaks
   - RED: >6h/day or >4 sessions/week or no breaks
6. Suggest next action

**Prompt Template:**
```
Check rhythm + burnout risk.

Query logs:
- Hyperfocus sessions (duration, type, timestamp)
- Breaks taken
- Last ship date
- Total active time today/week

Compare to baselines:
GREEN: <4h/day, regular breaks, balanced session types
YELLOW: 4-6h/day or irregular breaks
RED: >6h/day or no breaks

Return: risk level + one next action ≤15 min.
```

---

### SKILL 11: /dashboard

**Purpose:** One-screen state snapshot of all active runs.

**Tier:** B (Repo-integrated)

**Inputs:**
- None (or run_name filter)

**Outputs:**
```
_DASHBOARD.md (or printed):

ACTIVE RUNS
┌─────────────┬──────────┬─────────┬──────────┐
│ Run         │ Phase    │ Claims  │ Next Act │
├─────────────┼──────────┼─────────┼──────────┤
│ governance  │ Verify   │ 15 pend │ Challenge R-005 |
│ zeta-proof  │ Draft    │ 8 acc   │ Finish v1 |
└─────────────┴──────────┴─────────┴──────────┘

YOUR STATE
Last hyperfocus: 2h ago (expand)
Last break: 1h ago
Last ship: 3 days ago
Burnout risk: GREEN

IMMEDIATE NEXT (Pick one)
[ ] Governance: Challenge R-005 (10 min)
[ ] Zeta-proof: Draft section 3 (45 min)
[ ] Rhythm: Take 15-min break
[ ] Admin: Clean up deferred claims
```

**Acceptance Criteria:**
- ✅ Shows all active runs
- ✅ Current phase visible for each
- ✅ Claim counts at a glance
- ✅ One immediate next action (pick one)

**Procedure:**
1. Scan runs/ folder
2. For each run: extract phase, claim counts, latest decision
3. Build summary table
4. Add personal state (last action timestamp, burnout risk)
5. List 3-4 immediate next options
6. Output to _DASHBOARD.md or print

**Prompt Template:**
```
Build dashboard for runs/:

For each run:
- Extract phase (from MANIFEST)
- Count pending/accepted claims
- Latest decision (from logs)
- Next action (implied by state)

Add personal state:
- Last hyperfocus duration + type
- Last break + last ship timestamps
- Burnout risk (from /rhythm-check)

Produce _DASHBOARD.md with table + next actions.
```

---

### SKILL 12: /repeller-check

**Purpose:** Kill-switch validator — block shipping if integrity fails.

**Tier:** B (Repo-integrated)

**Inputs:**
- `target` — Artifact file (drafts/v2.md) or run (runs/<name>/)
- `test` — Falsifier test (optional custom rule)

**Outputs:**
```
✅ PASS: Artifact is safe to ship
❌ FAIL: Artifact is incoherent/false

If FAIL:
- Failure reason: <specific>
- Required action: [fix or abort]
- Open loops: [items blocking pass]
- Recommendations: [next steps]
```

**Acceptance Criteria:**
- ✅ Artifact satisfies falsifiers
- ✅ Internal contradictions resolved
- ✅ Gaps are marked or filled
- ✅ Tone is consistent
- ✅ Ready for real-world use

**Procedure:**
1. Read target artifact
2. Check for internal contradictions
3. Verify falsifiers are addressed
4. Confirm gaps are marked or filled
5. Validate tone consistency
6. If any FAIL: block shipping, return specific reason
7. If all PASS: clear for ship

**Prompt Template:**
```
Run repeller-check on this artifact:

Target: <target>
Custom Test: <test if any>

Check:
1. Are internal contradictions resolved?
2. Are falsifiers addressed (nothing explicitly disproven)?
3. Are gaps marked or filled?
4. Is tone consistent throughout?
5. Does it survive contact with reality?

Output: PASS (clear to ship) or FAIL (specific reason + action).
```

---

## Bootstrap Sequence (Step-by-Step)

### STEP 1: Create Folder Structure

```bash
cd your-project/
mkdir -p runs skills templates
touch _DASHBOARD.md
echo "# Foundry Town Dashboard" > _DASHBOARD.md
```

### STEP 2: Create One Starter Run

Choose a topic. Use `/foundry-new`:

```bash
# Example: "Can Foundry scale to 100+ agents?"
/foundry-new "Can Foundry scale to 100+ agents?" \
  --audience engineers \
  --artifact_type proposal \
  --timebox 4h
```

**Output:**
```
runs/can-foundry-scale-to-100-agents/
├── MANIFEST.md (with objective, constraints, 5-phase plan)
├── CONTEXT.md (assumptions, dependencies)
├── claims/ (empty files with headers)
├── drafts/ (v0, v1, v2 stubs)
├── logs/ (phase_transitions.md initialized)
└── sources/ (bibliography.md initialized)
```

### STEP 3: Submit 5–10 Starter Claims

Use `/claim` to seed ideas:

```bash
/claim fact "Foundry supports 6 atomic roles (no role creep)" \
  --support "CLAUDE.md: LEGO1 definition" \
  --confidence high

/claim lemma "Atomic roles enable parallel work without bottlenecks" \
  --support "Oracle Town architecture: no single point of authority" \
  --confidence medium

/claim conjecture "Scaling to 100+ agents requires K-gates (fail-closed validation)" \
  --support "Constitutional rules prevent authority blending" \
  --confidence medium \
  --dependencies "fact_1"

/claim design "New scaling layer: 'Districts' fork independently" \
  --support "CONQUEST uses districts; each replicates kernel" \
  --confidence medium

/claim risk "Scaling breaks if districts' ledgers don't sync" \
  --support "[ASSUMPTION] assumes deterministic replay" \
  --confidence high
```

### STEP 4: Check Claim Market

```bash
/claims-status
```

**Output:**
```
CLAIM MARKET STATUS
Total: 5 pending | 0 accepted | 0 rejected | 0 merged

┌────┬────────┬──────────┬─────────┬──────┐
│ ID │ Type   │ Owner    │ Status  │ Conf │
├────┼────────┼──────────┼─────────┼──────┤
│ F1 │ fact   │ you      │ pending │ high │
│ L1 │ lemma  │ you      │ pending │ med  │
│ C1 │ conj   │ you      │ pending │ med  │
│ D1 │ design │ you      │ pending │ med  │
│ R1 │ risk   │ you      │ pending │ high │
└────┴────────┴──────────┴─────────┴──────┘

Top Blockers: None (all pending, waiting for curation)
Next Action: Foreman curates claims → accept/reject/merge
```

### STEP 5: Install the 3 Enforcement Gates

```bash
# Gate 1: Phase transitions (forces orderly progression)
/phase-next explore \
  --reason "5 starter claims submitted, outline sketch ready"

# (This marks Phase 0 → Phase 1 complete)

# Gate 2: Red-team critical claims (mandatory tension)
/skeptic-challenge F1 --context "edge case: agents modifying their own roles"

/skeptic-challenge R1 --context "what if ledgers diverge?"

# Gate 3: Kill-switch validator (blocks bad artifacts)
# (Use /repeller-check before shipping)
```

### STEP 6: Run a Hyperfocus Session

```bash
/hyperfocus 90m \
  --objective "Expand: sketch out 3 scaling architectures for 100+ agents" \
  --stop_condition "time limit (90m) or 15+ claims submitted"
```

**During session:**
- Submit claims as ideas emerge
- Label assumptions with `[ASSUMPTION]`
- At 45m mark: `/rhythm-check` for break
- Continue until timer or 15 claims

**Output:**
- claims/pending.md updated with new claims (L2, L3, etc.)
- logs/experiments.md entry logged

### STEP 7: View Dashboard

```bash
/dashboard
```

**Output:**
```
_DASHBOARD.md updated with:
- Run state (phase, claim counts)
- Personal state (burnout risk, last action)
- Immediate next options
```

---

## Quick Copy-Paste Prompts (Minimal)

Use these exact prompts if you don't want to read the full skill definition.

### /foundry-new

```
Scaffold runs/<name>/ with the canonical tree. Write MANIFEST.md with:
- Objective (1 sentence)
- Deliverable (what ships)
- Non-goals (explicitly out)
- Constraints (scope, tone, length)
- Definition of Done (success criteria)
- 5-phase plan with exit conditions

Write CONTEXT.md with:
- Assumptions (what we take as given)
- Dependencies (what this requires)
- Known risks (what could derail)
- Decision points (where we choose)

Create drafts/v0.md as an outline sketch + claims/pending.md stub.
```

### /editorial-collapse

```
Merge these drafts into one canonical version:

Drafts: [files]
Target: [30/40/50]% reduction
Tone: [formal/casual/technical/narrative]

Steps:
1. Deduplicate (remove identical sections)
2. Resolve contradictions (editor decides, logs reason)
3. Cut lowest-value content to target
4. Harmonize notation + tone
5. Mark gaps explicitly or fill them

Produce:
- drafts/v2.md (final version)
- logs/decisions.md (what was cut, why)
```

### /ship

```
Freeze this artifact:

Artifact: [file]
Impact: [1-sentence impact statement]
Next: [what this unlocks]

Steps:
1. Summarize changes from last version
2. List open loops
3. Create immutable copy (archive/)
4. Log to logs/artifacts.md
5. Update MANIFEST.md: status = SHIPPED

Confirm: artifact is now immutable.
```

---

## Module Truth Table (Skills Status)

| Skill | Tier | Status | Purpose |
|-------|------|--------|---------|
| 01-foundry-new | B | ✅ Ready | Run scaffolder |
| 02-claim | B | ✅ Ready | Submit idea |
| 03-claims-status | B | ✅ Ready | Pipeline visibility |
| 04-phase-next | B | ✅ Ready | Phase gate |
| 05-skeptic-challenge | B | ✅ Ready | Red team |
| 06-editorial-collapse | B | ✅ Ready | Merge + finalize |
| 07-ship | B | ✅ Ready | Artifact freeze |
| 08-lego-check | B | ✅ Ready | Atomicity validator |
| 09-hyperfocus | B | ✅ Ready | Timebox sprint |
| 10-rhythm-check | B | ✅ Ready | Anti-burnout |
| 11-dashboard | B | ✅ Ready | State snapshot |
| 12-repeller-check | B | ✅ Ready | Kill-switch |

---

## Next: Your First Run

Pick a topic from your active work. Run:

```bash
/foundry-new "Your topic" --audience engineers --artifact_type proposal --timebox 2h
/hyperfocus 90m --objective "Expand on topic"
/claims-status
/phase-next explore --reason "Starter claims done"
/skeptic-challenge [claim_id] --context "edge case"
/editorial-collapse drafts/v1.md --reduce 40%
/repeller-check runs/[name]/
/ship drafts/v2.md --impact "One sentence" --next "What unlocks"
/dashboard
```

**Total time to ship:** ~2–4 hours (depending on topic complexity)

---

**Status:** Complete skills library, ready for integration
**Architecture:** 3-tier (Prompt, Repo, Scripted)
**Updated:** 2026-02-13
**Next:** Choose your first topic and run the bootstrap sequence
