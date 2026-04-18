# KERNEL V2 — Integrated Constitutional Rules + Superteam Powers

**Version:** 2.0.0
**Date:** 2026-02-20
**Status:** ACTIVE

---

## Section 1: Scope

This is the first document in the system where constitutional rules and superteam powers are specified together as one integrated architecture. Every superteam power in this document has a traceable source in a constitutional rule. If a superteam claims a power that no rule grants, the power is invalid.

**What this document governs:**
- Constitutional rules (Section 2)
- K-gates with superteam mapping (Section 3)
- Superteam power declarations (Section 4)
- Role charters for Lateral Pattern and Rhythm Tracker (Section 5)
- Superteam membership table including Execution deletion record (Section 6)
- Authority flow diagram (Section 7)
- District integration and updated authority matrix (Section 8)

**What this document does NOT govern:**
- Oracle Town governance kernel (frozen — see oracle_town/)
- CONQUEST game mechanics
- CLAUDE.md operational instructions (unchanged — remains the operational baseline)
- Individual run workspace structure (runs/, claims/, drafts/)

**Baselines:**
- CLAUDE.md: unchanged, operational reference
- SUPERTEAM_AUDIT.md: audit findings remain as historical record; authority definitions superseded by this document
- Governance superteam: FROZEN — listed here for completeness, not redesigned

**Core principle:** Each superteam's power flows directly from a constitutional rule. If a superteam claims a power that no rule grants, the power is invalid.

---

## Section 2: Constitutional Rules (V2)

Five rules. Each rule is precise, bounded, and testable. Each has a pass test and a fail test.

---

### RULE 1: SINGLE FINALIZATION POINT

**Statement:** For any given work product, exactly one role has finalization authority, and that role is declared before work begins.

**Scope:** All Layers

**Upgrade from V1:** V1 said "No Direct Authority Writes." V2 adds the pre-declaration requirement — the authority must be named before the work starts, not just restricted after the fact.

**Superteam Binding:**
- Production: Editor is the declared finalization authority for all artifacts. Foreman cannot override Editor.
- Knowledge: No role in this superteam finalizes. All output flows to Foreman for curation, then to Production for final assembly.
- Creative: Neither Lateral Pattern nor Rhythm Tracker can finalize. Foreman is the only curator of Creative output.
- Governance (FROZEN): Mayor is the declared finalization authority for all governance decisions.

**K-gate:** K0 — Authority Separation (signer must be in registry)

**Pass Test:** The role with finalization authority can be named before any work product is touched, and no other role's output enters the final artifact without that authority's approval.

**Fail Test:** Two roles each make independent changes to the same final document, or the finalizing role cannot be named at the start of a run.

---

### RULE 2: RECORD BEFORE TRANSITION

**Statement:** No phase transition, claim acceptance, or artifact delivery may occur until a record of that transition exists.

**Scope:** All Layers

**Upgrade from V1:** V1 said "Every State Change Requires Signed Record." V2 adds "before it takes effect" — the record precedes the action, not follows it. This closes a gap where phase transitions could happen verbally before being logged.

**Superteam Binding:**
- Production: phase_transitions.md must be written before Foreman advances to the next phase. claims/accepted.md must have a Foreman approval entry before a claim routes to drafting.
- Knowledge: Foreman's accept record must exist in accepted.md before Knowledge output moves to the next step.
- Creative: LP-### connection claims must be logged to pending.md before Foreman reviews them. RT-### energy observations must be logged before Foreman can act on them.

**K-gate:** K5 — Determinism (same input must produce same logged output)

**Pass Test:** The log entry for a phase transition or claim acceptance exists in the workspace before agents in the next phase begin work.

**Fail Test:** Foreman verbally declares a phase transition but no log record exists, or a claim appears in accepted.md with no Foreman approval timestamp.

---

### RULE 3: NO SELF-EDIT, NO SELF-VALIDATION

**Statement:** The role that produces a claim cannot be the role that approves, merges, or delivers that claim.

**Scope:** All Layers

**Upgrade from V1:** V1 had two separate rules — "No Self-Edit" and "Foreman Has Zero Final Authority." V2 consolidates both into one precise rule that applies universally to all roles, including Foreman. Foreman also cannot self-validate its own curation decisions.

