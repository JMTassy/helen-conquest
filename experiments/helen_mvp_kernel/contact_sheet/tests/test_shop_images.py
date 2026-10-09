import io
import json
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import shop_images as si  # noqa: E402


def png(w, h):
    b = io.BytesIO()
    Image.new("RGB", (w, h), (200, 30, 60)).save(b, "PNG")
    return b.getvalue()


PRODUCTS = {"products": [
    {"title": "Active Glow Cranberry", "handle": "active-glow-cranberry",
     "variants": [{"id": 1, "title": "15 ml"}],
     "images": [{"id": 11, "position": 1, "src": "https://cdn.shop/files/cran.png?v=1", "width": 2000, "height": 2000,
                 "alt": "Active Glow Cranberry porté", "variant_ids": [1]},
                {"id": 12, "position": 2, "src": "https://cdn.shop/files/routine_800x.png?v=2", "width": 800, "height": 800,
                 "alt": "Routine avec Green Coral Reef", "variant_ids": []}]},
    {"title": "Green Coral Reef", "handle": "green-coral-reef", "variants": [],
     "images": [{"id": 21, "position": 1, "src": "https://cdn.shop/files/routine.png?v=9", "width": 1600, "height": 1600,
                 "alt": None, "variant_ids": []}]},
    {"title": "Solvant doux", "handle": "solvant", "variants": [], "images": []}]}


def fake_fetch(url):
    if "products.json" in url:
        return json.dumps(PRODUCTS if "page=1" in url else {"products": []}).encode()
    if url.endswith("cran.png"):
        return png(40, 30)
    if url.endswith("routine.png"):
        raise OSError("HTTP 404")
    raise AssertionError(url)


def test_inventory_separates_claims_from_facts_and_dedups(tmp_path):
    dl = tmp_path / "images"
    dl.mkdir()
    rows, cov = si.inventory("https://shop.test", ["cranberry", "coral reef"], fetch=fake_fetch, download_dir=dl)
    assert cov["products_total"] == 3 and cov["products_matched"] == 2 and cov["images_listed"] == 3
    first = rows[0]
    assert first["page_claims"]["image_alt"] == "Active Glow Cranberry porté" and first["page_claims"]["variants"] == ["15 ml"]
    assert first["image_facts"]["measured_width"] == 40 and first["image_facts"]["declared_width"] == 2000  # declared ≠ measured is kept visible
    assert first["visual_class"] is None
    # the 800px routine image and the full one are the same file: counted once
    assert rows[2]["duplicate_of"] == "active-glow-cranberry#2" and cov["images_unique"] == 2
    # failed download is recorded, not hidden
    assert "download_error" in rows[1]["image_facts"] and cov["errors"]


def test_outputs_and_canonical_urls(tmp_path):
    rows, cov = si.inventory("https://shop.test", [], fetch=fake_fetch)
    si.write_outputs(rows, cov, tmp_path / "o")
    assert "Images listed: 3" in (tmp_path / "o/coverage.md").read_text()
    assert si.canonical("//cdn.x/files/a_1024x1024.jpg?v=3") == "https://cdn.x/files/a.jpg"


def test_network_failure_is_reported(tmp_path):
    def down(url):
        raise OSError("blocked")
    rows, cov = si.inventory("https://shop.test", [], fetch=down)
    assert rows == [] and cov["pages_read"] == 0 and "blocked" in cov["errors"][0]
