# WULMATH_THEORY_BOUND_VERIFIER_V0

> **No compression without a theory of decompression.**

`A ⊬ B` with no theory and no named inference relation is not a
proposition. It is a KQML performative — an evocative token whose
meaning lives in the author's head, and whose divergence between two
readers nothing can detect. The repaired form binds both:

```
Γ ∪ {A} ⊬_R B
```

Shipped: `helen_os/kernel/constitution/wulmath_verifier.py`,
18 tests, gate probe 109. **Gate 109/109 CONSTITUTION_HELD**,
constitution suite **1344 passed**.

## The four obligations, as built

### O1 · every law names its theory Γ and its inference relation

**Γ is DERIVED, never asserted.** Each probe's theory is the set of
constitutional modules its body actually touches, read out of
`verify.py` by AST — including the one probe that reaches its module
through a dynamic `__import__("welding_1918")`. `verify.py` is
**parsed, never imported**, so there is no cycle.

The registry is **live**: it reads the file that registers the probe
that checks it, so adding a probe changes the count by construction.
The first version of probe 109 asserted `len(THEORIES) == 108` and
**broke the gate the moment it was registered** — a magic number where
an invariant belonged. It now asserts the invariant: every probe has a
non-empty Γ, and the count tracks the probe count.

### O1 · the two levels are kept apart

Conflating them is the first way a notation lies.

| level | operators | relates |
|---|---|---|
| **judgment** | `⊢` `⊬` | a theory to a formula |
| **connective** | `⇒` `⟺` `=` `≤` `≥` `⊊` `⊋` `≺` `⊥` `∈` `∉` `≠` | terms to terms |

`A ⇒ B` is a **formula**, not a judgment. Asserted with no turnstile it
never says whether it is derivable, denied, or definitional —
`E_FORMULA_WITHOUT_JUDGMENT`.

`⊬` is the complement of a preorder, so it is **not transitive** and
may not be chained. `·` is a **conjunction separator, not a chain
link**: `A ⊬ B · A ⊬ C` is two judgments.

Only two rules derive negative facts, and **both consume a positive
premise** — negative facts alone derive nothing:

```
R1   (a ⊢ b) ∧ (a ⊬ c)  ⟹  b ⊬ c
R2   (b ⊢ c) ∧ (a ⊬ c)  ⟹  a ⊬ b
```

### O2 · capabilities live in their native formalism

`Mint(κ) ⊢ UseCount(κ) ≤ 1` written as an arithmetic side condition
throws the enforcement away. As an affine judgment

```
Γ; κ:Cap ⊢ consume(κ)
```

the second consumption is not *counted and refused* — it has **no
derivation at all**: `E_NO_DERIVATION_FOR_SECOND_CONSUMPTION`.

### O3 · colour stays a non-authoritative projection

`semantic hue ⊥ effect bits`. Law 069 freezes the palette and sends
rival concepts to an orthogonal marker axis, so `ε = (dP,dA,dE)` gets
its **own** axis rather than overloading the hue. A rendering claiming
`ε ≠ 0` is refused; a hue without its mono label is refused.

### O4 · the verifier is mutation-sensitive

A verifier that emits silence for a healthy line *and* for an invalid
one is not a verifier. Eight sacrificial counterexamples, each of
which must be refused **by its own reason** — a mutation caught by the
wrong check is a coincidence, not a control:

| mutation | refused with |
|---|---|
| drop the theory | `E_NO_THEORY` |
| invent a theory | `E_UNKNOWN_THEORY` |
| unname the relation | `E_UNNAMED_RELATION` |
| claim an effect | `E_REPRESENTATION_CLAIMS_EFFECT` |
| strip the mono label | `E_STATE_BY_COLOUR_ALONE` |
| leave the palette | `E_HUE_OUT_OF_PALETTE` |
| unbind the witness | `E_NO_WITNESS` |
| forge the witness | `E_WITNESS_NOT_IN_GATE` |

Plus: bare `⊬` chain refused, transitive chain under a turnstile
allowed, false transitivity refused by name, second consumption
underivable. Positive control BOUND.

## What the verifier did to my own compression

Run against the 108 lines as published, **57 of 108 were refused**:

| | first run | after repair |
|---|---|---|
| bound | 51 | **108** |
| `E_FORMULA_WITHOUT_JUDGMENT` | 49 | 0 |
| `E_UNNAMED_RELATION` | 7 | 0 |
| `E_CHAINED_INTRANSITIVE_RELATION` | 1 | 0 |

**Nearly half the plate asserted formulas with no turnstile.** That is
the under-specification, measured rather than argued.

The repair is not cosmetic: the probe *holds*, so Γ derives the stated
property, and `Γ ⊢ φ` is the true form. 57 lines were rewritten into
judgment form; line 098's implicit `⊬` chain was made an explicit
conjunction.

**An intermediate false positive, recorded.** The first parser counted
every relation glyph in a line and flagged `A ⊬ B · A ⊬ C` as a chain
— including line 107, which had just been repaired correctly. The
verifier was wrong, not the line. Splitting on `·` before checking for
chains fixed it. A checker's first refusals must themselves be
audited.

## Non-deltas

Goblin 6's basis experiment was **not run**: deriving a smaller
generating set needs the positive `⊢` edges over the corpus, and those
have not been extracted — `derive()` exists and is tested on synthetic
pairs only. No claim is made that 108 is irreducible.

Mutation sensitivity is **scoped to the eight mutations enumerated**,
not to every possible malformation. Γ is the set of modules a probe
*touches*, which is a sound over-approximation of the theory it
depends on, not a minimal axiom set. The colour assignment remains a
reading; the v2 entropy result stands against part of it.

`authority=false · canon=false · ledger_effect=none`.
