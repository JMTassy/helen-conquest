# Foundry Town Skills: Quick Start Guide

**For:** Running Foundry Town projects through Claude Code
**Status:** Ready to use
**Updated:** 2026-02-13

---

## The 10 Skills at a Glance

```
SESSION MANAGEMENT
  /hyperfocus        — Start bounded work session with timer
  /rhythm-check      — Check burnout risk (pattern analysis)

RUN SETUP & PHASES
  /foundry-new       — Create new run folder + structure
  /phase-next        — Transition to next phase, log change
  /claims-status     — View all claims (pending/accepted/rejected)

IDEA SUBMISSION
  /claim             — Submit one claim to claim market
  /skeptic-challenge — Red-team a claim or draft section

CONVERGING & SHIPPING
  /editorial-collapse — Merge drafts, cut 30-50%, finalize
  /ship              — Archive artifact, log outcome

VALIDATION
  /lego-check        — Test if role/team/district is atomic
```

---

## Typical Foundry Workflow

### START: Create a Run

```bash
/foundry-new "Why decision memos matter" \
  --audience executives \
  --format memo \
  --duration 45m
```

**What happens:**
- Creates `runs/why-decision-memos-matter/` with all structure
- MANIFEST.md shows subject + constraints
- Empty claims/ and drafts/ folders ready
- Timer starts (if --duration specified)

---

### PHASE 1: Explore (Divergent)

**Goal:** Generate raw material — facts, structure, assumptions.

```bash
# Start hyperfocus session
/hyperfocus 90m --discipline expand --subject "Decision memo benefits"

# [During session, submit claims as ideas emerge]

/claim evidence "Decision memos reduce meeting overhead by 40%" \
  --source "HBR article on async communication" \
  --confidence high

/claim structure "Outline: Problem → Why Now → Recommendation → Timeline" \
  --author Structurer

/claim critique "[Test this] Assumes executives read memos (true?)" \
  --author Skeptic \
  --confidence medium

# [At 45m break: /rhythm-check]

# [Continue until timer expires]

# Log phase transition
/phase-next exploration --reason "Facts gathered, outline sketched, assumptions surface"
```

**Output:**
- claims/pending.md filled with R-###, T-###, C-### ideas
- v0_fragments.md shows raw notes
- Phase log updated

---

### PHASE 2: Tension (Mandatory Challenge)

**Goal:** Red-team all accepted claims. Surface contradictions.

```bash
# View current accepted claims
/claims-status --status accepted

# Challenge the highest-confidence claims
/skeptic-challenge R-001 --depth deep --angle assumptions

/skeptic-challenge R-002 --depth deep --angle evidence-gaps

# Researcher clarifies (adds to claims)
/claim evidence "Executive memo adoption rate: 73% (McKinsey 2024)" \
  --source McKinsey research \
  --confidence high

# Foreman marks contested items as resolved
/claims-status --status pending

# Transition when contradictions resolved
/phase-next tension --reason "All accepted claims challenged; contradictions documented"
```

