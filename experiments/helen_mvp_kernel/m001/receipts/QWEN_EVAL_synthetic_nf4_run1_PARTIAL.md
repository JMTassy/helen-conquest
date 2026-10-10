# Qwen-Image-2.1-Turbo eval · synthetic hand · nf4 · runs 1–2 — PARTIAL

NON_SOVEREIGN · authority=false · research licence (non-commercial evaluation only) · budget 0
Source of every fact below: HAL·WITNESS reports of 2026-10-10 17:18 and 18:15, **not re-verified by the cloud
lane** (images, logs and `report.json` stay on the witness machine).

## Status

- **Run 1** (17:18): seed 0 of 3 completed, then the process died during seed 1 (reported as SIGTERM, exit 15).
  The script then wrote `report.json` only at the end: **no numbers**.
- **Run 2** (18:15, commit `669088d`, no local patch): seed 0 completed and its numbers were saved; the process
  was killed during seed 1 by the kernel for lack of RAM (resident memory 15.2 GB against WSL's 15 GB limit).
  Seeds 1 and 2 were then started as separate processes; their results are not in this receipt.
- Cause of run 1: the witness thinks it was the same RAM limit. Not confirmed: the kernel's OOM killer normally
  sends SIGKILL (exit 137), not the SIGTERM (exit 15) reported for run 1.

**One seed, on a flat synthetic drawing. Not a verdict on real photos, nor on the bf16 model.**

## What ran

- Run 1: commit `64cd569` plus an uncommitted patch (`pipe.vae.enable_tiling()` with nf4), since folded into
  `669088d`. Run 2: `669088d` as committed.
- Command (from `qwen_eval/`):
  ```
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python qwen_turbo_eval.py runs/hand.png \
    --mask runs/mask.png --target "coral_approx=#E2483B" --colour-words "coral red" \
    --source-kind synthetic --accept-research-license --seeds 0 1 2 --quantize nf4 \
    --offload model --revision d65dbc9a7e8f6b5479e33dee6030eaab2a906509 --out runs/synthetic_nf4
  ```
- Weights: `Qwen/Qwen-Image-2.1-Turbo` @ `d65dbc9a7e8f6b5479e33dee6030eaab2a906509` (run 2 `report.json`:
  resolved revision equals the requested one).
- Run 2 `report.json`: label "Turbo 4-bit (official weights, NF4 at load: transformer + text encoder; not the
  published precision)", VAE tiling on, run status "1 of 3 seeds done".
- Environment: Python 3.14.4 · torch 2.14.1+cu130 · torchvision 0.29.1 · diffusers 0.41.0 ·
  transformers 5.19.0 · accelerate 1.15.0 · bitsandbytes 0.50.2 · RTX 5070, 11.9 GB · WSL limited to 15 GB RAM.

## Run 2, seed 0 — numbers (colour difference dE76, as reported)

| Measure | Deterministic tool | Resize loss alone | Qwen seed 0 |
|---|---|---|---|
| Mean change outside the nail | 0.09 ¹ | 0.12 | **6.56** |
| Share of outside pixels changed visibly (dE > 2.3) | 0.5 % ¹ | 0.6 % | **100 %** |
| Mean change on the skin band 3–15 px around the nail | — | — | 6.73 |
| Outside pixels left identical | — | — | 0 % |
| Global image shift (px) | — | — | 0, 0 |
| Nail colour (chroma) error to the target | small | — | **37.7** |
| Nail shading kept (correlation of lightness) | high | — | **−0.54** |

¹ As printed by `669088d`, the deterministic tool's line used the strict outside-mask measure, which includes its
1 px feather ring, while the resize and Qwen lines exclude a 3 px band. Excluding the band, the deterministic
tool's figure is 0 by construction (to confirm in `report.json`). The printout now uses one measure for all lines.

Reading: with no shift, a uniform change of about 6.5 everywhere (about 50 times the resize loss) means the model
re-rendered the whole frame rather than editing the nail. On the nail, the target colour is missed and the
shading is inverted.

## Observation by eye (seed 0; not a measure)

Corrected wording (HAL·WITNESS): Qwen turned the oval into a beige fingertip and drew a small coral nail on it.
The background shifted from brown to olive. It did not simply paint the nail beige. Caveat: the synthetic hand
is a flat drawing, far from a photograph.

## Files reported (SHA-256, run 1, truncated as received)

| File | SHA-256 |
|---|---|
| `00_source.png` | `43d68f1a…`, same as the synthetic hand built in the cloud lane (`43d68f1a8cba3b73…`) |
| `01_baseline_deterministic.png` | `80c77f52…` |
| `qwen_seed0_raw.png` (2400×1792) | `87ed6285…` |
| `qwen_seed0_at_source.png`, `qwen_seed0_dE_map.png` | not received (relay text cut off) |

Run 2 output hashes: not yet received.

## Not claimed

No result for seeds 1–2, no average over seeds, nothing about real photos, the bf16 model, or any client image.

## Script changes

- `669088d` (after run 1): VAE tiling with nf4; nf4 refused without `--offload model` below 16 GB; torchvision
  pinned; `report.json` rewritten after every seed.
- Next commit (after run 2): memory released between seeds; `--resume` adds seeds to an existing report (same
  image, mask, target, prompt and model settings, else refused); a plain rerun into a folder that already holds
  finished seeds is refused instead of overwriting them; one measure in every printed line.
