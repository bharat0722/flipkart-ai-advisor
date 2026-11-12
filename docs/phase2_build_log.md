# Phase 2 build log — Embeddings, chunking and vector database

**Owner:** M2 (Retrieval & Index) · **Receiving lead:** M3 (Grounded RAG) · **QA:** M5 · **Branch:** `feat/phase-02-retrieval-index` · **Date:** 12 November 2026

This document records everything built in Phase 2: what each piece does, why it was designed that way, the exact commands, and the results observed on real data. The formal acceptance record is the [Phase 2 handoff](handoffs/phase-02.md). Generated top-five evidence for 14 sample queries is in [retrieval_evidence.md](retrieval_evidence.md).

---

## 1. Goal

Make the Phase 1 product catalogue searchable **by meaning**, not exact words, and return inspectable evidence (text + product identity + source) that M3 can pass to an LLM in Phase 3.

Plan tasks (PDF page 6) and where each one is implemented:

| # | Plan task | Implemented in | Status |
| --- | --- | --- | --- |
| 01 | Convert product records into structured text documents | `src/chunking.py` → `build_document()` | Done |
| 02 | Keep short records together; split lengthy descriptions | `src/chunking.py` → `chunk_product()` | Done |
| 03 | Start with 500–800-char chunks, 75-char overlap; test context preservation | `src/settings.py`, `split_text()`; experiment in §6 | Done (700/75 chosen) |
| 04 | Generate embeddings with Sentence Transformers | `src/embeddings.py` (`all-MiniLM-L6-v2`) | Done |
| 05 | Store embeddings and source metadata in ChromaDB | `src/vector_store.py`, `scripts/build_index.py` | Done |
| 06 | Semantic similarity search, ~5 results per question | `src/retrieval.py` → `Retriever.search()` | Done |
| 07 | Verify retrieved chunks keep product name, ID, price and source | Tests + `scripts/retrieval_report.py` | Done |

---

## 2. What was built (file by file)

| File | New/changed | Purpose |
| --- | --- | --- |
| `src/settings.py` | New | One place for every Phase 2 setting: model name, collection name, chunk size/overlap, top-k, index path. Indexing and querying import the same values. |
| `src/chunking.py` | New | Loads `data/processed/electronics.csv`, validates columns and unique IDs, builds one structured document per product, splits long bodies into overlapping chunks, attaches metadata. |
| `src/embeddings.py` | New | Thin wrapper around Sentence Transformers. Normalised 384-dim vectors. Defines an `Embedder` interface so tests can use a fake embedder (no download). |
| `src/vector_store.py` | New | Persistent ChromaDB client (telemetry off), collection creation that records the model and chunk settings, idempotent `sync_chunks()` (upsert + delete stale), model-mismatch guard, manifest read/write. |
| `src/retrieval.py` | New | `Retriever.search(query, k=5, max_price=, min_price=, categories=)` → `list[RetrievedChunk]`. De-duplicates to one best chunk per product. CLI for manual inspection. |
| `scripts/build_index.py` | New | Ingestion command. CSV → chunks → embeddings → ChromaDB → `chroma_db/index_manifest.json`. |
| `scripts/retrieval_report.py` | New | Runs 14 real sample queries and writes `docs/retrieval_evidence.md` with pass/fail per query. |
| `tests/test_chunking.py` | New | 14 tests: splitting, overlap, word boundaries, documents, unknown prices, metadata types, CSV loading. |
| `tests/test_retrieval.py` | New | 15 offline tests on a real temporary ChromaDB (fake embedder) + 6 real-model acceptance tests (`RUN_MODEL_TESTS=1`). |
| `requirements.txt` | Changed | Added pinned `torch`, `sentence-transformers`, `transformers`, `chromadb`. |
| `.github/workflows/checks.yml` | Changed | Installs CPU-only torch first (avoids multi-GB CUDA wheels), compiles `scripts/`. |
| `.env.example` | Changed | Documents optional `RUN_MODEL_TESTS` and `HF_HOME`. No secrets needed in Phase 2. |
| `docs/architecture.md` | Changed | Phase 2 data flow and module table. |
| `docs/handoffs/phase-02.md`, `docs/phase_status.json`, `docs/PRD.md`, `README.md` | Changed/new | Handoff, status and setup. |

