# contact_sheet — choose a master image from real files

NON_SOVEREIGN · authority=false · no AI · no spending. Built for HELEN mission M001 (Manucurist COLOR SHIFT); generic.

> Three contact-sheet tools were written in parallel for M001 (this one, a ChatGPT zip, and `helen-os-JMTC/tools/contact_sheet.py`
> on the operator's machine). For M001, use **one**: the operator chooses. This version includes the two fixes found by the
> local one: colour-aware near-duplicates (shade variants are never merged) and denoised sharpness.

```
pip install pillow numpy          # ffmpeg/ffprobe optional (videos)

# 1. Stills / rushes you downloaded (e.g. the 10 "Still 2025-05-17…" JPEGs, the 4 Calvi .mov)
python contact_sheet.py ~/Downloads/calvi --out ~/HELEN_M001/contact_sheet --fps 1

# 2. Optional, after marking the nail on each image: roi.json {"file.jpg": [x, y, w, h]}
python contact_sheet.py ~/Downloads/calvi --roi roi.json --min-roi-short-side 400

# 3. Public official product images (Shopify store), page claims kept apart from image facts
python shop_images.py --store https://www.manucurist.com \
  --match "active glow,coral reef,pistachio,chestnut" --out ~/HELEN_M001/public --download
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
