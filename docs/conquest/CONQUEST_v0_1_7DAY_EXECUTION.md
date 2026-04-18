# CONQUEST v0.1 — 7-Day Execution Sprint
**From Artifact to Real Human Test**

**Sprint Start**: Today
**Sprint End**: Day 7
**Objective**: 3 real humans test the 24-hour loop and answer: "Did it feel alive?"

---

## DAY 1 (TODAY): SETUP & VALIDATE

### Morning
- [ ] Install dependencies: `pip install fastapi uvicorn`
- [ ] Verify files exist:
  - `conquest_v0_1_app.py`
  - `conquest_v0_1_index.html`
  - `CONQUEST_v0_1_LAUNCH.md`
- [ ] Start server: `uvicorn conquest_v0_1_app:app --reload`

### Afternoon
- [ ] Test locally:
  - Create user (test name)
  - Issue order (test action)
  - Seal it
  - Get user ID
  - Verify database (`conquest.db` created)
- [ ] Confirm everything works
- [ ] Reset database: `rm conquest.db`
- [ ] Restart server

### Evening
- [ ] Identify 3 humans to test:
  - Should be: people you trust, willing to wait 24h, not designers/developers
  - Should NOT be: colleagues who will overthink it, people looking for features
  - Ideal: Someone who hasn't seen any CONQUEST materials
- [ ] **Do not send them the loop yet.** Just confirm they're available.

**Day 1 Status**: Local validation complete, 3 testers identified

---

## DAY 2: SEND TO FIRST TESTER

### Morning
- [ ] Send first tester the link (local URL or deployed URL)
- [ ] Instruction they receive (copy/paste):

```
You're testing an experiment.

No explanation needed.

1. Enter your name
2. Describe one change you want to see in this place
3. Seal it
4. Leave

Note the ID you receive.

Come back in 24 hours.

Don't think about it until then.
```

- [ ] Set phone alarm for 24h from now: **FIRST RETURN CHECK**
- [ ] Record:
  - Tester 1 name
  - Order they issued
  - Timestamp
  - User ID

### Afternoon
- [ ] Send second tester the link (same instructions)
- [ ] Record same data
- [ ] Set alarm for 24h

### Evening
- [ ] Send third tester the link (same instructions)
- [ ] Record same data
- [ ] Set alarm for 24h

**Day 2 Status**: All 3 testers have sealed their orders

---

## DAY 3: WAITING

Nothing happens today.

But:
- [ ] Monitor server (is it still running?)
- [ ] Verify database persists
- [ ] Do NOT contact testers

**Day 3 Status**: System stable, testers in absence period

---

## DAY 4: WAITING

Still waiting.

- [ ] Server still running?
- [ ] Do NOT contact testers

**Day 4 Status**: System stable, testers still absent

---

## DAY 5: WAITING

Still waiting.

**Day 5 Status**: System stable

---

## DAY 6: WAITING

Still waiting.

In evening, prepare for returns:

- [ ] Ensure server is running
- [ ] Have phone/laptop ready for capture
- [ ] Prepare recording method (voice memo, notes, screenshot)
- [ ] Plan questions to ask on return:

**Script for when they return:**

You: "Welcome back."

Them: [They check return message]

You: "Did it feel alive?"

**That is the only question.** No other words.

Let them answer without prompt.

Listen for:

**Alive signals:**
- "I forgot about it"
- "When I came back..."
- "It moved without me"
- "That's different"

**Hollow signals:**
- "It's just a message"
- "Nothing actually happened"
- "It feels empty"

**Decorative signals:**
- "It's nice but..."
- "Cool aesthetic"
- "Clever but..."

**Day 6 Status**: Ready for returns tomorrow

---

## DAY 7: FIRST RETURNS + ASSESSMENT

### Morning (Tester 1)

- [ ] Tester 1 connects and checks `/return/{user_id}`
- [ ] They see: "While you were away, the world continued."
- [ ] They see their sealed order in ledger

**Immediate observation:**
- Did they seem surprised?
- Did they reread it?
- Pause? Reaction?

**Your question:**
"Did it feel alive?"

**Record their response EXACTLY:**
- What they said
- How they said it (tone)
- What they did next (left? explored? checked again?)

### Afternoon (Tester 2)

- [ ] Same process
- [ ] Record response

### Evening (Tester 3)

