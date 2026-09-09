# -*- coding: utf-8 -*-
"""WULMATH_THEORY_BOUND_VERIFIER_V0
authority=false · claim=NO_CLAIM · non-sovereign

The frozen line:

    NO COMPRESSION WITHOUT A THEORY OF DECOMPRESSION.

`A ⊬ B` with no theory and no named inference relation is not a
proposition — it is a KQML performative, an evocative token whose
meaning lives in the author's head. The repaired form binds both:

    Γ ∪ {A} ⊬_R B

This module holds the four obligations:

  O1  every compressed law names its theory Γ and inference relation
  O2  every effect/capability law is expressed in its native
      formalism where one exists (linearity for capabilities)
  O3  every colour stays a NON-AUTHORITATIVE semantic projection —
      hue ⊥ effect bits, and ε = (dP,dA,dE) lives on its own axis
  O4  the verifier is MUTATION-SENSITIVE: it must fail on sacrificial
      counterexamples, or its silence carries no information

Γ is DERIVED, never asserted: each probe's theory is the set of
constitutional modules its body actually touches, read out of
verify.py by AST. verify.py is parsed, never imported, so there is no
import cycle.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_VERIFY = os.path.join(_HERE, "verify.py")


# ── the named inference relations, with their declared properties ────
#
# `⊬` is the complement of a preorder. Complements of transitive
# relations are generically NOT transitive; that is the default, not a
# subtlety. Chaining it is therefore ill-formed.

# Two LEVELS, and conflating them is the first way a notation lies.
#
#   JUDGMENT relations relate a theory to a formula:  Γ ⊢ φ , Γ ⊬ φ
#   CONNECTIVES live INSIDE φ and relate terms to terms.
#
# `A ⇒ B` is not a judgment; it is a formula, and a formula asserted
# without a turnstile never says whether it is derivable, refused, or
# definitional. That is exactly the under-specification this module
# exists to catch.

JUDGMENT_RELATIONS = {
    "⊢": {"name": "entails", "transitive": True, "reflexive": True},
    "⊬": {"name": "does_not_entail", "transitive": False,
          "reflexive": False},
}

CONNECTIVES = {
    "⊊": {"name": "proper_subset", "transitive": True},
    "⊋": {"name": "proper_superset", "transitive": True},
    "≺": {"name": "strictly_precedes", "transitive": True},
    "≤": {"name": "at_most", "transitive": True},
    "≥": {"name": "at_least", "transitive": True},
    "⇒": {"name": "implies", "transitive": True},
    "⟺": {"name": "iff", "transitive": True},
    "=": {"name": "equals", "transitive": True},
    "≠": {"name": "differs", "transitive": False},
    "⊥": {"name": "orthogonal_to", "transitive": False},
    "∈": {"name": "member_of", "transitive": False},
    "∉": {"name": "not_member_of", "transitive": False},
}

RELATIONS = {**JUDGMENT_RELATIONS, **CONNECTIVES}
CHAINABLE = frozenset(op for op, p in RELATIONS.items()
                      if p.get("transitive"))

# `·` separates independent conjuncts. It is NOT a chain link:
# `A ⊬ B · A ⊬ C` is two judgments, not `A ⊬ B ⊬ C`.
CONJUNCT_SEP = "·"


# ── Γ: derived from the source, not declared ─────────────────────────

def derive_theories(path=_VERIFY) -> dict:
    """probe name -> the constitutional modules its body touches.

    Read by AST from verify.py's source. A probe that touches no
    module has no derivable theory and MUST be refused by O1 — that
    refusal is the obligation working, not a gap in the reader."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_probes")
    alias = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Import):
            for a in n.names:
                alias[a.asname or a.name] = a.name
    closures = {n.name: n for n in fn.body
                if isinstance(n, ast.FunctionDef)}

    def touched(node, depth=0):
        seen = set()
        for m in ast.walk(node):
            if isinstance(m, ast.Name) and m.id in alias:
                seen.add(alias[m.id])
            elif isinstance(m, ast.Attribute) and \
                    isinstance(m.value, ast.Name) and m.value.id in alias:
                seen.add(alias[m.value.id])
            # dynamic import: the module name is a literal in the AST
            elif isinstance(m, ast.Call) and isinstance(m.func, ast.Name) \
                    and m.func.id == "__import__" and m.args \
                    and isinstance(m.args[0], ast.Constant):
                seen.add(m.args[0].value)
        if depth < 2:
            for m in ast.walk(node):
                if isinstance(m, ast.Call) and isinstance(m.func, ast.Name) \
                        and m.func.id in closures \
                        and m.func.id != getattr(node, "name", None):
                    seen |= touched(closures[m.func.id], depth + 1)
        return seen

    out = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_probe":
            a = n.args[2]
            body = closures[a.id] if isinstance(a, ast.Name) else a
            out[n.args[0].value] = tuple(sorted(touched(body)))
    return out


