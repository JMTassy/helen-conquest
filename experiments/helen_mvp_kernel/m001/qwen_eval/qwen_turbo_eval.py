#!/usr/bin/env python3
"""M001 · research-only evaluation: Qwen-Image-2.1-Turbo nail recolouring against the deterministic baseline.

NON_SOVEREIGN · authority=false · local weights only, no API, no credits.
Qwen-Image-2.1-Turbo is under the Qwen RESEARCH LICENSE: non-commercial research or evaluation only.
Its outputs must not reach a client deliverable without a separate commercial licence.

    # 1. preflight: versions, GPU, disk, licence flag. Downloads nothing.
    python qwen_turbo_eval.py --check --accept-research-license

    # 2. run (first download of the weights happens here, ~tens of GB)
    python qwen_turbo_eval.py hand.png --mask mask.png --target "coral_approx=#E2483B" \\
        --colour-words "coral red" --source-kind synthetic --accept-research-license \\
        --seeds 0 1 2 --out runs/qwen_hand

--mask is a PNG, white = nail (for example the mask.png written by ../recolor_nails.py, checked at 100 %).
--source-kind synthetic|helen|client: client photos are refused unless --allow-client-image is also given.

What is measured, on each output brought back to the source geometry (Lanczos), against the source:
  - outside the nail: mean and 95th-percentile dE76, share of pixels above 2.3 (about one just-noticeable
    difference), strictly outside the mask and outside a 3 px band (generous to soft edges);
  - the skin band 3-15 px around the nail (colour bleed);
  - global shift (phase correlation), since a re-rendered image can move;
  - on the nail body: chroma error to the target, dE76, texture kept (same definitions as recolor_nails.py);
  - a resize floor: the source sent to the generation size and back, measured the same way, so the cost of the
    resize itself is not charged to the model.
The deterministic baseline (recolor_nails.recolour) is measured with the same code on the same mask.

Not measured: whether the result looks like the product, whether a person would accept it. A person looks at
the sheet at 100 %. Results stay local: do not commit client images, masks or outputs.
"""
import argparse
import hashlib
import json
import pathlib
import platform
import shutil
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import recolor_nails as rn  # noqa: E402

MODEL_ID = "Qwen/Qwen-Image-2.1-Turbo"
PINNED = {"diffusers": "0.41.0", "transformers": "5.19.0", "accelerate": "1.15.0"}
BNB_PIN = "0.50.2"  # only for --quantize nf4
LICENSE_NOTE = ("Qwen RESEARCH LICENSE AGREEMENT (2026-09-20): non-commercial research or evaluation only; "
                "commercial use needs a separate licence from the licensor")
# resolution presets from the model card (width, height)
PRESETS = {"1:1": (2048, 2048), "4:3": (2400, 1792), "3:4": (1792, 2400), "3:2": (2528, 1696),
           "2:3": (1696, 2528), "16:9": (2752, 1536), "9:16": (1536, 2752)}
JND = 2.3          # dE76 of about one just-noticeable difference
BAND_GAP = 3       # px excluded around the mask for the "outside, generous" measure
BAND_SKIN = 15     # outer radius of the skin band checked for colour bleed

DEFAULT_PROMPT = ("Change only the colour of the fingernail polish to {words} (hex {hex}), opaque glossy finish. "
                  "Keep everything else exactly the same: same hand, same skin, same pose, same background, "
                  "same lighting, same framing and composition.")


# ------------------------------------------------------------------ geometry and measures (no GPU needed)

def preset_for(width, height):
    """The model-card preset whose aspect ratio is closest to the source (log-ratio distance)."""
    r = np.log(width / height)
    name = min(PRESETS, key=lambda k: abs(np.log(PRESETS[k][0] / PRESETS[k][1]) - r))
    return name, PRESETS[name]


def to_size(rgb, size):
    return np.asarray(Image.fromarray(rgb).resize(size, Image.LANCZOS))


def dilate(mask, radius):
    out = mask.copy()
    for _ in range(radius):
        out = rn._dilate(out)
    return out