- [ ] Same process
- [ ] Record response

**Day 7 Status**: All 3 testers have returned, responses recorded

---

## ASSESSMENT PROTOCOL (Day 7 Evening)

### Data Collected

For each tester, you have:
1. Their order (what they wanted to change)
2. Their response to return (what they felt)
3. Their answer: "Did it feel alive?"

### Assessment Framework

**For each tester, score:**

| Question | Score |
|----------|-------|
| Did they return? (yes/no) | - |
| Did they seem surprised by change? | Yes / Neutral / No |
| Did they reread the return message? | Yes / No |
| Their exact words on "Did it feel alive?" | [Record] |
| Overall tone (engaged/neutral/disappointed) | Engaged / Neutral / Disappointed |

### Pass/Fail Decision

**PASS (Alive)**:
- 2+ testers said "yes" or equivalent
- All returned without reminder
- Surprise or engagement evident

**CONDITIONAL (Ambiguous)**:
- 1 said yes, 2 neutral
- OR all said something like "interesting but..."

**FAIL (Hollow)**:
- 0 or 1 said yes
- OR testers forgot/didn't return
- OR "Nothing actually happened" repeated

---

## IF PASS

### Next Steps (Days 8-14)

1. **Document the moment** — Write out exactly what each person said when they returned
2. **Analyze signals** — What made it feel alive? Was it the seal? The absence? The change?
3. **Identify the key variable** — One thing that made the difference
4. **Plan expansion** — What do you test next?

**Likely next phase**:
- Run same loop with 5 more humans (validation)
- If consistent alive signal, move to Phase δ (integration with AGI Kernel)

---

## IF CONDITIONAL

### Next Steps (Days 8-14)

1. **Identify the friction point** — What felt hollow?
   - Was the 24-hour delay too long?
   - Was the return message not clear?
   - Did they not feel the change?
   - Was the seal not permanent enough?

2. **Change ONE element**:
   - Shorter delay? (12h instead of 24h)
   - Better return message? (more narrative?)
   - More visible change? (add a banner?)
   - Different seal ritual?

3. **Re-test with 2 new humans** using modified loop

4. **Re-assess** — Did the change help?

---

## IF FAIL

### Next Steps (Days 8-14)

1. **Do not expand** — Loop is not alive yet
2. **Interview testers** — Why didn't it feel alive?
3. **Hypothesis** — What's missing?
4. **Iterate** — Change core experience
5. **Re-test** with different humans

**Do not move to Phase δ until you have PASS.**

---

## DAILY CHECKLIST

### Day 1 ✓
- [ ] Setup complete
- [ ] Local test passed
- [ ] Testers identified

### Day 2 ✓
- [ ] All 3 sent to live
- [ ] Orders recorded
- [ ] Alarms set

### Days 3-6 ✓
- [ ] Server stable
- [ ] Do nothing

### Day 7 ✓
- [ ] All 3 returned
- [ ] Responses recorded
- [ ] Assessment complete

### Day 7 Evening ✓
- [ ] PASS / CONDITIONAL / FAIL decision made
- [ ] Next phase locked

---

## CRITICAL RULES

1. **One question only**: "Did it feel alive?"
2. **No explanation**: Don't explain the system
3. **No influencing**: Don't hint at what should feel alive
4. **Record exactly**: What they say, not what you want them to say
5. **No expansion until PASS**: Stay disciplined

---

## SUCCESS SNAPSHOT

By end of Day 7, you will have one of three outcomes:

**PASS**: "I forgot about it. When I came back 24 hours later, something had changed. That felt real."

**CONDITIONAL**: "It's interesting, but I'm not sure if I feel invested."

**FAIL**: "It's just a message. Nothing actually happened."

Based on that, you know exactly what to do next.

---

## REFERENCE

**Files you have:**
- `conquest_v0_1_app.py` — Backend
- `conquest_v0_1_index.html` — Frontend
- `CONQUEST_v0_1_LAUNCH.md` — Setup guide
- `CONQUEST_v0_1_7DAY_EXECUTION.md` — This document

**Success metric:**
2+ testers say the return felt alive.

**Timeline:**
Day 7 evening = decision point.

**Next phase:**
Determined by Day 7 result.

---

**The only thing that matters now is what real humans feel.**

Everything else is secondary.

Go.

🚀

