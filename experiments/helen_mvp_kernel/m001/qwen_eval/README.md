# M001 · Qwen-Image-2.1-Turbo research evaluation (NON_SOVEREIGN · authority=false · budget 0)

Question: told only to change the nail polish colour, does a generative editor keep the rest of the photo
intact? The deterministic baseline (`../recolor_nails.py`) changes nothing outside the nail by construction;
this script measures the generative model against it with the same code, on the same mask.

**Licence.** Qwen-Image-2.1-Turbo is under the *Qwen Research License*: non-commercial research or evaluation
only. Outputs of this test never go into a client deliverable. Local weights only: no Pro/Turbo API, no credits.
The script refuses to run without `--accept-research-license`.

## For HAL·WITNESS (GPU machine), in order

1. Separate venv, pinned packages (nothing else changes on the machine):
   ```bash
   python -m venv .venv-qwen && source .venv-qwen/bin/activate
   pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cu130   # match nvidia-smi
   pip install -r requirements-qwen-eval.txt
   ```
2. Preflight, downloads nothing: `python qwen_turbo_eval.py --check --accept-research-license`.
   Report the JSON. Below ~40 GB of VRAM use `--offload model`. Keep 60 GB free for the weights cache.
   **Smaller GPU or RAM-limited WSL:** add `--quantize nf4` to every command (check and run). It loads the
   *official* weights in 4-bit at load time (transformer and Qwen3-VL text encoder) with the pinned
   `bitsandbytes`; `report.json` labels the run `Turbo 4-bit`. Its numbers describe the 4-bit model, not the
   published bf16 one. Do not use third-party GGUF conversions instead (e.g. Viggle builds): they are a
   different, fine-tuned model whose card states it does not reproduce the upstream outputs.
   On a ~12 GB card, nf4 also needs `--offload model`; the script refuses nf4 without it below 16 GB. nf4 turns
   on VAE tiling (the 2K decode ran out of memory otherwise), recorded as `model.vae_tiling`. `report.json` is
   rewritten after every seed (`run_status`), so a run stopped half-way keeps the seeds it finished.
   If RAM runs out (WSL capped at 15 GB killed a run at seed 1), run one seed per process into the same
   `--out` with `--resume` (e.g. `--seeds 1 --resume`, then `--seeds 2 --resume`): seeds are added, never
   overwritten; a plain rerun into a folder with finished seeds is refused.
3. Synthetic first. From `..`, make the synthetic hand and its exact mask:
   ```bash
   python -c "import sys; sys.path[:0]=['tests','.']; from test_recolor_nails import synthetic_hand; \
   from PIL import Image; import numpy as np; s,t,_=synthetic_hand(); \
   Image.fromarray(s).resize((640,480),Image.NEAREST).save('qwen_eval/runs/hand.png'); \
   Image.fromarray((t*255).astype(np.uint8)).resize((640,480),Image.NEAREST).save('qwen_eval/runs/mask.png')"
   ```
   (create `qwen_eval/runs/` first). Then, from `qwen_eval/`:
   ```bash
   python qwen_turbo_eval.py runs/hand.png --mask runs/mask.png --target "coral_approx=#E2483B" \
       --colour-words "coral red" --source-kind synthetic --accept-research-license --seeds 0 1 2 --out runs/synthetic
   ```
4. Then one HELEN image (`--source-kind helen`) with a mask painted by a person and checked at 100 %.
5. Client photos only on JM's explicit word (`--source-kind client --allow-client-image`), outputs kept local.

On the first run, note `model.revision_resolved` in `report.json` and pass it as `--revision` afterwards, so
later runs use the same weights.

## Reading `report.json`

- `outside_mask_excluding_3px_band`: dE76 against the source away from the nail. Mean, p95, and the share of
  pixels above 2.3 (about one just-noticeable difference). The baseline scores 0 here.
- `resize_floor`: the same measure for the source resized to the generation size and back. Differences at or
  below this floor are the resize, not the model.
- `skin_band_3_to_15px`: colour bleed onto the skin around the nail.
- `global_shift_px`: a re-rendered frame can move; a non-zero shift inflates every outside measure.
- `nail_body`: chroma error to the target, dE76 (mostly kept shading), texture kept. Same definitions as the baseline.
- No number says whether it looks like the product or whether a person accepts it: look at `qwen_eval_sheet.png` at 100 %.

Generation is not bit-reproducible across hardware or `use_kv_cache` settings (per the pipeline's own docs);
seeds make runs comparable on one machine, not identical everywhere. Outputs, images and masks stay in `runs/`
(gitignored); commit only a summary without client material.

Tests (no GPU, fake edits): `python -m pytest ../tests/test_qwen_eval_metrics.py -q`.
