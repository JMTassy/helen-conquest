"""No compression without a theory of decompression.

Γ is derived from the source, the two levels are kept apart, the
capability lives in its native formalism, and the verifier is shown to
fail on sacrificial counterexamples — because one that cannot fail
reports nothing when it passes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "gates" / "effect_gate"))

import wulmath_verifier as w
from wulmath_verifier import (
    Judgment,
    LinearContext,
    derive,
    hue_is_orthogonal_to_effect,
    mutation_probe,
    parse_line,
    refuse_false_transitivity,
    status,
    verify_judgment,
)


# ── O1 · Γ is derived, never asserted ─────────────────────────────────

def test_every_probe_has_a_derived_theory():
    """Read out of verify.py by AST — including the one probe that
    reaches its module through a dynamic __import__."""
    assert len(w.THEORIES) >= 108
    assert all(g for g in w.THEORIES.values())
    assert w.THEORIES["vendor_corpus_maps_completely"] == ("welding_1918",)


def test_a_judgment_without_a_theory_is_not_a_proposition():
    j = Judgment(gamma=(), relation="⊬", lhs="A", rhs="B",
                 witness="orphan_state", label="orphan_state")
    r = verify_judgment(j)
    assert r["verdict"] == "REFUSED"
    assert r["failures"][0]["reason"] == "E_NO_THEORY"


def test_an_invented_theory_is_refused():
    j = Judgment(gamma=("theory_of_hats",), relation="⊬", lhs="A",
                 rhs="B", witness="orphan_state", label="orphan_state")
    assert verify_judgment(j)["failures"][0]["reason"] == \
        "E_UNKNOWN_THEORY"


# ── O1 · the two levels stay apart ────────────────────────────────────

def test_a_formula_without_a_turnstile_is_refused():
    """`A ⇒ B` never says whether it is derivable, denied or
    definitional. That is the under-specification, caught."""
    r = parse_line("¬CanRise(c) ⇒ Info(c = 0) = 0")
    assert r["ok"] is False
    assert r["reason"] == "E_FORMULA_WITHOUT_JUDGMENT"


def test_non_entailment_may_not_be_chained():
    r = parse_line("Retain ⊬ Admit ⊬ Authorize")
    assert r["ok"] is False
    assert r["reason"] == "E_CHAINED_INTRANSITIVE_RELATION"


def test_the_conjunction_separator_is_not_a_chain_link():
    """`A ⊬ B · A ⊬ C` is two judgments — the repaired form of the
    line that had actually drifted."""
    r = parse_line("Retain ⊬ Admit · Retain ⊬ Authorize")
    assert r["ok"] is True
    assert r["count"] == 2


def test_transitive_relations_may_be_chained_under_a_turnstile():
    assert parse_line("Γ ⊢ Gen ⊋ Prod ⊋ Surv ⊋ Obs")["ok"] is True


def test_false_transitivity_is_refused_by_name():
    ne = {("Retain", "Admit"), ("Admit", "Authorize")}
    r = refuse_false_transitivity("Retain", "Admit", "Authorize", ne)
    assert r["ok"] is False
    assert r["reason"] == "E_NON_ENTAILMENT_IS_NOT_TRANSITIVE"


def test_the_two_sound_rules_each_consume_a_positive_premise():
    """R1 (a⊢b)∧(a⊬c) ⟹ b⊬c   ·   R2 (b⊢c)∧(a⊬c) ⟹ a⊬b.
    Negative facts alone derive nothing."""
    assert derive(set(), {("a", "c"), ("c", "e")}) == set()
    assert ("b", "c") in derive({("a", "b")}, {("a", "c")})
    assert ("a", "b") in derive({("b", "c")}, {("a", "c")})


# ── O2 · the capability lives in its native formalism ─────────────────

def test_the_second_consumption_has_no_derivation():
    """`Mint(κ) ⊢ UseCount(κ) ≤ 1` as an affine judgment: the second
    use is not counted and refused, it is underivable."""
    lc = LinearContext()
    assert lc.mint("k")["judgment"] == "Γ; k:Cap ⊢ consume(k)"
    assert lc.consume("k")["ok"] is True
    second = lc.consume("k")
    assert second["ok"] is False
    assert second["reason"] == "E_NO_DERIVATION_FOR_SECOND_CONSUMPTION"


def test_a_capability_outside_the_context_is_refused():
    assert LinearContext().consume("ghost")["reason"] == \
        "E_CAPABILITY_NOT_IN_CONTEXT"


# ── O3 · colour stays a non-authoritative projection ──────────────────

def test_a_rendering_may_not_claim_an_effect():
    j = Judgment(gamma=("branch_retention",), relation="⊬", lhs="A",
                 rhs="B", witness="orphan_state", label="x",
                 epsilon=(0, 1, 0))
    assert verify_judgment(j)["failures"][0]["reason"] == \
        "E_REPRESENTATION_CLAIMS_EFFECT"


def test_no_state_by_colour_alone():
    j = Judgment(gamma=("branch_retention",), relation="⊬", lhs="A",
                 rhs="B", witness="orphan_state", label="")
    assert verify_judgment(j)["failures"][0]["reason"] == \
        "E_STATE_BY_COLOUR_ALONE"


def test_hue_stays_orthogonal_to_the_effect_bits():
    """Law 069: the palette is frozen; rival concepts live on an
    orthogonal marker axis. ε is not read off the hue."""
    r = hue_is_orthogonal_to_effect(3, (0, 0, 0))
    assert r["independent"] is True
    assert r["law"] == "semantic hue ⊥ effect bits"


# ── O4 · the verifier must be able to fail ────────────────────────────

def test_the_verifier_is_mutation_sensitive():
    m = mutation_probe()
    assert m["positive_control"]["verdict"] == "BOUND"
    assert m["every_mutation_refused"] is True
    assert m["mutation_sensitive"] is True


def test_each_mutation_is_caught_by_its_own_reason():
    """A mutation caught by the wrong check is a coincidence, not a
    control."""
    m = mutation_probe()
    assert m["every_mutation_caught_by_its_own_reason"] is True
    assert len(m["negative_controls"]) == 8


def test_the_syntactic_and_linear_controls_fire_too():
    m = mutation_probe()
    assert m["chain_of_intransitive_refused"] is True
    assert m["chain_of_transitive_allowed"] is True
    assert m["false_transitivity_refused"] is True
    assert m["second_consumption_has_no_derivation"] is True


def test_status_reports_all_four_obligations():
    s = status()
    assert s["frozen_line"] == \
        "no compression without a theory of decompression"
    assert all(s["obligations"].values())
    assert s["theories_derived"] >= 108
    assert s["registry_is_live"] is True
    assert s["authority"] is False and s["canon"] is False