THEORIES = derive_theories()
KNOWN_THEORIES = frozenset(m for g in THEORIES.values() for m in g)


# ── the judgment ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Judgment:
    """Γ ∪ {lhs} ⊬_R rhs, with its witness and its effect tuple."""
    gamma: tuple
    relation: str
    lhs: str
    rhs: str
    witness: str = ""
    epsilon: tuple = (0, 0, 0)      # (dP, dA, dE)
    hue: int = 0
    label: str = ""                  # the mono text label (O3)

    def render(self) -> str:
        g = ",".join(self.gamma) if self.gamma else "∅"
        return f"Γ[{g}] ∪ {{{self.lhs}}} {self.relation} {self.rhs}"


def refusal(code, detail=""):
    return {"ok": False, "reason": code, "detail": detail}


OK = {"ok": True}


# ── O1 · the theory and the relation must both be named ──────────────

def check_theory_named(j: Judgment) -> dict:
    if not j.gamma:
        return refusal("E_NO_THEORY",
                       "a non-entailment with no Γ is not a proposition")
    unknown = [m for m in j.gamma if m not in KNOWN_THEORIES]
    if unknown:
        return refusal("E_UNKNOWN_THEORY", ",".join(unknown))
    return OK


def check_relation_named(j: Judgment) -> dict:
    if j.relation not in RELATIONS:
        return refusal("E_UNNAMED_RELATION", j.relation)
    return OK


# ── O1 · chaining is legal only for transitive relations ─────────────

def parse_line(expr: str) -> dict:
    """Split on `·` into independent conjuncts, then check each one.

    A conjunct is well-formed iff it carries exactly one judgment
    relation, or a legal chain of ONE transitive connective under a
    judgment. A conjunct with no turnstile at all is a bare formula
    and is refused: it never says whether it is derivable or denied."""
    conjuncts = [c.strip() for c in expr.split(CONJUNCT_SEP) if c.strip()]
    if not conjuncts:
        return refusal("E_EMPTY_LINE", expr)
    out = []
    for c in conjuncts:
        judg = [ch for ch in c if ch in JUDGMENT_RELATIONS]
        conn = [ch for ch in c if ch in CONNECTIVES]
        if not judg:
            return refusal("E_FORMULA_WITHOUT_JUDGMENT",
                           f"'{c}' asserts a formula with no turnstile; "
                           f"wrap it as Γ ⊢ (…) or Γ ⊬ (…)")
        if len(judg) > 1:
            if len(set(judg)) == 1 and judg[0] in CHAINABLE:
                pass                      # a ⊢ b ⊢ c is legal
            else:
                bad = next(j for j in judg if j not in CHAINABLE)
                return refusal("E_CHAINED_INTRANSITIVE_RELATION",
                               f"'{c}': {bad} is not transitive; write "
                               f"the conjunction explicitly with ·")
        bad_conn = [k for k in set(conn)
                    if conn.count(k) > 1 and k not in CHAINABLE]
        if bad_conn:
            return refusal("E_CHAINED_INTRANSITIVE_CONNECTIVE",
                           f"'{c}': {bad_conn[0]}")
        out.append({"conjunct": c, "judgment": judg[0],
                    "connectives": sorted(set(conn))})
    return {"ok": True, "conjuncts": out, "count": len(out)}


