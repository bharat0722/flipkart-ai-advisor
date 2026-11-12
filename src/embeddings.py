"""Sentence Transformers embeddings shared by indexing and querying.

The same model and normalisation are used on both sides. ``Embedder`` is a tiny
interface so tests can inject a deterministic fake without downloading a model.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Protocol, Sequence

from src import settings

# Keep library logs quiet and avoid tokenizer fork warnings.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


class Embedder(Protocol):
    model_name: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """L2-normalised all-MiniLM-L6-v2 embeddings (cosine similarity = dot product)."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, batch_size: int = settings.EMBEDDING_BATCH_SIZE):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = _load_model(model_name)
        get_dimension = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
        self.dimension = int(get_dimension())

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts), batch_size=self.batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=len(texts) > self.batch_size,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "sentence-transformers is not installed. Run `python -m pip install -r requirements.txt`."
        ) from exc
    return SentenceTransformer(model_name, device="cpu")


def get_embedder(model_name: str = settings.EMBEDDING_MODEL) -> Embedder:
    return SentenceTransformerEmbedder(model_name)
