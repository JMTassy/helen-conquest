"""Render keyframes — skeleton, Pillow-based stub for G().

Per SKILL.md §2 non-negotiable experimental rule: all evaluation/editing routes
through clone_from_latent(z_struct) with NO re-encoding. Until G/E are wired
(Phase 4), this script selects from the curated MIA reference set and applies
Pillow transforms (color grade, crop, overlay tint) as a placeholder. The
stub is honest: each output carries a `rendered_via: stub` marker and a
`TODO: wire G(z_struct)` note.

Usage:
    python3 scripts/render_keyframes.py <arc_spec.json>
        [--refs mia/refs/real] [--out /tmp/helen_keyframes]

Pure stdlib + PIL. No numpy / torch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance
except ImportError:
    print("ERROR: Pillow required. Laptop pip is broken — if PIL missing, install via "
          "alternate Python or system package.", file=sys.stderr)
    sys.exit(3)


MOOD_GRADE = {
    "calm_open":            {"saturation": 0.95, "brightness": 1.02, "contrast": 0.98},
    "quiet_bloom":          {"saturation": 1.05, "brightness": 1.05, "contrast": 1.00},
    "curious_turn":         {"saturation": 1.10, "brightness": 1.00, "contrast": 1.05},
    "tender_gaze":          {"saturation": 1.00, "brightness": 1.08, "contrast": 0.95},
    "dramatic_rise":        {"saturation": 1.15, "brightness": 0.95, "contrast": 1.15},
    "serene_hold":          {"saturation": 0.90, "brightness": 1.03, "contrast": 0.97},
    "playful_shift":        {"saturation": 1.20, "brightness": 1.05, "contrast": 1.05},
    "vulnerable_drop":      {"saturation": 0.85, "brightness": 0.92, "contrast": 0.90},
    "intense_center":       {"saturation": 1.10, "brightness": 0.90, "contrast": 1.20},
    "contemplative_drift":  {"saturation": 0.88, "brightness": 1.00, "contrast": 0.92},
    "joyful_release":       {"saturation": 1.25, "brightness": 1.10, "contrast": 1.05},
    "canonical_return":     {"saturation": 1.00, "brightness": 1.00, "contrast": 1.00},
}


def apply_grade(img: Image.Image, grade: dict) -> Image.Image:
    img = ImageEnhance.Color(img).enhance(grade["saturation"])
    img = ImageEnhance.Brightness(img).enhance(grade["brightness"])
    img = ImageEnhance.Contrast(img).enhance(grade["contrast"])
    return img


def clone_from_latent_stub(ref_path: Path, mood: str) -> Image.Image:
    """Placeholder for G(clone_from_latent(z_struct)).

    TODO Phase 4: wire real G (StyleGAN3 / SD / Flux) + clone_from_latent from
    helen_os/render/math_to_face.py. Until then: open ref + PIL color grade.
    """
    img = Image.open(ref_path).convert("RGB")
    grade = MOOD_GRADE.get(mood, MOOD_GRADE["canonical_return"])
    return apply_grade(img, grade)


def select_ref(refs: list[Path], idx: int) -> Path:
    return refs[idx % len(refs)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("arc_spec")
    ap.add_argument("--refs", default="mia/refs/real",
                    help="directory with curated HELEN reference images")
    ap.add_argument("--out", default="/tmp/helen_keyframes_v04",
                    help="output directory for rendered PNGs")
    args = ap.parse_args()

    spec = json.loads(Path(args.arc_spec).read_text())
    refs_dir = Path(args.refs)
    refs = sorted([p for p in refs_dir.glob("*.jpg")] + [p for p in refs_dir.glob("*.png")])
    if not refs:
        print(f"ERROR: no references in {refs_dir}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": "keyframe_render_v1",
        "rendered_via": "stub",
        "TODO": "wire G(clone_from_latent(z_struct)) per SKILL.md §2 / Phase 4",
        "arc_spec": args.arc_spec,
        "refs_dir": str(refs_dir),
        "n_refs_available": len(refs),
        "keyframes": [],
    }

    for seg in spec["segments"]:
        ref = select_ref(refs, seg["idx"])
        img = clone_from_latent_stub(ref, seg["mood"])
        out_path = out_dir / f"{seg['keyframe_id']}.png"
        img.save(out_path)
        manifest["keyframes"].append({
            "keyframe_id": seg["keyframe_id"],
            "mood": seg["mood"],
            "ref_used": str(ref),
            "out_path": str(out_path),
        })
        print(f"  rendered {seg['keyframe_id']}  mood={seg['mood']:20s} ref={ref.name}")

    manifest_path = out_dir / "keyframes_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"[render_keyframes] wrote {len(manifest['keyframes'])} keyframes → {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
