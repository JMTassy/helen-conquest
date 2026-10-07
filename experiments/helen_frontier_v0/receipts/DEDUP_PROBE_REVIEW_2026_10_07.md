---
schema: HELEN_PROPOSAL_V1
title: Dedup probe — manual review of the cheap tiers on the real outbox — 2026-10-07
authority: false
sovereign: false
canon: false
ledger_effect: none
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: operator GO on "one real test of the cost rule"; branch claude/wonderful-cannon-gua790
---

# Dedup probe — manual review (seat judgement, operator confirmation pending)

🔵 OBSERVED for every number below (receipts named inline). The judgement column is this seat's reading of the snippets, not an operator verdict.

## 1. What ran, what did not

| Tier | Mechanism | Ran | Receipt |
|---|---|---|---|
| exact | sha256 of normalised text | yes | `dedup_probe_exact_20261007T155312Z.json` |
| structural | parse scanner template, group by source path | yes | `dedup_probe_structural_20261007T155312Z.json` |
| lexical | word-Jaccard ∨ char-5-gram Jaccard | yes | `dedup_probe_lexical_20261007T155313Z.json` |
| embedding | google/embeddinggemma-2, text-only 270M, CPU float32 | **no** | — |

The embedding tier did not run. The environment's network policy answers 403 to CONNECT for `huggingface.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co` and `download.pytorch.org`. PyPI is reachable, so the dependencies could be installed but not the weights. The tier is wired and will run unchanged once those hosts are allowed. Nothing was sent to any third-party inference endpoint.

## 2. Numbers

| Quantity | Value |
|---|---|
| Packets in outbox | 117 |
| Packets with a usable text field (summary → hypothesis → title) | 113 |
| Packets without text (all four are `AR-sandbox-vgrammar-e77…e80`) | 4 |
| Exact duplicate groups | 0 |
| Template-shaped packets ("Scanner findings in <path>: signals=[…]") | 26 |
| Distinct source paths among them | 26 |
| Same path scanned twice (real duplicate at template level) | 0 |
| Free-form packets | 87 |
| Lexical pairs compared | 6 328 |
| Lexical pairs ≥ 0.5 / 0.6 / 0.7 / 0.8 | 295 / 138 / 61 / 0 |
| Of the 61 pairs ≥ 0.7: template × template / mixed / free × free | 61 / 0 / 0 |
| Wall time, all three tiers | < 1 s on 4 CPU |

## 3. Manual review of the lexical top 30

All thirty pairs have the shape *"Scanner findings in docs/proposals/A.md: signals=[…]"* × *"Scanner findings in docs/proposals/B.md: signals=[…]"* with A ≠ B. Word-Jaccard sits at 0.75–0.78 because the template contributes most of the tokens; the only distinguishing tokens are the two file paths, which differ in every pair.

Seat judgement: **0 / 30 are duplicates of a distinction. 30 / 30 are template collisions.** Extending the same rule to all 61 pairs ≥ 0.7 gives the same class for every pair (verified by classification, not by reading each one).

## 4. What this measures, and only that

- The lexical tier, on this corpus, measures **the template, not the distinction**. Its precision for "duplicate distinction" at ≥ 0.7 is 0 / 61.
- The structural tier is the weakest mechanism that answers the actual question here, and it answers it exactly: 0 rescans of the same path. It costs a regex.
- Report B's column "189 duplicates" from fixture F9 has, for this outbox, a first real value: **0** at exact and structural level. Whether semantic near-duplicates exist among the 87 free-form packets is **unmeasured**: no free-form pair reaches 0.7 lexically, and the embedding tier did not run.
- An embedding model will also see the template. If it is ever run here, the structural tier must run first and the embedding tier must be scored on the 87 free-form packets, or on template packets with the boilerplate stripped. Otherwise it will reproduce the 61 false candidates at a higher cost and call it semantics.

## 5. Cost-rule reading (AGENTS.md@helen-os 51a4109f)

NewEvidence: yes (first measured dedup numbers). DecisionRelevant: yes (whether to spend on an embedding tier). Unresolved: yes. Testable: yes. NotDuplicate: yes. All five conjuncts held and the whole pass still cost under one second of CPU and zero model calls. The expensive discriminator was not needed to reach the first real distinction: *lexical similarity ≠ duplicate distinction on templated packets*. That is the cost rule working in the direction it was written for.

## 6. Not established

- Any semantic duplicate among free-form packets.
- Any number for the embedding tier (latency, precision, agreement at 768 vs 256 dims).
- Whether EmbeddingGemma 2's quality claims hold on this corpus.

## 7. Operator decisions

1. Allow `huggingface.co` and `cdn-lfs.huggingface.co` (and `download.pytorch.org` for the lean CPU wheel) in the environment's network settings, then `dedup_probe.py --tier embedding` runs as written.
2. Whether the structural tier should become a fail-closed check in the autoresearch scanner itself (it would need to live in `temple/autoresearch/`, outside this seat's lane).
