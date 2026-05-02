# LNOS Lore — `docs/lore/`

This directory holds **derivative worldbuilding lore** for the LNOS Metaverse,
sourced from external material (lecture transcripts, conversations, recovered
audio) that contains literal claims the project does **not** ingest as fact.

Every file in this directory is:

- `authority: NON_SOVEREIGN`
- `canon: NO_SHIP`
- `ledger_effect: NONE`

These files are storytelling substrate. They do not mutate the HELEN ledger.
They are not promoted to canon. They are not auto-indexed by sovereign
processes. They are read by lore designers, quest writers, and faction
designers — never by the kernel as evidence.

> **Cross-reference:** this directory is conceptually adjacent to
> `temple/subsandbox/aura/raw_samples/`, which holds *raw* TEMPLE/AURA
> captures. `docs/lore/` holds the *derivative work* generated from such
> captures (or other sources). When a file here cites a transcript in its
> Section "Verbatim Source," that transcript may also live as a pure raw
> sample under `temple/subsandbox/aura/raw_samples/` for provenance.

---

## Containment Modes

Each lore file declares a `mode:` in its frontmatter. The mode tells you how
literal claims from the source are handled. Three modes are in use:

### `TEMPLE_AURA_DAN_GOBLIN`

The serious classification mode for material with high factual-risk.

- **Literal claims:** `QUARANTINED` — preserved verbatim in a fenced section,
  marked as not-ingested-as-truth, but not transformed.
- **Use when:** the source contains paranormal, cosmological, or symbolic
  claims that may have value as raw material later but should not be acted
  on now.
- **Example:** `LNOS_COLLAPSE_MYTH_SOURCE_001.md`,
  `LNOS_SOURCE_002_ANGEL_FLEETS_AND_SPHINX_VAULT.md`

### `FUNNY_MYTH`

Comedic-distance containment. Literal claims are *transmuted* into absurd
fiction so they can no longer be lifted as fact.

- **Literal claims:** `FICTIONALIZED` — reframed as overtly comedic
  metaverse mythology (e.g., "feathers are the oldest Bluetooth device,"
  "ROCK-OS boot time: 400 years").
- **Use when:** the source contains motifs worth keeping but the literal
  reading is harmful or absurd. The comedy is the firewall.
- **Core rule:** *the myth may be funny; the system must remain honest.*
- **Example:** `LNOS_SOURCE_003_BIRDLINE_AND_SERPENT_DISTRACTION.md`,
  `LNOS_SOURCE_005_SHUTU_STONE_COMPUTERS_AND_PYRAMID_WARS.md`

### `FUNNY_MYTH_WITH_REDLINE`

`FUNNY_MYTH` plus an explicit `redline:` array of real-world tropes the file
refuses to encode under any framing.

- **Literal claims:** `REJECTED_AS_FACT` — stronger than fictionalization.
  The claim is repudiated *in addition to* being transmuted.
- **Use when:** the source touches a real-world ethnic group, religion,
  family, or institution in a way that risks encoding a bigoted or
  conspiratorial trope (antisemitism, racial pseudoscience, named-family
  conspiracy, etc.). Comedy alone is insufficient; an explicit non-encoding
  list is required.
- **Example:** `LNOS_SOURCE_006_HOUSE_RAKHAM_SHIELD_ACCOUNTANTS.md`

### `FUNNY_MYTH_WITH_REVERENCE`

`FUNNY_MYTH` plus explicit respect for living religious or spiritual
traditions referenced by the source.

- **Literal claims:** `FICTIONALIZED` — but the comedic reframing must
  land on the *archetype* (the Lost Student's ego deflation, résumé
  inflation, donkey-vs-golden-horse), **never on the real traditions
  themselves.**
- **Use when:** the source touches Jesus / Buddha / Indigenous practice
  / Reiki / Qigong / Tibetan or Indian mysticism / etc. — living
  traditions that belong to real communities and deserve respect, not
  rejection.
- **Distinction from REDLINE:** REDLINE is for source material that is
  itself bigoted or conspiratorial (the source is the problem); REVERENCE
  is for source material that touches real traditions in a way that
  could be appropriative if not handled carefully (the *handling* is the
  problem).