`chroma_db/` (the generated index) is already in `.gitignore` and is **not committed**; it is rebuilt from the documented inputs.

---

## 3. Design decisions and why

### 3.1 Document format

Each product becomes a structured text document:

```
Product: <name>
Product ID: P-<uniq_id>
Category: <category>
Brand: <brand or unknown>
Historical price (2015-16 catalogue): INR <price> | unknown
Description: <description>
Specifications: <Key: value | Key: value ...>
```

- **Identity header on every chunk.** The first five lines are repeated on every chunk of a product. This satisfies the plan's rule "never detach specifications from their product identity": even chunk 7 of 10 says which product it belongs to, both to the embedding model and to the LLM later.
- **Price labelled as historical.** The text says "Historical price (2015-16 catalogue)" so nothing downstream reads it as a current Flipkart price.
- **Unknown price is the word `unknown`, never `0`.** 10 of 288 products have no valid price.
- **No duplicated specs.** When Phase 1 built the description *from* the specifications (`description_source = source_specifications`, 112 products), the specifications line is omitted to avoid repeating the same facts.

### 3.2 Chunking

- Body (description + specifications) **≤ 800 chars → one chunk** ("keep short records together").
- Longer bodies → windows of **700 chars with 75-char overlap**. Window ends move back to the nearest space so words are never cut; the next window starts 75 chars earlier, also on a word boundary. Continuation chunks are marked `(continued)`.
- **Why 700:** with the ~230-char identity header, a chunk is at most ~1,017 chars ≈ 250 word-pieces, which fits inside `all-MiniLM-L6-v2`'s 256-token input window. Larger windows (800) push some chunks past 256 tokens, and the model silently truncates the tail. See the measured comparison in §6.
- **Stable chunk IDs:** `P-<uniq_id>::chunk-NN`. The same CSV always produces the same IDs, which is what makes rebuilds idempotent.

Observed on the real catalogue: documents range from 306 to 6,438 chars (median 1,701). **254 of 288 products are split**, giving **863 chunks** (max 10 chunks for one product).

### 3.3 Metadata stored with every chunk

| Key | Example / meaning |
| --- | --- |
| `chunk_id`, `chunk_index`, `chunk_count` | `P-…::chunk-02`, 2, 5 |
| `product_id`, `name`, `category`, `brand` | Product identity |
| `price` | Float INR, **present only when known** |
| `price_known` | `True` / `False` (ChromaDB cannot store `None`, so unknown prices are omitted and flagged rather than stored as 0) |
| `retail_price` | Float INR when known |
| `source_ref`, `source_uniq_id`, `source_url`, `source_row` | Provenance back to the raw Kaggle row |
| `description_source` | `source_description` or `source_specifications` |
| `content_sha256` | Hash of the chunk text (change detection) |

### 3.4 Embeddings

