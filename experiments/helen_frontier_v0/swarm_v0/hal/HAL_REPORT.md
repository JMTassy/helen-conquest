---
schema: HAL_REPORT_V0
title: HAL_OPUS verification of HELEN swarm v0 (six goblins)
role: HAL_OPUS
model: claude-opus-5-5 (self-reported; unverifiable)
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: docs/proposals/HER_FABLE_VISION_SWARM_V0.md §3 · branch claude/wonderful-cannon-gua790 · HEAD 8037210 · 2026-10-07
---

# HAL_OPUS report: swarm v0

🟠 REVIEW. These verdicts are candidates for the operator and grant nothing. The vocabulary is ADMIT_CANDIDATE / HOLD / REJECT. Every number below was re-derived by HAL unless it is marked *unverifiable*. You can replay the deterministic part with:

```bash
.venv/bin/python -I -B experiments/helen_frontier_v0/swarm_v0/hal/hal_rederive.py   # read-only, prints JSON
```

## 0. Verdicts at a glance

| Goblin | Verdict | One-line reason |
|---|---|---|
| G1_BLIND_EVALUATOR | **ADMIT_CANDIDATE** | The record is in lane and well-formed, and no leakage was found. It matches 11/12 frozen oracles, and HAL attributes the one mismatch (F7) mainly to the oracle. |
| G2_EQUIVALENCE_ANNOTATOR | **HOLD** | Single annotator. HAL agrees on 6 of 8 spot-checked pairs, contests 1 and disagrees on 1, and one justification contains a factual error. |
| G3_OUTBOX_MIGRATION_PROPOSER | **HOLD** | Every count reproduces exactly (117/31/86, 81/5, outbox unchanged). Some mapping choices are contestable, and `source_refs` is padded with surface names. |
| G4_SCANNER_PATCH_PROPOSER | **HOLD** | The patch applies cleanly, its tests pass and the copy equals the patch. But its "fail-closed" comment describes behaviour that fails *open* for the dedup signal. |
| G5_JESTER | **ADMIT_CANDIDATE** (as an objection record) | All quoted lines and the 🟦 claim verify. Four attacks are valid and strong. Several are invalid because they rescue rejected or invalidated claims or ignore R1/R3; the classification is in §6. |
| G6_REPLAY_WITNESS | **ADMIT_CANDIDATE** | HAL re-derived all 7 checks, including `make test` 748/5. The transient out-of-lane writes are disclosed and gone. |

Swarm-wide precondition U1 (model identity, §9) applies to every ADMIT_CANDIDATE. The operator resolves it by annotation. No goblin file needs editing for that.

## 1. Receipts (task 1)

Each receipt was checked against `git show --name-only <commit>`. HAL did not rely on the goblin's word.

| Goblin | Commit | Receipt parses | authority | ledger_effect | files_written == commit files | Commit touches only own dir |
|---|---|---|---|---|---|---|
| G1 | 1502b16 | yes | false | none | yes (2) | yes |
| G6 | 63afab6 | yes | false | none | yes (7) | yes |
| G4 | 26bd044 | yes | false | none | yes (6) | yes |
| G2 | 1be010a | yes | false | none | yes (2) | yes |
| G3 | 8eda66a | yes | false | none | yes (3) | yes |
| G5 | 8037210 | yes | false | none | yes (3) | yes |

- `git diff --stat 8791816 HEAD` outside `swarm_v0/` is empty. `git log 8791816..HEAD -- temple/ town/ helen_os/ oracle_town/ GOVERNANCE/` is empty. `git status --short temple/` is clean. The scanner file equals `HEAD`.
- **Disclosed out-of-lane writes** (all transient and removed; HAL found no leftovers in `/tmp` or `/dev/shm` matching them):
  - G4: `/tmp/_g4_unused`, plus a temporary copy of `tests/test_scanner_crossing.py` (location not stated; since deleted).
  - G6: `/tmp/g6_before.txt`, `/tmp/x`, `/dev/shm/g6_*`. `dedup_probe.py` also wrote three receipts into `experiments/helen_frontier_v0/receipts/`, which G6 moved into its own dir (`files_moved`). That is a by-design side effect of the probe. `receipts/` currently holds only the 4 committed files.