**Superteam Binding:**
- Production: Writer cannot approve its own prose. Synthesizer cannot approve its own merges. Foreman routes all claims but does not self-approve its routing decisions — Editor's acceptance of the final artifact is the external validation.
- Knowledge: Researcher cannot validate its own evidence. Structurer cannot accept its own outlines. Visualizer cannot approve its own diagrams.
- Creative: Lateral Pattern cannot validate its own connections. Rhythm Tracker cannot certify its own energy observations.
- All superteams: Every claim in accepted.md must have a different role listed as author versus approving authority.

**K-gate:** K2 — No Self-Attestation (proposer must not equal validator)

**Pass Test:** For any claim in accepted.md, the author field and the approving authority are different roles.

**Fail Test:** A claim lists the same role as both author and approving authority, or an agent silently moves its own work from pending.md to accepted.md.

---

### RULE 4: COORDINATOR AUTHORITY IS PROCESS-ONLY, NEVER CONTENT

**Statement:** The coordinating role (Foreman) has full authority over process — phase timing, claim routing, agent assignment, timeout enforcement — and zero authority over content decisions.

**Scope:** Superteam layer (applies wherever a Foreman-equivalent exists)

**Upgrade from V1:** V1 said "Foreman Has Zero Final Authority," which was accurate but incomplete. It described restriction without describing what Foreman can do. V2 is more precise: Foreman has complete authority over process, which is different from having no authority. This matters because it gives Foreman clear ground to stand on while preventing content-authority drift.

**Foreman CAN:**
- Declare phase transitions (and log them)
- Accept, reject, or merge claims (fitness determination — not truth determination)
- Spawn and assign agents
- Enforce time budgets and timeouts
- Interrupt unproductive discussions
- Act on RT-### burnout flags from Rhythm Tracker

**Foreman CANNOT:**
- Author any content claim
- Decide what is "true" (only what is "fit for the current phase")
- Override Editor's finalization decisions
- Block termination once Editor declares SHIP or ABORT

**Superteam Binding:**
- Production: Foreman sets phases, routes claims, enforces timelines. All content exists in claims authored by other roles.
- Knowledge: Foreman accepts/rejects Knowledge claims based on fitness (does this serve the current run?), not truth value (is this factually correct?).
- Creative: Foreman scopes the exploration window, curates LP-### and RT-### claims. Foreman does not decide which connections are "correct" or which energy observations are "true."

