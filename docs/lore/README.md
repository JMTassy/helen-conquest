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

---

## Frontmatter Conventions

Every lore file should declare in YAML frontmatter:

| Field | Required | Notes |
|---|---|---|
| `authority` | yes | Always `NON_SOVEREIGN` in this directory. |
| `canon` | yes | Always `NO_SHIP` in this directory. |
| `mode` | yes | One of the three modes above. |
| `literal_claims` | yes | `QUARANTINED` / `FICTIONALIZED` / `REJECTED_AS_FACT` |
| `source_type` | yes | `OLD_LECTURE_TRANSCRIPT`, `CONVERSATION`, `BOOK`, etc. |
| `segment` | yes | Short label for the source segment. |
| `approved_use` | yes | List of allowed downstream uses. |
| `forbidden_use` | yes | List of disallowed downstream uses. Machine-actionable. |
| `redline` | conditional | Required for `FUNNY_MYTH_WITH_REDLINE`. List of real-world tropes the file refuses to encode. |
| `cultural_risk` | conditional | Set to `HIGH` if the source touches a real living culture. |
| `risk` | conditional | Free-form risk tag (e.g. `conspiracy_drift_possible`). |
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
