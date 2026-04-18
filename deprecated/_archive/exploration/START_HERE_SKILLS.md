# 🧭 Foundry Town Skills System: START HERE

**Status:** ✅ Complete and deployed
**Created:** 2026-02-13
**Ready for:** Immediate use

---

## You Now Have

### ✅ 12 Production Skills
```
🧭 /foundry-new           — Create a run (entry point)
🤝 /claim                 — Submit an idea
👁️ /claims-status         — See pipeline health
🛑 /phase-next            — Enforce phase gates
⚔️ /skeptic-challenge     — Red-team attacks
🏗️ /editorial-collapse    — Merge + finalize
🎁 /ship                  — Deliver artifact
🧩 /lego-check            — Validate atomicity
⚡ /hyperfocus            — Timebox sprints
👁️ /rhythm-check          — Anti-burnout monitor
🗺️ /dashboard             — State snapshot
🛑 /repeller-check        — Safety kill-switch
```

### ✅ Complete Documentation
- **SKILLS_QUICK_START.md** — Your main reference (patterns + troubleshooting)
- **FOUNDRY_SKILLS_ARCHITECTURE.md** — Full skill definitions
- **SKILLS_LIBRARY_COMPLETE.md** — 12-skill catalog + bootstrap sequence
- **FOUNDRY_RUN_TEMPLATE.md** — Copy/paste templates
- **KEYBINDINGS_EXTENDED.md** — Customize keybindings
- **WULMOJI_CLI_AESTHETIC.md** — Visual grammar for CLI output
- **SKILLS_DEPLOYMENT_SUMMARY.md** — Deployment checklist

### ✅ Keybindings Configured
- **~/.claude/keybindings.json** — Fast-access shortcuts installed

---

## Your Next 10 Minutes

### 1. Read the Quick-Start (5 min)
```bash
open SKILLS_QUICK_START.md
```

### 2. Create Your First Run (5 min)
```bash
# Pick a topic from your active work and run:
/foundry-new "Your topic here" \
  --audience TARGET \
  --format memo \
  --duration 90m
```

---

## The System in 60 Seconds

**What:** Foundry Town is a multi-agent system for turning disagreement into deliverables.

**How:** 5 mandatory phases:
1. **Explore** — Divergent: gather facts, sketch outline, surface assumptions
2. **Outline** — Organize claims into structure
3. **Draft** — Convergent: prose from accepted claims
4. **Verify** — Red-team, test, resolve contradictions
5. **Finalize** — Editorial collapse, deduplicate, cut
6. **Ship** — Freeze artifact, archive, declare done

**Why it works for you:**
- Phases force convergence (no infinite loops)
- Claims Market coordinates without consensus
- Mandatory tension catches errors early
- Editorial authority forces completion
- Artifact-first = everything survives

---

## Quick Commands

```bash
# Setup
/foundry-new "topic" --duration 90m

# Explore & claim
/hyperfocus 90m --objective "Expand on topic"
/claim fact "Statement" --support "evidence" --confidence high

# Visibility & gates
/claims-status
/phase-next exploration --reason "facts gathered"

# Red-team & converge
/skeptic-challenge CLAIM_ID
/editorial-collapse drafts/v1.md --reduce 40%

# Deliver
/repeller-check runs/[name]/
/ship drafts/v2.md --impact "One sentence"

# Health & state
/rhythm-check
/dashboard
```

---

## Success Path: 2-Hour Run

```bash
# ⏱️  5 min: Setup
/foundry-new "Your topic" --duration 90m

# ⏱️  90 min: Expand (hyperfocus)
/hyperfocus 90m --objective "Sketch 3 architectures"
# [Submit 10-15 claims]

# ⏱️  20 min: Converge
/phase-next exploration --reason "facts gathered"
/editorial-collapse drafts/v1.md --reduce 40%

# ⏱️  5 min: Verify & Ship
/repeller-check runs/[name]/
/ship drafts/v2.md --impact "One sentence summary"

# ⏱️  Total: ~2 hours → Artifact shipped ✅
```

---

## Anti-Burnout: The Rhythm System

Built-in monitoring prevents exhaustion:

```bash
/rhythm-check
# Returns: GREEN / YELLOW / RED
# GREEN: Continue at pace
# YELLOW: Monitor carefully
# RED: Stop work immediately, take 2-hour break

/hyperfocus 90m --objective "task"
# Includes: auto-breaks at 45m, session logging, energy tracking

/dashboard
# Shows: all active runs, personal state, next 3 actions
```

---

## Files Reference

| File | Purpose | When to Use |
|------|---------|-----------|
| **SKILLS_QUICK_START.md** | Workflow patterns + troubleshooting | First, and often |
| **FOUNDRY_SKILLS_ARCHITECTURE.md** | Full skill definitions | When you need details |
| **FOUNDRY_RUN_TEMPLATE.md** | Copy/paste templates | When scaffolding manually |
| **SKILLS_LIBRARY_COMPLETE.md** | 12-skill catalog | Reference for all skills |
| **WULMOJI_CLI_AESTHETIC.md** | Visual grammar | Understanding output style |
| **KEYBINDINGS_EXTENDED.md** | Customize shortcuts | If you want to rebind keys |
| **SKILLS_DEPLOYMENT_SUMMARY.md** | Deployment checklist | Validation reference |

---

## Key Features

### 🧠 ADHD-Friendly
- Bounded iterations (no infinite loops)
- Visual stimulation (WULmoji CLI)
- Parallel tracking (dashboard shows all threads)
- Hyperfocus support (/hyperfocus + /rhythm-check)