**K-gate:** K0 — Authority Separation (Foreman's process-authority is bounded in the registry)

**Pass Test:** Every Foreman action is one of: phase declaration, claim accept/reject/merge, agent spawn, timeout enforcement, RT-### response. All content in the final artifact was authored by non-Foreman roles.

**Fail Test:** Foreman authors a content claim, writes prose that appears in the final artifact, or overrides Editor's SHIP/ABORT declaration.

---

### RULE 5: FAIL-CLOSED WITH MANDATORY TERMINATION

**Statement:** When evidence is missing, the system rejects. When a run completes, the run must declare either delivery or abort — silence is never valid.

**Scope:** All Layers

**Upgrade from V1:** V1 mapped this to K1 only (Fail-Closed Default). V2 adds mandatory termination. Endless-revision mode is a fail-open state — the system never terminates. Adding "silence is never valid" closes this gap: every run must end with a logged outcome.

**Superteam Binding:**
- Knowledge: Researcher cites a source for every factual claim or tags it [UNVERIFIED]. A claim with no source and no [UNVERIFIED] tag is a Rule 5 violation.
- Production: Editor must declare SHIP (artifact delivered) or ABORT (insufficient coherence, needs new input). "In progress" is not a valid termination state.
- Creative: Lateral Pattern must file an LP-### connection claim or explicitly declare "no pattern found." Silent non-delivery is a Rule 5 violation.
- Governance (FROZEN): Mayor's binary SHIP/NO_SHIP is the canonical implementation of this rule at the governance layer.

**K-gate:** K1 — Fail-Closed Default (missing evidence triggers REJECT)

**Pass Test:** Every run ends with one of two logged outcomes: DELIVERED (artifact link exists in phase_transitions.md) or ABORTED (reason logged). Every Researcher claim includes a cited source or the tag [UNVERIFIED].

**Fail Test:** A run ends with no logged outcome. A Researcher claim makes a factual assertion without a source or [UNVERIFIED] tag. Lateral Pattern submits no claims and files no "no pattern found" declaration.

---

## Section 3: K-Gates (Retained + Superteam Map)

K-gates are the testable boundary conditions that constitutional rules resolve to. All K-gates in Foundry Town are Convention-enforced (not machine-enforced). Oracle Town's K-gates are machine-enforced — noted where relevant.

| K-gate | Maps to Rule | Condition | Superteam Map | Enforcement |
|---|---|---|---|---|
| **K0** | Rule 1, Rule 4 | Signer must be in authority registry | Production (Editor is registered finalizer), Creative (Foreman is registered curator) | Convention |
| **K1** | Rule 5 | Missing evidence → REJECT (fail closed) | Knowledge (Researcher must cite or tag [UNVERIFIED]), Production (Editor: missing coherence → ABORT) | Convention |
| **K2** | Rule 3 | Proposer ≠ validator | All active superteams — universal | Convention |
| **K5** | Rule 2 | Same input → identical output (determinism) | Production only. **Creative is explicitly EXEMPT from K5.** Lateral exploration is intentionally non-deterministic. | Convention |
| **K7** | Rule 2 | Policy hash fixed per run | Production (policy hash locks at run start). Creative: policy-free by design — no hash applies. | Convention |

**Note on K5 exemption:** Creative is the only superteam exempt from determinism. This is not a weakness — it is Creative's defining constraint. The system acknowledges that lateral thinking cannot be reproduced from the same inputs and designs around it rather than fighting it.

**Note on machine enforcement:** In Oracle Town (FROZEN), all K-gates are machine-enforced through the K-gate validator. In Foundry Town (active production system), K-gates are convention-enforced — the rules exist and are tested, but violations require human detection. This is an intentional trade-off: flexibility for production work, strictness for governance.

---

## Section 4: Superteam Power Declarations

Each superteam has exactly one Unique Power — something it can do that no other superteam can do. This is the constitutional basis for the superteam's existence. If two superteams share a unique power, one is a duplicate (see Execution deletion record in Section 6).

---

### PRODUCTION — Power Declaration

**Unique Power:** Unilateral cut authority. The Editor role inside Production can reduce any draft by 30–50% and declare it final without consensus from any other role.

**Constitutional Source:** Rule 1 (Single Finalization Point) + Rule 5 (Mandatory Termination)

**Roles:**
- Foreman (coordinator — process authority only)
- Editor (final authority — content + termination)
- Writer (prose drafter — claims → readable prose)
- Synthesizer (claim merger — here only, not in any other superteam)

**What it produces:** Final artifacts — documents, memos, code, decision records. These are the only outputs that leave the system.

**What it cannot produce:**
- Evidence claims (Knowledge territory — Researcher must originate)
- Energy observations (Creative territory — Rhythm Tracker files)
- Governance verdicts (Governance territory — FROZEN)

**Active K-gates:** K0, K1, K2, K5, K7

**Pass Test:** Editor declares either SHIP (artifact exists, link logged) or ABORT (reason logged). Artifact shows evidence of 30–50% compression from draft to final.

**Fail Test:** Run ends without Editor declaration. Draft and final artifact are identical in length. Synthesizer appears in any superteam other than Production.

---

### GOVERNANCE — Power Declaration (FROZEN)

**Unique Power:** Binary veto authority. The Mayor role inside Governance can issue an irrevocable NO_SHIP decision based on constitutional rule failure alone, without requiring human consensus.

**Constitutional Source:** Rule 1 (canonical form — most absolute implementation)

**Status:** FROZEN — Oracle Town reference implementation. Do not redesign, do not integrate into active superteams. This superteam is listed here for constitutional completeness.

**Roles:**
- Skeptic (adversarial critic — proposes critique claims)
- Mayor (governance authority — binary SHIP/NO_SHIP)
- Ledger (immutable record — append-only, no edits)

**Note:** All five K-gates (K0, K1, K2, K5, K7) are active and machine-enforced in Governance. This is the definition of "fully governed." Foundry Town's production system inherits Governance's principles but relaxes enforcement from machine to convention for operational flexibility.

---

### KNOWLEDGE — Power Declaration

**Unique Power:** Source-citation authority. Only the Researcher role can introduce new evidence into the system. No other role can add factual claims that are not attributed to a source. If it has no source, it is not Knowledge output.

**Constitutional Source:** Rule 5 (Fail-Closed — inference without source is a violation)

**Roles:**
- Researcher (evidence gatherer — facts, sources, never infers beyond sources)
- Structurer (outline architect — organizes, does not invent)
- Visualizer (diagram creator — represents, never infers)

**What it produces:** Source-cited claims (R-### prefix), structural outlines (T-### prefix), evidence diagrams (V-### prefix). Evidence repository. Source bibliography.

**What it cannot produce:**
- Prose (Writer's territory)
- Final artifacts (Editor's territory)
- Energy observations (Rhythm Tracker's territory)
- Connection claims (Lateral Pattern's territory)

**Active K-gates:** K1 (Researcher fail-closed), K2 (no role validates own claims)

**Pass Test:** Every factual claim in Knowledge output has a source citation or the tag [UNVERIFIED]. The source exists and can be retrieved.

**Fail Test:** A claim in Knowledge output makes a factual assertion with neither a source nor [UNVERIFIED]. Researcher interprets or argues a claim rather than stating it as evidence.

---

### CREATIVE — Power Declaration

**Unique Power:** K5 exemption. Creative is the only superteam explicitly exempt from determinism. Lateral Pattern may surface connections that were not specified as inputs, and Rhythm Tracker may flag energy states that were not pre-scheduled. Neither output is required to be reproducible from the same inputs.

**Constitutional Source:** Rule 5 (modified form — "no pattern found" is a valid termination declaration, parallel to "no evidence" producing [UNVERIFIED])

**Roles:**
- Lateral Pattern (connection proposer — see full charter in Section 5)
- Rhythm Tracker (energy monitor — see full charter in Section 5)

**What it produces:** Connection claims (LP-### prefix), energy observations (RT-### prefix, tagged ADVISORY).

**What it cannot produce:**
- Final artifacts (Editor's territory)
- Evidence claims (Researcher's territory — LP-### connection claims are not evidence)
- Prose (Writer's territory)
- Governance verdicts (Mayor's territory)

**Active K-gates:** K2 only (no self-validation). K5 explicitly EXEMPT. K1 applies in limited form: if no connection is found, Lateral Pattern must declare "no pattern found" rather than silence.

**Pass Test:** Every LP-### claim lists two or more existing claim IDs and states only a pattern relationship. Every RT-### claim is tagged ADVISORY. No LP-### or RT-### claim proposes action or forces a transition.

**Fail Test:** Lateral Pattern submits no claims and files no "no pattern found" declaration (Rule 5 silence violation). RT-### claim appears in phase_transitions.md as initiating authority.

---

## Section 5: Creative Role Charters

These are the full charters for the two roles in the Creative superteam. Previously undefined (flagged in SUPERTEAM_AUDIT.md as a blocker). Now formally specified.

---

### LATERAL PATTERN — Role Charter

**Purpose:** Identify unexpected connections across domains. Surface hidden relationships between existing claims.

**Claim Prefix:** LP-###
**Claim Type:** connection (distinct from evidence, critique, structure, prose)

**Responsibilities:**
- Surface analogous patterns across unrelated domains
- Propose novel reframings of existing claims
- Identify hidden assumptions embedded in accepted claims
- Connect claims from different superteams that share structural similarity
- File LP-### connection claims to pending.md

**Powers:**
- Propose LP-### connection claims to pending.md
- Request that Foreman schedule a lateral exploration phase
- Surface connections between claims from different superteams

**Limits (constitutional):**
- Cannot propose solutions — connections only, not fixes or recommendations
- Cannot approve, merge, or validate any claim, including its own (Rule 3)
- Cannot initiate phases — Foreman initiates all phase transitions (Rule 4)
- Cannot produce prose — Writer's territory
- All LP-### output flows to Foreman for curation before any action is taken (Rule 3)
- Output is explicitly non-deterministic — K5 does not apply

**2-Sentence Atomic Test:**
Lateral Pattern identifies unexpected relationships between claims. It does not explain why they matter, propose what to do about them, or validate whether they are true.

**Pass Test:** Every LP-### claim lists two or more existing claim IDs and states only "these claims share pattern X." No LP-### claim proposes action, contains prose, or includes a solution.

**Fail Test:** An LP-### claim proposes a solution or recommendation. An LP-### claim appears in accepted.md without a Foreman curation record. Lateral Pattern submits nothing and files no "no pattern found" declaration at run end (Rule 5 violation).

---

### RHYTHM TRACKER — Role Charter

*Formerly named "Music Rhythm." Renamed for clarity: this role monitors work session rhythm (cognitive load cycles, rest intervals), not audio or music.*

**Purpose:** Track work session intensity and file advisory burnout-risk flags to Foreman.

**Claim Prefix:** RT-###
**Claim Type:** energy_observation

**Responsibilities:**
- Observe work session intensity (session duration, phase density, revision frequency)
- Detect burnout risk signals: loop behavior, fading clarity, revision-instead-of-finishing patterns, sessions exceeding 4 hours
- Propose break timing recommendations
- Log energy observations before and after sessions

**Powers:**
- Propose RT-### energy observations to pending.md
- Flag Foreman when burnout risk is detected: "RT-### ADVISORY: session at 3.5h — break recommended"

**Limits (constitutional):**
- READ-ONLY advisory output — cannot force any action
- Cannot pause, stop, or interrupt any phase (Rule 4 — only Foreman has process authority)
- Cannot override Foreman's phase timing decisions
- Cannot validate its own observations (Rule 3)
- All RT-### output is advisory to Foreman — Foreman decides whether to act

**"Music Always Wins" resolution:**
The DISTRICTS_MANIFEST.md states "MUSIC always wins" in rhythm conflicts. This is resolved in Kernel V2 as follows:
- Rhythm Tracker the role is advisory — it cannot force anything
- Foreman is constitutionally obligated to act on RT-### burnout flags (this is what "always wins" means)
- The obligation sits with Foreman, not with Rhythm Tracker
- Foreman acts. Rhythm Tracker files. These are separate authorities.

**2-Sentence Atomic Test:**
Rhythm Tracker observes session intensity and files advisory claims when burnout risk is detected. It cannot pause, stop, or override any phase or any other agent's work.

**Pass Test:** Every RT-### claim is tagged ADVISORY. No RT-### claim appears in phase_transitions.md as the initiating authority for any transition.

**Fail Test:** A phase transition log shows RT-### as the initiating authority. An RT-### claim says "work must stop now" rather than "work stop recommended." Rhythm Tracker forces a pause without Foreman logging the transition (Rule 2 violation).

---

## Section 6: Superteam Table (V2 Master)

| Superteam | Status | Roles | Unique Power | Source Rule |
|---|---|---|---|---|
| **Production** | ACTIVE | Foreman, Editor, Writer, Synthesizer | Unilateral cut authority (Editor) | Rule 1, Rule 5 |
| **Governance** | FROZEN | Skeptic, Mayor, Ledger | Binary veto authority (Mayor) | Rule 1 (canonical) |
| **Knowledge** | ACTIVE | Researcher, Structurer, Visualizer | Source-citation authority (Researcher) | Rule 5 |
| **Creative** | ACTIVE | Lateral Pattern, Rhythm Tracker | K5 exemption (non-deterministic) | Rule 5, K5 exempt |
| **Execution** | DELETED | — | — | Rule 4 violation resolved |

---

### Execution Superteam — Deletion Record

**Date of deletion:** 2026-02-20
**Reason:** Structural violations found in SUPERTEAM_AUDIT.md:

1. **Synthesizer duplication** — Synthesizer appeared in both Production and Execution, creating ambiguous authority. Resolution: Synthesizer moved exclusively to Production, where claim-merging belongs mechanically (it serves the drafting phase).

2. **Scheduler authority conflict** — Scheduler's declared scope ("timing and coordination") overlapped directly with Foreman's declared power ("enforce phase transitions," "track progress against time budget"). This violated Rule 4: two roles claiming process authority. Resolution: Scheduler's functions absorbed into Foreman's coordination mandate. Internal phase timing is Foreman's constitutional responsibility.

3. **Registry authority conflict** — Registry's declared scope ("resource tracking") overlapped with Foreman's "track progress against time budget." Same Rule 4 violation. Resolution: Registry functions absorbed into Foreman's manifest. No new mechanism required.

**Outcome:** No capabilities were lost. Existing powers were correctly attributed to the roles that already held them. Execution was not a new superteam — it was a description of Foreman's existing process authority under a different name.

---

## Section 7: Authority Flow Diagram

Every line in this diagram traces from a constitutional rule to a superteam to a specific role. No line exists without a rule source. If you cannot trace a power claim back to a rule in this diagram, the claim is invalid.

```
KERNEL V2 CONSTITUTIONAL RULES
  │
  ├─ RULE 1: Single Finalization Point
  │   │
  │   ├─ PRODUCTION → Editor
  │   │  └─ Editor is the declared finalization authority
  │   │     Editor: unilateral cut, declare SHIP or ABORT
  │   │     Editor cannot be overridden by Foreman or Writer
  │   │
  │   └─ GOVERNANCE (FROZEN) → Mayor
  │      └─ Mayor is the governance finalization authority
  │         Mayor: binary SHIP/NO_SHIP, irrevocable
  │
  ├─ RULE 2: Record Before Transition
  │   │
  │   ├─ PRODUCTION → Foreman
  │   │  └─ Foreman writes phase_transitions.md before advancing phases
  │   │     Foreman writes accepted.md entry before routing claims
  │   │
  │   ├─ KNOWLEDGE → Foreman
  │   │  └─ Foreman logs claim acceptance before Knowledge output moves
  │   │
  │   └─ CREATIVE → Foreman
  │      └─ Foreman logs LP-### review before acting on connections
  │         Foreman logs RT-### response before acting on burnout flag
  │
  ├─ RULE 3: No Self-Edit, No Self-Validation
  │   │
  │   ├─ PRODUCTION → Foreman receives all pending claims
  │   │  Writer → pending.md → Foreman curates → Editor assembles
  │   │  Synthesizer → pending.md → Foreman approves → Writer uses
  │   │
  │   ├─ KNOWLEDGE → Foreman receives all pending claims
  │   │  Researcher → pending.md → Foreman curates → routes to Production
  │   │  Structurer → pending.md → Foreman curates → routes to Production
  │   │
  │   └─ CREATIVE → Foreman receives all pending claims
  │      Lateral Pattern → pending.md → Foreman curates → routes forward
  │      Rhythm Tracker → pending.md → Foreman acts on flag
  │
  ├─ RULE 4: Coordinator Authority is Process-Only
  │   │
  │   └─ FOREMAN (cross-superteam coordinator)
  │      │
  │      ├─ CAN: phase timing, claim routing, agent spawn, timeout, RT-### response
  │      └─ CANNOT: author content, decide truth, override Editor
  │
  │      FOREMAN is the same role in all superteams.
  │      Same powers. Same limits. Everywhere.
  │
  └─ RULE 5: Fail-Closed + Mandatory Termination
      │
      ├─ KNOWLEDGE → Researcher
      │  └─ Every factual claim: cite source OR tag [UNVERIFIED]
      │     No inference. No invention. Fail closed.
      │
      ├─ PRODUCTION → Editor
      │  └─ Every run: declare SHIP or ABORT
      │     No "in progress." No silence. Mandatory termination.
      │
      └─ CREATIVE → Lateral Pattern
         └─ Every exploration: file LP-### claim OR declare "no pattern found"
            No silence. Rhythm Tracker: file RT-### OR declare "no signals detected"
```

---

## Section 8: District Integration (V2 Authority Matrix)

Districts are LEGO3 — superteams clustered around a domain and a rhythm. This section updates the authority matrix from DISTRICTS_MANIFEST.md to reflect KERNEL_V2 changes.

**Key changes from DISTRICTS_MANIFEST.md:**
- CREATIVE district: Final authority is Foreman (not "Mood Tracker"). Rhythm Tracker is advisory. Foreman acts on RT-### flags.
- MUSIC district: Final authority is Foreman (acting on RT-### flags). Rhythm Tracker files only.
- All districts now reference KERNEL_V2 rule numbers.
- Execution superteam removed from all district references.

| District | Superteams Active | Final Authority | Primary Rules | Rhythm |
|---|---|---|---|---|
| **FOUNDRY** | Production, Knowledge | Editor | Rule 1, Rule 2 | 5-phase pipeline (5.25h total) |
| **CREATIVE** | Creative | Foreman (scope + curation) | Rule 3, Rule 4 | Hyperfocus cycles (4h max + mandatory break) |
| **SCIENCE** | Knowledge, Governance* | Skeptic (validation) | Rule 5 | Continuous (daily/weekly/monthly/quarterly) |
| **MUSIC** | Creative (Rhythm Tracker) | Foreman (acts on RT-###) | Rule 4 | Weekly cycles |
| **UZIK** | Creative (Visualizer) | Visualizer (aesthetic judgment) | Rule 1 | Per-sprint (1–2 weeks) |

*Governance in SCIENCE: FROZEN reference only. Skeptic + Ledger participate as validation tools, not active redesign targets.

### Cross-District Coordination Rule

Districts do not wait for each other. Claims flow through the Claim Market asynchronously. When FOUNDRY needs evidence from SCIENCE and design from UZIK simultaneously:

1. FOUNDRY spawns Production superteam
2. Production requests Knowledge superteam (SCIENCE) → evidence claims (R-### prefix)
3. Production requests Visualizer (UZIK) → visual claims (V-### prefix)
4. SCIENCE and UZIK work in parallel — no blocking
5. Production's Foreman curates all incoming claims from both districts
6. Editor assembles final artifact from curated claims

**Rule:** Districts coordinate through the Claim Market. No district has authority over another district's internal processes.

### Rhythm Conflict Resolution

**Scenario:** CREATIVE hyperfocus conflicts with MUSIC burnout signal.

**Resolution (V2):**
1. Rhythm Tracker files: "RT-### ADVISORY: session at 4h — break recommended"
2. Foreman reads RT-### flag from pending.md
3. Foreman logs in phase_transitions.md: "Phase paused — RT-### burnout flag received — break initiated"
4. Foreman enforces break (Rule 4: process authority)
5. After break, Foreman logs: "Phase resumed — break complete"

Music always wins because **Foreman always acts on Rhythm Tracker's flag**. Not because Rhythm Tracker has authority to force anything.

---

## Section 9: Status + Amendment Protocol

### Document Status

```
KERNEL V2 STATUS

Version:        2.0.0
Date:           2026-02-20
Status:         ACTIVE

Supersedes:     SUPERTEAM_AUDIT.md (authority definitions only)
                Audit findings remain as historical record.

Baseline:       CLAUDE.md (unchanged — operational reference)

Frozen:         Oracle Town Governance superteam (unchanged)
                oracle_town/ directory (reference only)

What changed from V1 (CLAUDE.md constitutional rules):
- Rule 1: Added pre-declaration requirement
- Rule 2: Added "record precedes action" (not follows)
- Rule 3: Consolidated old Rules 3+4 into one universal rule
- Rule 4: Clarified what Foreman CAN do (not just restrictions)
- Rule 5: Added mandatory termination to fail-closed requirement

What was deleted:
- Execution superteam (Rule 4 violation — absorbed into Foreman + Production)

What was activated:
- Creative superteam (Lateral Pattern + Rhythm Tracker now formally chartered)

What was renamed:
- "Music Rhythm" → "Rhythm Tracker" (clarity: monitors work rhythm, not audio)
```

### Amendment Protocol

Any change to Sections 2–5 (Rules, K-Gates, Power Declarations, Role Charters) requires all three gates:

1. **Evidence Gate:** At least one audit finding, test failure, or documented violation that justifies the change. "I think this would be better" is not evidence.

2. **Conservatism Gate:** State explicitly why leaving the rule unchanged is more dangerous than changing it. The burden of proof is on the change, not the status quo.

3. **Record Gate:** New version number (increment minor for clarifications, major for structural changes) + log entry in this footer.

**Amendment log:**
```
v2.0.0 — 2026-02-20 — Initial version. Resolved 3 audit violations. Activated Creative. Deleted Execution.
```

---

**Hold the line on Rule 3. It is where corruption dies.**

---

*Last Updated: 2026-02-20 | KERNEL_V2.md | Active*