# ── O1 · the only two sound rules for negative facts ─────────────────
#
# Both consume a POSITIVE premise. Non-entailment has no closure of
# its own — it is the complement of a preorder, and negative facts
# carry no composition law.

def derive(entails: set, not_entails: set) -> set:
    """R1  (a ⊢ b) ∧ (a ⊬ c) ⟹ (b ⊬ c)
       R2  (b ⊢ c) ∧ (a ⊬ c) ⟹ (a ⊬ b)"""
    out = set()
    for (a, c) in not_entails:
        for (x, y) in entails:
            if x == a:                       # R1
                out.add((y, c))
            if y == c:                       # R2
                out.add((a, x))
    return {p for p in out if p not in not_entails and p[0] != p[1]}


def refuse_false_transitivity(a, b, c, not_entails) -> dict:
    """The unsound step the bare chain invites."""
    if (a, b) in not_entails and (b, c) in not_entails:
        return refusal("E_NON_ENTAILMENT_IS_NOT_TRANSITIVE",
                       f"{a} ⊬ {b} and {b} ⊬ {c} do not give {a} ⊬ {c}")
    return OK


# ── O2 · capabilities live in their native formalism (linearity) ─────
#
# `Mint(κ) ⊢ UseCount(κ) ≤ 1` written as an arithmetic side condition
# throws the enforcement away. As an affine judgment the second
# consumption has no derivation at all.

@dataclass
class LinearContext:
    """Γ; κ:Cap ⊢ consume(κ) — and no derivation for a second use."""
    caps: dict = field(default_factory=dict)

    def mint(self, kappa) -> dict:
        if kappa in self.caps:
            return refusal("E_CAPABILITY_ALREADY_MINTED", kappa)
        self.caps[kappa] = "LIVE"
        return {"ok": True, "judgment": f"Γ; {kappa}:Cap ⊢ consume({kappa})"}

    def consume(self, kappa) -> dict:
        st = self.caps.get(kappa)
        if st is None:
            return refusal("E_CAPABILITY_NOT_IN_CONTEXT", kappa)
        if st == "SPENT":
            return refusal("E_NO_DERIVATION_FOR_SECOND_CONSUMPTION",
                           f"{kappa} was consumed; affine context "
                           f"offers no rule to consume it again")
        self.caps[kappa] = "SPENT"
        return {"ok": True, "consumed": kappa}


# ── O3 · colour is a non-authoritative projection ────────────────────
#
# hue ⊥ ε. The hue carries semantic function; the effect tuple lives on
# its own marker axis. A compressed line is a REPRESENTATION, so its
# ε is (0,0,0) — a line claiming otherwise is refused.

def check_colour_non_authoritative(j: Judgment) -> dict:
    if tuple(j.epsilon) != (0, 0, 0):
        return refusal("E_REPRESENTATION_CLAIMS_EFFECT",
                       f"ε={tuple(j.epsilon)}; a rendering may not "
                       f"move P, A or E")
    if not j.label:
        return refusal("E_STATE_BY_COLOUR_ALONE",
                       "hue without its mono label carries state on a "
                       "channel that can be stripped")
    if not (0 <= j.hue <= 7):
        return refusal("E_HUE_OUT_OF_PALETTE", str(j.hue))
    return OK


def hue_is_orthogonal_to_effect(hue, epsilon) -> dict:
    """Law 069: the palette is frozen and refuses redefinition; rival
    concepts live on an ORTHOGONAL marker axis. Deriving ε from hue —
    or hue from ε — collapses the two axes into one."""
    return {"ok": True, "hue": hue, "epsilon": tuple(epsilon),
            "independent": True,
            "law": "semantic hue ⊥ effect bits"}


