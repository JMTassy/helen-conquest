# Foundry Town Skills Architecture

**Status:** Implemented for operational integration
**Last Updated:** 2026-02-13
**Scope:** 10 core skills for Foundry Town workflow automation

---

## Quick Reference: Skill Invocation

All skills follow the format: `/skill-name [args]`

| Skill | Shortcut | Purpose | Example |
|-------|----------|---------|---------|
| `foundry-new` | `N/A` | Scaffold new Foundry run | `/foundry-new "Topic" --audience execs --format memo --duration 45m` |
| `claim` | `N/A` | Submit a claim to pending.md | `/claim evidence "Statement" --source ref --confidence high` |
| `phase-next` | `N/A` | Transition to next phase, log change | `/phase-next exploration --reason "facts gathered"` |
| `skeptic-challenge` | `N/A` | Red-team a claim or section | `/skeptic-challenge R-005` |
| `editorial-collapse` | `N/A` | Merge drafts, cut 30-50%, finalize | `/editorial-collapse v1_draft.md --reduce 40%` |
| `ship` | `N/A` | Archive artifact, log outcome, create link | `/ship v2_editorial.md --impact "Governance clarified"` |
| `claims-status` | `N/A` | Show claim market state (pending/accepted/rejected) | `/claims-status --author Researcher` |
| `hyperfocus` | `N/A` | Bounded timer + context tracking | `/hyperfocus 90m --discipline expand` |
| `rhythm-check` | `N/A` | Anti-burnout query (work pattern analysis) | `/rhythm-check` |
| `lego-check` | `N/A` | Validate role/team/district atomicity | `/lego-check role "My new agent"` |

---

## Skill Definitions (Implementation)

### 1. FOUNDRY-NEW — Run Scaffold

**Purpose:** Create a new Foundry Town run with complete workspace structure.

**Syntax:**
```bash
/foundry-new <SUBJECT> [OPTIONS]
```

**Required Arguments:**
- `<SUBJECT>` — The topic or question being explored (quoted string)

**Optional Arguments:**
- `--audience AUDIENCE` — Target audience (default: general)
- `--format FORMAT` — Output format: memo, doc, guide, proposal, code (default: doc)
- `--duration DURATION` — Hyperfocus window: 45m, 90m, 2h, etc. (default: 90m)
- `--tone TONE` — Voice: formal, casual, technical, narrative (default: formal)
- `--length LENGTH` — Scope: short, medium, long (default: medium)

**Output Structure:**
```
runs/<normalized-subject>/
├── MANIFEST.md                    # Subject, constraints, phase log
├── claims/
│   ├── pending.md                # [inbox for agent submissions]
│   ├── accepted.md               # [curated, flows to drafting]
│   ├── rejected.md               # [audit trail]
│   └── merged.md                 # [synthesis log]
├── drafts/
│   ├── v0_fragments.md           # [raw notes, Phase 1]
│   ├── v1_draft.md               # [convergent draft, Phase 3]
│   └── v2_editorial.md           # [final, Phase 4]
├── logs/
│   └── phase_transitions.md      # [hard timeline: PHASE → timestamp → reason]
└── sources/
    └── references.md             # [evidence, organized by type]
```

**Example:**
```
/foundry-new "Why we need decision memos" \
  --audience executives \
  --format memo \
  --duration 45m \
  --tone formal
```

**Output:**
```
✅ Foundry run created: runs/why-we-need-decision-memos/
   - MANIFEST.md
   - claims/ (all subdirs)
   - drafts/ (v0, v1 stubs)
   - logs/ (phase_transitions.md)
   - sources/ (references.md)

Ready for Phase 1: Exploration (45 min timer running)
```

**Implementation Details:**
- Generates run folder from sanitized subject name
- Pre-populates MANIFEST.md with subject, constraints, phase 0 (init)
- Creates empty claim files with headers (PENDING, ACCEPTED, REJECTED, MERGED)
- Logs initial timestamp in phase_transitions.md
- Returns ready state + timer start message

---

### 2. CLAIM — Claim Submission

**Purpose:** Format and submit a claim to the Claim Market (pending.md).

