---
schema: HELEN_PROPOSAL_V1
title: Scanner adaptation pilot — corpus manifest CANDIDATE V0
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
manifest_sha256: sha256:46111de2ae838750aa001672f02f8f4a30877ce7e5cb0d0934a22952d78bce73
origin: next bounded deliverable named by the operator's reviewing agent, 2026-10-09 · HOLD on the pilot stands
---

# Scanner pilot — corpus manifest candidate

🔵 OBSERVED: every path, blob id and sha256 below is read from git objects at the pinned revision `9c07f33`, never from the working tree. 🟣 CLAIM: the eligibility, grouping and split rules are proposed. **Not frozen.** Freezing is one operator act: copying `sha256:46111de2ae838750aa001672f02f8f4a30877ce7e5cb0d0934a22952d78bce73` into the pilot protocol. Until then it binds nothing.

Machine-readable: `experiments/helen_frontier_v0/scanner_pilot/corpus_manifest_candidate.json`, rebuilt identically by `build_corpus_manifest.py <revision>` (asserted by `tests/test_corpus_manifest.py`).

## 1. The three refinements, applied

| Refinement | How the manifest applies it |
|---|---|
| Sample independently of scanner predictions | The sampling frame is every eligible proposal document on `main`, not the 117 packets. Seed derived from the pinned revision hash, recorded. Packet appearance is computed **after** selection and stored as a covariate: 14 of the 40 selected documents appear in at least one packet, 26 do not. No stratification on flagged status was declared, so none was applied. |
| Separate source recovery from historical provenance | Each document carries its blob id and sha256 **at the pinned revision**. The bytes the scanner once read are marked `UNVERIFIED` on every document: packets carry no source digest. A pilot baseline runs the frozen scanner on these bytes; it does not reconstruct history. |
| Separate model identity from evaluation validity | Not a manifest concern. Noted here because the pilot's scorer is deterministic against independently fixed labels; unverified model weights block lineage claims, not the score. |

## 2. Rules and counts

| Rule | Effect at `9c07f33` |
|---|---|
| E1 `docs/proposals/*.md` tracked at revision | 72 |
| E2 exists on `origin/main` (nothing authored on this branch may enter) | 9 excluded, all of them this seat's own notes |
| E3 1 500 to 40 000 bytes | 0 excluded |
| E4 exact-content dedup | 0 duplicates found |
| E5 near-duplicate, char-5-gram Jaccard ≥ 0.80 | 0 found |
| **Eligible** | **63** |
| Selected (seed 8158772414391826527) | 40 |
| Development / holdout | 25 / 15 |
| Source groups among selected | 37; no group straddles the split |

Baseline scanner revision candidate: blob `c68109f0dd71fc75b44b42b6ba1e03283ccaa423` of `temple/autoresearch/autoresearch_scanner.py` at `9c07f33`. Recorded, not frozen.

## 3. Grouping rule and its weakness

Group = first two underscore tokens of the basename after stripping version and date suffixes, so `HELEN_OS_V2_INTERACTION_GRAMMAR` and `HELEN_OS_V2_VISUAL_CANON_LOCK` share a group. With 37 groups over 40 documents the rule rarely merges, which means it rarely protects against near-duplicate leakage across the split either. E5 found no near-duplicates at 0.80, so the exposure is small; a tighter family rule can be declared before freezing if the annotators see shared boilerplate.

## 4. Still unbound before the pilot can start

Labels (two independent annotators plus adjudicator, none of them Claude seats that touched the scanner), the AMBIGUOUS rule, the deterministic scorer, recall floor, precision guardrail, practical-gain threshold, non-inferiority margin, human-baseline reviewer, and the freeze itself. The holdout list is visible in this candidate; once frozen, the holdout labels must live where the proposer cannot read them, enforced by a test like the blind-fixture ones.

## 5. Decisions this unblocks

1. Accept or amend the five eligibility rules and the grouping rule.
2. Accept the seed source (revision hash) or supply a different recorded seed.
3. Freeze by recording the digest, or hold.
