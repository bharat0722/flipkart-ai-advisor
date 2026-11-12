"""Persistent ChromaDB storage for product chunks.

Chunks are upserted by their stable ``chunk_id`` and stale IDs are deleted, so a
repeated build converges on exactly one copy of each chunk. The collection
metadata records the embedding model and chunk settings; queries refuse to run
against a collection built with a different model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from src import settings
from src.chunking import Chunk


class IndexNotReadyError(RuntimeError):
    """Raised when the index is missing or incompatible with the current settings."""


def get_client(index_dir: Path = settings.INDEX_DIR):
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    index_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(index_dir),
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
    )


def collection_metadata(model_name: str, chunk_settings: dict) -> dict:
    return {
        "hnsw:space": settings.DISTANCE_METRIC,
        "embedding_model": model_name,
        "index_schema_version": settings.INDEX_SCHEMA_VERSION,
        **{f"chunk_{key}": value for key, value in chunk_settings.items()},
    }


def get_or_create_collection(client, name: str, model_name: str, chunk_settings: dict, reset: bool = False):
    if reset:
        try:
            client.delete_collection(name)
        except Exception:  # collection did not exist
            pass
    collection = client.get_or_create_collection(
        name=name, metadata=collection_metadata(model_name, chunk_settings), embedding_function=None,
    )
    existing = (collection.metadata or {}).get("embedding_model")
    if existing and existing != model_name:
        raise IndexNotReadyError(
            f"Collection {name!r} was built with {existing!r}, not {model_name!r}. Rebuild with --reset."
        )
    return collection


def open_collection(index_dir: Path = settings.INDEX_DIR, name: str = settings.COLLECTION_NAME,
                    model_name: str = settings.EMBEDDING_MODEL):
    """Open an existing collection for querying, validating the embedding model."""
    if not index_dir.is_dir():
        raise IndexNotReadyError(f"No index at {index_dir}. Run `python scripts/build_index.py` first.")
    client = get_client(index_dir)
    try:
        collection = client.get_collection(name=name, embedding_function=None)
    except Exception as exc:
        raise IndexNotReadyError(
            f"Collection {name!r} not found in {index_dir}. Run `python scripts/build_index.py`."
        ) from exc
    built_with = (collection.metadata or {}).get("embedding_model")
    if built_with != model_name:
        raise IndexNotReadyError(f"Index was built with {built_with!r}; queries use {model_name!r}. Rebuild the index.")
    return collection


def sync_chunks(collection, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]], batch_size: int = 256) -> dict:
    """Upsert ``chunks`` and delete any stored chunk IDs that are no longer produced."""
    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk needs exactly one embedding.")
    new_ids = [chunk.chunk_id for chunk in chunks]
    existing_ids = set(collection.get(include=[])["ids"])
    stale = sorted(existing_ids.difference(new_ids))
    for start in range(0, len(stale), batch_size):
        collection.delete(ids=stale[start:start + batch_size])
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        collection.upsert(
            ids=[chunk.chunk_id for chunk in batch],
            documents=[chunk.text for chunk in batch],
            metadatas=[chunk.metadata for chunk in batch],
            embeddings=[list(vector) for vector in embeddings[start:start + batch_size]],
        )
    return {
        "upserted": len(chunks),
        "new": len(set(new_ids) - existing_ids),
        "updated": len(set(new_ids) & existing_ids),
        "deleted_stale": len(stale),
        "stored": collection.count(),
    }


def write_manifest(index_dir: Path, manifest: dict) -> Path:
    path = index_dir / settings.MANIFEST_NAME
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_manifest(index_dir: Path = settings.INDEX_DIR) -> dict | None:
    path = index_dir / settings.MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
