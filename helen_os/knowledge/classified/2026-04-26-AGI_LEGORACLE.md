# KNOWLEDGE_ENTRY: AGI LEGORACLE $

```
lifecycle:        DRAFT
artifact_type:    KNOWLEDGE_ENTRY
authority:        NON_SOVEREIGN
source_corpus:    plugins
source_path:      ~/Desktop/PLUGINS_JMT/#pluginAGI LEGORACLE $.txt
preserved_tag:    #pluginAGI LEGORACLE $                     # source-native, including the trailing dollar sign
domain:           LEGORACLE_RECEIPTS
secondary_domains: [ORACLE_GOVERNANCE, HELEN_OS]
ingest_date:      2026-04-26
excerpt_lines:    1-150 of 117369
extraction_quality: GOOD                                     # text extraction clean throughout the excerpt
confidence:       HIGH                                       # internal coherence very strong; explicit lineage to current SOT
```

---

## Source-native tag preservation

Filename keyword is `AGI LEGORACLE $` — the trailing `$` is operator-meaningful (likely a finance / commercial tag the operator uses across the corpus). The classifier MUST preserve it; stripping `$` would conflate this with `#pluginAGI LEGORACLE` (a sibling, if it exists) or `#pluginLEGORACLE` (a more general bucket).

## Detected domain

Primary: **LEGORACLE_RECEIPTS** — the file's central artifact is `ORACLE SUPERTEAM`, a "governance-first multi-agent framework" anchored on `NO_RECEIPT = NO_SHIP` (explicit at line 110, line 60). This is the direct upstream of today's `helen_os/governance/legoracle_gate_poc.py` and the `LEGORACLE` gate in repo CLAUDE.md.

Secondary: **ORACLE_GOVERNANCE** (the framework is called ORACLE SUPERTEAM); **HELEN_OS** (the constitutional principles are now HELEN's invariants).

## Extracted units

### CLAIM
- *line 5–10 / restated 94–112*: "ORACLE SUPERTEAM, a governance-first multi-agent framework designed to transform loosely structured human or artificial reasoning into auditable, deterministic, and institutionally reliable decisions. Unlike conventional multi-agent systems that emphasize emergent consensus, narrative collaboration, or optimization through averaging, ORACLE SUPERTEAM is grounded in epistemic sovereignty: no claim may be accepted without explicit, verifiable evidence, and no agent—human or artificial—possesses unilateral authority to decide outcomes." — central thesis. **This is HELEN's constitutional foundation, in earlier wording.**
- *line 60*: "NO RECEIPT = NO SHIP prominently displayed" — the seed of HELEN's `NO RECEIPT = NO CLAIM`.
- *line 110–112*: "the principle NO_RECEIPT = NO_SHIP, ensuring that any claim asserting real-world effects or attestable facts is blocked unless accompanied by cryptographically hashable proof." — operational definition.
- *line 113–119*: "rejecting conversational consensus, probabilistic voting, and opaque 'reasoning traces' as decision criteria" — explicit anti-pattern list.

### FRAMEWORK
- **Three-layer pipeline** (line 104–110):
  1. **Production** — specialized agent teams ("Superteams") generate candidate obligations and non-binding signals.
  2. **Adjudication** — a critic agent applies lexicographic veto rules based on evidence sufficiency, logical coherence, real-world impact.
  3. **Integration** — a deterministic automaton emits a binary verdict (SHIP / NO_SHIP).
  Maps directly onto HELEN's current `oracle_town/kernel/` + `helen_os/governance/legoracle_gate_poc.py` + ledger architecture.

- **Six-card observability dashboard** (line 49–58): claims, ship rate, obligations, latency, kill switches, replay pass rate. Reusable for any future HELEN ops UI.

### THEOREM_DRAFT
- (No formal theorems in the excerpt; this artifact is operational/architectural rather than mathematical. The companion #pluginRIEMANN files carry the math layer.)

### OPERATING_RULE
- *line 60*: **NO RECEIPT = NO SHIP** — the load-bearing rule.
- *line 116–119*: "event-sourced memory, deterministic hashing, and explicit obligation semantics to guarantee replayability, auditability, and resistance to rhetorical inflation." — three-property test for kernel correctness. (Today: `town/ledger_v1.ndjson` is event-sourced, `CANONICALIZATION_V1` does the hashing, `LEGORACLE` does the obligation check.)
- *line 117–119*: "Superteams are deliberately constrained to an upstream, non-sovereign role: they may propose obligations and surface risks, but they cannot influence verdicts directly." — the **proposer ≠ validator** rule (today K2 / Rule 3).
- *line 138–140*: "STEP 0 — Fix the Non-Negotiables (Constitution). Before any code, agents, or UI: Hard axioms 1. NO_RECEIPT" — staging discipline rule.

### OPEN_QUESTION
- The transition from "this is what we're building" (line 132–137) to "STEP 0 — Fix the Non-Negotiables" (line 136) implies a sequel section the excerpt does not fully cover. The full step-by-step execution plan continues past line 150.
- Whether the "lexicographic veto rules" (line 108) survive in HELEN today as MAYOR's adjudication logic is asserted-by-lineage but not proven against the current `mayor_*.json` registry.

### PROMPT_PATTERN
- *line 132–135*: "Understood. Below is a complete, step-by-step execution plan, from zero to a running ORACLE SUPERTEAM / ORACLE TOWN system. This is written as an operational manual, not marketing, not philosophy." — operator-meaningful instruction-pattern: *operational-manual mode*. Reusable.

### RECEIPT_CANDIDATE
- **Highest-value receipt candidate in the 5-file batch.** A `helen_say.py` receipt binding this artifact's content SHA to today's `helen_os/governance/legoracle_gate_poc.py` would close the constitutional-lineage gap explicitly. Operator routing required (proposer ≠ validator on the binding).

## What should NOT be promoted to canon

- The visual / UI claims (line 47–58: "stunning dashboard", "Deep navy/dark theme with golden amber accents") — these are aesthetic decisions for one specific Lovable.dev demo, not constitutional. Promoting them would conflate UI taste with governance principle.
- The "Lovable Cloud" enablement section (line 73–90) — vendor-specific implementation detail, not portable doctrine.
- The assertion "the design follows your constitutional principles" (line 59) — this is the LLM speaking, not a verified mapping. The constitutional alignment must be re-derived against the current SOT, not inherited from the chat record.
- Any inferred date in the excerpt — line 65 says "15 janv.at 15:19" which is a Lovable.dev session timestamp, not a HELEN doctrinal date.

## Suggested future classifier rule

For artifacts where the operator's `preserved_tag` ends with a punctuation glyph (`$`, `!`, `?`), the classifier MUST:
1. Preserve the glyph as part of the tag.
2. Emit a `tag_punctuation_signal` field naming the glyph and a one-line operator-private interpretation slot (operator may bulk-fill later).
3. Refuse to deduplicate against the same tag without the glyph (treat as semantically distinct artifacts).

The `$` here likely marks "commercial / operationally consequential", but the classifier should not assume — only preserve.
