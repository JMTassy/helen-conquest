#!/usr/bin/env python3
"""Inventory (and optionally download) the public product images of a Shopify store. No AI.

    python shop_images.py --store https://www.manucurist.com --match "active glow,coral reef,pistachio,chestnut" \\
        --out manucurist_public --download

Reads the store's public /products.json (paginated). For each matching product, records every image with
two separate blocks:
  page_claims  what the page says: product title, handle, URL, image alt text, variants the image is attached to;
  image_facts  what the file is: canonical URL, declared width x height, and after --download the measured
               size, sha256 and measured width x height.
visual_class is left empty on purpose: packshot / worn hand / macro detail / swatch / mood must be filled by
someone who looks at the image (an image on the Cranberry page can show another product).
Writes inventory.json, inventory.csv and coverage.md (pages read, products matched, images, failures).
Public availability is not permission to modify or deliver: rights are a separate check.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

UA = "helen-m001-inventory/1.0 (internal research; low rate)"


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def canonical(src):
    """Shopify serves the same image in many sizes: strip query and _WxH suffixes to get one key."""
    p = urllib.parse.urlsplit(src if not src.startswith("//") else "https:" + src)
    path = re.sub(r"_(\d+x\d*|\d*x\d+|pico|icon|thumb|small|compact|medium|large|grande|original|master)(?=\.\w+$)", "", p.path)
    return f"https://{p.netloc}{path}"


def products(store, fetch, max_pages=20):
    out, pages, errors = [], 0, []
    for page in range(1, max_pages + 1):
        url = f"{store.rstrip('/')}/products.json?limit=250&page={page}"
        try:
            data = json.loads(fetch(url))
        except Exception as e:  # network, HTTP or JSON error: recorded, never guessed
            errors.append(f"{url}: {type(e).__name__}: {e}")
            break
        pages += 1
        batch = data.get("products") or []
        if not batch:
            break
        out += batch
    return out, pages, errors


def inventory(store, terms, fetch=http_get, download_dir=None):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    allp, pages, errors = products(store, fetch)
    terms = [t.strip().lower() for t in terms if t.strip()]
    matched = [p for p in allp if not terms or any(t in (p.get("title") or "").lower() for t in terms)]
    rows, seen = [], {}
    for p in matched:
        variants = {v.get("id"): v.get("title") for v in p.get("variants") or []}
        for img in p.get("images") or []:
            key = canonical(img.get("src", ""))
            row = {
                "collected_at": now,
                "page_claims": {"product_title": p.get("title"), "handle": p.get("handle"),
                                "product_url": f"{store.rstrip('/')}/products/{p.get('handle')}",
                                "image_alt": img.get("alt"), "position": img.get("position"),
                                "variants": [variants.get(v) for v in img.get("variant_ids") or [] if v in variants]},
                "image_facts": {"src": key, "declared_width": img.get("width"), "declared_height": img.get("height"),
                                "shopify_image_id": img.get("id"), "updated_at": img.get("updated_at")},
                "visual_class": None,
                "duplicate_of": seen.get(key),
            }
            seen.setdefault(key, f"{p.get('handle')}#{img.get('position')}")
            if download_dir and not row["duplicate_of"]:
                try:
                    blob = fetch(key)
                    sha = hashlib.sha256(blob).hexdigest()
                    name = f"{p.get('handle')}__{img.get('position')}__{sha[:10]}{pathlib.Path(urllib.parse.urlsplit(key).path).suffix}"
                    (download_dir / name).write_bytes(blob)
                    row["image_facts"].update(file=name, bytes=len(blob), sha256=sha)
                    try:
                        from PIL import Image
                        with Image.open(io.BytesIO(blob)) as im:
                            row["image_facts"].update(measured_width=im.width, measured_height=im.height, format=im.format)
                    except Exception as e:
                        row["image_facts"]["measure_error"] = type(e).__name__
                except Exception as e:
                    row["image_facts"]["download_error"] = f"{type(e).__name__}: {e}"
                    errors.append(f"{key}: {type(e).__name__}")
            rows.append(row)
    coverage = {"store": store, "collected_at": now, "pages_read": pages, "products_total": len(allp),
                "products_matched": len(matched), "images_listed": len(rows),
                "images_unique": sum(1 for r in rows if not r["duplicate_of"]),
                "images_downloaded": sum(1 for r in rows if r["image_facts"].get("sha256")),
                "errors": errors, "terms": terms}
    return rows, coverage


def write_outputs(rows, coverage, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(json.dumps({"coverage": coverage, "images": rows}, indent=1, ensure_ascii=False))
    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_title", "handle", "position", "image_alt", "variants", "src", "declared_wxh",
                    "measured_wxh", "bytes", "sha256", "duplicate_of", "visual_class"])
        for r in rows:
            c, i = r["page_claims"], r["image_facts"]
            w.writerow([c["product_title"], c["handle"], c["position"], c["image_alt"], "; ".join(filter(None, c["variants"])),
                        i["src"], f"{i['declared_width']}x{i['declared_height']}",
                        f"{i.get('measured_width')}x{i.get('measured_height')}" if i.get("measured_width") else "",
                        i.get("bytes", ""), i.get("sha256", "")[:12], r["duplicate_of"] or "", ""])
    c = coverage
    (out / "coverage.md").write_text(
        f"# Coverage — {c['store']} — {c['collected_at']}\n\n"
        f"- Pages of /products.json read: {c['pages_read']}\n- Products in store: {c['products_total']}\n"
        f"- Products matching {c['terms'] or 'all'}: {c['products_matched']}\n- Images listed: {c['images_listed']} "
        f"(unique: {c['images_unique']}, downloaded: {c['images_downloaded']})\n- Errors: {len(c['errors'])}\n"
        + "".join(f"  - {e}\n" for e in c["errors"][:20])
        + "\nPage claims and image facts are separate; visual_class is empty until someone looks at the images. "
          "Public availability is not permission to modify or deliver.\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", required=True)
    ap.add_argument("--match", default="", help="comma-separated words matched in product titles (empty = all)")
    ap.add_argument("--out", default="shop_images_out")
    ap.add_argument("--download", action="store_true", help="download unique images into <out>/images")
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    dl = out / "images" if args.download else None
    if dl:
        dl.mkdir(parents=True, exist_ok=True)
    rows, cov = inventory(args.store, args.match.split(","), download_dir=dl)
    write_outputs(rows, cov, out)
    print((out / "coverage.md").read_text())
    if dl:
        print(f"Next: python contact_sheet.py {dl} --out {out / 'contact_sheet'}")
    return rows, cov


if __name__ == "__main__":
    main()
