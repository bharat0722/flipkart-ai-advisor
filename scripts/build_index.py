"""Build (or rebuild) the persistent ChromaDB product index from the Phase 1 CSV.

Usage::

    python scripts/build_index.py            # incremental, idempotent sync
    python scripts/build_index.py --reset    # drop and recreate the collection

Repeated runs upsert by stable chunk ID and delete stale chunks, so the stored
count always equals the number of chunks produced from the current CSV.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import settings  # noqa: E402
from src.chunking import build_document, chunk_products, load_products  # noqa: E402
from src.vector_store import get_client, get_or_create_collection, sync_chunks, write_manifest  # noqa: E402


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build_index(input_path: Path, index_dir: Path, collection_name: str, *, reset: bool = False,
                max_record_chars: int = settings.MAX_RECORD_CHARS, chunk_size: int = settings.CHUNK_SIZE,
                overlap: int = settings.CHUNK_OVERLAP, embedder=None) -> dict:
    started = time.perf_counter()
    products = load_products(input_path)
    chunk_settings = {"max_record_chars": max_record_chars, "size": chunk_size, "overlap": overlap}
    chunks = chunk_products(products, max_record_chars=max_record_chars, chunk_size=chunk_size, overlap=overlap)

    if embedder is None:
        from src.embeddings import get_embedder
        embedder = get_embedder()
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])

    client = get_client(index_dir)
    collection = get_or_create_collection(client, collection_name, embedder.model_name, chunk_settings, reset=reset)
    sync = sync_chunks(collection, chunks, embeddings)
    if sync["stored"] != len(chunks):
        raise RuntimeError(f"Stored {sync['stored']} chunks but produced {len(chunks)}.")

    per_product = Counter(chunk.product_id for chunk in chunks)
    doc_lengths = sorted(len(build_document(p)) for p in products)
    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "index_schema_version": settings.INDEX_SCHEMA_VERSION,
        "input_csv": input_path.resolve().relative_to(ROOT).as_posix() if input_path.resolve().is_relative_to(ROOT) else str(input_path),
        "input_sha256": sha256(input_path),
        "collection": collection_name,
        "index_dir": index_dir.resolve().relative_to(ROOT).as_posix() if index_dir.resolve().is_relative_to(ROOT) else str(index_dir),
        "distance": settings.DISTANCE_METRIC,
        "embedding_model": embedder.model_name,
        "embedding_dimension": embedder.dimension,
        "chunk_settings": chunk_settings,
        "products": len(products),
        "chunks": len(chunks),
        "products_split_into_multiple_chunks": sum(1 for n in per_product.values() if n > 1),
        "max_chunks_per_product": max(per_product.values()),
        "products_with_unknown_price": sum(1 for p in products if p.price is None),
        "categories": dict(sorted(Counter(p.category for p in products).items())),
        "document_chars": {
            "min": doc_lengths[0], "median": doc_lengths[len(doc_lengths) // 2], "max": doc_lengths[-1],
        },
        "sync": sync,
        "python": platform.python_version(),
        "seconds": round(time.perf_counter() - started, 1),
    }
    write_manifest(index_dir, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=settings.PROCESSED_CSV)
    parser.add_argument("--index-dir", type=Path, default=settings.INDEX_DIR)
    parser.add_argument("--collection", default=settings.COLLECTION_NAME)
    parser.add_argument("--max-record-chars", type=int, default=settings.MAX_RECORD_CHARS)
    parser.add_argument("--chunk-size", type=int, default=settings.CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=settings.CHUNK_OVERLAP)
    parser.add_argument("--reset", action="store_true", help="Delete the collection before building.")
    args = parser.parse_args(argv)
    try:
        manifest = build_index(
            args.input, args.index_dir, args.collection, reset=args.reset,
            max_record_chars=args.max_record_chars, chunk_size=args.chunk_size, overlap=args.overlap,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 2
    sync = manifest["sync"]
    print(f"Indexed {manifest['products']} products as {manifest['chunks']} chunks "
          f"({manifest['products_split_into_multiple_chunks']} products split) into "
          f"'{manifest['collection']}' at {manifest['index_dir']}.")
    print(f"Sync: {sync['new']} new, {sync['updated']} updated, {sync['deleted_stale']} stale deleted, "
          f"{sync['stored']} stored. Model {manifest['embedding_model']}. {manifest['seconds']}s.")
    print(f"Input SHA-256 {manifest['input_sha256']}. Manifest: {manifest['index_dir']}/{settings.MANIFEST_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
