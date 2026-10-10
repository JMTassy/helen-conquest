"""« INCI de l'image » — label cards and an 8 s film for a nail-shade simulation. NON_SOVEREIGN · authority=false.

One photo, one nail mask, N shades. For each shade: the deterministic CIELAB recolour (../recolor_nails.py),
its measures, and a printable label (1080×1350) saying what was done, what was measured and what is not
claimed. The film (1080×1350, 30 fps, 8 s, silent): the original, the shades changing on the same hand by a
nail-only wipe, the map of differences, 0.3 s of black, the label.

    python inci_film.py spec.json --fonts DIR --out DIR

spec.json (client files stay outside the repository; the script refuses an --out inside a git tree):
    {"image": "...jpg", "mask": "...png", "status": "BROUILLON",
     "source": "Shooting Calvi, mai 2025", "source_ref": "calvi_04, version e-mail",
     "mask_provenance": "automatique, non vérifié indépendamment",
     "shades": [{"name": "Corail", "hex": "#E2483B"}, ...]}

Rule: nothing is ever drawn on the photograph; captions live in the bands around it. Claims are computed on the
native pixels; the film shows a square crop resized for display, and the label says so.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import recolor_nails as rn  # noqa: E402

W, H, FPS = 1080, 1350, 30
IMG_Y, IMG_S = 90, 1080                       # photo area: 1080×1080 square under a 90 px top band
INK, PARCH, GOLD, COPPER, MID, PAPER = (10, 10, 12), (232, 222, 200), (201, 160, 74), (168, 88, 58), (128, 120, 106), (246, 242, 233)
SERIF, SERIF_IT, MONO, MONO_MED = "Cormorant-SemiBold.ttf", "Cormorant-MediumItalic.ttf", "PlexMono-Regular.ttf", "PlexMono-Medium.ttf"
SCRIPT_SHA = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
_FONTS = {}


def font(name, size):
    key = (name, size)
    if key not in _FONTS:
        path = _FONTS["dir"] / name
        _FONTS[key] = ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size)
    return _FONTS[key]


def fr(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def wrap(d, text, f, width):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def square_crop(mask, shape):
    """Largest square that fits the image, centred on the nails."""
    h, w = shape
    s = min(h, w)
    ys, xs = np.nonzero(mask)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    y0 = int(np.clip(round(cy - s / 2), 0, h - s))
    x0 = int(np.clip(round(cx - s / 2), 0, w - s))
    return x0, y0, s


def prepare(spec):
    src = np.asarray(Image.open(spec["image"]).convert("RGB"))
    mask = np.asarray(Image.open(spec["mask"]).convert("L")) > 127
    if mask.shape != src.shape[:2]:
        raise SystemExit(f"mask {mask.shape[::-1]} and image {src.shape[1::-1]} differ in size")
    shades = []
    for s in spec["shades"]:
        tl = rn.hex_to_lab(s["hex"])
        out, alpha, info = rn.recolour(src, mask, tl)
        shades.append({**s, "out": out, "alpha": alpha, "measures": {**rn.measure(src, out, mask, alpha, tl), **info}})
    return src, mask, shades


# ------------------------------------------------------------------ drawing helpers

def crop_view(rgb, crop):
    x0, y0, s = crop
    return Image.fromarray(rgb[y0:y0 + s, x0:x0 + s]).resize((IMG_S, IMG_S), Image.LANCZOS)


def diff_view(src, out, crop):
    x0, y0, s = crop
    a, b = src[y0:y0 + s, x0:x0 + s], out[y0:y0 + s, x0:x0 + s]
    d = np.abs(a.astype(int) - b.astype(int)).max(axis=2)
    lum = (a.astype(float) @ [0.299, 0.587, 0.114]) * 0.16
    img = np.repeat(lum[..., None], 3, axis=2)
    k = np.clip(d / 40, 0, 1)[..., None] * 0.7 + (d > 0)[..., None] * 0.3
    img = img * (1 - k) + np.array(GOLD, float) * k
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((IMG_S, IMG_S), Image.NEAREST)


def band(d, spec, right=""):
    d.text((40, 56), "INCI DE L'IMAGE", font=font(MONO_MED, 20), fill=PARCH)
    if spec.get("status"):
        x = 40 + d.textlength("INCI DE L'IMAGE", font=font(MONO_MED, 20)) + 24
        d.text((x, 56), spec["status"].upper(), font=font(MONO_MED, 20), fill=COPPER)
    if right:
        d.text((W - 40, 56), right, font=font(MONO, 20), fill=MID, anchor="rs")


def caption(d, title, sub1, sub2="", sub2_col=GOLD):
    y = IMG_Y + IMG_S
    d.text((40, y + 72), title, font=font(SERIF, 58), fill=PARCH, anchor="ls")
    d.text((40, y + 114), sub1, font=font(MONO, 20), fill=MID, anchor="ls")
    if sub2:
        d.text((40, y + 146), sub2, font=font(MONO, 20), fill=sub2_col, anchor="ls")


def label_lines(spec, src_sha, shade, crop, shape):
    m = shade["measures"]
    x0, y0, s = crop
    return [
        ("Source", f"{spec['source']} · {spec['source_ref']} · {shape[1]} × {shape[0]} px · sha256 {src_sha[:12]}…"),
        ("Opération", "Ongles uniquement. Recoloration dans l'espace CIELAB : la luminance de l'ongle (reflets, stries) "
                      "est conservée, la teinte est déplacée vers la cible. Rendu déterministe, aucune IA générative."),
        ("Masque", f"{spec['mask_provenance']} · {m['mask_pixels']} px d'ongle."),
        ("Mesures", f"Pixels modifiés hors ongles et liseré : {m['pixels_changed_outside_mask']}. "
                    f"Liseré adouci de 1 px : {m['feather_ring_pixels_changed']} px. "
                    f"Texture conservée (corrélation de L) : {fr(m['texture_kept_corr_L_body'], 3)}. "
                    f"Écart de teinte (chroma, corps de l'ongle) : {fr(m['mean_chroma_error_nail_body'])}."),
        ("Non revendiqué", f"Fidélité à la teinte du produit : non calibrée (cible approximative {shade['hex']}). "
                           "Le masque ne vaut que s'il a été vérifié à 100 %. Peau, décor et tout le reste de la photo : non modifiés."),
        ("Affichage", f"Recadrage carré {s} × {s} px agrandi pour l'écran ; les mesures portent sur les pixels d'origine."),
        ("Reçu", f"inci_film.py sha256 {SCRIPT_SHA[:12]}… · authority = false"),
    ]


def label_card(spec, src_sha, src, shade, crop, n=None):
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.text((60, 104), "INCI de l'image", font=font(SERIF, 64), fill=INK, anchor="ls")
    if spec.get("status"):
        d.text((W - 60, 104), spec["status"].upper(), font=font(MONO_MED, 18), fill=COPPER, anchor="rs")
    d.line([(60, 126), (W - 60, 126)], fill=INK, width=2)
    thumb = crop_view(shade["out"], crop).resize((520, 520), Image.LANCZOS)
    im.paste(thumb, (60, 156))
    rgb = tuple(int(shade["hex"][i:i + 2], 16) for i in (1, 3, 5))
    d.ellipse([612, 160, 668, 216], fill=rgb)
    d.text((688, 204), shade["name"], font=font(SERIF, 52), fill=INK, anchor="ls")
    d.text((612, 252), f"env. {shade['hex']} · teinte approximative", font=font(MONO, 18), fill=MID, anchor="ls")
    m = shade["measures"]
    d.text((612, 296), f"{m['pixels_changed_outside_mask']} px modifié hors ongles", font=font(MONO_MED, 20), fill=INK, anchor="ls")
    d.text((612, 322), "et liseré de 1 px", font=font(MONO_MED, 20), fill=INK, anchor="ls")
    dv = diff_view(src, shade["out"], crop).resize((300, 300), Image.LANCZOS)
    im.paste(dv, (612, 376))
    d.text((612, 366), "carte des différences", font=font(MONO, 15), fill=MID, anchor="ls")
    y = 730
    for head, text in label_lines(spec, src_sha, shade, crop, src.shape):
        d.text((60, y), head, font=font(SERIF_IT, 26), fill=INK)
        for ln in wrap(d, text, font(MONO, 17), W - 280):
            d.text((240, y), ln, font=font(MONO, 17), fill=(40, 38, 34))
            y += 24
        y += 14
    d.line([(60, H - 74), (W - 60, H - 74)], fill=INK, width=1)
    d.text((60, H - 46), "Rien n'est dessiné sur la photo · rendu reproductible au pixel près", font=font(MONO, 15),
           fill=MID, anchor="ls")
    return im


# ------------------------------------------------------------------ film

def eo(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def film_frames(spec, src, mask, shades, crop):
    zone = shades[0]["alpha"] > 0
    ys = np.nonzero(zone)[0]
    top, bot = ys.min(), ys.max()
    rows = np.arange(src.shape[0])[:, None]
    total = len(shades)
    seq = []                                               # (frame image builder)
    t = 0

    def frame(photo, title, s1, s2="", s2c=GOLD, right=""):
        im = Image.new("RGB", (W, H), INK)
        im.paste(photo, (0, IMG_Y))
        d = ImageDraw.Draw(im)
        band(d, spec, right)
        caption(d, title, s1, s2, s2c)
        return im

    orig = crop_view(src, crop)
    for _ in range(18):
        seq.append(frame(orig, "Original", spec["source"], "aucune retouche", MID))
    cur = src
    for i, sh in enumerate(shades):
        m = sh["measures"]
        sub2 = f"{m['pixels_changed_outside_mask']} px modifié hors ongles et liseré de 1 px"
        for k in range(30):
            if k < 7:
                sweep = top + (bot - top + 1) * eo((k + 1) / 7)
                sel = (zone & (rows <= sweep))[..., None]
                img = np.where(sel, sh["out"], cur)
                photo = crop_view(img, crop)
            elif k == 7:
                photo = crop_view(sh["out"], crop)
            seq.append(frame(photo, sh["name"], f"env. {sh['hex']} · teinte approximative", sub2, right=f"{i + 1} / {total}"))
        cur = sh["out"]
    last = shades[-1]
    dv = diff_view(src, last["out"], crop)
    for _ in range(30):
        seq.append(frame(dv, "Seuls les ongles ont changé",
                         f"carte des différences · {last['measures']['pixels_changed_outside_mask']} px modifié hors ongles et liseré",
                         "le reste de la photo est identique au pixel près", MID))
    seq += [Image.new("RGB", (W, H), INK)] * 9
    card = label_card(spec, sha(spec["image"]), src, last, crop)
    n_end = 8 * FPS - len(seq)
    seq += [card] * max(n_end, 30)
    return seq


def inside_git(path):
    p = pathlib.Path(path).resolve()
    return any((q / ".git").exists() for q in [p, *p.parents])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-film", action="store_true")
    ap.add_argument("--allow-in-repo", action="store_true", help="only for synthetic test images")
    a = ap.parse_args(argv)
    if inside_git(a.out) and not a.allow_in_repo:
        ap.error(f"{a.out} is inside a git working tree: client images must not land in a repository")
    _FONTS["dir"] = pathlib.Path(a.fonts)
    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    src, mask, shades = prepare(spec)
    crop = square_crop(mask, src.shape[:2])
    src_sha = sha(spec["image"])
    receipt = {"what": "INCI de l'image", "status": spec.get("status", ""), "authority": False,
               "script_sha256": SCRIPT_SHA, "image_sha256": src_sha, "mask_sha256": sha(spec["mask"]),
               "mask_provenance": spec["mask_provenance"], "crop_square_px": list(crop), "shades": []}
    for i, sh in enumerate(shades, 1):
        p = out / f"label_{i:02d}_{sh['name'].lower().replace(' ', '_')}.png"
        label_card(spec, src_sha, src, sh, crop).save(p)
        Image.fromarray(sh["out"]).save(out / f"shade_{i:02d}.png")
        receipt["shades"].append({"name": sh["name"], "hex": sh["hex"], "label": p.name,
                                  "label_sha256": sha(p), "measures": sh["measures"]})
    if not a.no_film:
        fdir = out / "frames"
        fdir.mkdir(exist_ok=True)
        frames = film_frames(spec, src, mask, shades, crop)
        for k, im in enumerate(frames):
            im.save(fdir / f"f{k:04d}.png", compress_level=1)
        mp4 = out / "inci_film_8s.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(fdir / "f%04d.png"),
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(mp4)], check=True)
        receipt["film"] = {"file": mp4.name, "frames": len(frames), "fps": FPS, "size": [W, H], "sha256": sha(mp4)}
    (out / "inci_receipt.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False))
    for s in receipt["shades"]:
        m = s["measures"]
        print(f"{s['name']}: outside {m['pixels_changed_outside_mask']} px, ring {m['feather_ring_pixels_changed']} px, "
              f"texture {m['texture_kept_corr_L_body']}, chroma err {m['mean_chroma_error_nail_body']}")
    return receipt


if __name__ == "__main__":
    main()