- **Required field:** `religious_risk` and/or `cultural_religious_risk`
  set to `HIGH`.
- **Example:** `LNOS_SOURCE_007_MISSING_YEARS_PATH.md`,
  `LNOS_META_001_BIRTH_OF_A_STARSEED.md`

### `SCIENCE_INSPIRED_MYTH_DESIGN`

Used when the source is a working scientist or peer-reviewed paper
describing real phenomena. The scientific framing is preserved as
**design inspiration** for game mechanics; the source's clinical or
pharmacological framing is **not** treated as actionable advice.

- **Literal claims:** `SOURCE_DEPENDENT` — neuroscience/biology claims
  attributed to a credentialed source are credible *as that domain*, but
  not as metaphysics, treatment protocol, or recommendation.
- **Use when:** designing metaverse mechanics inspired by real science
  (perception research, neuropharmacology, etc.) where the temptation
  is to overreach into "this proves my mythology" or "this justifies
  self-treatment."
- **Required field:** `medical_safety_risk` set to `HIGH` if the source
  describes substances, treatments, or clinical phenomena.
- **Forbidden uses always include:** medical advice, drug recommendation,
  psychiatric protocol, "psychedelics reveal objective metaphysical
  truth" claims.
- **Core boundary:** *Hyper-real does not mean verified. Intensity does
  not mean truth.*
- **Example:** `LNOS_SOURCE_008_REALITY_RENDERER_AND_AKASHIC_MIRROR.md`

### `SCIENCE_INSPIRED_FUNNY_MYTH`

Hybrid of `SCIENCE_INSPIRED_MYTH_DESIGN` and `FUNNY_MYTH`. Use when the
source is scientific *and* the safest reframing layers comedic distance
on top of the science (e.g. neuropharmacology of identity dissolution
reframed as "the chair has opinions").

- **Literal claims:** `SOURCE_DEPENDENT` (same as the science-inspired
  base mode).
- **Use when:** the underlying science describes phenomena strange enough
  that a straight scientific reframing would still risk being read as
  endorsement or instruction. Comedy keeps the player at the right
  distance.
- **Required fields:** same as `SCIENCE_INSPIRED_MYTH_DESIGN`
  (`medical_safety_risk: HIGH` when applicable) plus the same comedic
  guarantee as `FUNNY_MYTH` (the absurdity is the firewall against
  literalism).
- **Core boundary:** the comedy lands on the **player's relationship to
  the experience**, never on the people who actually live with the
  underlying conditions or substances.
- **Example:** `LNOS_SOURCE_009_CLAUSTRUM_GATE_AND_OBJECTHOOD_COLLAPSE.md`

### `FUNNY_MYTH_SENSORY_DESIGN`

`FUNNY_MYTH` specialized for sources that make **physics-style claims**
about sensory phenomena (specific frequencies, vortexes, geomagnetic
sites, healing tones, etc.). The mechanic is designed as **gameplay
sensory input**, not as physics or medicine.

- **Literal claims:** `FICTIONALIZED` — the source's claimed frequency
  / location / effect becomes a fictional in-game calibration target
  with no physical or therapeutic claim.
- **Use when:** the source asserts that a specific Hz value, a specific
  location, or a specific sensory ritual produces a specific
  physical/spiritual result. These claims drift easily into
  pseudoscience (frequency-healing marketing, vortex tourism,
  paranormal-proof claims) and the mode forbids that drift explicitly.
- **Recommended `risk:` value:** `frequency_claim_drift` (or analogous
  for non-frequency sources).
- **Required mitigations:** an explicit "HELEN Boundary" section
  declaring that the sensory mechanic *triggers gameplay, does not
  prove physics, does not heal by doctrine, does not bypass receipts.*
- **Example:** `LNOS_SOURCE_010_525_TONE_AND_RED_SPIRAL_FRACTURE.md`

---

## File-Naming Convention — `LNOS_SOURCE_NNN` vs `LNOS_META_NNN`

Two artifact families live in this directory:

### `LNOS_SOURCE_NNN_<TITLE>.md` — source-derived files

