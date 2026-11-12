"""Run the Phase 2 sample queries against the real index and write inspectable evidence.

Usage::

    python scripts/retrieval_report.py                      # writes docs/retrieval_evidence.md
    python scripts/retrieval_report.py --output other.md

Each query lists its top-five products with score, product ID, category, price
and source reference, so reviewers can check relevance and identity before any
LLM is involved. A query "passes" when at least ``min_hits`` of the top five
belong to the expected category (or, for budget queries, when every result has a
known price within the limit).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import settings  # noqa: E402
from src.retrieval import Retriever  # noqa: E402
from src.vector_store import read_manifest  # noqa: E402

SAMPLE_QUERIES = [
    # (id, query, expected category or None, min hits in top 5, max_price)
    ("Q1", "laptop for students", "Laptops", 1, None),
    ("Q2", "wifi router for home internet", "Routers & Networking", 3, None),
    ("Q3", "wireless range extender to boost wifi signal", "Routers & Networking", 3, None),
    ("Q4", "headphones with mic for calls", "Headphones & Earphones", 3, None),
    ("Q5", "bluetooth earphones for running", "Headphones & Earphones", 3, None),
    ("Q6", "portable bluetooth speaker", "Speakers", 3, None),
    ("Q7", "fast mobile phone charger", "Chargers & Adapters", 3, None),
    ("Q8", "laptop power adapter replacement", "Chargers & Adapters", 3, None),
    ("Q9", "power bank to charge my phone while travelling", "Power Banks", 2, None),
    ("Q10", "home theater system for movies", "Home Theater", 2, None),
    ("Q11", "pen drive to store files", "USB Storage", 2, None),
    ("Q12", "gaming mouse", "Mice", 1, None),
    ("Q13", "headphones under 1000 rupees", "Headphones & Earphones", 3, 1000),
    ("Q14", "router under 1500", "Routers & Networking", 3, 1500),
]


def run(retriever: Retriever) -> list[dict]:
    rows = []
    for qid, query, category, min_hits, max_price in SAMPLE_QUERIES:
        results = retriever.search(query, settings.DEFAULT_TOP_K, max_price=max_price)
        hits = sum(r.category == category for r in results) if category else None
        budget_ok = all(r.price is not None and r.price <= max_price for r in results) if max_price else True
        identity_ok = all(f"Product ID: {r.product_id}" in r.text and r.source_ref for r in results)
        passed = bool(results) and identity_ok and budget_ok and (hits is None or hits >= min_hits)
        rows.append({"id": qid, "query": query, "category": category, "min_hits": min_hits,
                     "max_price": max_price, "results": results, "hits": hits,
                     "budget_ok": budget_ok, "identity_ok": identity_ok, "passed": passed})
    return rows


def render(rows: list[dict], manifest: dict | None) -> str:
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(row["passed"] for row in rows)
    out = [
        "# Phase 2 retrieval evidence",
        "",
        f"Generated {when} by `python scripts/retrieval_report.py`. Top {settings.DEFAULT_TOP_K} unique products per query, "
        "straight from ChromaDB, with no LLM involved. Scores are cosine similarity (higher is closer). "
        "Prices are historical 2015-16 catalogue values; `unknown` means the source had no valid price.",
        "",
    ]
    if manifest:
        out += [
            "| Index property | Value |", "| --- | --- |",
            f"| Collection | `{manifest['collection']}` in `{manifest['index_dir']}` |",
            f"| Embedding model | `{manifest['embedding_model']}` ({manifest['embedding_dimension']} dims, {manifest['distance']}) |",
            f"| Chunk settings | {manifest['chunk_settings']} |",
            f"| Products / chunks | {manifest['products']} / {manifest['chunks']} "
            f"({manifest['products_split_into_multiple_chunks']} products split) |",
            f"| Input CSV SHA-256 | `{manifest['input_sha256']}` |",
            f"| Built | {manifest['built_at_utc']} |",
            "",
        ]
    out += [f"**Summary: {passed} of {len(rows)} sample queries passed.**", "",
            "| ID | Query | Expectation | Result |", "| --- | --- | --- | --- |"]
    for row in rows:
        expectation = f">= {row['min_hits']} of 5 in {row['category']}"
        if row["max_price"]:
            expectation += f"; all known prices <= INR {row['max_price']:,}"
        got = f"{row['hits']}/5 in category" if row["hits"] is not None else ""
        if row["max_price"]:
            got += f"; budget {'respected' if row['budget_ok'] else 'VIOLATED'}"
        out.append(f"| {row['id']} | {row['query']} | {expectation} | {got} - **{'PASS' if row['passed'] else 'FAIL'}** |")
    for row in rows:
        title = f"## {row['id']} - \"{row['query']}\""
        if row["max_price"]:
            title += f" (max_price={row['max_price']})"
        out += ["", title, "", "| # | Score | Product | Category | Price | Product ID | Source |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in row["results"]:
            price = f"INR {r.price:,.0f}" if r.price is not None else "unknown"
            name = r.name.replace("|", "/")
            source = f"row {r.source_row}, chunk {r.chunk_index + 1}/{r.chunk_count}"
            out.append(f"| {r.rank} | {r.score:.3f} | {name} | {r.category} | {price} | `{r.product_id}` | {source} |")
        if not row["results"]:
            out.append("| - | - | No results | - | - | - | - |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "retrieval_evidence.md")
    parser.add_argument("--index-dir", type=Path, default=settings.INDEX_DIR)
    args = parser.parse_args(argv)
    retriever = Retriever(index_dir=args.index_dir)
    rows = run(retriever)
    args.output.write_text(render(rows, read_manifest(args.index_dir)), encoding="utf-8")
    for row in rows:
        print(f"{row['id']:>4} {'PASS' if row['passed'] else 'FAIL'}  {row['query']}")
    print(f"{sum(r['passed'] for r in rows)}/{len(rows)} passed. Evidence written to {args.output}")
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
