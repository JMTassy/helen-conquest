"""True slice sweep — v0.3.1 correction.

Perturb z_id / z_control / z_style directly in latent space and render via
clone_from_latent(). No payload salting (which would re-run H and contaminate
the experiment).

Output:
    out/sweep/baseline.png
    out/sweep/<slice>_s<strength>_k<repeat>.png   (one duo poster per trial)
    out/sweep/sweep_results.csv                   (pass/fail + metrics)
"""
from __future__ import annotations

import os
import csv
import numpy as np

from helen.types import MathObject
from helen.latent import StructuredLatent
from helen.latent_spec import LatentSpec
from helen.pipeline_dual import HelenDualCloner
from helen.compose_duo_poster import compose_duo_poster


OUT_DIR = "out/sweep"
os.makedirs(OUT_DIR, exist_ok=True)


def unit(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x) + 1e-8)


def perturb_struct(
    z: StructuredLatent, which: str, strength: float, seed: int
) -> StructuredLatent:
    """Apply controlled perturbation to ONE slice, leaving others untouched."""
    rng = np.random.default_rng(seed)
    if which == "id":
        delta = unit(rng.normal(size=z.z_id.shape).astype(np.float32))
        z_id = unit(z.z_id + strength * delta)
        return StructuredLatent(z_id, z.z_control, z.z_style, z.z_temporal, spec=z.spec)
    if which == "control":
        delta = unit(rng.normal(size=z.z_control.shape).astype(np.float32))
        z_control = unit(z.z_control + strength * delta)
        return StructuredLatent(z.z_id, z_control, z.z_style, z.z_temporal, spec=z.spec)
    if which == "style":
        delta = unit(rng.normal(size=z.z_style.shape).astype(np.float32))
        z_style = unit(z.z_style + strength * delta)
        return StructuredLatent(z.z_id, z.z_control, z_style, z.z_temporal, spec=z.spec)
    raise ValueError(which)


def main() -> None:
    # --- Replace with calibrated anchors from demo_calibrate.py ---
    real_mu = np.zeros((256,), np.float32); real_mu[0] = 1.0; real_mu = unit(real_mu)
    twin_mu = real_mu.copy()
    real_tau = 0.70
    twin_tau = 0.70

    spec = LatentSpec(id_dim=256, control_dim=128, style_dim=128, temporal_dim=0)
    cloner = HelenDualCloner(spec, real_mu, real_tau, twin_mu, twin_tau)

    m = MathObject(payload={
        "tag": "HELEN",
        "primes": [2, 3, 5, 7, 11, 13],
        "zeta_zeros": [14.1347, 21.0220],
        "fractal_dim": 1.618,
    })

    # --- Baseline (shared across all sweeps) ---
    base = cloner.clone(m, seed=42, use_phi_refine=False)
    z_base = base.z_refined  # the StructuredLatent we perturb around
    base_poster = compose_duo_poster(
        base.img_real.pil, base.img_twin.pil,
        title="BASELINE", subtitle="sweep"
    )
    base_poster.save(os.path.join(OUT_DIR, "baseline.png"))

    # --- Sweep plan ---
    strengths = [0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00]
    slices = ["control", "style", "id"]

    csv_path = os.path.join(OUT_DIR, "sweep_results.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "slice", "strength", "seed",
            "real_pass", "twin_pass", "real_metric", "twin_metric", "img_path",
        ])
        for which in slices:
            for s in strengths:
                for k in range(5):
                    seed = 1000 + 97 * k + int(100 * s)
                    z_pert = perturb_struct(z_base, which=which, strength=s, seed=seed)
                    run = cloner.clone_from_latent(z_pert, seed=seed, use_phi_refine=False)

                    poster = compose_duo_poster(
                        run.img_real.pil, run.img_twin.pil,
                        title=f"{which.upper()}  strength={s:.2f}",
                        subtitle=f"seed={seed}",
                    )
                    img_name = f"{which}_s{str(s).replace('.', 'p')}_k{k}.png"
                    img_path = os.path.join(OUT_DIR, img_name)
                    poster.save(img_path)

                    real_metric = list(run.gate_real.metrics.values())[0]
                    twin_metric = list(run.gate_twin.metrics.values())[0]
                    w.writerow([
                        which, s, seed,
                        int(run.gate_real.passed), int(run.gate_twin.passed),
                        float(real_metric), float(twin_metric),
                        img_path,
                    ])

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] images in {OUT_DIR}")


if __name__ == "__main__":
    main()
