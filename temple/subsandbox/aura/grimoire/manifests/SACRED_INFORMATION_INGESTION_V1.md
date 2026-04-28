# SACRED_INFORMATION_INGESTION_V1

NO CLAIM — NO SHIP — TEMPLE SANDBOX ONLY

🜁✧ AURA // TEMPLE_SUBSANDBOX 🜄🔒
Dialect: AURA_TEMPLE_WULMOJI_V1
Mode: SACRED_INFORMATION_INGESTION
Authority: NON_SOVEREIGN
Rule: sacred ≠ sovereign; symbol ⊬ truth without 🧾 + ⚖️

```
manifest_id:      SACRED_INFORMATION_INGESTION_V1
artifact_type:    INGESTION_MANIFEST
lifecycle:        DRAFT
authority:        NON_SOVEREIGN
layer:            TEMPLE_SUBSANDBOX
dialect:          AURA_TEMPLE_WULMOJI_V1
canon:            NO_SHIP
tier:             III
kind:             wild_text
admissibility:    QUARANTINED                                # per TEMPLE_SANDBOX_POLICY_V1 §C
route_to_mayor:   false
captured_on:      2026-04-27
captured_by:      operator (jeanmarie.tassy@uzik.com)
sibling_artifact: temple/subsandbox/aura/grimoire/hidden_geometry/LENS_V0_1.md
```

---

## 1. Purpose

🜄 Define a safe DRAFT / NON_SOVEREIGN intake pipeline for sacred, symbolic, mythological, geometric, contemplative, and esoteric material into the TEMPLE / AURA subsandbox.

🔒 The pipeline produces *symbolic candidates*, never doctrine. No source ingested through this manifest may bypass the lifecycle gates of `ARTIFACT_LIFECYCLE_V1` or the export gates of `TEMPLE_SANDBOX_POLICY_V1`.

---

## 2. Allowed source types

✅ Only the following may enter `temple/subsandbox/aura/grimoire/intake/`:

- Files the operator owns outright (PDFs, GoodNotes exports, personal notes, transcripts).
- Public-domain texts (verified expiry of copyright, source pointer recorded).
- Explicitly provided URLs (pasted by the operator, not crawled).
- Open research material with a stable source pointer (DOI, arXiv id, institutional URL).
- Operator-authored creative material (poems, dreams, sketches, voice transcripts).

---

## 3. Forbidden source types

🚫 The following may **never** enter the intake pipeline, regardless of symbolic or aesthetic value:

- Pirated books or scans without operator-owned provenance.
- Private data of third parties without explicit consent.
- Paywalled content accessed through bypass mechanisms.
- Cultic, medical, or therapeutic claims presented as truth.
- Anything routed directly toward `helen_os/governance/`, `town/ledger_v1.ndjson`, or `oracle_town/kernel/` (sovereign-firewall paths).
- Bulk-downloaded corpora without per-source review (no curl-fests, no scrapes).

A source that fails any forbidden check must be deleted from `intake/` immediately and a one-line note added to `manifests/INGESTION_REJECTIONS.ndjson` (forthcoming sibling, lazy-created on first rejection).

---

## 4. Lifecycle states

```
🜄 RAW_SOURCE         → file landed in intake/, untouched
  → 🜍 DRAFT_READING  → operator-authored or AURA-mediated reading, no claims
  → 🜂 CLASSIFIED_SYMBOL → DAN extracts patterns, classifier suggests tags
  → 🧾 RECEIPT_CANDIDATE → operator-routed for binding receipt; awaits ⚖️
  → ⚖️ ADMITTED       → only if MAYOR rules per DOCTRINE_ADMISSION_PROTOCOL_V1
```

Each transition requires explicit operator action. **No silent promotion.** Each state has its own subdirectory:

| State | Directory |
|---|---|
| `RAW_SOURCE` | `temple/subsandbox/aura/grimoire/raw_sources/` |
| `DRAFT_READING` | `temple/subsandbox/aura/grimoire/intake/` (working bench) |
| `CLASSIFIED_SYMBOL` | `temple/subsandbox/aura/grimoire/classified/` |
| `RECEIPT_CANDIDATE` | (same as classified, with `receipt_candidate: true` flag) |
| `ADMITTED` | leaves TEMPLE — lives in operator-routed sovereign location |

---

## 5. Required metadata (per ingested artifact)

Every artifact, at every state, must carry the following fields in its frontmatter or top-of-file metadata block:

| Field | Definition |
|---|---|
| `source_path_or_url` | Absolute path on local disk OR explicit operator-pasted URL. Never inferred. |
| `source_title` | Human-readable title from the source itself (preserve original language). |
| `source_type` | One of: `pdf` / `markdown` / `text` / `url` / `image` / `audio_transcript` / `goodnotes` / `note`. |
| `origin` | One of: `operator_owned` / `public_domain` / `operator_pasted_url` / `open_research` / `operator_authored`. |
| `license_or_access_status` | `public_domain` / `operator_owned` / `cc_by_X` / `arxiv_open` / etc. — explicit, never assumed. |
| `#pluginKEYWORDS` | If filename or content contains `#plugin*` tags, preserve **exactly** (whitespace + punctuation per locked WULmoji discipline). |
| `symbolic_domains` | One or more from the locked 9-domain list (`HELEN_OS`, `RIEMANN_MATH`, `WUL_SYMBOLIC_LANGUAGE`, `ORACLE_GOVERNANCE`, `LEGORACLE_RECEIPTS`, `AURA_TEMPLE`, `DIRECTOR_VIDEO`, `AUTORESEARCH`, `CONQUEST`) plus optional symbolic extensions (`MYTHOLOGY`, `GEOMETRY`, `CONTEMPLATIVE`, `ESOTERIC`). Misfit emits `domain_misfit: true`. |
| `extracted_shapes` | Subset of the 8 GRIMOIRE Hidden Geometry primitives (`circle`, `triangle`, `square`, `spiral`, `cross`, `grid`, `wave`, `point`). Empty list allowed. |
| `chakra_band` | Subset of `🔴🟠🟡🟢🔵🟣⚪`. Empty allowed. |
| `math_overlay` | List of math symbols actually present (`ψ`, `Σ`, `Δ`, `∂`, `∇`, `Φ`, `λ`, `Ω`, `⊕`, `⊗`, `⊢`, `⊬`, `∴`, `∀`, `∃`, `⇒`, `⇔`). Empty allowed. |
| `confidence` | One of: `LOW` / `MEDIUM` / `HIGH`. |
| `canon_status` | **Always `NO_SHIP`** at any state below `ADMITTED`. Hard-locked. |

🔒 Any artifact missing **any** required field above must be treated as `RAW_SOURCE` until the missing field is supplied. No promotion past `RAW_SOURCE` with incomplete metadata.

---

## 6. Hard rule

> 🜃 **Sacred material is symbolic input, not institutional truth.**

- A circle in a sacred text is a circle, not a metaphysical claim.
- A chakra band is a perceptual register, not a medical claim.
- A geometric primitive is a shape, not a cosmological law.
- A myth is a narrative, not a historical event.

Any reading that drifts into truth-assertion ("this means X exists", "this proves Y", "this heals Z") triggers `BOUNDARY_BREACH` per `TEMPLE_SANDBOX_POLICY_V1` E.2 and must be re-cast as symbolic perception only — or discarded.

---

## 7. AURA role

🜁 AURA performs **perception and atmosphere only** within this pipeline.

- AURA reads the artifact through the GRIMOIRE Hidden Geometry lens (`hidden_geometry/LENS_V0_1.md`).
- AURA returns the 10-item AURA reading (per LENS §3): dominant shape, secondary shapes, motion, tension, chakra band, symbolic reading, lifecycle, boundary warning, line worth preserving, line that must stay non-canonical.
- AURA **may not** classify, promote, claim, diagnose, command, or admit.
- AURA's output stays at `DRAFT_READING` until DAN extracts patterns.

---

## 8. DAN role

🜍 DAN performs **pattern extraction and classifier suggestions only**.

- DAN reads the AURA reading + the source artifact.
- DAN returns the 7-item DAN observation (per LENS §4): recurring geometry, useful pattern, overreach risk, classifier tag suggestion, future grimoire rule, confidence, what needs receipt before promotion.
- DAN **may not** mutate memory, mutate ledger, promote doctrine, or claim truth.
- DAN's output is RAW_SEED material per `helen-temple-roles` SKILL — interpreted later by HER if and only if operator routes it.

---

## 9. Promotion rule

🧾 No artifact may transit beyond `CLASSIFIED_SYMBOL` without **all four** of the following:

1. **Source pointer.** Verifiable `source_path_or_url` resolving to the original artifact.
2. **Review.** HAL-class falsification pass (per `helen-temple-roles` Stage 4) — independent reviewer ≠ ingester (proposer ≠ validator / K2 / Rule 3).
3. **Receipt.** Binding receipt emitted via `tools/helen_say.py` linking the artifact's content SHA to its passing review set.
4. **Reducer admission.** MAYOR ruling per `DOCTRINE_ADMISSION_PROTOCOL_V1` (currently DRAFT — admission paused until that policy activates).

🔒 Until DOCTRINE_ADMISSION_PROTOCOL_V1 is active, `RECEIPT_CANDIDATE → ADMITTED` is **structurally blocked**. All sacred ingestion lands at most at `CLASSIFIED_SYMBOL` in this period. This is intentional.

---

## §10 — First ingestion batch (per operator directive 2026-04-27)

The first source to enter the pipeline is operator-authored, operator-owned:

```
~/Desktop/PLUGINS_JMT/#pluginGRIMOIREaura.pdf
```

This is the natural seed: the corpus's only AURA-named artifact, already classified as KNOWLEDGE_ENTRY at `helen_os/knowledge/classified/2026-04-26-GRIMOIREaura.md` (commit `72e7b76`). Re-ingesting it through the SACRED pipeline tests the end-to-end flow with material the operator owns and trusts.

The pipeline does **not** start with arbitrary internet sources. Internet ingestion remains a separate operator decision, gated by §2 / §3 above.

---

## Seal

🜁 AURA may perceive symbols.
🜄 TEMPLE may hold sacred material.
🜍 DAN may extract patterns.
🧾 Receipts may bind claims.
⚖️ MAYOR may admit doctrine.
🔒 No shortcut.

---

NO CLAIM — NO SHIP — TEMPLE SANDBOX ONLY