- `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, run on CPU.
- Vectors are **L2-normalised**, and the collection uses **cosine** distance. Results report `score = 1 − cosine distance` (higher = more similar).
- The **same embedder object** encodes both documents and queries. The model name is stored in the collection metadata; `open_collection()` refuses to query an index built with a different model (`IndexNotReadyError`).

### 3.5 Vector store and idempotent ingestion

- `chromadb.PersistentClient` at `chroma_db/`, collection `flipkart_electronics_v1`, anonymised telemetry disabled.
- `sync_chunks()` **upserts by `chunk_id`** and **deletes IDs no longer produced** by the current CSV. Running the build twice leaves exactly 863 chunks; shrinking the CSV removes the stale chunks. `--reset` drops and recreates the collection.
- Each build writes `chroma_db/index_manifest.json`: model, dimension, chunk settings, collection, input CSV SHA-256, product/chunk counts, category counts, document length stats, sync counts, Python version, build time. This is the "index build metadata" the plan's integration contract asks for.

### 3.6 Retrieval

- `Retriever.search()` embeds the query, asks ChromaDB for `k × 4` candidate chunks, then keeps the **best chunk per product** until it has `k` products (default 5). `unique_products=False` returns raw chunks.
- **Budget filters:** `max_price` / `min_price` add `price_known == True` to the ChromaDB `where` filter, so a product with unknown price can **never** be returned as "within budget".
- **Category filter:** `categories=["Speakers"]`.
- Each result (`RetrievedChunk`) carries: `rank, score, chunk_id, product_id, name, category, brand, price (None if unknown), source_ref, source_url, source_row, chunk_index, chunk_count, text`. `to_dict()` gives JSON.
- Results are inspectable **without any LLM**: `python -m src.retrieval "query"` prints them; `--json` gives machine-readable output.

---

## 4. Environment notes (what happened during the build)

- Repository cloned from `bharat0722/flipkart-ai-advisor` at `main` = `be70f63`. Branch `feat/phase-02-retrieval-index` created from it.
- The machine is **Windows 11 on ARM64**. Native ARM64 Python 3.12 could not install the pinned stack: there is no Windows-ARM64 wheel for `pandas==2.2.3` (Phase 1 pin), PyPI has no Windows-ARM64 `torch`, and `chromadb` had to compile from Rust source.
- **Fix:** used [`uv`](https://github.com/astral-sh/uv) to fetch a user-local **x64 CPython 3.12.16**, which runs under Windows' x64 emulation, and created `.venv` with it. Every pinned wheel exists for win-amd64. Teammates on macOS/Linux/x64 Windows can follow the normal README steps.
  ```powershell
  python -m pip install --user uv
  python -m uv python install cpython-3.12-windows-x86_64-none
  python -m uv venv .venv --python cpython-3.12-windows-x86_64-none --seed
  .venv\Scripts\python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
  .venv\Scripts\python -m pip install -r requirements.txt
  ```
- Resolved versions: torch 2.15.0+cpu, sentence-transformers 6.3.0, transformers 5.22.2, chromadb 1.5.9, onnxruntime 1.31.1, tokenizers 0.23.3, numpy 2.3.5, pandas 2.2.3. `pip check`: no broken requirements.
- CI (`ubuntu-latest`) now installs CPU-only torch first so the job does not download CUDA libraries.

---

## 5. Commands run and results

| Step | Command | Observed result |
| --- | --- | --- |
| Download data | `curl -fL …/promptcloudhq/flipkart-products -o flipkart-products.zip` then `python -m zipfile -e … data/raw` | Raw SHA-256 `56f8f699…93ad1` — **matches** Phase 1 |
| Reproduce Phase 1 | `python -m src.preprocess` | `Retained 288 of 20000 records from 389 candidates.` Cleaned SHA-256 `f13d7836…4bc9` — **byte-identical** to the Phase 1 handoff |
| Build index | `python scripts/build_index.py` | `Indexed 288 products as 863 chunks (254 products split)`. 863 new, 863 stored. First run 141.9 s (includes model download) |
| Rebuild (idempotency) | `python scripts/build_index.py` again | `0 new, 863 updated, 0 stale deleted, 863 stored`; direct check: 863 IDs, 863 unique |
| Offline tests | `python -m unittest discover -s tests -v` | `Ran 44 tests … OK (skipped=6)` |
| Real-model tests | `RUN_MODEL_TESTS=1 python -m unittest discover -s tests` | `Ran 44 tests … OK` |
| Compile | `python -m compileall -q app.py src tests scripts` | Exit 0 |
| Evidence report | `python scripts/retrieval_report.py` | 12 of 14 sample queries pass; 2 documented failures (§7) |

---

## 6. Chunk-setting experiment (plan task 03: "test whether these preserve context")

All four configurations were built on the same 288 products with the real model and scored on the same 14 sample queries. "Category hits@5" counts top-5 results in the expected category (max 70). "Top-1 correct" means the first result is in the expected category.

| Chunk size | Keep-whole limit | Chunks | Queries passed | Category hits@5 | Top-1 correct |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 800 | 1,159 | 14/14 | 56/70 | 13/14 |
| **700** (chosen) | **800** | **863** | 12/14 | 55/70 | **14/14** |
| 800 | 800 | 751 | 13/14 | 56/70 | 14/14 |
| 700 | 1,200 | 795 | 12/14 | 54/70 | 14/14 |

**Conclusion.** The configurations differ by at most two category hits out of 70, which is within noise for 14 queries. 700/75 keeps every chunk inside the model's 256-token window, gets the top result right on every query, and is in the middle of the plan's 500–800 range. The pass/fail differences come from the two data-limited queries in §7, so tuning chunk size to pass them would be over-fitting. M5 should re-run this comparison against the Phase 5 evaluation set.

---

## 7. Observed failure cases (real, not invented)

**F1 — "portable bluetooth speaker" (Q6).** Expected ≥3 of 5 Speakers. Got 2 of 5. #1 is the correct and **only** Bluetooth speaker in the catalogue (Janhvi Bluetooth Beatz Pill, INR 595). Ranks 2–3 are home-theatre systems whose spec chunks mention Bluetooth and speakers; rank 5 is a Bluetooth headset. *Cause:* the catalogue has 14 speakers but only one is Bluetooth, and home-theatre spec chunks are semantically close. *Proposed fix (Phase 3/4):* if the query names a product type, add a category filter or boost; Hybrid RAG keyword matching on "speaker" would also help.

**F2 — "power bank to charge my phone while travelling" (Q9).** Expected ≥2 of 5 Power Banks. Got 1 of 5. #1 is the correct Wayona 10000 mAh power bank; ranks 2–5 are D'clair battery chargers. *Cause:* only 5 power banks exist, and "charge my phone" is strongly associated with the 102 chargers. *Proposed fix:* the same category intent detection as F1; M3's query understanding can map "power bank" → `categories=["Power Banks"]`.

Neither is a defect in identity or metadata: every result carries the correct product ID, price and source.

---

## 8. Integration contract for M3 (Phase 3)

```python
from src.retrieval import Retriever