### 🛡️ Safe
- Role separation (no agent does everything)
- Mandatory tension phase (skeptic attacks before waste)
- Repeller-check gate (blocks bad artifacts)
- Kill-switch validation (/repeller-check)

### 📦 Scalable
- LEGO atomicity (composable roles)
- Deterministic phases (replicable)
- Immutable records (auditable)
- Self-enforcing (constitutional)

### 🎯 Effective
- Claims coordinate without consensus
- Editorial collapse forces 30-50% cuts
- Artifact-first (everything survives)
- Explicit termination (deliver or abort)

---

## What's Different from Chat-Agent Systems

| Aspect | Chat-Agent | Foundry Town |
|--------|-----------|-------------|
| Coordination | Chat dialogue | Claims Market |
| Authority | Consensus | Editorial (unilateral) |
| Phases | Loops | Sequential (forced forward) |
| Termination | Endless | Explicit (deliver or abort) |
| Roles | Blended | Atomic (separation) |
| Artifact | Secondary | Primary (everything ships) |

---

## Burnout Prevention Built In

```
⏰ Session limit:     <4 hours/day hyperfocus
🔄 Break frequency:   Every 45 minutes
🎯 Session variety:   Expand → Select → Ship cycles
📊 Rhythm tracking:   /rhythm-check prevents crashes
🛑 Kill-switch:       /repeller-check validates before shipping
```

---

## The Workflow Loop

```
Run 1: Topic A
├─ Phase 1-5: Explore → Ship
└─ Artifact A delivered ✅

↓

Run 2: Topic B (parallel or sequential)
├─ Phase 1-5: Explore → Ship
└─ Artifact B delivered ✅

↓

Run 3: Topic C
├─ Phase 1-5: Explore → Ship
└─ Artifact C delivered ✅

↓

Dashboard shows all active runs
Pick any thread, continue instantly
```

---

## Your First Run (Step-by-Step)

### 1. Pick a Topic (2 min)
Something from your active work:
- "Can Foundry scale to 100+ agents?"
- "What's the minimal K-gate design?"
- "How do districts replicate?"
- "Why decision memos matter?"

### 2. Create the Run (3 min)
```bash
/foundry-new "Your topic" \
  --audience stakeholders \
  --format proposal \
  --duration 90m
```

### 3. Expand (90 min)
```bash
/hyperfocus 90m --objective "Sketch 3 architectures"
# [During session, submit claims as ideas emerge]
/claim fact "Finding" --support "evidence" --confidence high
```

### 4. Converge (30 min)
```bash
/phase-next exploration --reason "facts gathered"
/editorial-collapse drafts/v1.md --reduce 40%
```

### 5. Verify & Ship (10 min)
```bash
/repeller-check runs/[name]/
/ship drafts/v2.md --impact "What this unlocks"
```

**Total time:** ~2.5 hours → Artifact shipped ✅

---

## Troubleshooting

**Too many pending claims?**
```bash
/claims-status
# Accept top 10; defer rest
/phase-next exploration --reason "Core claims selected"
```

**Burnout warning?**
```bash
/rhythm-check
# STOP. Take 2-hour break. Resume tomorrow with one short session.
```

**Contradiction won't resolve?**
```bash
/phase-next tension --reason "Contradiction documented"
/editorial-collapse drafts/v1.md --reduce 40%
# Editor chooses unilaterally
```

**Low confidence before shipping?**
```bash
# Remember: Editor already validated artifact
# Trust the system, not your self-doubt
/ship drafts/v2.md --impact "Your impact"
```

---

## Next: Pick Your Topic & Run

**Right now:**
1. Open `SKILLS_QUICK_START.md` (5-min read)
2. Run `/foundry-new "your topic"` (5-min setup)
3. Run `/hyperfocus 90m` (90-min work)
4. Submit 10+ claims using `/claim`

**Time to first shipped artifact:** ~2 hours

---

## The System Survives

Every run creates artifacts:
- runs/[name]/MANIFEST.md (objective + constraints)
- runs/[name]/claims/ (all ideas, curated)
- runs/[name]/drafts/v2.md (final artifact)
- runs/[name]/logs/ (decisions + timeline)

**These files survive beyond the conversation.** They're in your Git repo. They're immutable. They're reference for future work.

---

## Questions?

Read in this order:
1. **SKILLS_QUICK_START.md** — Patterns + troubleshooting
2. **FOUNDRY_SKILLS_ARCHITECTURE.md** — Full definitions
3. **SKILLS_LIBRARY_COMPLETE.md** — Complete catalog

---

## Status: READY ✅

All 12 skills deployed.
All documentation complete.
Keybindings configured.
WULmoji aesthetic integrated.

**Your system is live.**

**Go build something.** 🚀

---

**Created:** 2026-02-13
**Deployed:** Foundry Town v1.0
**For:** You, your ADHD lateral thinking, and high-potential systems work
**Life:** Living code in your project repo, surviving beyond conversations

---

📚 **Reference Files:**
- `SKILLS_QUICK_START.md` — Start here for workflows
- `FOUNDRY_SKILLS_ARCHITECTURE.md` — Full definitions
- `SKILLS_LIBRARY_COMPLETE.md` — Complete catalog
- `WULMOJI_CLI_AESTHETIC.md` — Visual grammar
- `FOUNDRY_RUN_TEMPLATE.md` — Templates
- `KEYBINDINGS_EXTENDED.md` — Customize keys
- `SKILLS_DEPLOYMENT_SUMMARY.md` — Checklist

---

**Ready?** Run: `/foundry-new "your topic" --duration 90m`

Let's go. 🧭