def phase_shift(a, b):
    """Integer (dy, dx) translation of b relative to a, by phase correlation on luminance."""
    ga, gb = (x.astype(np.float64).mean(axis=2) for x in (a, b))
    fa, fb = np.fft.fft2(ga - ga.mean()), np.fft.fft2(gb - gb.mean())
    r = fb * np.conj(fa)
    corr = np.fft.ifft2(r / np.maximum(np.abs(r), 1e-12)).real
    dy, dx = np.unravel_index(int(np.argmax(corr)), corr.shape)
    h, w = corr.shape
    return int(dy - h if dy > h // 2 else dy), int(dx - w if dx > w // 2 else dx)


def de76(a, b):
    return np.sqrt(((rn.srgb_to_lab(a) - rn.srgb_to_lab(b)) ** 2).sum(axis=2))


def _stats(d, sel):
    if not sel.any():
        return {"mean": None, "p95": None, "share_above_jnd": None}
    v = d[sel]
    return {"mean": round(float(v.mean()), 3), "p95": round(float(np.percentile(v, 95)), 3),
            "share_above_jnd": round(float((v > JND).mean()), 4)}


def evaluate(src, edited, mask, target_lab):
    """Measures of one edited image (already at the source geometry) against the source."""
    d = de76(src, edited)
    near = dilate(mask, BAND_GAP)
    skin_band = dilate(mask, BAND_SKIN) & ~near
    nail = rn.measure(src, edited, mask, mask.astype(np.float64), target_lab)
    return {"outside_mask_strict": _stats(d, ~mask),
            "outside_mask_excluding_3px_band": _stats(d, ~near),
            "skin_band_3_to_15px": _stats(d, skin_band),
            "pixels_identical_outside_mask": round(float((np.abs(edited.astype(int) - src.astype(int)).max(axis=2)[~mask] == 0).mean()), 4),
            "global_shift_px": phase_shift(src, edited),
            "nail_body": {k: nail[k] for k in ("mean_chroma_error_nail_body", "mean_dE76_to_target_nail_body",
                                               "texture_kept_corr_L_body")}}


def resize_floor(src, gen_size):
    return to_size(to_size(src, gen_size), (src.shape[1], src.shape[0]))


def heatmap(d, vmax=10.0):
    t = np.clip(d / vmax, 0, 1)
    return (np.stack([t, np.clip(1.5 - np.abs(2 * t - 1) * 1.5, 0, 1) * 0.6, 1 - t], axis=2) * 255).astype(np.uint8)


def sheet(cols, path, width=300):
    thumbs = [(Image.fromarray(im).resize((width, int(im.shape[0] * width / im.shape[1]))), lab) for im, lab in cols]
    h = max(t.height for t, _ in thumbs) + 26
    s = Image.new("RGB", (width * len(thumbs), h), (24, 24, 24))
    d = ImageDraw.Draw(s)
    for i, (t, lab) in enumerate(thumbs):
        s.paste(t, (i * width, 0))
        d.text((i * width + 6, h - 20), lab, fill=(235, 235, 235))
    s.save(path)


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


# ------------------------------------------------------------------ model side (GPU machine only)

def preflight(quantize="none"):
    """Versions, GPU, disk. Imports torch/diffusers but downloads nothing."""
    info = {"python": platform.python_version(), "pinned": PINNED, "quantize": quantize, "problems": []}
    if quantize == "nf4":
        try:
            import bitsandbytes
            info["bitsandbytes"] = bitsandbytes.__version__
            if bitsandbytes.__version__ != BNB_PIN:
                info["problems"].append(f"bitsandbytes {bitsandbytes.__version__} installed, {BNB_PIN} pinned")
        except ImportError:
            info["problems"].append(f"--quantize nf4 needs bitsandbytes=={BNB_PIN} (see requirements)")
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda"] = bool(torch.cuda.is_available())
        if info["cuda"]:
            p = torch.cuda.get_device_properties(0)
            info["gpu"] = p.name
            info["vram_gb"] = round(p.total_memory / 2 ** 30, 1)
            if info["vram_gb"] < 40 and quantize == "none":
                info["problems"].append(f"{info['vram_gb']} GB VRAM: run with --offload model (slower) "
                                        "or --offload sequential (slowest)")
        else:
            info["problems"].append("no CUDA GPU visible to torch: the model cannot run here")
    except ImportError:
        info["problems"].append("torch not installed (install the CUDA build first, see README)")
    for pkg in PINNED:
        try:
            mod = __import__(pkg)
            info[pkg] = mod.__version__
            if mod.__version__ != PINNED[pkg]:
                info["problems"].append(f"{pkg} {mod.__version__} installed, {PINNED[pkg]} pinned")
        except ImportError:
            info["problems"].append(f"{pkg} not installed")
    try:
        from diffusers import QwenImage21Pipeline  # noqa: F401
    except Exception as e:  # noqa: BLE001
        info["problems"].append(f"QwenImage21Pipeline not importable: {type(e).__name__}")
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
        free = shutil.disk_usage(pathlib.Path(HF_HUB_CACHE).anchor or "/").free / 2 ** 30
        info["hf_cache"], info["disk_free_gb"] = str(HF_HUB_CACHE), round(free, 1)
        if free < 60:
            info["problems"].append(f"{free:.0f} GB free for the weights cache; keep at least 60 GB")
    except Exception:  # noqa: BLE001
        info["problems"].append("huggingface_hub not importable")
    return info


QUANT_LABEL = {"none": "Turbo bf16 (official weights as published)",
               "nf4": "Turbo 4-bit (official weights, NF4 at load: transformer + text encoder; not the published precision)"}


def load_pipeline(revision, offload, quantize="none"):
    import torch
    from diffusers import QwenImage21Pipeline
    kw = {}
    if quantize == "nf4":  # official checkpoint quantized in memory at load; no third-party converted weights
        from diffusers.quantizers import PipelineQuantizationConfig
        kw["quantization_config"] = PipelineQuantizationConfig(
            quant_backend="bitsandbytes_4bit",
            quant_kwargs={"load_in_4bit": True, "bnb_4bit_quant_type": "nf4", "bnb_4bit_compute_dtype": torch.bfloat16},
            components_to_quantize=["transformer", "text_encoder"])
    pipe = QwenImage21Pipeline.from_pretrained(MODEL_ID, revision=revision, dtype=torch.bfloat16, **kw)
    if quantize == "nf4":  # decoding the 2K frame in one piece runs out of memory on ~12 GB cards
        pipe.vae.enable_tiling()  # tile seams, if any, show up in the outside-mask measures: recorded in report
    if offload == "model":
        pipe.enable_model_cpu_offload()
    elif offload == "sequential":
        pipe.enable_sequential_cpu_offload()
    else:
        pipe = pipe.to("cuda")
    try:
        from huggingface_hub import model_info
        resolved = model_info(MODEL_ID, revision=revision).sha
    except Exception:  # noqa: BLE001
        resolved = None
    return pipe, resolved


def qwen_edit(pipe, rgb, prompt, size, seed):
    import torch
    out = pipe(prompt=prompt, image=Image.fromarray(rgb).convert("RGB"), width=size[0], height=size[1],
               use_kv_cache=True, generator=torch.Generator("cpu").manual_seed(seed)).images[0]
    return np.asarray(out.convert("RGB"))


# ------------------------------------------------------------------ main

def main(argv=None, edit_fn=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?")
    ap.add_argument("--mask", help="PNG, white = nail (checked at 100 %% before use)")
    ap.add_argument("--target", help="name=#RRGGBB")
    ap.add_argument("--colour-words", default=None, help='words for the prompt, e.g. "coral red"')
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, help="template with {words} and {hex}")
    ap.add_argument("--source-kind", choices=["synthetic", "helen", "client"])
    ap.add_argument("--allow-client-image", action="store_true")
    ap.add_argument("--accept-research-license", action="store_true",
                    help="confirm this run is non-commercial research/evaluation under the Qwen Research License")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--revision", default=None, help="Hugging Face commit of the checkpoint; pin after the first run")
    ap.add_argument("--offload", choices=["none", "model", "sequential"], default="none")
    ap.add_argument("--quantize", choices=["none", "nf4"], default="none",
                    help="nf4: load the official weights in 4-bit (for ~12-24 GB GPUs); results are labelled Turbo 4-bit")
    ap.add_argument("--out", default="runs/qwen_eval")
    ap.add_argument("--check", action="store_true", help="preflight only; downloads nothing")
    args = ap.parse_args(argv)

    if not args.accept_research_license:
        ap.error("--accept-research-license is required: " + LICENSE_NOTE)
    if args.check:
        info = preflight(args.quantize)
        print(json.dumps(info, indent=1))
        return info
    if not (args.image and args.mask and args.target and args.source_kind):
        ap.error("image, --mask, --target and --source-kind are required for a run")
    if args.source_kind == "client" and not args.allow_client_image:
        ap.error("client photo refused: start with a synthetic or HELEN image; add --allow-client-image only on JM's word")

    src_path, out = pathlib.Path(args.image), pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src = np.asarray(Image.open(src_path).convert("RGB"))
    mask = np.asarray(Image.open(args.mask).convert("L")) > 127
    if mask.shape != src.shape[:2]:
        ap.error(f"mask size {mask.shape[::-1]} differs from image size {src.shape[1::-1]}")
    name, hexv = args.target.split("=", 1)
    tl = rn.hex_to_lab(hexv)
    prompt = args.prompt.format(words=args.colour_words or name.replace("_", " "), hex=hexv)
    preset, gen_size = preset_for(src.shape[1], src.shape[0])

    base, _, base_info = rn.recolour(src, mask, tl)
    floor = resize_floor(src, gen_size)
    report = {"status": "NON_SOVEREIGN", "authority": False, "licence": LICENSE_NOTE,
              "use": "research/evaluation only; outputs not for client deliverables",
              "source": {"file": src_path.name, "sha256": sha16(src_path.read_bytes()), "kind": args.source_kind,
                         "size": [int(src.shape[1]), int(src.shape[0])]},
              "mask": {"file": pathlib.Path(args.mask).name, "pixels": int(mask.sum())},
              "target": {"name": name, "hex": hexv, "note": "approximate parameter, not a product reference"},
              "prompt": prompt, "generation_size": {"preset": preset, "size": list(gen_size)},
              "baseline_deterministic": {**evaluate(src, base, mask, tl), **base_info},
              "resize_floor": evaluate(src, floor, mask, tl), "runs": []}
    Image.fromarray(src).save(out / "00_source.png")
    Image.fromarray(base).save(out / "01_baseline_deterministic.png")
    cols = [(src, "source"), (base, "baseline (deterministic)")]

    resolved = None
    if edit_fn is None:
        report["environment"] = env = preflight(args.quantize)
        if args.quantize == "nf4" and args.offload == "none" and (env.get("vram_gb") or 99) < 16:
            ap.error(f"{env.get('vram_gb')} GB VRAM: --quantize nf4 needs --offload model below 16 GB "
                     "(without it the run failed with a CUDA error on a 12 GB card)")
        pipe, resolved = load_pipeline(args.revision, args.offload, args.quantize)
        edit_fn = lambda rgb, s: qwen_edit(pipe, rgb, prompt, gen_size, s)  # noqa: E731
    report["model"] = {"id": MODEL_ID, "revision_requested": args.revision, "revision_resolved": resolved,
                       "steps": "checkpoint's saved 8-step schedule", "use_kv_cache": True, "offload": args.offload,
                       "quantize": args.quantize, "label": QUANT_LABEL[args.quantize],
                       "vae_tiling": args.quantize == "nf4"}

    report["run_status"] = f"in progress: 0 of {len(args.seeds)} seeds done"
    (out / "report.json").write_text(json.dumps(report, indent=1))
    for s in args.seeds:
        t0 = time.time()
        raw = edit_fn(src, s)
        at_src = raw if raw.shape == src.shape else to_size(raw, (src.shape[1], src.shape[0]))
        Image.fromarray(raw).save(out / f"qwen_seed{s}_raw.png")
        Image.fromarray(at_src).save(out / f"qwen_seed{s}_at_source.png")
        heat = heatmap(de76(src, at_src))
        Image.fromarray(heat).save(out / f"qwen_seed{s}_dE_map.png")
        report["runs"].append({"seed": s, "seconds": round(time.time() - t0, 1), "raw_size": [int(raw.shape[1]), int(raw.shape[0])],
                               "output_sha256": sha16(at_src.tobytes()), **evaluate(src, at_src, mask, tl)})
        cols += [(at_src, f"qwen seed {s}"), (heat, f"dE map seed {s} (0-10)")]
        report["run_status"] = f"in progress: {len(report['runs'])} of {len(args.seeds)} seeds done"
        (out / "report.json").write_text(json.dumps(report, indent=1))
    report["run_status"] = f"complete: {len(report['runs'])} of {len(args.seeds)} seeds"
    sheet(cols, out / "qwen_eval_sheet.png")
    (out / "report.json").write_text(json.dumps(report, indent=1))

    b = report["baseline_deterministic"]["outside_mask_strict"]
    f = report["resize_floor"]["outside_mask_excluding_3px_band"]
    print(f"baseline: outside-mask mean dE {b['mean']} (identical outside: "
          f"{report['baseline_deterministic']['pixels_identical_outside_mask']})")
    print(f"resize floor: outside mean dE {f['mean']}, share > JND {f['share_above_jnd']}")
    for r in report["runs"]:
        o = r["outside_mask_excluding_3px_band"]
        print(f"qwen seed {r['seed']}: outside mean dE {o['mean']}, p95 {o['p95']}, share > JND {o['share_above_jnd']}, "
              f"shift {r['global_shift_px']}, nail chroma error {r['nail_body']['mean_chroma_error_nail_body']}")
    print(f"model: {report['model']['label']}")
    print("Research/evaluation only. A person reviews qwen_eval_sheet.png at 100 %. Keep outputs off the public repo.")
    return report


if __name__ == "__main__":
    main()