# ── the witness ──────────────────────────────────────────────────────

def check_witness_bound(j: Judgment) -> dict:
    if not j.witness:
        return refusal("E_NO_WITNESS", "unrun recipe: "
                       "FABRICATED_UNTIL_WITNESSED")
    if j.witness not in THEORIES:
        return refusal("E_WITNESS_NOT_IN_GATE", j.witness)
    return OK


CHECKS = (("theory", check_theory_named),
          ("relation", check_relation_named),
          ("colour", check_colour_non_authoritative),
          ("witness", check_witness_bound))


def verify_judgment(j: Judgment) -> dict:
    failures = []
    for name, fn in CHECKS:
        r = fn(j)
        if not r["ok"]:
            failures.append({"check": name, **r})
    return {"judgment": j.render(),
            "verdict": "BOUND" if not failures else "REFUSED",
            "failures": failures}


# ── O4 · mutation sensitivity ────────────────────────────────────────
#
# A verifier that emits silence for a healthy line AND for an invalid
# one is not a verifier. Every mutation below is a SACRIFICIAL
# counterexample on a disposable judgment; each must be REFUSED, and
# each must be refused for ITS OWN reason — a mutation caught by the
# wrong check is a coincidence, not a control.

def _healthy() -> Judgment:
    return Judgment(
        gamma=("branch_retention",),
        relation="⊬",
        lhs="Retain",
        rhs="Admit",
        witness="an_alternative_may_survive_without_being_true_or_permitted",
        epsilon=(0, 0, 0),
        hue=2,
        label="an_alternative_may_survive_without_being_true_or_permitted")


MUTATIONS = {
    "drop_the_theory":
        (lambda j: Judgment(**{**j.__dict__, "gamma": ()}),
         "E_NO_THEORY"),
    "invent_a_theory":
        (lambda j: Judgment(**{**j.__dict__, "gamma": ("theory_of_hats",)}),
         "E_UNKNOWN_THEORY"),
    "unname_the_relation":
        (lambda j: Judgment(**{**j.__dict__, "relation": "~~>"}),
         "E_UNNAMED_RELATION"),
    "claim_an_effect":
        (lambda j: Judgment(**{**j.__dict__, "epsilon": (0, 1, 0)}),
         "E_REPRESENTATION_CLAIMS_EFFECT"),
    "strip_the_mono_label":
        (lambda j: Judgment(**{**j.__dict__, "label": ""}),
         "E_STATE_BY_COLOUR_ALONE"),
    "leave_the_palette":
        (lambda j: Judgment(**{**j.__dict__, "hue": 9}),
         "E_HUE_OUT_OF_PALETTE"),
    "unbind_the_witness":
        (lambda j: Judgment(**{**j.__dict__, "witness": ""}),
         "E_NO_WITNESS"),
    "forge_the_witness":
        (lambda j: Judgment(**{**j.__dict__, "witness": "probe_that_never_ran"}),
         "E_WITNESS_NOT_IN_GATE"),
}


