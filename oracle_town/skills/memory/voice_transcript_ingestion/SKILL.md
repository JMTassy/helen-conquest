---
name: memory/voice_transcript_ingestion
description: Non-sovereign intake protocol for voice / speech-to-text transcripts. Structures, classifies, and compresses raw transcripts into classified candidates (claims, hypotheses, actions, open questions) without promoting any of them to doctrine. Transcript is cognitive intake, not a receipt.
helen_faculty: MEMORY
helen_status: DOCTRINE (calibrated 2026-04-20; not yet INVARIANT)
helen_prerequisite: NO RECEIPT = NO CLAIM invariant; admissibility chain (helen_say.py → ndjson_writer.py → town/ledger_v1.ndjson)
---

# Voice Transcript Ingestion — Non-Sovereign Intake Skill

**Class**: Non-sovereign. No kernel authority. No ledger write. A transcript is capture, not proof.

**Scope**: How to take a raw voice-to-text transcript (operator speech, meeting recording, reflection log) and compress it into a structured, re-usable memory candidate set — without auto-promoting any item into doctrine, the ledger, or the constitutional spine.

---

## 1. Governing law

```
capture → transcribe → classify → compress → reuse
  — never direct transcript → doctrine.
```

A transcript is:
- useful for proposals, drafts, prompts, reflections, memory candidates
- **not** a receipt
- **not** a verified fact
- **not** a governed ledger event
- **not** an authoritative state transition

Promotion of any extracted item to doctrine / invariant / ledger entry requires the normal admissibility chain: `helen_say.py --op <op>` → kernel boundary → payload_hash → ledger write.

---

## 2. The reusable ingest template

Every voice-transcript ingestion request should be structured with these fields:

```
TYPE: [idea | question | decision | architecture | reflection | meeting]
CONTEXT: [project name]
SOURCE: [file path | live recording | Telegram voice msg | other]

HELEN: ingest this transcript as non-sovereign input.

1. Clean transcription noise
2. Flag uncertain names / terms / formulas
3. Separate observations from assertions
4. Extract claims
5. Extract hypotheses
6. Extract action items
7. Extract open questions
8. Mark what needs receipts
9. Output a 5-line summary
10. Do not promote anything to doctrine
```

Each numbered step is a required pass. Missing a pass = skill not executed.

---

## 3. What each step produces

| # | Pass | Output shape | Sovereignty |
|---|------|--------------|-------------|
| 1 | Clean transcription noise | Paragraph text with filler removed, punctuation restored | non-sovereign |
| 2 | Flag uncertain tokens | List of `[token → confidence?]` pairs with `?` or `[unclear]` markers | non-sovereign |
| 3 | Separate observation / assertion | Two sub-lists: `OBSERVED:` (what was said/seen) vs `ASSERTED:` (claims made) | non-sovereign |
| 4 | Claims | Bullet list, each claim tagged `[unverified]` unless accompanied by receipt | non-sovereign (candidates only) |
| 5 | Hypotheses | Bullet list, each with a falsifiability clause | non-sovereign |
| 6 | Action items | Checklist with owner + by-date; no auto-execution | non-sovereign |
| 7 | Open questions | Plain questions, no speculative answers | non-sovereign |
| 8 | Receipt needs | For each claim/hypothesis, one line: "needs receipt via helen_say" OR "does not need receipt (scope = draft only)" | non-sovereign meta |
| 9 | 5-line summary | Exactly 5 lines, operator-readable | non-sovereign |
| 10 | Promotion guard | Explicit final line: "No items promoted to doctrine. Promotion requires separate helen_say + K2." | discipline marker |

---

## 4. Required safety passes

Two passes are NON-negotiable regardless of operator request:

### 4a. Uncertain token flagging

Every name, technical term, number, or formula that STT may have misheard must carry a visible confidence mark:

- `JMTassy [confirmed]` — verified against context
- `helen-conquest [confirmed]` — verified against SOT
- `Seedance [?]` — likely but not verified
- `[unclear] Moeru` — likely mishearing of operator term

Rule: **if a token cannot be independently confirmed from the transcript context or from known SOT canon, flag it.** Never silently auto-correct into what "sounds right."

### 4b. Observation-vs-assertion separation

Transcripts conflate these constantly. The output must split them:

- **OBSERVED**: "The operator said X." — a fact about the transcript itself.
- **ASSERTED**: "X is true in the world." — a claim requiring verification.

Never promote an assertion to a claim without a `[unverified]` marker unless an external receipt is cited.

---

## 5. What must NOT happen

- No item from a transcript is written to `town/ledger_v1.ndjson` directly.
- No item is injected into `helen_os/governance/**` or any firewalled path.
- No MAYOR ruling is issued on the basis of a transcript alone.
- No closure receipt references a transcript-derived artifact without an intermediate `helen_say.py` call that computes the canonical payload_hash.
- No auto-extraction of "decisions" as binding — a decision from a transcript is a DECISION CANDIDATE until separately receipted.
- No cross-session memory write that encodes a transcript assertion as fact without the `[unverified]` marker.

---

## 6. Proper promotion path (transcript → doctrine)

If, after ingestion, an item deserves to become doctrine:

1. Operator reviews the structured output.
2. Operator identifies the specific claim / hypothesis / action to promote.
3. Operator runs `tools/helen_say.py "<claim>" --op <op>` — this computes payload_hash and routes through the kernel.
4. The resulting ledger entry is the first sovereign trace of the claim.
5. K2 / Rule 3 applies: proposer ≠ validator. A separate session validates before the claim can become doctrine.
6. Only then does the item leave the non-sovereign candidate pool.

Skipping any of steps 3–5 means the item is still a candidate, regardless of how confident the operator feels.

---

## 7. Output template

```
--- VOICE TRANSCRIPT INGEST ---
TYPE: <type>
CONTEXT: <project>
SOURCE: <path>
TIMESTAMP: <ISO-8601>

[1] CLEANED TEXT
<paragraph>

[2] UNCERTAIN TOKENS
- <token> [?]
- <token> [unclear]

[3] OBSERVED vs ASSERTED
OBSERVED:
  - <fact about the transcript>
ASSERTED:
  - <claim made in the transcript>

[4] CLAIMS
- [unverified] <claim 1>
- [unverified] <claim 2>

[5] HYPOTHESES
- <H1> — falsifiable by: <test>
- <H2> — falsifiable by: <test>

[6] ACTION ITEMS
- [ ] <action> — owner: <x> — by: <date>

[7] OPEN QUESTIONS
- <question 1>
- <question 2>

[8] RECEIPT NEEDS
- <claim 1> → needs receipt via helen_say
- <claim 2> → draft only, no receipt needed

[9] 5-LINE SUMMARY
1. <line>
2. <line>
3. <line>
4. <line>
5. <line>

[10] PROMOTION GUARD
No items promoted to doctrine. Promotion requires separate helen_say + K2.
```

---

## 8. Governance notes

- All files produced by this skill are non-sovereign artifacts. They may be stored in `artifacts/` or an operator-chosen non-firewalled path.
- The skill MUST NOT write to any firewalled path (see `~/.claude/CLAUDE.md` sovereign-path firewall: `oracle_town/kernel/**`, `helen_os/governance/**`, `helen_os/schemas/**`, `town/ledger_v1*.ndjson`, `mayor_*.json`, `GOVERNANCE/**`).
- Per `NO RECEIPT = NO CLAIM`: no claim is "validated" by this skill. The skill's output carries zero constitutional weight on its own.
- Per K-tau `mu_DETERMINISM`: same transcript + same skill run = same output. No model-call randomness allowed in the structural classification pass. Summary generation may use a model but the classification structure must be deterministic.

---

## 9. Complement — sibling docs

- `~/.claude/CLAUDE.md` — HELEN OS Non-Sovereign Execution Shell policy (where this skill's firewall discipline comes from)
- `helen_os/governance/validators.py` — for claim structural validation if an extracted item is later promoted
- `tools/helen_say.py` — the admissible bridge for any transcript-derived item that is ever promoted

---

## 10. Admission status

**DOCTRINE** — calibrated 2026-04-20 from operator recap after HELEN consolidation session. Not yet INVARIANT.

Promotion to INVARIANT requires:
- Second independent session applies this template to a real voice transcript and produces output that matches this structure ≤10% deviation
- `helen_say.py` receipt binding this document's SHA256 to the ledger
- K2 / Rule 3: the session that promotes must not be the session that authored

Until then: cite as "current working doctrine for voice transcript intake."
