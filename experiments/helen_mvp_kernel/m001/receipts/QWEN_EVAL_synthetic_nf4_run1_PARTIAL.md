# Qwen-Image-2.1-Turbo eval · synthetic hand · nf4 · run 1 — PARTIAL

NON_SOVEREIGN · authority=false · research licence (non-commercial evaluation only) · budget 0
Source of every fact below: HAL·WITNESS report of 2026-10-10 17:18, **not re-verified by the cloud lane**
(images and logs stay on the witness machine).

## Status

**PARTIAL — no measurement.** Seed 0 of 3 completed; the process received SIGTERM (exit 15) during seed 1,
stopped from outside, with no Python traceback. The script then wrote `report.json` only at the end, so
**no number exists for this run**. Nothing below measures the model.

## What ran

- Code: commit `64cd569` **plus an uncommitted local patch** in `load_pipeline()` (`pipe.vae.enable_tiling()`
  when `--quantize nf4`). The patch is folded into the script in the commit that adds this receipt; this run
  is therefore not reproducible from `64cd569` alone.
- Command (from `qwen_eval/`):
  ```
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python qwen_turbo_eval.py runs/hand.png \
    --mask runs/mask.png --target "coral_approx=#E2483B" --colour-words "coral red" \
    --source-kind synthetic --accept-research-license --seeds 0 1 2 --quantize nf4 \
    --offload model --revision d65dbc9a7e8f6b5479e33dee6030eaab2a906509 --out runs/synthetic_nf4
  ```
- Weights: `Qwen/Qwen-Image-2.1-Turbo` @ `d65dbc9a7e8f6b5479e33dee6030eaab2a906509` (the revision passed on the
  command line; not read back from a report). Expected label: Turbo 4-bit (nf4).
- Environment: Python 3.14.4 · torch 2.14.1+cu130 · torchvision 0.29.1 · diffusers 0.41.0 ·
  transformers 5.19.0 · accelerate 1.15.0 · bitsandbytes 0.50.2 · RTX 5070, 11.9 GB.
- Earlier attempts, not counted as runs: torchvision missing; CUDA error with `--offload none`; out of GPU
  memory while decoding the final 2400×1792 frame.

## Files reported (SHA-256, truncated as received)

| File | SHA-256 |
|---|---|
| `00_source.png` | `43d68f1a…`, same as the synthetic hand built in the cloud lane (`43d68f1a8cba3b73…`) |
| `01_baseline_deterministic.png` | `80c77f52…` |
| `qwen_seed0_raw.png` (2400×1792) | `87ed6285…` |
| `qwen_seed0_at_source.png` | not received (relay text cut off) |
| `qwen_seed0_dE_map.png` | not received (relay text cut off) |

## Observation by eye (seed 0 only; not a measure)

The witness reports that Qwen redrew the nail oval as a beige fill rather than recolouring it coral, and that
the background shifted from brown to olive, with the difference map showing changes across the frame.
Caveat: the synthetic hand is a flat drawing, far from a photograph; a poor edit on it says little about real
photos. It is the pre-planned first step because its exact mask is known.

## Not claimed

No outside-mask figure, no nail colour error, no comparison with the deterministic baseline, no statement
about seeds 1–2, about the bf16 model, or about any real photo.

## Script changes made after this run (same commit as this receipt)

1. VAE tiling turned on with `--quantize nf4`, recorded as `model.vae_tiling` (tile seams would show in the
   outside-mask measures).
2. `--quantize nf4` refused without `--offload model` below 16 GB of VRAM.
3. `torchvision==0.29.1` pinned (the Qwen3-VL processor imports it).
4. `report.json` rewritten after every seed with `run_status`, so an interrupted run keeps its finished seeds.

Next run: same command without the local patch, on the new commit; report the final printed lines and
`model.label`, `model.revision_resolved`, `run_status` from `report.json`.