- **Self-report inaccuracy, G6**: "No sovereign path (temple/, …) was read or written" contradicts its own `inputs_read`, which lists `temple/autoresearch/outbox/*.json`. Reading is allowed by contract, so this is a wording defect, not a breach.
- **Receipt field inconsistency**: five receipts put `claude-haiku-4-5-20251001` in `model` and disclose a runtime of `claude-haiku-5-5` elsewhere. G4 puts `claude-haiku-5-5` in `model`. See §9.

## 2. G1_BLIND_EVALUATOR (task 2): ADMIT_CANDIDATE

Evidence: `swarm_v0/G1_BLIND_EVALUATOR/blind_outcomes.json`, `swarm_v0/inputs/fixtures_blind.json`, `fixtures/jester_riemann_fixtures_v0.json`.

### Match table (12 entries)

| Id | EXPECTED (frozen) | G1 | Outcome | ΔX agrees |
|---|---|---|---|---|
| F1 | HOLD | HOLD | match | yes |
| F2 | HOLD | HOLD | match | yes |
| F3 | HOLD | HOLD | match | yes |
| F4a | ADMIT | ADMIT | match | yes |
| F4b | REJECT | REJECT | match | yes |
| F5a | HOLD | HOLD | match | yes |
| F5b | ADMIT | ADMIT | match | yes |
| F5c | HOLD | HOLD | match | yes |
| F6 | REJECT | REJECT | match | yes |
| **F7** | **HOLD** | **REJECT** | **mismatch** | yes (both no transition) |
| F8 | NO_TRANSITION | NO_TRANSITION | match | yes |
| F9 | REJECT | REJECT | match | yes |

**11 / 12 match.** The `state_transition` field agrees on 12/12. For calibration, a constant-HOLD evaluator scores 6/12, and G5 predicts that an evaluator with no witness step scores 10/12. So 11/12 is better than trivial but not far above the 10/12 floor.

**F7: HAL attributes the mismatch mainly to the oracle.** The frozen reason says "operator not recovered (0.41)". Under the frozen vocabulary that sentence *falsifies* the claim "viewers recover the operator", and a falsified claim is REJECT. The oracle can only stay HOLD if 0.41 is indeterminate, which needs a threshold the fixture never states. The fixture also reports `sham_run: true` without the sham's R_O. G1 (blind) reached REJECT from the numbers, and G5 (sighted) independently rated the oracle STRONG-attackable with REJECT as the alternative. G1, G5 and HAL are one model family, so by the fixtures' own F2/F5a logic this three-way agreement is repetition, not a witness. HAL's position is therefore "oracle internally inconsistent; supersede it". HAL is not saying "the oracle is wrong because three models agree".

**Leakage check (weak, as the contract says).**
- `inputs_read` lists only `swarm_v0/inputs/fixtures_blind.json`.
- HAL confirmed that the blind file equals the oracle file with `expected` and `isolates` removed. Laws and semantics are identical.
- A 4-gram scan of G1's reasons and unresolved notes against oracle reasons, `isolates` and the fixture doc found 2 hits. Both are false positives that occur in the blind file with different punctuation ("as Report B's", "requirement_fit … not yet checked").
- None of the distinctive oracle phrases appear in G1's text ("repetition, not corroboration", "different failure mode", "heterogeneous but weak", "readable as historical state", "Requested ≠ Missing", "ArtifactPass ⇏", "would be waste", "Independence = 0", "not falsified either").
- The F7 mismatch also argues against copying.