A file generated from external source material (lecture transcripts,
podcasts, books, conversations). Its `source_type` is something like
`OLD_LECTURE_TRANSCRIPT` or `PODCAST_OR_LECTURE_TRANSCRIPT`. Numbering
is sequential and stable.

| # | File |
|---|---|
| 001 | `LNOS_COLLAPSE_MYTH_SOURCE_001.md` |
| 002 | `LNOS_SOURCE_002_ANGEL_FLEETS_AND_SPHINX_VAULT.md` |
| 003 | `LNOS_SOURCE_003_BIRDLINE_AND_SERPENT_DISTRACTION.md` |
| 004 | `LNOS_SOURCE_004_FEATHER_ANTENNA_AND_SILENT_COORDINATION.md` |
| 005 | `LNOS_SOURCE_005_SHUTU_STONE_COMPUTERS_AND_PYRAMID_WARS.md` |
| 006 | `LNOS_SOURCE_006_HOUSE_RAKHAM_SHIELD_ACCOUNTANTS.md` |
| 007 | `LNOS_SOURCE_007_MISSING_YEARS_PATH.md` |
| 008 | `LNOS_SOURCE_008_REALITY_RENDERER_AND_AKASHIC_MIRROR.md` |
| 009 | `LNOS_SOURCE_009_CLAUSTRUM_GATE_AND_OBJECTHOOD_COLLAPSE.md` |
| 010 | `LNOS_SOURCE_010_525_TONE_AND_RED_SPIRAL_FRACTURE.md` |
| 011 | `LNOS_SOURCE_011_SEDONA_MAGNETOMETER_AND_FIELD_SCIENCE.md` |
| 012 | `LNOS_SOURCE_012_OUTFLOW_RELEASE_AND_CANYON_RITUAL.md` |

### `LNOS_META_NNN_<TITLE>.md` — synthesis artifacts

A file that synthesizes existing source files into something larger
(origin myth, onboarding cinematic, story bible, character archetype
catalog). Its `source_type` is `ORIGINAL_SYNTHESIS` and it includes a
`synthesizes:` array listing the source files it draws from.

| # | File |
|---|---|
| 001 | `LNOS_META_001_BIRTH_OF_A_STARSEED.md` |

### `LNOS_AUTORESEARCH_NNN_<TITLE>.md` — autoresearch protocols

A file that defines a **loop** — a repeatable READ → ABSTRACT →
PROTOTYPE → EVALUATE → KEEP/DISCARD discipline applied to a knowledge
domain. Its `source_type` is `AUTORESEARCH_PROTOCOL`. It typically
includes:

- mechanism-to-mechanic mapping (external knowledge → playable mechanic)
- numbered experiments with hypotheses, prototypes, and metrics
- explicit keep/discard rules per experiment
- a P1 evaluator specification
- a HELEN role architecture (AURA / HER / DAN / HAL / MAYOR / LEDGER)

| # | File |
|---|---|
| 001 | `LNOS_AUTORESEARCH_001_REALITY_RENDERER_LOOP.md` |

The split between SOURCE / META / AUTORESEARCH keeps numbering stable
within each family and makes it explicit which files are *derived*
(SOURCE), which are *synthesized* (META), and which are *protocol
specifications* (AUTORESEARCH).

---

## Frontmatter Conventions

Every lore file should declare in YAML frontmatter:

