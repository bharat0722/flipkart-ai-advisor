"""Semantic product retrieval over the persistent ChromaDB index.

Returns inspectable evidence (text + product/source metadata) without calling an
LLM. Optional metadata filters support budget limits and categories; products
with an unknown price are never returned when a price filter is applied.

CLI::

    python -m src.retrieval "laptop for students"
    python -m src.retrieval "wireless headphones" --max-price 2000 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from src import settings
from src.embeddings import Embedder, get_embedder
from src.vector_store import IndexNotReadyError, open_collection


@dataclass(frozen=True)
class RetrievedChunk:
    """One piece of evidence. ``price`` is ``None`` when the catalogue price is unknown."""

    rank: int
    score: float          # cosine similarity in [-1, 1]; higher is more similar
    chunk_id: str
    product_id: str
    name: str
    category: str
    brand: str
    price: float | None
    source_ref: str
    source_url: str
    source_row: int
    chunk_index: int
    chunk_count: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_where(max_price: float | None = None, min_price: float | None = None,
                categories: list[str] | None = None) -> dict | None:
    """Build a ChromaDB metadata filter. Price filters require a known price."""
    conditions: list[dict] = []
    if max_price is not None or min_price is not None:
        conditions.append({"price_known": {"$eq": True}})
        if max_price is not None:
            conditions.append({"price": {"$lte": float(max_price)}})
        if min_price is not None:
            conditions.append({"price": {"$gte": float(min_price)}})
    if categories:
        conditions.append({"category": {"$in": list(categories)}} if len(categories) > 1
                          else {"category": {"$eq": categories[0]}})
    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


class Retriever:
    """Embeds a query with the indexing model and searches the collection."""

    def __init__(self, collection=None, embedder: Embedder | None = None,
                 index_dir: Path = settings.INDEX_DIR, collection_name: str = settings.COLLECTION_NAME):
        self.embedder = embedder or get_embedder()
        self.collection = collection if collection is not None else open_collection(
            index_dir, collection_name, self.embedder.model_name,
        )

    def search(self, query: str, k: int = settings.DEFAULT_TOP_K, *, max_price: float | None = None,
               min_price: float | None = None, categories: list[str] | None = None,
               unique_products: bool = True) -> list[RetrievedChunk]:
        query = (query or "").strip()
        if not query:
            raise ValueError("Query must not be empty.")
        if k <= 0:
            raise ValueError("k must be positive.")
        total = self.collection.count()
        if total == 0:
            return []
        n_results = min(total, k * settings.CANDIDATE_MULTIPLIER if unique_products else k)
        response = self.collection.query(
            query_embeddings=[self.embedder.embed_query(query)],
            n_results=n_results,
            where=build_where(max_price, min_price, categories),
            include=["documents", "metadatas", "distances"],
        )
        results: list[RetrievedChunk] = []
        seen_products: set[str] = set()
        for chunk_id, text, meta, distance in zip(
            response["ids"][0], response["documents"][0], response["metadatas"][0], response["distances"][0],
        ):
            if unique_products and meta["product_id"] in seen_products:
                continue
            seen_products.add(meta["product_id"])
            results.append(RetrievedChunk(
                rank=len(results) + 1,
                score=round(1.0 - float(distance), 4),
                chunk_id=chunk_id,
                product_id=meta["product_id"],
                name=meta["name"],
                category=meta["category"],
                brand=meta.get("brand", ""),
                price=meta.get("price") if meta.get("price_known") else None,
                source_ref=meta["source_ref"],
                source_url=meta["source_url"],
                source_row=int(meta["source_row"]),
                chunk_index=int(meta["chunk_index"]),
                chunk_count=int(meta["chunk_count"]),
                text=text,
            ))
            if len(results) == k:
                break
        return results


def format_results(query: str, results: list[RetrievedChunk], show_text: bool = True) -> str:
    """Human-readable evidence listing for inspection before anything reaches an LLM."""
    lines = [f'Query: "{query}" - {len(results)} result(s)']
    for item in results:
        price = f"INR {item.price:,.0f}" if item.price is not None else "unknown"
        lines.append(
            f"\n#{item.rank}  score={item.score:.3f}  {item.name}\n"
            f"    product_id={item.product_id}  category={item.category}  brand={item.brand or 'unknown'}\n"
            f"    historical_price={price}  chunk={item.chunk_index + 1}/{item.chunk_count}\n"
            f"    source={item.source_ref} (row {item.source_row})"
        )
        if show_text:
            snippet = item.text.replace("\n", " | ")
            lines.append(f"    text: {snippet[:300]}{'...' if len(snippet) > 300 else ''}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search the product index and print the evidence.")
    parser.add_argument("query")
    parser.add_argument("-k", "--top-k", type=int, default=settings.DEFAULT_TOP_K)
    parser.add_argument("--max-price", type=float)
    parser.add_argument("--min-price", type=float)
    parser.add_argument("--category", action="append", help="Restrict to a category (repeatable).")
    parser.add_argument("--all-chunks", action="store_true", help="Do not collapse multiple chunks of one product.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--index-dir", type=Path, default=settings.INDEX_DIR)
    args = parser.parse_args(argv)
    try:
        retriever = Retriever(index_dir=args.index_dir)
        results = retriever.search(
            args.query, args.top_k, max_price=args.max_price, min_price=args.min_price,
            categories=args.category, unique_products=not args.all_chunks,
        )
    except (IndexNotReadyError, ValueError) as exc:
        print(f"Retrieval failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([item.to_dict() for item in results], indent=2, ensure_ascii=False))
    else:
        print(format_results(args.query, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
