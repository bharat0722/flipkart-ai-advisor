"""Turn cleaned product records into identity-preserving text chunks.

Every chunk starts with the same identity header (name, product ID, category,
brand, historical price), so a specification can never be separated from the
product it belongs to. Short records become a single chunk. Long bodies are split
into overlapping character windows that break on whitespace.
"""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path

from src import settings

REQUIRED_COLUMNS = {
    "product_id", "name", "category", "brand", "price", "description", "specifications",
    "source_ref", "source_uniq_id", "source_url", "source_row", "description_source",
}


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    brand: str
    price: float | None
    retail_price: float | None
    description: str
    specifications: str
    description_source: str
    source_ref: str
    source_uniq_id: str
    source_url: str
    source_row: int


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    product_id: str
    text: str
    metadata: dict = field(hash=False)


def parse_price(value: str) -> float | None:
    """Return a positive finite price or ``None``. Unknown is never zero."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        price = float(value)
    except ValueError:
        return None
    return price if math.isfinite(price) and price > 0 else None


def load_products(path: Path = settings.PROCESSED_CSV) -> list[Product]:
    """Read the Phase 1 CSV and validate the columns Phase 2 depends on."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Processed catalogue not found at {path}. Run `python -m src.preprocess` first."
        )
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Processed CSV is missing columns: {', '.join(sorted(missing))}")
        products = []
        seen = set()
        for row in reader:
            product_id = row["product_id"].strip()
            if not product_id or not row["name"].strip():
                raise ValueError(f"Row {reader.line_num} has no product_id or name.")
            if product_id in seen:
                raise ValueError(f"Duplicate product_id {product_id} in {path}.")
            seen.add(product_id)
            products.append(Product(
                product_id=product_id,
                name=row["name"].strip(),
                category=row["category"].strip(),
                brand=row["brand"].strip(),
                price=parse_price(row["price"]),
                retail_price=parse_price(row.get("retail_price", "")),
                description=row["description"].strip(),
                specifications=row["specifications"].strip(),
                description_source=row["description_source"].strip(),
                source_ref=row["source_ref"].strip(),
                source_uniq_id=row["source_uniq_id"].strip(),
                source_url=row["source_url"].strip(),
                source_row=int(row["source_row"]),
            ))
    if not products:
        raise ValueError(f"{path} contains no products.")
    return products


def format_price(price: float | None) -> str:
    if price is None:
        return "unknown"
    return f"INR {price:,.0f}" if float(price).is_integer() else f"INR {price:,.2f}"


def identity_header(product: Product) -> str:
    """Identity lines repeated on every chunk of a product."""
    return "\n".join([
        f"Product: {product.name}",
        f"Product ID: {product.product_id}",
        f"Category: {product.category}",
        f"Brand: {product.brand or 'unknown'}",
        f"Historical price (2015-16 catalogue): {format_price(product.price)}",
    ])


def document_body(product: Product) -> str:
    """Description plus specifications, without repeating specs already in the description."""
    parts = [f"Description: {product.description}"]
    if product.specifications and product.description_source != "source_specifications":
        parts.append(f"Specifications: {product.specifications}")
    return "\n".join(parts)


def build_document(product: Product) -> str:
    """Full structured text document for one product."""
    return f"{identity_header(product)}\n{document_body(product)}"


def split_text(text: str, size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> list[str]:
    """Split ``text`` into windows of at most ``size`` characters with ``overlap``.

    Window ends move back to the nearest whitespace so words are not cut; the
    next window starts ``overlap`` characters before the previous end (also
    aligned to whitespace).
    """
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size.")
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    pieces = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start + size // 2, end)
            if space != -1:
                end = space
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        next_start = max(end - overlap, start + 1)
        # Align the overlap start to a word boundary.
        space = text.find(" ", next_start, end)
        start = space + 1 if space != -1 else next_start
    return pieces


def chunk_product(
    product: Product,
    max_record_chars: int = settings.MAX_RECORD_CHARS,
    chunk_size: int = settings.CHUNK_SIZE,
    overlap: int = settings.CHUNK_OVERLAP,
) -> list[Chunk]:
    header = identity_header(product)
    body = document_body(product)
    bodies = [body] if len(body) <= max_record_chars else split_text(body, chunk_size, overlap)
    chunks = []
    for index, piece in enumerate(bodies):
        if index > 0 and not piece.startswith(("Description:", "Specifications:")):
            piece = f"(continued) {piece}"
        text = f"{header}\n{piece}"
        chunk_id = f"{product.product_id}::chunk-{index:02d}"
        chunks.append(Chunk(
            chunk_id=chunk_id,
            product_id=product.product_id,
            text=text,
            metadata=chunk_metadata(product, chunk_id, index, len(bodies), text),
        ))
    return chunks


def chunk_metadata(product: Product, chunk_id: str, index: int, count: int, text: str) -> dict:
    """ChromaDB metadata. Values must be str/int/float/bool, so unknown prices are omitted
    and flagged with ``price_known=False`` rather than stored as zero."""
    metadata = {
        "chunk_id": chunk_id,
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "price_known": product.price is not None,
        "source_ref": product.source_ref,
        "source_uniq_id": product.source_uniq_id,
        "source_url": product.source_url,
        "source_row": product.source_row,
        "description_source": product.description_source,
        "chunk_index": index,
        "chunk_count": count,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    if product.price is not None:
        metadata["price"] = float(product.price)
    if product.retail_price is not None:
        metadata["retail_price"] = float(product.retail_price)
    return metadata


def chunk_products(products: list[Product], **kwargs) -> list[Chunk]:
    chunks = [chunk for product in products for chunk in chunk_product(product, **kwargs)]
    ids = [chunk.chunk_id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Chunk IDs are not unique.")
    return chunks