retriever = Retriever()                       # opens chroma_db/, loads all-MiniLM-L6-v2 once
results = retriever.search(
    "headphones with mic", k=5,
    max_price=1000,                           # optional; excludes unknown prices
    categories=["Headphones & Earphones"],    # optional
)
for r in results:
    r.product_id, r.name, r.price, r.source_ref, r.text, r.score   # evidence + identity
    r.to_dict()                                                     # JSON-safe dict
```

- `price is None` means **unknown**; never treat it as 0 or as meeting a budget.
- `text` begins with the identity header, so it can be passed to the LLM as-is with `product_id` as the citation ID.
- Valid category names: Chargers & Adapters, Headphones & Earphones, Home Theater, Keyboards, Laptops, Mice, Power Banks, Routers & Networking, Speakers, USB Storage.
- Budget extraction ("under ₹50,000" → `max_price=50000`) is M3's task. The filter is ready for it.
- Errors: a missing or mismatched index raises `IndexNotReadyError` with a message telling the user to run `python scripts/build_index.py`.

---

## 9. Known limitations

- **Catalogue scope:** the catalogue has 2 laptops and 0 phones. "laptop for students" returns both laptops at ranks 1–2, then laptop adapters. Broad laptop/phone comparisons are not supported by this data. This was already flagged in Phase 1.
- **Prices are historical** (2015–16 crawl). Text and metadata label them that way.
- **Long, boilerplate-heavy listings** (warranty text) produce some low-information chunks. Per-product de-duplication keeps them from crowding out results.
- **Scores are relative.** Cosine scores of ~0.3–0.6 are typical for this model. M3 should not use a fixed score threshold as the only "insufficient evidence" signal without testing it.
- **First run downloads the model** (~90 MB) from Hugging Face into the user cache. Later runs are offline.
- The `RUN_MODEL_TESTS` acceptance tests are not run in CI because CI has no built index; run them locally.
