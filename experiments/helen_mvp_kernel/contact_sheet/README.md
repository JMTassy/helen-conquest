# contact_sheet — choose a master image from real files

NON_SOVEREIGN · authority=false · no AI · no spending. Built for HELEN mission M001 (Manucurist COLOR SHIFT); generic.

> **Working version** for M001, consolidated from three parallel implementations; the ChatGPT zip stays a separate
> prototype (reference only). Exact duplicates (file or decoded pixels) are excluded, keeping the annotated copy;
> resemblances (luminance hash AND local colour) are only flagged. Sharpness is denoised and a noise estimate flags
> images whose sharpness is unreliable. Blown highlights are penalised inside the nail box only.
> The ranking is content-blind: it cannot see whether nails are visible at all. A person chooses.

```
pip install pillow numpy          # ffmpeg/ffprobe optional (videos)

# 1. Stills / rushes you downloaded (e.g. the 10 "Still 2025-05-17…" JPEGs, the 4 Calvi .mov)
python contact_sheet.py ~/Downloads/calvi --out ~/HELEN_M001/contact_sheet --fps 1

# 2. After marking the nail: metadata.json {"file.jpg": {"nail_roi": [x, y, w, h], "source": "..."}}
python contact_sheet.py ~/Downloads/calvi --metadata metadata.json --require-nail --min-roi-short-side 400

# 3. Public official product images (Shopify store), page claims kept apart from image facts
python shop_images.py --store https://www.manucurist.com \
  --match "<shades named in the M001 sources>" --out ~/HELEN_M001/public --download
# (e.g. the shades seen in the S3 Instagram captions; tie each one to an M001 source before using it)
python contact_sheet.py ~/HELEN_M001/public/images --out ~/HELEN_M001/public/contact_sheet
```

`contact_sheet.py` reports, per image: pixel dimensions, size, estimated JPEG quality, EXIF, sharpness (Laplacian
variance) of the whole image, of the sharpest tile and of the nail ROI if given, duplicates, and, when videos are in
the folder, the nearest sampled video frame (checks whether stills come from those rushes). It proposes up to 3
candidates that pass the resolution gates and are not far blurrier than the best; if none pass, the verdict says HD
originals are needed. Numbers rank; a person confirms at 100 %.

`shop_images.py` writes `inventory.json/.csv` and `coverage.md`; `visual_class` stays empty until someone looks.
Public availability is not permission to modify or deliver.

Tests: `pytest experiments/helen_mvp_kernel/contact_sheet/tests -q` (synthetic images; the video test needs ffmpeg).
