# MATH_TO_DIRECTOR_BRIDGE

Optional, non-blocking. The Director skill works without this. This file
documents how `math_to_face_phase0` outputs can feed directorial decisions
**deterministically** — so the same brief + same primes produce the same
shot list, every time.

## The bridge in one diagram

```
brief (text)              primes (e.g. [2,3,5,7,11,13,17])
     │                              │
     │                              ▼
     │                     math_to_face_phase0
     │                       (Phase 0 receipts)
     │                              │
     │           ┌──────────────────┴──────────────────┐
     │           │                  │                   │
     │     operator_hash      z_T_summary       spectral_summary
     │           │                  │                   │
     │     prompt seed       arc / pacing       shot count / length
     │           │                  │                   │
     ▼           ▼                  ▼                   ▼
              HELEN DIRECTOR (this skill)
                       │
                       ▼
            DIRECTOR DECISION + 3 STEPS + RECEIPT
```

## Concrete bindings (deterministic)

The Director can read `temple/subsandbox/research/<problem_id>/research_run_receipt.json`
and use these fields to drive parameters that would otherwise be arbitrary:

| Director parameter | Math source | Rule |
|--------------------|-------------|------|
| `prompt_seed`        | `operator_hash` | Take last 8 hex chars → int → backend seed |
| `shot_count`         | `lambda_max - lambda_min` (spectral gap) | larger gap → more shots (energy budget) |
| `mood_arc`           | `z_T contraction trace` | Decreasing norm → contemplative → calm arc |
| `intensity_curve`    | `frobenius_norm` | Higher F-norm → tighter cuts, faster pace |
| `seed_variation_n`   | `z_T_summary.first_8` | 8 floats → 8 deterministic per-shot variations |

## Why this matters

- **Deterministic creativity.** Same brief + same prime fixture → bit-identical production packet. No randomness leak into receipts.
- **Receipt-bound.** The packet's `prompt_seed` is *literally derived* from `operator_hash`, so anyone can verify the Director did not silently change the math.
- **Composable.** Director needs only the JSON of `research_run_receipt.json`. No re-running the math; the receipts are already there.

## Hard scope (what this bridge does NOT do)

- Does not modify `math_to_face_phase0/`
- Does not require image generation
- Does not require cloud
- Does not extend the Director skill's hard rules
- Does not bind sovereignty (still NON_SOVEREIGN, RESEARCH_SUBSANDBOX outputs flow into TEMPLE_SUBSANDBOX director output)

## Activation

Director runs without this bridge by default. To enable, the operator (or the prompt that invokes Director) supplies a `--math-receipt PATH` flag pointing at a `research_run_receipt.json`. If absent, Director uses its own deterministic defaults.

This file is documentation only. Implementation is one if-statement in any future Director runner — not added today (HAL: ship the SKILL.md MVP first, don't expand).

## Mantra slot

```
HANDS render.
MATH parameterizes.
HELEN governs.
DIRECTOR steers.
```