**Syntax:**
```bash
/claim <TYPE> "<STATEMENT>" [OPTIONS]
```

**Required Arguments:**
- `<TYPE>` — Claim type: evidence, critique, structure, content, synthesis, visual, meta
- `"<STATEMENT>"` — The actual claim (quoted string, max 200 words)

**Optional Arguments:**
- `--source SOURCE` — Reference or origin (file, URL, agent name)
- `--confidence LEVEL` — low, medium, high (default: medium)
- `--author ROLE` — Agent role (Researcher, Skeptic, Writer, Structurer, etc.)
- `--run PATH` — Run folder (default: current/latest)

**Output Format (appended to pending.md):**
```yaml
---
CLAIM: [AUTO-INCREMENTED ID]
type: [TYPE]
statement: "[STATEMENT]"
source: "[SOURCE]"
confidence: [LEVEL]
author: [ROLE]
status: pending
timestamp: [ISO 8601]
---
```

**Example:**
```
/claim evidence "Oracle Town has K-gates that prevent self-modification" \
  --source CLAUDE.md \
  --confidence high \
  --author Researcher
```

**Output:**
```
✅ Claim submitted
   ID: R-042
   Status: pending
   Location: runs/[current]/claims/pending.md

Awaiting Foreman curation (accept/reject/merge)
```