**Output:**
- Critique claims (C-###) added to pending
- Contested items resolved or merged
- Ready for convergence

---

### PHASE 3: Draft (Convergent)

**Goal:** Convert accepted claims to coherent prose.

```bash
# View all accepted claims
/claims-status --status accepted --verbose

# [Writer drafts prose from claims]

# Check draft structure
/claims-status --author Structurer --status accepted

# [Continue drafting until all accepted claims are prose]

# Transition when draft complete
/phase-next drafting --reason "All accepted claims drafted; v1_draft.md complete"
```

**Output:**
- v1_draft.md has prose (with gaps marked as `[DRAFT: expand this]`)
- Ready for editorial review

---

### PHASE 4: Editorial Collapse

**Goal:** Merge contradictions, cut ruthlessly, finalize.

```bash
# Merge all drafts, reduce by 40%
/editorial-collapse drafts/v1_draft.md --reduce 40% --tone formal

# [Editor makes unilateral cuts]

# Result: v2_editorial.md (final artifact)
```

**Output:**
- v2_editorial.md (final, coherent, 40% shorter)
- EDITORIAL_LOG.md (what was cut, why)

---

### PHASE 5: Terminate

**Goal:** Deliver artifact or abort. Explicit outcome only.

```bash
# DELIVER (most common)
/ship drafts/v2_editorial.md \
  --impact "Decision memo framework adopted by exec team" \
  --next "Implement memo template + training"

# OR ABORT (if coherence fails)
/ship drafts/v2_editorial.md \
  --outcome abort \
  --next "Restart with clearer subject: execution-risk memo vs. decision memo?"
```

**Output:**
- Artifact archived to archive/ folder
- MANIFEST.md shows DELIVERED or ABORT
- Completion timestamp logged
- Run terminal (no reversions)

---

## Common Session Patterns

### Pattern 1: Quick Memo (90 min)

```bash
# 1. Create run
/foundry-new "Q2 planning constraints" --format memo --duration 90m

# 2. Hyperfocus (45m expand + 45m select)
/hyperfocus 45m --discipline expand
# [submit claims]
/hyperfocus 45m --discipline select
# [mark best claims accepted]

# 3. Skip to editorial (for short, simple outputs)
/phase-next exploration --reason "Quick scope"
/phase-next tension --reason "Self-evident; no red team needed"
/phase-next drafting --reason "Direct prose from accepted"
/editorial-collapse drafts/v1_draft.md --reduce 30%

# 4. Ship
/ship drafts/v2_editorial.md --impact "Q2 plan clarity"
```

**Total time:** ~2 hours

---

### Pattern 2: Deep Exploration (3–4 days)

```bash
# Day 1: EXPAND (2 sessions, 90m each)
/foundry-new "Can Foundry scale to 100+ agents?" --duration full-week

/hyperfocus 90m --discipline expand
# [claims: R-001 through R-015]

/hyperfocus 90m --discipline expand
# [claims: R-016 through R-030]

# Day 2: TENSION (1 session, 2h)
/phase-next exploration --reason "Evidence gathered"

/hyperfocus 120m --discipline select
# [Skeptic challenges: C-001 through C-008]
# [Researcher clarifies gaps]

# Day 3: DRAFTING (2 sessions, 90m each)
/phase-next tension --reason "Contested items resolved"

/hyperfocus 90m --discipline ship
# [Writer drafts v1]

/hyperfocus 90m --discipline ship
# [Structurer refines flow; Synthesizer merges overlaps]

# Day 4: EDITORIAL (1 session, 1h)
/phase-next drafting --reason "Draft complete"

/editorial-collapse drafts/v1_draft.md --reduce 40%

/ship drafts/v2_editorial.md --impact "Scalability constraints identified"
```

**Total time:** ~9 hours over 4 days (sustainable, no burnout)

---

### Pattern 3: Burnout Recovery

```bash
# If /rhythm-check shows CRITICAL:

# 1. STOP immediately
/rhythm-check --verbose
# → "Total hyperfocus >6 hours. Stop work now."

# 2. Take 2-hour break (offline)

# 3. Next day, ONE short session only
/hyperfocus 45m --discipline select
# [Curate what you have; don't expand]

# 4. Ship whatever is ready (don't wait for perfection)
/editorial-collapse drafts/v1_draft.md --reduce 50%
/ship drafts/v2_editorial.md --outcome deliver

# 5. Archive and rest
# [No new Foundry runs for 3 days]
```

---

## Troubleshooting

### Problem: Too many pending claims (>20)

**Cause:** Expansion phase is sprawling; Foreman not curating.

**Fix:**
```bash
# Review pending claims
/claims-status --status pending

# Foreman decision: accept the top 10 by confidence
# Mark rest as "deferred" (create new file: claims/deferred.md)

# Then proceed to next phase
/phase-next exploration --reason "Core claims selected; rest deferred"
```

---

### Problem: Contradiction won't resolve

**Cause:** Two incompatible claims; editorial decision needed.

**Fix:**
```bash
# Log the contradiction explicitly
/claim meta "Claims R-005 and R-009 contradict on governance model; \
  awaiting editorial decision (Model A vs Model B)" \
  --confidence medium

# Move to EDITORIAL COLLAPSE early
/phase-next tension --reason "Contradiction documented; ready for editor decision"
/editorial-collapse drafts/v1_draft.md --reduce 40%
# [Editor chooses Model A or B unilaterally]
```

---

### Problem: Burnout warning

**Cause:** You've hyperfocused >6 hours without break.

**Fix:**
```bash
# STOP immediately; don't push
/rhythm-check

# Follow recovery pattern (above)

# Schedule next session for tomorrow
# (You're not lazy; your brain needs recovery cycles)
```

---

### Problem: Run is ready to ship, but I don't feel confident

**Cause:** Imposter syndrome; perfectionism loop.

**Fix:**
```bash
# Remember: Editorial already happened
# Editor decided the artifact is coherent and useful

# Trust the system (not your self-doubt)
/ship drafts/v2_editorial.md --impact "[your one-liner]"

# Artifact is now complete
# Next phase: gather feedback, iterate in NEW run if needed
```

---

## Cheatsheet: Command Reference

```bash
# Start a run
/foundry-new "Topic" --audience X --format Y --duration Zm

# Submit idea (during expansion)
/claim TYPE "Statement" --source REF --confidence LEVEL

# Challenge a claim (during tension)
/skeptic-challenge CLAIM_ID --depth deep

# View all claims
/claims-status --status pending
/claims-status --author Researcher

# Transition phases
/phase-next exploration|tension|drafting|editorial --reason "..."

# Merge & finalize
/editorial-collapse drafts/v1_draft.md --reduce 40%

# Deliver
/ship drafts/v2_editorial.md --impact "..." --next "..."

# Check health
/rhythm-check
/rhythm-check --verbose

# Validate atomicity
/lego-check role "Description"
/lego-check superteam "Description"

# Session timing
/hyperfocus 90m --discipline expand|select|ship
```

---

## Anti-Patterns: What NOT to Do

### ❌ Loop revision forever
❌ Phase 1 → Phase 2 → Phase 1 → Phase 2 (endless)
✓ Each phase ends; move forward only

### ❌ Skip Tension phase
❌ "I'm confident; no red team needed"
✓ Tension is mandatory; Skeptic always attacks

### ❌ Accept all claims
❌ Foreman says "yes" to 50 ideas
✓ Foreman curates ruthlessly; expect 50% rejection

### ❌ Revise after Editorial Collapse
❌ "I don't like the cuts; let me fix it"
✓ Editorial decision is final; if it fails, abort and restart fresh

### ❌ Ignore rhythm-check warnings
❌ "I'm fine; one more session"
✓ Rhythm-check predicts burnout; listen to the data

### ❌ Mix roles (e.g., Writer + Skeptic)
❌ "I'll write prose AND challenge claims"
✓ Roles are atomic; one agent = one responsibility

---

## Success Metrics

### Run Complete = Artifact Shipped

A Foundry run is **successful** when:
1. ✅ Subject is clear (no sprawl)
2. ✅ Phases are sequential (no reversions)
3. ✅ Editorial Collapse happened (30-50% cut achieved)
4. ✅ Outcome is explicit (deliver or abort)
5. ✅ Artifact is archived with link

### Session Sustainable = No Burnout

A work session is **sustainable** when:
1. ✅ Hyperfocus <4 hours/day
2. ✅ Breaks observed (every 45m)
3. ✅ Variety in disciplines (expand → select → ship)
4. ✅ /rhythm-check shows GREEN
5. ✅ You want to come back tomorrow

---

## Next: Your First Run

Pick a topic. Run this:

```bash
/foundry-new "Your topic here" --duration 90m
/hyperfocus 90m --discipline expand
# [work for 90 minutes]
/phase-next exploration --reason "Facts gathered"
/editorial-collapse drafts/v1_draft.md --reduce 40%
/ship drafts/v2_editorial.md --impact "One sentence about what this unlocks"
```

**Time to ship:** ~2 hours

---

**Created:** 2026-02-13
**Status:** Ready for use
**Questions?** See FOUNDRY_SKILLS_ARCHITECTURE.md for full definitions
