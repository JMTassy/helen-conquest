"""3×3 HELEN-duo mood grid — v0.3.1 correction.

Moods are applied directly to latent slices (z_control, z_style), NOT by
salting the payload. Same identity (z_id) across all 9 panels.

Output:
    out/montage/tile_NN_<MOOD>.png
    out/montage/HELEN_DUO_3x3_MOODS.png
"""
from __future__ import annotations

import os
import numpy as np
from PIL import Image, ImageDraw

from helen.types import MathObject
from helen.latent import StructuredLatent
from helen.latent_spec import LatentSpec
from helen.pipeline_dual import HelenDualCloner
from helen.compose_duo_poster import compose_duo_poster


OUT_DIR = "out/montage"
os.makedirs(OUT_DIR, exist_ok=True)


def unit(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x) + 1e-8)


def mood_offsets(mood: str):
    """Deterministic small offsets for (z_control[:3], z_style[:3])."""
    table = {
        "JOY":      (np.array([+0.20, -0.05, +0.60], np.float32), np.array([+0.10, +0.20, +0.10], np.float32)),
        "SADNESS":  (np.array([-0.10, +0.10, -0.30], np.float32), np.array([-0.05, -0.10, +0.05], np.float32)),
        "CONFID":   (np.array([+0.05,  0.00, +0.35], np.float32), np.array([+0.15, +0.25, +0.05], np.float32)),
        "SURPRISE": (np.array([ 0.00, -0.15, +0.80], np.float32), np.array([+0.05, +0.10, +0.20], np.float32)),
        "ANGER":    (np.array([-0.05, -0.05, +0.10], np.float32), np.array([+0.25, +0.35, +0.10], np.float32)),
        "SERENE":   (np.array([+0.05, +0.05, -0.10], np.float32), np.array([-0.10, -0.05, +0.05], np.float32)),
        "FEAR":     (np.array([-0.15, +0.10, +0.50], np.float32), np.array([+0.10, +0.05, +0.35], np.float32)),
        "PLAYFUL":  (np.array([+0.15, -0.10, +0.55], np.float32), np.array([+0.05, +0.30, +0.15], np.float32)),
        "MYSTERY":  (np.array([ 0.00, +0.05, +0.05], np.float32), np.array([+0.30, +0.10, +0.25], np.float32)),
    }
    return table[mood]


def apply_mood(z: StructuredLatent, mood: str) -> StructuredLatent:
    """Apply mood offsets to z_control[:3] and z_style[:3]; renormalize each slice."""
    c_off, s_off = mood_offsets(mood)
    zc = z.z_control.copy()
    zs = z.z_style.copy()
    zc[:3] = zc[:3] + c_off
    zs[:3] = zs[:3] + s_off
    zc = zc / (np.linalg.norm(zc) + 1e-8)
    zs = zs / (np.linalg.norm(zs) + 1e-8)
    return StructuredLatent(z.z_id, zc, zs, z.z_temporal, spec=z.spec)


def montage_3x3(images, tile_w: int = 1536, tile_h: int = 1024) -> Image.Image:
    grid = Image.new("RGB", (tile_w * 3, tile_h * 3), (0, 0, 0))
    for i, im in enumerate(images):
        r = i // 3
        c = i % 3
        grid.paste(im, (c * tile_w, r * tile_h))
    return grid


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

    # Compute baseline latent ONCE; moods are applied to slices, not to payload
    z_base = cloner.H(m)

    moods = ["JOY", "SADNESS", "CONFID", "SURPRISE", "ANGER", "SERENE", "FEAR", "PLAYFUL", "MYSTERY"]
    tiles = []
    for i, mood in enumerate(moods):
        seed = 500 + i
        z_mood = apply_mood(z_base, mood)
        run = cloner.clone_from_latent(z_mood, seed=seed, use_phi_refine=False)

        tile = compose_duo_poster(
            run.img_real.pil, run.img_twin.pil,
            title=f"{mood}  |  HELEN + TWIN",
            subtitle="HELEN OS  •  CONQUEST",
        )
        d = ImageDraw.Draw(tile)
        d.text((1200, 24), f"R:{'OK' if run.gate_real.passed else 'FAIL'}", fill=(255, 255, 255))
        d.text((1200, 55), f"T:{'OK' if run.gate_twin.passed else 'FAIL'}", fill=(255, 255, 255))

        out_tile = os.path.join(OUT_DIR, f"tile_{i+1:02d}_{mood}.png")
        tile.save(out_tile)
        tiles.append(tile)

    grid = montage_3x3(tiles)
    grid_path = os.path.join(OUT_DIR, "HELEN_DUO_3x3_MOODS.png")
    grid.save(grid_path)
    print(f"[OK] wrote {grid_path}")
    print(f"[OK] individual tiles in {OUT_DIR}")


if __name__ == "__main__":
    main()