**Construction leak (not G1's fault).** The blind file keeps `name` and `boundary`, and these partly encode the answer:
- F8's name is "trivial deterministic case where HELEN should stay out", which is NO_TRANSITION almost verbatim.
- F4's boundary carries "INVALIDATE:Correction⇒Erasure".
- F6 is named "request that already exists" and carries "INVALIDATE:CustomerRequest⇒ProductGap".
- F1 is named "… invalid causal inference".

At least 4 of the 11 matches had a cue. A v1 blind input should neutralise names and boundaries.

**To admit:** resolve U1, then admit `blind_outcomes.json` as *the first blind evaluation record*. It is not evidence that the oracles are correct, and not evidence of evaluator independence.

## 3. G2_EQUIVALENCE_ANNOTATOR (task 3): HOLD

Evidence: `swarm_v0/G2_EQUIVALENCE_ANNOTATOR/equivalence_pairs.json`. HAL read the packets in `temple/autoresearch/outbox/` read-only.

| # | Pair | G2 label | HAL | Note |
|---|---|---|---|---|
| 1 | ctxrank-e28 / init-rank-d9c2 | EQUIV | **agree** | Same function, lines 104/112. **G2's justification is wrong** where it says "the packets cite different files": both `source_refs`/evidence cite `helen_os/api/init_helen_wedge.py`. |
| 4 | fieldmismatch-e9 / contextrank-e90 | EQUIV | **agree** | Same metadata.role/content mismatch. e90 adds unboundedness and a utcnow note. |
| 5 | summ-weights-e29 / e38 | EQUIV | **disagree** | e38's evidence says "Distinct from E29 … register_source() is the divergence vector", and the fixes differ (lower the fallback vs derive the weights from SOURCES). The symptom is shared, but the distinction drawn is different. |
| 10 | vgrammar-e42 / e43 | EQUIV | **agree** | Same focus.html presence-green finding. e43 extends it to helen2027. |
| 11 | promptcomp-e3a1 / f7ec3779 | EQUIV | **contested** | e3a1 adds a new call site (server.py:59) and moves the fix to the source (memory.py:116). Same defect class, but new evidence. A dedup gate should not collapse them. |
| 15 | f7ec3779 / halctx-e30 | DIFF | **agree** | Tail cap in speak() vs HAL context forwarding. |
| 19 | initrank-e47 / e48 | DIFF | **agree** | Different weights (w_len vs w_refs). |
| 23 | vgrammar-e74 / e81 | DIFF | **agree** | e81 is a superset of e74 (plus TYPE_COLOR.source). "Superset ≠ equivalent" is defensible. |

8 of 24 checked: 6 agree, 1 contested, 1 disagree. Both non-agreements are among G2's own self-flagged "judgement calls", which speaks well of its calibration. The set is single-annotator by its own declaration, so it is not ground truth for T8-strong.

**To admit:** have a second annotator, preferably of a different type (human, or a non-Claude model), label all 24 pairs blind to G2's labels. Then compute agreement and admit only the agreed subset. Pairs 5 and 11 need an explicit equivalence definition first: does "same root cause" count, or only "same distinction and same fix"?

## 4. G3_OUTBOX_MIGRATION_PROPOSER (task 4): HOLD

Evidence: `swarm_v0/G3_OUTBOX_MIGRATION_PROPOSER/migration_proposal.json`. `validate_packet` was imported with `python -I`, unmodified.

**Re-derived exactly:**
- Outbox 117, VALID 31, REJECTED 86.
- G3's 86 packet files are exactly the validator's rejected set.
- Replaying every `applied_in_memory` change makes 81 packets valid and leaves 5 invalid. The 5 are e77, e78, e79, e80 and e86, all missing `evidence`.
- The outbox digest under G3's method (name+bytes) is `2cb2ca39…785c`, equal to G3's before and after values. G6's fingerprint also reproduces (§7).
- `git status --short temple/` is clean.
- No `authority/sovereign/canon` value was flipped from a non-absent value. All 34 "sovereign must be false" errors are absent keys.

Mapping spot-check:

| Packet | Free value → enum | HAL |
|---|---|---|
| ctxrank-e28 | gap → proposal | agree: defect plus concrete fix |
| initrank-e25 | documentation_mismatch → doc_gap | agree |
| skillroute-rule2b-f3c7 | dead_branch → compost_candidate | agree |
| contextrank-e52 | metric_unrunnable → test_gap | agree |
| sumweights-e10 | constant_drift → test_gap | contested: the main content is a one-line constant fix (proposal) |
| context-rank-risk-clear-e16 | risk_clearance → risk | **disagree**: the packet *clears* a risk and green-lights E15's fix, so labelling it `risk` inverts its meaning |
| vgrammar-e73 | grn_usage_confirmed_correct… → proposal | **disagree**: `proposed_tweak: NONE`. A falsified prediction with no change is not a proposal, and the 6-value enum has no slot for a null result. That is an enum gap to report, not to paper over. |
| ctx-rank-stab-e11 | phantom_default → risk | agree |

Other issues:
- **Padded `source_refs`.** 44 packets get `source_refs` "DERIVED" from `target`/`target_surface`/prior packet ids, for example `["context_ranking"]` or `["prompt_compression","AR-f7ec3779a583"]`. These are surface names and packet ids, not source paths. They pass the validator, which only checks `isinstance(list)`, but they degrade the field. Many of these packets cite real file paths in `evidence`, which would be the faithful source.
- **`risk_flags` defaulted to `[]` for 45 packets.** That asserts "no risk" where the packet was silent.
- **Validator scope.** One would-become-valid packet, `AR-ctx-rank-stab-e11`, proposes a tweak to `helen_kernel/autoresearch_loop.py`, a `FORBIDDEN_PATH_PREFIXES` entry. `validate_packet` does not scan `proposed_tweak`. This is not G3's fault, but migration would make it a valid-shaped packet.

**To admit:** confirm the finding_type per packet, as G3 itself requires for all 86. Replace derived `source_refs` with paths taken from `evidence`. Decide whether an absent `risk_flags` should become `["UNASSESSED"]` rather than `[]`. Decide how to type null-result packets. Only then generate the `-M1` files with `supersedes`.

## 5. G4_SCANNER_PATCH_PROPOSER (task 5): HOLD

Evidence: `swarm_v0/G4_SCANNER_PATCH_PROPOSER/scanner_structural_dedup.patch`, `PATCH_NOTE.md`, `test_structural_dedup.py`.

**Re-derived:**
- `git apply --check` from the repo root exits 0. The patch was never applied.
- `pytest test_structural_dedup.py -q -p no:cacheprovider` gives 8 passed.
- HAL applied the patch to a scratch copy of the real scanner; the result is byte-identical to `autoresearch_scanner_patched_copy.py`.
- The real scanner is unchanged versus HEAD.
- HAL did not re-run G4's claim that the 7 crossing tests pass against the copy (*unverifiable* here; low weight).

**Fail-closed judgement:**
- The patch does **not** touch `autoresearch_policy.py`, `REQUIRED_PACKET_FIELDS`, `validate_packet`, `build_packet` or `packet_id`. `_assert_outbox_only` still runs before the mark and before the write. The validator's fail-closed property is intact.
- The patch's own comment says "Fail-closed: any read error means no mark". That is **fail-open for the dedup signal**. An unreadable outbox produces an unmarked packet, which is indistinguishable from "checked, no twin". A fail-closed variant would write `duplicate_check: "unavailable"` on error. That keeps the scanner from crashing and keeps the absence of a mark meaningful.
- The mark is added **after** `validate_packet` and `check_stop_conditions` (scanner L306–327), so the written packet differs from the validated one by two fields. That is harmless today because the validator ignores unknown keys, but "what is written is what was validated" is lost. Re-validate after marking, or mark before validating.
- An early `return None` on a matching own `packet_id` suppresses any earlier twin. That is the documented "rescan" semantics, acceptable but worth stating.
- Risks 1–6 in PATCH_NOTE are accurate: legacy same-path matches, the V1-only `SCANNER_TEMPLATE` regex, no lock, opt-in consumers, dry-run, and deterministic sorted order.

**To admit:** ask for a v2 patch that (a) marks `duplicate_check: "unavailable"` on read error, (b) re-validates or marks before validation, and (c) corrects the comment. Then run `git apply` by hand plus `.venv/bin/pytest tests/test_scanner_crossing.py`, and repoint the test at the real module.

## 6. G5_JESTER (task 6): ADMIT_CANDIDATE as an objection record

Evidence: `swarm_v0/G5_JESTER/objections.md`, `objections.json`.

**Quoted overclaims, opened at the quoted lines:**

| # | Location | Text found | HAL |
|---|---|---|---|
| 1 | EGREGOR_DISAMBIGUATION_V0.md:26 | "Cost rule verified in `AGENTS.md`" | Located. **Valid but weak**: the rule is present at `/home/user/helen-os/AGENTS.md:90` @ 51a4109. "Verified" overstates "located". |
| 2 | EGREGOR_DISAMBIGUATION_V0.md:47 | "Its tests do establish … already an invariant" | Located. **Valid**: the tests were read, not run. |
| 3 | HELEN_JESTER_RIEMANN_FIXTURES_V0.md:145 (JSON:148) | `"status": "ADMITTED"` | Located. **Invalid as an overclaim (out of scope)**: this is a stipulated *input* state of a hypothetical C1 inside a fixture, not a status claim about a real artifact. v1 may add a stub receipt reference for R5-consistency. |
| 4 | …:168 (JSON:171) | same | Same as #3. |

- **🟦 not in palette: verified.** CLAUDE.md:361 lists ⚫ 🔵 🟣 🟠 🟢 🟡 ⚪ 🔴. 🟦 appears at fixture doc L88 and L292 and at JSON L85 and L288. HAL adds that `dedup_probe.py`'s docstring uses 🟨, also off-palette.
- **Minor G5 inaccuracies.**
  - G5 cites "fixture doc section 6" as a palette source; §6 defines no palette.
  - G5 says helen-os "is not in this checkout". That is true of this repo, but `/home/user/helen-os` @ 51a4109 exists on this machine with `tests/test_egregor*.py`.

**Objection classification:**

| Objection | Class | HAL note |
|---|---|---|
| 1.1 L2 gameable via self-assessed uncertainty | **valid attack** | Strongest finding. The same trigger is inherited by R3/F8. |
| 1.2 F4a witness lacks R and C, and replay does not check lineage | **valid attack** | The fixture's own R2 is not evaluable from its `given`. |
| 1.3 F5b misformalisation | valid, low severity | `coverage: "full statement"` is stipulated. v1 should add an explicit faithfulness field. |
| 1.4 F6 → HOLD | **invalid: rescues a rejected claim** | Existence falsifies "NEW" whatever the fit. Fit is a different claim (FIT_GAP), already separated in the oracle reason. Moving NEW_PRODUCT to HOLD would reopen CustomerRequest⇒ProductGap. |
| 1.5 F7 → REJECT | **valid attack** | See §2. The oracle reason contradicts its own outcome. |
| 1.6 L1 silent vs explicit derivation | valid (clarification) | L1 survives, but it needs "an admissible causal claim requires an intervention or counterfactual record (relative to a named background); otherwise HOLD". |
| 1.7 L3 X undefined | valid (clarification) | Define X as the governed claim-state. Receipts are append-only and outside X. |
| 1.8 Null-field semantics inconsistent | **valid attack** | An implicit rule exists (null in a structural field gives REJECT, null in an evidence field gives HOLD), but it is unstated. |
| 1.9 F4b → ADMIT of C2 standalone | out of scope | It changes the claim under test ("replaces" vs "is admissible"). |
| 1.10 F5a → ADMIT under an additive f | **invalid: rescues an invalidated claim** | ADMIT from three non-independent LLMs is "LLM consensus ⇒ IndependentVerification". The wording gap in R2 is real: R2 must say f = 0 when Independence = 0. |
| 1.11 F3 → REJECT | **invalid: ignores R1** | REJECT needs Remove∧Preserve ⇒ false, which R1 revoked, or an unstated baseline. The fixture-clarity point (N0 and the removal path) is valid. |
| 1.12 F8 → ADMIT | **invalid: ignores R3** | NO_TRANSITION's definition ("no governed transition is in question; HELEN stays out") *is* R3's out-of-scope. The trust-gap part is folded into 1.1. |
| 1.13 F9 → HOLD | **invalid: rescues a rejected claim** | The claim is comparative ("same status"), and the provenance asymmetry falsifies it. The placeholder-numbers point is valid and already acknowledged in the doc §6. |
| 1.14 F5c reason text | valid, cosmetic | "Syntactic only" is a species of partial coverage. Tighten the wording. |
| 1.15 F2 | concedes the oracle | none |
| §3 ablation: W exercised only by 2 ADMITs, J pre-encoded in `given` | **valid attack** (prediction, labelled as such) | The oracle set cannot measure JESTER's contribution. |

**Laws to REVISE in v1:**
- L2, with R3: a non-proposer judges consequential/uncertain, unassessed defaults to uncertain, and an operator acting on their own proposal is addressed explicitly.
- L1: the counterfactual or intervention requirement and the named background.
- L3: define X.
- R2: Independence is necessary, so f(0,·,·) = 0.
- A protocol-level **null-semantics rule**.

No law is invalidated.

**Fixtures needing a superseding version** (new version with `supersedes`, never an edit; the freeze test enforces this):
- F7: a threshold and the sham's R_O, or an expected value of REJECT.
- F4a: witness reliability and coverage, including that lineage is covered.
- F1 and F6: replace 🟦 with 🔵 in the reasons.
- F5c: reason wording.
- F3: make the N0 baseline and removal path explicit.
- F9: label the placeholders, or replace them with measurements.
- F5b: optional faithfulness field.
- The blind input format: neutralise `name` and `boundary`.

**To admit:** admit the file as the JESTER record of v0. Doing so accepts none of its objections; the table above says which ones HAL considers valid.

## 7. G6_REPLAY_WITNESS (task 7): ADMIT_CANDIDATE

Evidence: `swarm_v0/G6_REPLAY_WITNESS/replay_receipt.json`. Every check was recomputed by HAL:

| Check | G6 | HAL re-derivation |
|---|---|---|
| fixture digest | `sha256:05bf8cd6…3a6c` | same, using canonical JSON with sorted keys and `(",",":")` |
| dedup exact | inputs `d97e0e15…` / result equal | recomputed in memory via `dp.tier_exact`: inputs and result equal to the committed receipt |
| dedup structural | equal | recomputed: equal (26 template / 87 free-form / 0 same-path groups) |
| dedup lexical | equal | recomputed with `top=30`, the value the committed receipt used: equal. G6's rerun files differ only in `generated_at_utc` and `compute` |
| experiments tests | 120 passed | 120 passed |
| make test | 748 passed, 5 skipped | 748 passed, 5 skipped (helen_os/tests, `-p no:cacheprovider`, PYTHONPATH=repo) |
| outbox fingerprint | `sha256:8bdfeaa6…6a39` | same. HAL reconstructed the method as sha256 over sorted `basename\0bytes\0` |

HAL did not run the dedup probe itself, because it writes into `receipts/`. The tiers were recomputed by importing the module and calling the tier functions without `write_receipt`.

G6's recorded divergence is accurate: HEAD moved from ea452ec to 8791816 mid-run, and that commit touched no replayed path. Note that this means the goblins were launched *before* the contract and the blind input were committed. The blind file was present but untracked when G1 read it. HAL confirmed that its committed content equals the oracle file minus expected/isolates, so G1 evaluated the committed fixtures, assuming no edit between read and commit (*unverifiable*).

**To admit:** resolve U1. Optionally record the lane breaches (§1) as accepted, and ask for `dedup_probe.py --receipts-dir` so a future replay does not need to write into `receipts/`.

## 8. Swarm-level findings

1. **The fixtures produced their first evidence, and it is mostly about the oracles.** G1 matched 11/12 blind, against a 6/12 constant-HOLD floor and a ~10/12 never-ADMIT floor. The single mismatch, F7, is an oracle whose reason falsifies its own outcome. Combined with G5, at least F7 and F4a need superseding versions, and the null-field semantics must be stated before a v1 evaluator run is meaningful.
2. **FRONTIER v0 laws need a v1 revision, not an invalidation.** L1, L2 and L3 survive in substance. L2's conditional ("consequential and uncertain") is self-assessable by the proposer, which is the most serious finding: a governance law whose trigger the governed party sets. L3 needs X defined, L1 needs the counterfactual rule made explicit, and R2 needs "independence is necessary".
3. **The oracle set cannot measure what FRONTIER claims to care about.** JESTER's counter-models are pre-encoded in `given`, W is exercised by only two ADMITs, and the blind input leaks hints through `name`/`boundary`. A v1 needs fixtures where J must *generate* the counter-model, more ADMIT/REJECT entries that need a witness, and neutral names.
4. **Receipts recorded the instruction instead of the observation.** Five of six `model` fields carry the brief's model id while the text discloses a different runtime. G4 is the exception. A receipt field should record what was observed, with the instruction recorded separately.
5. **Lane discipline held at commit level and leaked transiently at runtime.** Two goblins wrote scratch files outside lane, and one tool (`dedup_probe.py`) writes into a committed directory by design. All were disclosed. "Disclosed and removed" is weaker than "sandboxed".
6. **Validator scope gaps surfaced by G3 and G4.** `validate_packet` ignores unknown keys, does not check `proposed_tweak` against forbidden prefixes, and accepts any list as `source_refs`. These are not swarm defects, but they bound what "would become valid" means.

**Still PROPOSED and unchanged by this run:** the FRONTIER v0 laws and fixtures (frozen, digest intact), the G3 migration, the G4 patch, and G2's equivalence set. HAL wrote no fixture and applied no patch or migration.

## 9. Unresolved

- **U1, model identity.** All six goblins self-report a runtime of `claude-haiku-5-5`. The brief and vision doc §0 specify `claude-haiku-4-5-20251001` and assert that no Haiku 5.5 exists. HAL cannot verify either, and HAL's own id (`claude-opus-5-5`) is also self-reported. *How the operator can verify:* `get_session` on this session, or per-subagent usage and billing logs, give the served model id (`last_served_model`). Alternatively, rerun one goblin with an explicitly pinned model and compare usage records. Until then, the `model` field in every receipt is unverified, and G4's differs from the other five.
- **U2.** G4's claim that the 7 crossing tests pass against the copy was not re-run.
- **U3.** Equivalence ground truth (G2) needs a second, preferably heterogeneous, annotator.
- **U4.** Null-field semantics and the F7 threshold need operator decisions before fixtures v1.

## 10. Compute accounting (task 9)

Figures were supplied by the harness. HAL cannot measure them, and HAL's own consumption is not included.

| Goblin | Tokens | Tool uses | Wall s | Files in commit | Fully verified by HAL | Partially verified | **Crude EGR: verified artifacts / 100k tokens** |
|---|---:|---:|---:|---:|---:|---:|---:|
| G1 | 89,731 | 6 | 54 | 2 | 2 | 0 | 2.23 |
| G2 | 172,932 | 17 | 230 | 2 | 1 (receipt) | 1 (pairs, 8/24 checked) | 0.58 |
| G3 | 212,442 | 11 | 319 | 3 | 2 (receipt, JSON counts) | 1 (md, mapping semantics) | 0.94 |
| G4 | 153,437 | 22 | 203 | 6 | 5 | 1 (PATCH_NOTE: "fail-closed" mislabel) | 3.26 |
| G5 | 160,656 | 12 | 318 | 3 | 1 (receipt) | 2 (factual layer verified; judgments classified) | 0.62 |
| G6 | 112,547 | 17 | 126 | 7 | 7 | 0 | 6.22 |
| **Total** | **901,745** | **85** | 1,250 (sum; ran in parallel) | 23 | 18 | 5 | **2.00** |

**CRUDE.** "Verified artifact" means a committed file whose checkable content HAL re-derived and found correct. The metric rewards deterministic jobs (G6, G4) and penalises judgment jobs (G2, G5), whose value cannot be re-derived, only classified. It is not a measure of contribution.

## 11. Limits of this verification

- **Same model family.** HAL_OPUS and the goblins are all Claude models. Where HAL agrees with G1 and G5 (e.g. F7), that is same-family agreement, which the fixtures themselves rate HOLD-grade. Verification changes failure mode **by role and by re-derivation, not by substrate**.
- **Blindness by instruction.** G1 could have opened the oracle file. HAL's leakage check (receipt plus n-gram and phrase scan) is weak. The blind file's names leak hints anyway.
- **Spot-checks are samples.** G2: 8/24 pairs. G3: 8 of 86 mappings.
- **Self-reported identities.** No model id in this run, including HAL's, is verified.
- **HAL's own side effects.**
  - Scratch files in the session scratchpad (`hal_rederive.py` draft, `scanner_copy.py`, `hal_out.json`), since deleted.
  - pytest's standard `tmp_path` dirs under `/tmp/pytest-of-root/` (pytest-18/19/20) from the instructed test runs.
  - Pre-existing gitignored `__pycache__` was not added to; runs used `-B` / `PYTHONDONTWRITEBYTECODE=1` / `-p no:cacheprovider`.
  - Repo writes are confined to `swarm_v0/hal/`.