**Implementation Details:**
- Auto-increments ID based on type prefix (R-###, C-###, T-###, W-###, M-###, V-###)
- Validates claim statement (no >200 words; no jargon without context)
- Appends to pending.md with timestamp
- Returns claim ID for reference in subsequent work

---

### 3. PHASE-NEXT — Phase Transition

**Purpose:** Log phase transition, archive state, move to next phase.

**Syntax:**
```bash
/phase-next <CURRENT_PHASE> [OPTIONS]
```

**Required Arguments:**
- `<CURRENT_PHASE>` — Current phase: exploration, tension, drafting, editorial, termination

**Optional Arguments:**
- `--reason REASON` — Why transitioning (quoted string)
- `--run PATH` — Run folder (default: current/latest)

**Output:**
```
Phase Timeline Entry:
  FROM: Phase N
  TO: Phase N+1
  Timestamp: [ISO 8601]
  Reason: [REASON]
  Artifacts Preserved: [LIST]
```

**Example:**
```
/phase-next exploration --reason "sufficient facts gathered, outline sketched"
```

**Output:**
```
✅ Phase transition logged
   FROM: Exploration
   TO: Tension
   Timestamp: 2026-02-13T14:23:00Z
   Reason: sufficient facts gathered, outline sketched

TENSION PHASE ACTIVATED
   - All accepted claims are now under skeptic review
   - Pending claims on hold
   - Next: /phase-next tension --reason "contradictions resolved"
```

**Implementation Details:**
- Updates phase_transitions.md with hard timestamp
- Archives current drafts (copies v0_fragments.md if in Exploration)
- Resets pending claims to "under review" (don't delete)
- Prevents reversions (Phase 1 → Phase 2 only, never backward)
- No-op if already in requested phase

---

### 4. SKEPTIC-CHALLENGE — Adversarial Review

**Purpose:** Invoke Skeptic role to attack a claim or section.

**Syntax:**
```bash
/skeptic-challenge <TARGET> [OPTIONS]
```

**Required Arguments:**
- `<TARGET>` — Claim ID (R-042) OR section (drafts/v1_draft.md#section-name)

**Optional Arguments:**
- `--depth DEPTH` — Rigor: shallow, medium, deep (default: medium)
- `--angle ANGLE` — Attack vector: assumptions, evidence, logic, scope, precedent (default: all)
- `--run PATH` — Run folder (default: current/latest)

**Output:**
```yaml
CHALLENGE: [CLAIM/SECTION]
  Target: [ID OR SECTION]
  Skeptic Perspective: "[Adversarial analysis]"
  Assumptions Identified: [LIST]
  Evidence Gaps: [LIST]
  Logic Flaws: [LIST]
  Confidence: [IMPACT RATING]
  Status: pending (awaiting Researcher/Author response)
```

**Example:**
```
/skeptic-challenge R-005 --depth deep --angle assumptions
```

**Output:**
```
✅ Skeptic challenge submitted
   Target: R-005 (Evidence claim about K-gates)
   Challenge ID: C-087
   Status: pending (awaiting response)

Skeptic's Attack:
   - Assumes K-gates are deterministic without proof
   - Does not address edge case: malicious input
   - Conflates "prevents self-mod" with "prevents all exploits"
   - Evidence cites only CLAUDE.md (single source)

Next Steps:
   - Researcher clarifies evidence gaps
   - Author provides additional sources
   - Submit rebuttal as claim, or merge into R-005 revision
```

**Implementation Details:**
- Generates critique claim (C-###) automatically
- Appends to pending.md
- Links back to original claim (reference in YAML)
- Does NOT auto-reject; challenge is a *proposal* (awaiting curation)
- Flags for Foreman as contested item

---

### 5. EDITORIAL-COLLAPSE — Compression & Finalization

**Purpose:** Merge drafts, cut ruthlessly (30-50%), resolve contradictions, finalize artifact.

**Syntax:**
```bash
/editorial-collapse <DRAFT> [OPTIONS]
```

**Required Arguments:**
- `<DRAFT>` — Draft file: v1_draft.md (or other path)

**Optional Arguments:**
- `--reduce PERCENT` — Target reduction: 30, 40, 50 (default: 40%)
- `--tone TONE` — Final voice: formal, casual, technical, narrative (default: formal)
- `--merge-with FILE` — Merge additional draft(s) before collapse
- `--run PATH` — Run folder (default: current/latest)

**Output:**
```
v2_editorial.md (final artifact)
EDITORIAL_LOG.md (decision record)
  - Cuts made (sections, redundancy, asides)
  - Contradictions resolved (decision + rationale)
  - Tone enforced
  - Final word count + reduction %
```

**Example:**
```
/editorial-collapse drafts/v1_draft.md --reduce 40% --tone formal
```

**Output:**
```
✅ Editorial collapse complete
   Source: drafts/v1_draft.md (4,200 words)
   Target: drafts/v2_editorial.md (2,520 words)
   Reduction: 40% (1,680 words cut)

Decisions:
   [#1] Removed "Historical Background" section (3 pages)
       Rationale: Context, not argument. Appendix alternative rejected (out of scope).
   [#2] Merged 2 contradictory governance models
       Decision: Model A (organizational clarity) over Model B (flexibility)
       Rationale: Audience preference (executives need structure)
   [#3] Reordered sections: Context → Claims → Recommendations
       Rationale: Executive-friendly pyramid structure

Ready for termination: /ship v2_editorial.md
```

**Implementation Details:**
- Reads v1_draft.md (or specified draft)
- Identifies redundant sections (counts paragraphs, flags duplicates)
- Surfaces contradictions (queries for unresolved claims)
- Applies aggressive cuts (selects lowest-value content first)
- Reorders for coherence (follows specified tone structure)
- Outputs v2_editorial.md + EDITORIAL_LOG.md
- Does NOT modify source drafts

---

### 6. SHIP — Artifact Delivery & Logging

**Purpose:** Archive completed artifact, log outcome, create reference link.

**Syntax:**
```bash
/ship <ARTIFACT> [OPTIONS]
```

**Required Arguments:**
- `<ARTIFACT>` — File path to final artifact (typically v2_editorial.md)

**Optional Arguments:**
- `--impact IMPACT` — One-sentence impact statement (quoted)
- `--next NEXT` — What this artifact unlocks (quoted)
- `--outcome OUTCOME` — deliver, abort (default: deliver)
- `--run PATH` — Run folder (default: current/latest)

**Output:**
```
MANIFEST.md (updated)
  - Status: ✅ DELIVERED (or ❌ ABORT)
  - Final Artifact: [LINK]
  - Impact: [STATEMENT]
  - Next Steps: [RECOMMENDATION]
  - Completion Timestamp: [ISO 8601]
  - Archive Link: [PATH]
```

**Example:**
```
/ship drafts/v2_editorial.md \
  --impact "Governance model clarified for leadership decision-making" \
  --next "Draft implementation charter for Q2 kickoff"
```

**Output:**
```
✅ Artifact shipped
   File: runs/governance-tiers/drafts/v2_editorial.md
   Archive: archive/governance-tiers_2026-02-13_1423.md
   Status: DELIVERED

MANIFEST Updated:
   Phase 5: TERMINATION
   Status: ✅ DELIVERED
   Impact: Governance model clarified for leadership decision-making
   Next Steps: Draft implementation charter for Q2 kickoff
   Timestamp: 2026-02-13T14:23:00Z

   Public Link: [shareable URL if applicable]

Completion logged. Run ready for review or archival.
```

**Implementation Details:**
- Archives artifact with timestamp (runs/ → archive/)
- Updates MANIFEST.md with completion state
- Logs final outcome (deliver or abort)
- Generates shareable link (if applicable; depends on storage)
- Marks run as terminal (no further work without restart)
- One-shot: cannot re-ship same run

---

### 7. CLAIMS-STATUS — Claim Market Dashboard

**Purpose:** Show current state of all claims (pending, accepted, rejected, merged).

**Syntax:**
```bash
/claims-status [OPTIONS]
```

**Optional Arguments:**
- `--author ROLE` — Filter by author (Researcher, Skeptic, Writer, etc.)
- `--type TYPE` — Filter by type (evidence, critique, structure, content, synthesis, visual, meta)
- `--status STATUS` — Filter by status (pending, accepted, rejected, merged)
- `--confidence LEVEL` — Filter by confidence (low, medium, high)
- `--run PATH` — Run folder (default: current/latest)
- `--verbose` — Show full claim statements (default: summary only)

**Output (Table Format):**
```
CLAIM MARKET STATUS
Run: governance-tiers
Generated: 2026-02-13T14:25:00Z

┌─────┬────────┬──────────┬──────────┬─────────┬──────────┐
│ ID  │ Type   │ Author   │ Status   │ Conf.   │ Statement [truncated] │
├─────┼────────┼──────────┼──────────┼─────────┼──────────┤
│ R-001 │ evidence │ Researcher │ accepted │ high │ K-gates prevent self-modification... │
│ R-002 │ evidence │ Researcher │ pending │ medium │ Three-tier governance exists... │
│ C-087 │ critique │ Skeptic │ pending │ high │ Assumption: K-gates are deterministic... │
│ T-005 │ structure │ Structurer │ accepted │ high │ Outline: Context → Claims → Recs... │
│ W-012 │ content │ Writer │ accepted │ medium │ Draft prose: Governance section... │
└─────┴────────┴──────────┴──────────┴─────────┴──────────┘

Summary:
   Pending: 3  |  Accepted: 5  |  Rejected: 1  |  Merged: 2

Next Action:
   - Phase 2 (Tension): Resolve pending C-087 (skeptic challenge)
   - Then proceed to Phase 3 (Drafting) when Foreman approves
```

**Example (with filter):**
```
/claims-status --author Researcher --status accepted --verbose
```

**Output:**
```
CLAIM MARKET STATUS (Filtered)
Run: governance-tiers
Filter: author=Researcher, status=accepted

R-001 │ evidence │ accepted │ high
   "K-gates prevent self-modification of authority claims by non-authorized agents,
    enforced through deterministic signature verification in the Ledger system."
   Source: CLAUDE.md, Section "Constitutional Rules"
   Timestamp: 2026-02-13T10:15:00Z

R-003 │ evidence │ accepted │ high
   "Three-tier governance model (Observer, Decider, Analyst) parallels CALVI 2030
    strategic framework, tested in Oracle Town simulation."
   Source: ORACLE_TOWN_RESEARCH_PAPER.md, Section "Scaled Authority"
   Timestamp: 2026-02-13T11:02:00Z

Summary: 2 accepted claims from Researcher
```

**Implementation Details:**
- Aggregates claims from pending.md, accepted.md, rejected.md, merged.md
- Filters by any combination of author, type, status, confidence
- Displays table (concise) or full statements (verbose)
- Shows summary counts
- Suggests next action based on phase and pending items

---

### 8. HYPERFOCUS — Bounded Timer & Context Tracking

**Purpose:** Start hyperfocus session with timer, track context, prevent burnout.

**Syntax:**
```bash
/hyperfocus <DURATION> [OPTIONS]
```

**Required Arguments:**
- `<DURATION>` — Time: 45m, 90m, 2h, 4h, etc.

**Optional Arguments:**
- `--discipline DISCIPLINE` — Activity: expand, select, ship (default: expand)
- `--run PATH` — Run folder (default: current/latest)
- `--subject SUBJECT` — Explicit subject reminder (quoted)

**Output:**
```
🔥 HYPERFOCUS SESSION STARTED
   Duration: [DURATION]
   Discipline: [ACTIVITY]
   Run: [RUN NAME]
   Subject: [SUBJECT]

   Timer: [RUNNING]
   Breaks: [PLANNED at 30m mark]

   📌 Context:
      - No context-switching (silence notifications)
      - Produce claims/prose, not perfection
      - Break at halfway point
      - Output at session end: /hyperfocus-end
```

**Example:**
```
/hyperfocus 90m --discipline expand --run governance-tiers --subject "Can Foundry handle 3-tier governance?"
```

**Output:**
```
🔥 HYPERFOCUS SESSION STARTED
   Duration: 90 minutes
   Discipline: Expansion (lateral exploration, raw ideas)
   Run: governance-tiers
   Subject: Can Foundry handle 3-tier governance?

   Timer: 0:00 / 90:00 [RUNNING ▶]

   📌 SESSION RULES:
      ✓ Produce claims in claims/pending.md (one idea = one claim)
      ✓ No organizing, no editing — raw exploration
      ✓ Label assumptions with [ASSUMPTION] tags
      ✓ Silence notifications
      ✗ No context-switching
      ✗ No revision loops

   ⏰ BREAKS:
      └─ 45m: 10-minute break recommended (hydrate, reset)

   🎯 NEXT STEP: When timer expires, run /hyperfocus-end to log session
```

**At Halfway Point (45m):**
```
⏰ MID-SESSION BREAK
   Duration: 10 minutes (pause timer)

   📊 Progress So Far:
      - Claims submitted: 8
      - Words produced: ~2,400
      - Rate: ~27 words/min (sustain or increase)

   💧 Self-check:
      - Energy level? (restart or extend?)
      - Focus quality? (good or degrading?)
      - Any blockers?

   ▶ Resume hyperfocus when ready
```

**At Session End:**
```
✅ HYPERFOCUS SESSION COMPLETE
   Duration: 90 minutes (elapsed)
   Claims submitted: 12
   Words produced: ~3,100

   Run: governance-tiers
   Artifacts: claims/pending.md (updated)

   Next Phase: /phase-next or /rhythm-check to assess
```

**Implementation Details:**
- Starts timer (client-side tracking)
- Logs session start in run logs
- Silences notifications for duration
- Sends break reminder at 50% mark
- Tracks claims submitted during session
- Auto-logs session end with stats
- Feeds into rhythm-check data

---

### 9. RHYTHM-CHECK — Anti-Burnout Monitor

**Purpose:** Query your work pattern; flag burnout risk.

**Syntax:**
```bash
/rhythm-check [OPTIONS]
```

**Optional Arguments:**
- `--run PATH` — Check specific run (default: all runs in current session)
- `--window WINDOW` — Time window: today, week, month (default: today)
- `--verbose` — Show detailed pattern analysis

**Output (Summary):**
```
🎵 RHYTHM CHECK
   Last 24 hours:

   Hyperfocus Sessions: 2
   ├─ Session 1: 90m (10:00-11:30) — Expansion
   └─ Session 2: 45m (14:00-14:45) — Selection

   Total Active Time: 2h 15m
   Breaks Taken: 1 (only at midpoint of Session 1)

   ⚠️  BURNOUT RISK: LOW
      - Total hyperfocus <4 hours/day ✓
      - Breaks observed ✓
      - Session variety (expand + select) ✓
      - No late-night work ✓

   ✅ Rhythm is healthy. Continue at current pace.
```

**Example (High Risk):**
```
/rhythm-check --verbose
```

**Output:**
```
🎵 RHYTHM CHECK
   Last 24 hours:

   Hyperfocus Sessions: 3
   ├─ Session 1: 4h 30m (09:00-13:30) — Expansion (NO BREAK)
   ├─ Session 2: 2h 15m (14:00-16:15) — Selection (NO BREAK)
   └─ Session 3: 1h 45m (17:30-19:15) — Drafting (NO BREAK)

   Total Active Time: 8h 30m
   Breaks Taken: 0

   🚨 BURNOUT RISK: CRITICAL

   Issues Identified:
      ✗ Total hyperfocus >6 hours (guideline: 3-4 hours)
      ✗ No breaks taken (risk of context degradation)
      ✗ 3 sessions in one day (no recovery time)
      ✗ Evening work (17:30 start; circadian disruption)

   Recommendations:
      1. Stop work immediately (you're degrading)
      2. Take 2-hour break (food, walk, sleep)
      3. Resume tomorrow with single 90m session only
      4. Enable /rhythm-check alerts (daily check-in)

   History:
      - This pattern seen 2x this week
      - Last week: healthier (2h sessions, consistent breaks)
      - Hypothesis: Current run intensity is unsustainable

   Next: /rhythm-check --window week (for full pattern)
```

**Implementation Details:**
- Aggregates hyperfocus session logs (from /hyperfocus)
- Tracks total active time, break frequency, session distribution
- Compares against baseline (3-4 hours/day, 2-3 sessions/week)
- Flags risk levels: LOW, MODERATE, HIGH, CRITICAL
- Provides personalized recommendations
- Can be automated (daily check-in prompt)

---

### 10. LEGO-CHECK — Atomicity Validator

**Purpose:** Test if a role/superteam/district stays within LEGO atomic boundaries.

**Syntax:**
```bash
/lego-check <COMPONENT_TYPE> "<DESCRIPTION>" [OPTIONS]
```

**Required Arguments:**
- `<COMPONENT_TYPE>` — Type: role, superteam, district, kernel
- `"<DESCRIPTION>"` — What the component does (quoted string)

**Optional Arguments:**
- `--responsibilities LIST` — Quoted list of responsibilities (e.g., "explore, critique, reject")
- `--powers LIST` — Quoted list of powers (e.g., "propose, merge, cut")
- `--limits LIST` — Quoted list of limits (e.g., "cannot write, cannot decide")
- `--test-against COMPONENT` — Check overlap with existing component
- `--verbose` — Detailed analysis

**Output (Pass):**
```
✅ LEGO-CHECK: PASS
   Component: role
   Name: [extracted from description]
   Atomicity: ✓ ATOMIC (single responsibility)

   Analysis:
   └─ Responsibility: One clear capability identified
      "Propose evidence claims and cite sources"

   └─ Powers: 3 (propose, cite, surface)
      All support core responsibility; no scope creep

   └─ Limits: 4 (cannot interpret, cannot decide, cannot invent)
      Properly constrained; prevents role blending

   └─ No overlap with: Skeptic (critique role), Writer (prose role)

   Verdict: This component is atomic and safe to implement.
```

**Example (Fail):**
```
/lego-check role "Writer and Skeptic combined: writes prose AND challenges claims"
```

**Output:**
```
❌ LEGO-CHECK: FAIL
   Component: role
   Name: [Combined Writer-Skeptic]
   Atomicity: ✗ NOT ATOMIC (two responsibilities)

   Analysis:
   └─ Responsibility: Two conflicting roles identified
      1. "Writes prose from accepted claims"
      2. "Challenges claims and finds logical holes"
      → These require opposite mindsets (accept vs. attack)
      → Single agent cannot hold both without bias

   └─ Powers: 6 (too many)
      Propose + Draft + Challenge + Merge + Cut + Flag
      → Exceeds single-role authority

   └─ Limits: Insufficient
      Only says "cannot decide structure"
      → But CAN edit prose (creates authority blending)
      → But CAN challenge others (conflict of interest)

   Overlap with:
      🔴 MAJOR: Writer role (responsibility conflict)
      🔴 MAJOR: Skeptic role (responsibility conflict)
      🟡 MEDIUM: Foreman role (powers overlap on merge/cut)

   Recommendation:
      ✗ DO NOT IMPLEMENT as combined role
      ✓ DO split into:
         - Role A: Writer (prose only)
         - Role B: Skeptic (challenge only, no prose)
         - Role C: Synthesizer (merge claims, not write)
```

**Implementation Details:**
- Parses description for responsibility keywords
- Maps to LEGO1 atomic patterns (single responsibility)
- Checks powers for scope creep
- Identifies overlap with known roles
- Flags authority blending risks
- Suggests decomposition if not atomic
- References CLAUDE.md role definitions

---

## Integration Checklist

- [ ] Keybindings saved to `~/.claude/keybindings.json`
- [ ] `FOUNDRY_SKILLS_ARCHITECTURE.md` created (this file)
- [ ] Template scripts created for each skill (Bash, Python, or Claude prompts)
- [ ] Anti-burnout alerts enabled (rhythm-check automated)
- [ ] Run folder templates created (`scripts/new-run.sh`)
- [ ] Claims format standardized (YAML structure)
- [ ] Phase transition logging enabled (hard timestamps)
- [ ] Editorial collapse SOP documented (compression targets)
- [ ] Artifact archival system set up (run → archive/)

---

## Quick Start: Run Your First Foundry Project

```bash
# 1. Create new run
/foundry-new "Can Foundry handle micro-governance?" \
  --audience product-leaders \
  --format proposal \
  --duration 90m

# 2. Hyperfocus expansion (90 min)
/hyperfocus 90m --discipline expand --subject "Micro-governance: authority at scale"

# [Submit claims during session]
/claim evidence "Calvi 2030 uses 3-tier observer/decider/analyst model" \
  --source WUL_PERSONAL_REFERENCE_LIBRARY.md \
  --confidence high

# 3. Check rhythm at midpoint
/rhythm-check

# 4. Transition to tension phase
/phase-next exploration --reason "Sufficient facts gathered; outline structure complete"

# 5. Red-team critical claims
/skeptic-challenge R-001 --depth deep --angle assumptions

# 6. View claim market state
/claims-status --status accepted

# 7. Merge drafts and finalize
/editorial-collapse drafts/v1_draft.md --reduce 40%

# 8. Ship the artifact
/ship drafts/v2_editorial.md \
  --impact "Micro-governance model validated for product teams" \
  --next "Prototype in CONQUEST world model"
```

---

## Anti-Patterns & Gotchas

### ❌ DO NOT:
- Skip the break at 45m (hyperfocus degrades without rest)
- Revise after Editorial Collapse (if it fails, abort and restart)
- Mix roles (Writer claiming structure authority)
- Ignore rhythm-check warnings (they predict burnout 24-48h in advance)
- Defer termination decision (ship or abort, never "pending")

### ✓ DO:
- Produce claims, not prose, during Expansion
- Mark [ASSUMPTION] tags for unverified ideas
- Let Skeptic attack before Drafting
- Let Editor make unilateral cuts (that's their job)
- Archive every shipped artifact (reference trail)

---

## Module Truth Table (Skills)

| Skill | Status | Purpose | Integration |
|-------|--------|---------|-------------|
| foundry-new | ✅ Defined | Scaffold runs | In CLAUDE.md |
| claim | ✅ Defined | Submit ideas | Claims Market SOP |
| phase-next | ✅ Defined | Transition phases | Phase enforcement |
| skeptic-challenge | ✅ Defined | Red-team claims | Tension phase SOP |
| editorial-collapse | ✅ Defined | Merge & finalize | Phase 4 SOP |
| ship | ✅ Defined | Archive artifact | Termination SOP |
| claims-status | ✅ Defined | Dashboard view | Operations |
| hyperfocus | ✅ Defined | Bounded timer | Session tracking |
| rhythm-check | ✅ Defined | Anti-burnout | Health monitoring |
| lego-check | ✅ Defined | Validate atomicity | Architecture validation |

---

**Status:** Ready for implementation and integration with Claude Code workflow.
**Next:** Bind skills to keybindings and test in live Foundry run.