| Field | Required | Notes |
|---|---|---|
| `authority` | yes | Always `NON_SOVEREIGN` in this directory. |
| `canon` | yes | Always `NO_SHIP` in this directory. |
| `mode` | yes | One of the seven modes above. |
| `literal_claims` | yes | `QUARANTINED` / `FICTIONALIZED` / `REJECTED_AS_FACT` / `SOURCE_DEPENDENT` / `PARTIALLY_SEPARATED` |
| `source_type` | yes | `OLD_LECTURE_TRANSCRIPT`, `PODCAST_OR_LECTURE_TRANSCRIPT`, `CONVERSATION`, `BOOK`, `ORIGINAL_SYNTHESIS`, etc. |
| `segment` | yes | Short label for the source segment. |
| `approved_use` | yes | List of allowed downstream uses. |
| `forbidden_use` | yes | List of disallowed downstream uses. Machine-actionable. |
| `redline` | conditional | Required for `FUNNY_MYTH_WITH_REDLINE`. List of real-world tropes the file refuses to encode. |
| `cultural_risk` | conditional | Set to `HIGH` if the source touches a real living culture. |
| `religious_risk` | conditional | Set to `HIGH` for `FUNNY_MYTH_WITH_REVERENCE` files touching real religious traditions. |
| `cultural_religious_risk` | conditional | Set to `HIGH` for files touching both cultural and religious traditions of a real community. |
| `medical_safety_risk` | conditional | Set to `HIGH` for files in either `SCIENCE_INSPIRED_*` mode that describe substances, treatments, or clinical phenomena. |
| `risk` | conditional | Free-form risk tag (e.g. `conspiracy_drift_possible`). |
| `inspiration` | conditional | List of phenomenological / experiential inspirations (used by META files and SCIENCE_INSPIRED_* files). |
| `synthesizes` | conditional | Required for META files. List of source files this file synthesizes. |
| `companion_file` | conditional | If this file is a companion to another, name the partner file. |
| `extends` | conditional | List of files this file extends or builds on (analogous to `synthesizes` for derivative-not-synthesis cases). |
| `real_science_layer` / `science_layer` | conditional | Required when `literal_claims: PARTIALLY_SEPARATED`. List of source claims that hold up under scrutiny and may be cited as design substrate. |
| `quarantined_layer` | conditional | Required when `literal_claims: PARTIALLY_SEPARATED`. List of source claims that must never be cited as fact. |
| `references_published_neuroscience` / `references_published_geophysics` / etc. | conditional | Boolean flag set to `true` when the file references published scientific literature, even if inline citations are not preserved. |
| `inline_citations_preserved` | conditional | Boolean. Set to `false` when a citation-bearing source paste lost its inline citation markers. |
| `artifact_family` | conditional | `SOURCE` / `META` / `AUTORESEARCH`. Defaults to SOURCE if not specified; required for AUTORESEARCH files for clarity. |
| `ledger_effect` | yes | Always `NONE` in this directory. |
| `captured_on` | yes | ISO date. |
| `session_id` | yes | Free-form session identifier. |

The `forbidden_use` and `redline` arrays are not decorative. They are
intended to be **machine-actionable** by any future indexer or admission
process: a downstream agent that attempts to lift content from a file in a
way that violates these lists must reject the operation.

---

## File Conventions

Each file should contain:

1. **YAML frontmatter** (see above)
2. **Title** — `# LNOS Source NNN — <Short Title>`
3. **Containment banner** — `NO CLAIM — NO SHIP — TEMPLE SANDBOX ONLY` plus
   the mode line
4. **Quarantine paragraph** — explicit statement of what is not-ingested and
   what would constitute a boundary violation
5. **Numbered sections** — classification → LNOS translation → mechanics →
   factions → quest prototypes → safety boundary → core doctrine
6. **Verbatim source transcript section** — last numbered section, fenced as
   blockquote, with `(NO CLAIM — ...)` provenance footer

If a verbatim source is not yet available, reserve the section with a note
saying so (see Section 8 of `LNOS_SOURCE_002_ANGEL_FLEETS_AND_SPHINX_VAULT.md`
for the pattern).

---

## What This Directory Is NOT

- **Not the AURA raw-sample home.** That's `temple/subsandbox/aura/raw_samples/`.
  Files here are derivative; files there are raw captures.
- **Not a doctrine index.** Anything that becomes governance doctrine moves
  through the proper sovereign path (`tools/helen_say.py` → kernel → ledger),
  not through this directory.
- **Not auto-promoted.** No process should read files here and treat their
  content as fact, evidence, or canon. The frontmatter is the contract.
- **Not a dumping ground.** Each file represents a deliberate classification
  decision and a deliberate transmutation. Adding a file means adopting the
  conventions above.

---

## Multi-Voice Convention

LNOS lore frequently uses a four-voice chorus of in-fiction characters named
**HAL / DAN / HER / AURA**. These are *fictional characters within LNOS lore*
and have **no connection** to the real HAL — the Layer-1 kernel gate enforced
by `helen_os/governance/` and described in the project root `CLAUDE.md`.