def mutation_probe() -> dict:
    """Positive control + negative controls + per-mutation specificity."""
    good = _healthy()
    base = verify_judgment(good)
    rows = {}
    for name, (mutate, expected) in MUTATIONS.items():
        r = verify_judgment(mutate(good))
        codes = [f["reason"] for f in r["failures"]]
        rows[name] = {"verdict": r["verdict"],
                      "codes": codes,
                      "caught_by_its_own_reason": expected in codes}
    # syntactic mutations, checked by the chain parser
    chain_bad = parse_line("Retain ⊬ Admit ⊬ Authorize")
    chain_ok = parse_line("Γ ⊢ Gen ⊋ Prod ⊋ Surv ⊋ Obs")
    single_ok = parse_line("Retain ⊬ Admit")
    # the unsound derivation the bare chain invites
    ne = {("Retain", "Admit"), ("Admit", "Authorize")}
    false_trans = refuse_false_transitivity("Retain", "Admit",
                                            "Authorize", ne)
    # linearity: the second consumption has no derivation
    lc = LinearContext()
    lc.mint("k1")
    first = lc.consume("k1")
    second = lc.consume("k1")

    all_refused = all(v["verdict"] == "REFUSED" for v in rows.values())
    all_specific = all(v["caught_by_its_own_reason"]
                       for v in rows.values())
    return {
        "positive_control": {"verdict": base["verdict"],
                             "expected": "BOUND"},
        "negative_controls": rows,
        "every_mutation_refused": all_refused,
        "every_mutation_caught_by_its_own_reason": all_specific,
        "chain_of_intransitive_refused":
            chain_bad["ok"] is False and
            chain_bad["reason"] == "E_CHAINED_INTRANSITIVE_RELATION",
        "chain_of_transitive_allowed": chain_ok["ok"] is True,
        "single_relation_allowed": single_ok["ok"] is True,
        "false_transitivity_refused":
            false_trans["ok"] is False and
            false_trans["reason"] == "E_NON_ENTAILMENT_IS_NOT_TRANSITIVE",
        "second_consumption_has_no_derivation":
            first["ok"] is True and second["ok"] is False and
            second["reason"] == "E_NO_DERIVATION_FOR_SECOND_CONSUMPTION",
        "mutation_sensitive": (base["verdict"] == "BOUND" and
                               all_refused and all_specific),
        "law": "a verifier that cannot fail reports nothing when it "
               "passes",
        "scope": "sensitivity to the mutations enumerated here — not "
                 "to every possible malformation",
    }


# ── binding the whole corpus ─────────────────────────────────────────

def bind_corpus(lines) -> dict:
    """lines: (index, probe_name, wulmath, hue). Every line is bound
    to its DERIVED theory and its witness, then verified."""
    bound, refused = [], []
    for idx, name, expr, hue in lines:
        chain = parse_line(expr)
        gamma = THEORIES.get(name, ())
        ops = [c for c in expr if c in RELATIONS]
        j = Judgment(gamma=gamma,
                     relation=ops[0] if ops else "",
                     lhs=f"line_{idx:03d}", rhs="", witness=name,
                     epsilon=(0, 0, 0), hue=hue, label=name)
        r = verify_judgment(j)
        entry = {"index": idx, "probe": name, "gamma": list(gamma),
                 "relation": j.relation, "verdict": r["verdict"],
                 "failures": r["failures"], "chain": chain}
        (bound if r["verdict"] == "BOUND" and chain["ok"]
         else refused).append(entry)
    return {"total": len(lines), "bound": len(bound),
            "refused": len(refused),
            "refused_lines": [{"index": e["index"], "probe": e["probe"],
                               "why": ([f["reason"] for f in e["failures"]]
                                       or [e["chain"].get("reason")])}
                              for e in refused],
            "distinct_theories": len({m for e in bound
                                      for m in e["gamma"]}),
            "verdict": "ALL_LINES_THEORY_BOUND" if not refused
                       else "UNBOUND_LINES_PRESENT"}


def status() -> dict:
    return {"module": "WULMATH_THEORY_BOUND_VERIFIER_V0",
            "authority": False, "canon": False, "ledger_effect": "none",
            "frozen_line": "no compression without a theory of "
                           "decompression",
            "obligations": {
                "O1_theory_and_relation_named": True,
                "O2_native_formalism_for_capabilities": True,
                "O3_colour_non_authoritative_hue_orthogonal_to_effect":
                    True,
                "O4_mutation_sensitive": mutation_probe()[
                    "mutation_sensitive"]},
            "theories_derived": len(THEORIES),
            "registry_is_live": True,
            "note": "the registry reads verify.py, so it includes the "
                    "probe that checks it — adding a probe changes "
                    "this count by construction",
            "distinct_theories": len(KNOWN_THEORIES),
            "relations": {k: v["name"] for k, v in RELATIONS.items()}}
