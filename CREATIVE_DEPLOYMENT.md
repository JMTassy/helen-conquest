# CREATIVE SUPERTEAM — DEPLOYMENT GUIDE

**Status:** ✅ READY TO USE
**Activation Date:** 2026-02-20
**Roles:** Lateral Pattern (LP-###), Rhythm Tracker (RT-###)
**K-gates Active:** K2 only (no self-validation)
**K5 Status:** EXEMPT (non-deterministic by design)

---

## Quick Start

### When to Use CREATIVE

- **Exploring lateral connections** across domains (Oracle Town → Foundry → CONQUEST → CALVI)
- **Stuck in linear thinking** and need to break out
- **Domain-jumping** and finding unexpected patterns
- **Energy management** — need to track burnout risk and enforce breaks

### Creative Superteam Structure

```
CREATIVE Superteam
  │
  ├─ Lateral Pattern (LP-###)
  │  Purpose: Surface unexpected connections between claims
  │  Input: Existing claims from other superteams (R-###, C-###, T-###, W-###)
  │  Output: LP-### connection claims to pending.md
  │  Authority: None (advisory → Foreman curates)
  │
  └─ Rhythm Tracker (RT-###)
     Purpose: Monitor session intensity, flag burnout risk
     Input: Session observations (duration, loop detection, clarity level)
     Output: RT-### energy observations to pending.md (tagged ADVISORY)
     Authority: None (advisory → Foreman acts on flags)
```

---

## How to Invoke Each Role

### LATERAL PATTERN — Connection Finder

**When:** You have multiple claims from different superteams and want to find hidden relationships.

**Input:** 2+ existing claims (R-###, C-###, T-###, etc.)

**Command (simulated):**
```
Lateral Pattern: Find patterns connecting:
  - R-001: CONQUEST territory mechanics create asymmetric power
  - R-002: Real-money mechanics correlate with learning loss
  - LP-001: Prison = opportunity cost without friction
→ What unexpected relationship do these share?
```

**Output format:**
```
LP-### [Connection claim]
Statement: [These claims share pattern X]
Type: connection
Confidence: [low/medium/high]
Status: pending → Foreman curates
```

**Lateral Pattern CANNOT:**
- ❌ Propose solutions ("you should do X")
- ❌ Decide truth ("this connection is right")
- ❌ Approve other claims
- ❌ Override Foreman's curation

**Lateral Pattern CAN:**
- ✅ Surface connections NOT in source material (K5 exempt)
- ✅ Reframe existing claims with new context
- ✅ Find analogies across domains
- ✅ Propose "what if" scenarios as pattern claims

---

### RHYTHM TRACKER — Burnout Monitor

**When:** You're in a work session and want to track energy/intensity.

**Input:** Session observations (how long working, loop patterns, clarity level)

**Command (simulated):**
```
Rhythm Tracker: Monitor this session
  - Duration: 3.5 hours continuous
  - Pattern: Working, broke for 15 min, restarted, looping on same section
  - Clarity: "I should fix this" (not "I want to")
→ What's the burnout status?
```

**Output format:**
```
RT-### [Energy observation] — TAGGED ADVISORY
Statement: [Session has reached X intensity, recommend Y]
Type: energy_observation
Confidence: [low/medium/high]
Status: pending → Foreman receives → Foreman acts
```

**Rhythm Tracker CANNOT:**
- ❌ Force breaks
- ❌ Pause phases
- ❌ Override Foreman's decisions
- ❌ Validate its own observations

**Rhythm Tracker CAN:**
- ✅ Flag burnout signals (loop, low clarity, >4h continuous)
- ✅ Recommend break timing
- ✅ Log energy before/after sessions
- ✅ Propose rhythm adjustments (next week spacing)

---

## Integration with Other Superteams

### CREATIVE → PRODUCTION Pipeline

```
CREATIVE outputs (LP-###)
    ↓ (Foreman curates)
PRODUCTION workspace
    ├─ Accept LP-### → routes to Writer as input claim
    ├─ Reject LP-### → logged to rejected.md
    └─ Merge LP-### with other claims → Synthesizer consolidates
```

**Example:**
1. Lateral Pattern files: LP-001 (prison ≠ money pattern)
2. Foreman reads LP-001, asks: "Does this serve current run?"
3. Foreman accepts LP-001 → routes to Writer
4. Writer integrates LP-001 into decision memo
5. Editor cuts or keeps LP-001 based on memo needs

### CREATIVE → DISTRICTS Coordination

**MUSIC District (Energy Management):**
- RT-### burnout flag filed to pending.md
- Foreman receives flag
- Foreman logs: "Phase paused — RT-### burnout signal received"
- Break enforced
- After break: Phase resumes

**Relationship:** Rhythm Tracker advises. Foreman decides. MUSIC District rhythm is enforced by Foreman's constitutional obligation to act on RT-### flags.

---

## Charter Quick Reference

### LATERAL PATTERN

| Aspect | Details |
|---|---|
| **Claim Prefix** | LP-### |
| **Type** | connection |
| **K5 Status** | EXEMPT (non-deterministic) |
| **Powers** | Propose connections, surface reframings, find analogies |
| **Limits** | No solutions, no truth claims, no approvals |
| **Author Rule** | Lateral Pattern authors → Foreman approves (Rule 3) |
| **Pass Test** | LP-### lists 2+ claim IDs, states pattern only, no action proposed |
| **Fail Test** | LP-### proposes solution, contains prose, or skips Foreman curation |

### RHYTHM TRACKER

| Aspect | Details |
|---|---|
| **Claim Prefix** | RT-### |
| **Type** | energy_observation |
| **Tag** | ADVISORY (always) |
| **K-gates Active** | K2 (no self-validation) only |
| **Powers** | Flag burnout, propose breaks, log energy |
| **Limits** | READ-ONLY, cannot force anything, cannot override Foreman |
| **Author Rule** | Rhythm Tracker authors → Foreman acts (Rule 4) |
| **Pass Test** | RT-### tagged ADVISORY, never initiates phase transitions |
| **Fail Test** | RT-### forces action, says "must stop now", or appears as phase initiator |

---

## Running a Session with CREATIVE

### Setup Phase (5 min)

1. **Declare scope:** "I'm exploring [domain]. Lateral thinking enabled."
2. **Set duration:** "45 min hyperfocus, then select phase."
3. **Prepare inputs:** Gather existing claims from other runs to feed Lateral Pattern.
4. **Check energy:** Rhythm Tracker logs baseline (energy level, clarity, mood).

### Exploration Phase (40 min, hyperfocus)

1. **Lateral Pattern works:** Surface connections between claims. File LP-### as you find them.
2. **Rhythm Tracker monitors:** Observe session intensity. Flag if hitting 4h or showing loop behavior.
3. **No filtering:** Let Lateral Pattern work without curation. Chaos is OK here.
4. **No breaks forced:** Rhythm Tracker advises only. You decide to break.

### Selection Phase (15 min, fresh eyes)

1. **Step away:** 15 min break away from keyboard.
2. **Return:** Read all LP-### claims filed during exploration.
3. **Apply Skeptic:** Attack each connection. Is it real or beautiful distraction?
4. **Mark:** Accept/reject/defer each LP-###.
5. **Log:** Rhythm Tracker notes post-session energy.

### Integration Phase (variable)

1. **Route accepted LP-### to next superteam** (Production, Knowledge, or another Creative run).
2. **Foreman curates:** Decide which connections serve the current work.
3. **Use them:** Writer or Structurer integrates accepted LP-### into drafting.

---

## Constraints & Safeguards

### Rule 1: Single Finalization Point
**How it applies:** Lateral Pattern and Rhythm Tracker never finalize anything. All output flows through Foreman → then to other superteams/Editor.

### Rule 2: Record Before Transition
**How it applies:** Every LP-### and RT-### must be logged to pending.md before Foreman acts. Phase cannot advance until RT-### flag is addressed (break taken or explicitly overridden by Foreman with logged reason).

### Rule 3: No Self-Edit
**How it applies:** Lateral Pattern cannot approve its own connections. Rhythm Tracker cannot certify its own energy observations. Both require external curation (Foreman).

### Rule 4: Coordinator Authority is Process-Only
**How it applies:** Rhythm Tracker is advisory. Foreman is obligated to act on RT-### flags, but Foreman decides HOW (break now vs. break later, pause phase vs. continue). This is process authority, not content.

### Rule 5: Fail-Closed + Mandatory Termination
**How it applies:** If Lateral Pattern finds no pattern, it must declare "no pattern found" (not silence). If Rhythm Tracker detects no burnout, it still logs baseline energy (not silence). Every observation is recorded.

---

## Troubleshooting

### "Lateral Pattern keeps proposing solutions instead of patterns"

**Fix:** Remind Lateral Pattern of its 2-sentence atomic test: "Lateral Pattern identifies unexpected relationships between claims. It does not explain why they matter, propose what to do, or validate whether they are true."

If LP-### contains words like "should," "need to," "fix," or "implement" → reject and refile.

### "Rhythm Tracker is forcing breaks instead of advising"

**Fix:** Rhythm Tracker's power is advisory only. Check the RT-### claim — it should be tagged ADVISORY and phrased as "break recommended" not "break now." If it's forcing action, that's a Rule 4 violation. Foreman decides action.

### "I'm not sure if a connection is real or noise"

**That's the Skeptic's job.** Phase 2 (Tension) exists to challenge LP-### claims. Lateral Pattern's job is to surface connections, not validate them. Let Skeptic attack. If connection survives Skeptic, it's probably real.

### "Rhythm Tracker keeps flagging when I'm actually in deep focus"

**Distinguish hyperfocus from burnout:**
- Hyperfocus: "I'm in flow, high clarity, excited to keep going, energy is good"
- Burnout: "I should keep going, low clarity, looping on same issue, clarity is fading, energy is bad"

Rhythm Tracker should flag the second, not the first. If it's flagging hyperfocus, adjust the burnout signal detection criteria.

---

## Deployment Checklist

Before running Creative superteam in production:

- [ ] Read Section 5 of KERNEL_V2.md (full charters for Lateral Pattern + Rhythm Tracker)
- [ ] Understand Rule 3 (No Self-Edit) — these roles cannot validate their own output
- [ ] Understand Rule 4 (Foreman is Process-Only) — Rhythm Tracker is advisory, Foreman acts
- [ ] Test one LP-### claim on a real subject (does it pass the pass/fail test?)
- [ ] Test one RT-### observation (is it tagged ADVISORY?)
- [ ] Run through the "Running a Session" workflow above
- [ ] Have Skeptic ready to challenge LP-### claims in Phase 2
- [ ] Confirm Foreman understands obligation to act on RT-### flags

---

## Integration with MEMORY.md

Add to MEMORY.md when you've deployed Creative:

```
## Creative Superteam — ACTIVATED [2026-02-20]

- Lateral Pattern: Surfaces unexpected connections (K5 exempt)
- Rhythm Tracker: Monitors session intensity, flags burnout (advisory only)
- Both roles now have formal charters (KERNEL_V2.md Section 5)
- Integration: Foreman curates LP-### claims; Foreman acts on RT-### flags
- Ready to use in FOUNDRY, CONQUEST, CREATIVE district, or standalone hyperfocus runs
```

---

## Files Reference

| File | Section | Use This For |
|---|---|---|
| KERNEL_V2.md | Section 5 | Full Lateral Pattern + Rhythm Tracker charters |
| KERNEL_V2.md | Section 4 | Creative superteam unique power (K5 exemption) |
| KERNEL_V2.md | Section 7 | Authority flow diagram (Creative's role) |
| KERNEL_V2_TEST_MONETIZATION.md | LP-001, LP-002 | Examples of real LP-### claims in production |
| DOMAINS_MANIFEST.md | CREATIVE District | How Creative fits in the broader system |

---

**Status: CREATIVE SUPERTEAM OPERATIONAL**

Deploy now. Use immediately. Lateral Pattern + Rhythm Tracker are ready to work.

---

*Last Updated: 2026-02-20*
*Next: Run first CREATIVE-only hyperfocus session to validate in practice*
