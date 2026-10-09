---
schema: HELEN_PROPOSAL_V1
title: Preregistration — G2 embedding probe (EmbeddingGemma 2 on 24 annotated pairs)
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
prereg_digest: sha256:f0d9557bbd416a6320f48aff0cee4873d829eadd3893deb12b30316b8e70283d
blind_pairs_sha256: sha256:4126fcf6da580d9ea13d623654b4c1d27f098169fa8f60685ae2c50a15830419
origin: operator refinement 2026-10-09 ("preregister the G2 run"); fixed before any score exists
---

# Preregistration — G2 embedding probe

🔵 OBSERVED for the inputs, 🟣 CLAIM (PROPOSED) for the protocol. **No embedding has been computed.** The network policy still denies `huggingface.co`; this document exists so that, when the run becomes possible, nothing about model, preprocessing, similarity, scoring or adjudication can be chosen after seeing results.

Frozen by `experiments/helen_frontier_v0/tests/test_prereg_g2.py`: protocol JSON + scorer + blind-pair builder + runner, digest `sha256:f0d9557bbd416a6320f48aff0cee4873d829eadd3893deb12b30316b8e70283d`. A change is a new version with `supersedes`.

## 1. Fixed in advance

| Item | Value |
|---|---|
| Model | `google/embeddinggemma-2`, text-only (vision and audio encoders off), float32, CPU |
| Revision | hub `main` as of 2026-10-06; the runner records the resolved snapshot commit from the local cache path as an observed fact and checks `model.safetensors` is exactly 1 488 915 288 bytes (hub listing) |
| Prompt | `SentenceSimilarity` on both sides (symmetric task) |
| Dimension | 768 for the decision; 256 reported only |
| Similarity | cosine on L2-normalised vectors |
| Preprocessing | stored text, whitespace collapsed, field order summary > hypothesis > title > finding, no stripping |
| Separation statistic | AUC of EQUIVALENT vs DIFFERENT over the 12×12 pairings, ties 0.5, threshold-free |
| Disagreement rule | EQUIVALENT below the median of all 24 scores, or DIFFERENT above it |
| Pass/fail | none. The output is a per-pair table and a disagreement list |

## 2. Blinding

The runner reads only `prereg/pairs_blind.json` (ids and texts, sha256 `4126fcf6da580d9ea13d623654b4c1d27f098169fa8f60685ae2c50a15830419`). The test suite asserts that file carries no label, justification or snippet, and that the runner's source never names the labelled file. Labels are joined only by the scorer, after scores exist. No threshold is tuned on the 24 pairs because no threshold is used.

## 3. Adjudication

Consequential disagreements go to a party who did not annotate and did not run the embedding: the operator, a non-Claude model, or a human reader. The adjudicator sees both texts and the two positions, not G2's justification, and returns EQUIVALENT / DIFFERENT / UNDECIDABLE with one line. A disagreement is a signal to adjudicate, not proof that the dissenter is right. The useful outcome is a disagreement that survives blinded adjudication and exposes a failure the G2 oracle missed.

## 4. Receipt rule — observed versus asserted

Swarm v0 showed receipts copying the briefed model id into the `model` field while the runtime said otherwise. From this run on, a receipt has two blocks that never merge:

- **observed**: Python, torch and sentence-transformers versions; resolved snapshot path and commit; `model.safetensors` size and sha256; sha256 of the embedding arrays; sha256 of the blind input; wall time; CPU count; git HEAD.
- **asserted**: the configured model id, operator notes.
- **unverifiable**: `runtime_attestation` is marked UNVERIFIED. The host does not attest which weights executed. Saying so is the receipt's job.

## 5. Declared limits

- 24 pairs, one annotator, no agreement measure: an exploratory comparison, never a reliability claim.
- A different measurement path is not yet an independent witness: the embedding model may share training data, lineage or blind spots with the reasoning models. Provenance must be read before "independent" is written.
- G2 pair 1 has a factually wrong justification and pair 5 is disputed by HAL. Both stay in the set, flagged, so that the probe is not tuned by removing inconvenient pairs.

## 6. Run procedure, when the hosts are allowed

```
.venv-embed/bin/pip install torch sentence-transformers transformers      # isolated venv, gitignored
.venv-embed/bin/python -I experiments/helen_frontier_v0/prereg/embed_pairs_runner.py
.venv/bin/python -I experiments/helen_frontier_v0/prereg/score_pairs.py
```

Outputs: `scores.json` (runner, blind), `scored_report_768.json` and `scored_report_256.json` (scorer), then `adjudications.json` from the adjudicator. All under `prereg/`, all `authority: false`.
