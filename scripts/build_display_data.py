"""Build the product image and rating lookup used by the Streamlit product cards.

Usage::

    python scripts/build_display_data.py

Reads the raw Kaggle CSV and the Phase 1 cleaned CSV and writes
``data/processed/product_display.json``: ``{product_id: {"image_url", "rating"}}``.
The Phase 1 and Phase 2 outputs are not changed. ``rating`` is ``None`` when the
catalogue says "No rating available". Images are served from Flipkart's HTTPS
image CDN (the catalogue's 2015 ``img5a`` links are plain HTTP).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "flipkart_com-ecommerce_sample.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "electronics.csv"
OUTPUT = ROOT / "data" / "processed" / "product_display.json"
IMAGE_CDN = "https://rukminim1.flixcart.com/image/400/400/"


def image_url(images: str) -> str | None:
    """First catalogue image, rewritten to the HTTPS CDN. ``None`` if the row has no image."""
    try:
        urls = json.loads(images)
    except (TypeError, ValueError):
        return None
    for url in urls:
        _, sep, path = url.partition("/image/")
        if sep and path:
            return IMAGE_CDN + path
    return None


def rating(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):  # "No rating available" or blank
        return None


def build(raw_csv: Path = RAW_CSV, clean_csv: Path = CLEAN_CSV) -> dict[str, dict]:
    clean = pd.read_csv(clean_csv, dtype=str)
    raw = pd.read_csv(raw_csv, dtype=str).set_index("uniq_id")
    out = {}
    for product_id, uniq_id in zip(clean["product_id"], clean["source_uniq_id"]):
        if uniq_id not in raw.index:  # synthetic records have no Flipkart row, image or rating
            continue
        row = raw.loc[uniq_id]
        out[product_id] = {"image_url": image_url(row["image"]), "rating": rating(row["overall_rating"])}
    return out


def main() -> int:
    if not RAW_CSV.exists() or not CLEAN_CSV.exists():
        print("Missing data. Download the raw CSV and run `python -m src.preprocess` first (see README).")
        return 1
    data = build()
    OUTPUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    images = sum(v["image_url"] is not None for v in data.values())
    rated = sum(v["rating"] is not None for v in data.values())
    print(f"Wrote {len(data)} products to {OUTPUT.relative_to(ROOT)}: {images} with images, {rated} with ratings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
