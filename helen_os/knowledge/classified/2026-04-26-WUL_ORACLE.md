# KNOWLEDGE_ENTRY: WUL ORACLE

```
lifecycle:        DRAFT
artifact_type:    KNOWLEDGE_ENTRY
authority:        NON_SOVEREIGN
source_corpus:    plugins
source_path:      ~/Desktop/PLUGINS_JMT/#pluginWUL ORACLE.txt
preserved_tag:    #pluginWUL ORACLE                          # source-native, do not normalize to "#pluginWUL_ORACLE" — the space is preserved
domain:           ORACLE_GOVERNANCE                          # primary
secondary_domains: [WUL_SYMBOLIC_LANGUAGE]
ingest_date:      2026-04-26
excerpt_lines:    1-200 of 87378
extraction_quality: DEGRADED                                 # PDF→text artifact: descriptive bullets render as one-character-per-line for long stretches
confidence:       MEDIUM                                     # title + opening claim are clear; body extraction needs re-run
```

---

## Source-native tag preservation

Filename keyword is `WUL ORACLE` with a space. The corpus also contains `#pluginWUL_ORACLE.pdf`, `#pluginWUL_ORACLE3.pdf`, `#pluginWUL FINE TUNE LATERAL THINKING.pdf`. These are distinct artifacts; the classifier MUST preserve the exact filename keyword (whitespace included) — collapsing `WUL ORACLE` and `WUL_ORACLE` would lose the operator's chronological versioning signal.

## Detected domain

Primary: **ORACLE_GOVERNANCE**. The document opens (line 1–10) by self-identifying as a blueprint for "the ORACLE + Simulated Science Loop" and references "ORACLE TOWN V2: a Hierarchical Multi-Agent Governance System with a Constitutional Kernel." This is the canonical pre-HELEN-naming-period name for what is now `oracle_town/kernel/`.

Secondary: **WUL_SYMBOLIC_LANGUAGE** — the WUL keyword in the filename anchors the symbolic-overlay register that today lives at `oracle_town/skills/ops/wulmoji_enhancer/SKILL.md` (locked v1 14-symbol palette).

## Extracted units

### CLAIM
- *line 5–10*: "the framework you're calling {FRAMEWORK_ORACLE} corresponds to ORACLE TOWN V2: a Hierarchical Multi-Agent Governance System with a Constitutional Kernel, designed as a Simulation UX wrapped around a law-bound, receipt-driven Truth Kernel." — direct identification of ORACLE TOWN V2 as the parent frame for HELEN's governance kernel today.
- The phrase "law-bound, receipt-driven Truth Kernel" is the lineage source for `NO RECEIPT = NO CLAIM` (now in repo CLAUDE.md).

### FRAMEWORK
- **ORACLE + Simulated Science Loop** — symbolic infrastructure + simulation-based world modeling. Two-layer system. (Body extraction degraded — re-run required for full architecture diagram.)
- "Cognition produces proposals (obligations, risks, narratives) → Governance produces receipts (attestations)" — the two-pole separation visible in the operator-narrated bullets at lines 102–200 (extraction-degraded, reconstructed from neighboring narrative).

### THEOREM_DRAFT
- (No formal theorems in the excerpt.)

### OPERATING_RULE
- *line 5–10 (paraphrased from extraction-readable parts)*: A claim entering the kernel MUST carry an attestation receipt; otherwise it is rejected. (This is the same rule encoded today in `tools/helen_say.py` and `tools/kernel_guard.sh`.)

### OPEN_QUESTION
- "If you meant a different 'Oracle' framework—e.g., Oracle ADF/JET/APEX—say so and I'll switch targets." (line 9–10) — disambiguation question that was answered downstream of this extract; without that answer, the artifact is ambiguous about which Oracle it discusses.
- Whether ORACLE TOWN V2 in this document is bit-identical to today's `oracle_town/kernel/` or a snapshot of an earlier draft is not establishable from the excerpt.

### PROMPT_PATTERN
- *line 1–4*: "Great. Here's a high-level blueprint for the ORACLE + Simulated Science Loop, combining your symbolic infrastructure with simulation-based world modeling." — canonical "blueprint-on-request" opener. Reusable as a template for any future skill-design conversation.

### RECEIPT_CANDIDATE
- The "law-bound, receipt-driven Truth Kernel" identification (line 7–9) is the strongest receipt candidate — it is the lineage proof for HELEN's `NO RECEIPT = NO CLAIM` invariant. A receipt artifact bridging this claim to the current `helen_os/governance/legoracle_gate_poc.py` would close a 4-month provenance gap.

## What should NOT be promoted to canon

- The unscoped reference to "{FRAMEWORK_ORACLE}" (line 6) — this is a placeholder substitution from a templated conversation; it is not a name to be canonicalized.
- Any architectural detail recovered from extraction-degraded sections — until re-extraction, treat as `RAW_NOTE` only.
- The implicit identity ORACLE TOWN V2 == HELEN_OS — they share lineage but are not bit-identical; promoting the equivalence would erase the version delta.

## Suggested future classifier rule

When the source filename contains BOTH a tag and an operator-meaningful spacing pattern (e.g. `#pluginWUL ORACLE` vs `#pluginWUL_ORACLE`), the classifier MUST:
1. Preserve the exact whitespace in `preserved_tag`.
2. Emit a `tag_family: WUL` field that groups related artifacts without merging them.
3. Surface a `version_signal` field if the filename contains numeric or chronological hints (`_001`, `_002`, dates, V2, V3).

This protects the operator's pre-HELEN chronological organization signal across the 80-file corpus.