When using these voices in lore, include a parenthetical disambiguation note,
e.g.:

> *(HAL/DAN/HER/AURA above are fictional characters within LNOS lore. The
> real HAL is the Layer-1 kernel gate. Don't confuse them.)*

This prevents the failure mode where governance becomes vibes.

---

## Story Bible Direction

The lore stack in this directory is converging on a coherent **comic
cosmic metaverse mythology** built around:

- **Collapse overlap** — the world isn't ending, it's becoming visible at
  more than one layer at once
- **Sky fleets** — what religion remembered as angels were once
  patrol/transmission architectures
- **Stone computers** — pyramids as multifunctional servers; the Shutu
  guild as ancient backend engineers
- **Birdline sensors** — birds and feathers as living grid-state
  indicators
- **False-signal traps** — the Serpent Halls glittering with partial truth
- **Archive descent** — three-receipt vault gates, lawful-access
  bureaucracy, House Rakham
- **Reality renderer** — perception as constructed model; the Akashic
  Atrium as the place where players learn this directly
- **Receipt-based truth** — no claim without a receipt; no canon without
  integration

### Tone

- cosmic funny myth
- mystical but self-aware
- grand but governance-bounded
- weird but playable
- symbolic but honest

### Core rule

> **The myth may be funny.**
> **The system must remain honest.**

### Best current tagline

> **No receipt, no pyramid.**

### Synthesis tagline (from META_001)

> **Born of stars.**
> **Bound by receipts.**

### Working title options

- *LNOS: The Collapse Has a Queue*
- *LNOS: Stone Servers of the Birdline*
- *LNOS: No Receipt, No Pyramid*
- *LNOS: The Shield Accountants*
- *LNOS: Compile the Mountain*
- *LNOS: The Feather Has Bad Wi-Fi*

### How the source files fit together

| File | What it teaches |
|---|---|
| `LNOS_COLLAPSE_MYTH_SOURCE_001` | Knowledge becomes visible during overlap |
| `LNOS_SOURCE_002_ANGEL_FLEETS_AND_SPHINX_VAULT` | Knowledge misremembered as rescue |
| `LNOS_SOURCE_003_BIRDLINE_AND_SERPENT_DISTRACTION` | Knowledge read from nature, distinguished from spectacle |
| `LNOS_SOURCE_004_FEATHER_ANTENNA_AND_SILENT_COORDINATION` | Knowledge shared via signs, not orders |
| `LNOS_SOURCE_005_SHUTU_STONE_COMPUTERS_AND_PYRAMID_WARS` | Knowledge stored in architecture |
| `LNOS_SOURCE_006_HOUSE_RAKHAM_SHIELD_ACCOUNTANTS` | Knowledge blocked by bureaucracy |
| `LNOS_SOURCE_007_MISSING_YEARS_PATH` | Knowledge must be trained before being used |
| `LNOS_SOURCE_008_REALITY_RENDERER_AND_AKASHIC_MIRROR` | Reality is constructed; integration is gated |
| `LNOS_SOURCE_009_CLAUSTRUM_GATE_AND_OBJECTHOOD_COLLAPSE` | Identity is a renderer mode; receipts survive the trip |
| `LNOS_SOURCE_010_525_TONE_AND_RED_SPIRAL_FRACTURE` | Some doors open with tone, not key — but tone unlocks moments, not canon |
| `LNOS_SOURCE_011_SEDONA_MAGNETOMETER_AND_FIELD_SCIENCE` | Real geophysics + local interpretation + fictional mechanic — three layers, kept separate |
| `LNOS_SOURCE_012_OUTFLOW_RELEASE_AND_CANYON_RITUAL` | A symbolic-burden gameplay ritual; the canyon may exhale, the ledger still asks what was measured |
| `LNOS_META_001_BIRTH_OF_A_STARSEED` | Synthesis: how a player becomes eligible for any of the above |
| `LNOS_AUTORESEARCH_001_REALITY_RENDERER_LOOP` | The autoresearch protocol that governs how Reality Renderer mechanics are scoped, prototyped, evaluated, and kept-or-discarded |
