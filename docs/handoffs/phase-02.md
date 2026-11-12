# Phase 2 handoff — Embeddings, chunking and vector database

**Prepared 12 November 2026.** Outgoing lead M2 (Retrieval & Index). Receiving lead M3 (Grounded RAG). QA M5 (Evaluation & Release). Team member names are pending. Full design notes and the chunk-size experiment are in the [Phase 2 build log](../phase2_build_log.md).

## Objective and scope

- **Objective:** make the Phase 1 catalogue searchable by meaning and return inspectable evidence with product identity and source.
- **Completed:** all seven plan tasks (PDF page 6). This includes a document builder, chunking with tested settings, `all-MiniLM-L6-v2` embeddings, a persistent ChromaDB collection with source metadata, idempotent rebuilds, top-five semantic retrieval with price and category filters, a CLI, an evidence report and tests.
- **Deferred:** query understanding and budget extraction from text (Phase 3, M3), and Hybrid keyword + semantic retrieval (Phase 4 option). The `max_price`/`categories` filters are ready for both.
- **Key decisions:** an identity header on every chunk, 700-char windows with 75-char overlap so chunks fit the model's 256-token limit, unknown prices omitted and flagged instead of stored as 0, and upsert by stable chunk ID plus deletion of stale chunks for duplicate-free rebuilds. See build log §3 and §6.

## Prerequisite status

Phase 1 is `ready_for_review` and **not yet accepted** in `docs/phase_status.json`. As part of this work, M2 reproduced Phase 1 independently. The raw SHA-256 `56f8f699…93ad1` and cleaned SHA-256 `f13d7836d8530b4506500738b418e9fe3f54c3711644f04722036aacbd434bc9` match the Phase 1 handoff, with 288 rows. M2 still needs to record the Phase 1 acceptance decision and agree on catalogue scope in issue #4. Phase 2 should merge after that.

## Snapshot and artifacts

| Item | Value |
| --- | --- |
| Repository | [bharat0722/flipkart-ai-advisor](https://github.com/bharat0722/flipkart-ai-advisor) |
| Base | `main` at `be70f63` |
| Feature branch | `feat/phase-02-retrieval-index` |
| Issue / milestone | [#5 Phase 2 retrieval index and handoff](https://github.com/bharat0722/flipkart-ai-advisor/issues/5) · [Milestone 2](https://github.com/bharat0722/flipkart-ai-advisor/milestone/2) |
| Reviewed commit / PR / tag | Record at review. Tag `phase-2-complete` after acceptance. |
| Input | `data/processed/electronics.csv`, 288 products, SHA-256 `f13d7836…4bc9` |
| Index | `chroma_db/`, collection `flipkart_electronics_v1`, cosine. Not committed. |
| Model | `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, normalized |
| Chunk settings | Keep whole when the body is at most 800 chars. Otherwise use 700-char windows with 75-char overlap. |
| Counts | 288 products → 863 chunks. 254 products were split, with a maximum of 10 chunks per product. 10 products have an unknown price. |
| Build metadata | `chroma_db/index_manifest.json` records model, settings, input hash, counts and sync results. |

| Changed files | Interface |
| --- | --- |
| `src/settings.py` | Shared constants |
| `src/chunking.py` | `load_products(path)`, `build_document(p)`, `chunk_product(p, ...)`, `chunk_products(ps, ...)` |
| `src/embeddings.py` | `get_embedder()` → `embed_documents(texts)`, `embed_query(text)` |
| `src/vector_store.py` | `get_client`, `get_or_create_collection`, `open_collection`, `sync_chunks`, `read_manifest`, `IndexNotReadyError` |
| `src/retrieval.py` | `Retriever().search(query, k=5, max_price=None, min_price=None, categories=None, unique_products=True)` → `list[RetrievedChunk]`; CLI `python -m src.retrieval` |
| `scripts/build_index.py` | `python scripts/build_index.py [--reset] [--chunk-size N] [--overlap N] [--max-record-chars N]` |
| `scripts/retrieval_report.py` | Writes `docs/retrieval_evidence.md` |
| `tests/test_chunking.py`, `tests/test_retrieval.py` | 35 new tests, including 6 real-model tests gated by `RUN_MODEL_TESTS=1` |
| `requirements.txt`, `.github/workflows/checks.yml`, `.env.example`, `README.md`, `docs/architecture.md` | Pins, CPU-only torch in CI, setup |

## Reproduction

Use Python 3.12 and run from the repository root. No credentials are needed. On Windows ARM64, use an x64 Python 3.12, as described in build log §4.

```sh
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu   # optional on macOS
python -m pip install -r requirements.txt
python -m pip check
# Data, as in Phase 1:
curl -fL 'https://www.kaggle.com/api/v1/datasets/download/promptcloudhq/flipkart-products' -o flipkart-products.zip
python -m zipfile -e flipkart-products.zip data/raw
python -m src.preprocess
# Phase 2:
python scripts/build_index.py                 # expect: Indexed 288 products as 863 chunks (254 products split)
python scripts/build_index.py                 # expect: 0 new, 863 updated, 0 stale deleted, 863 stored
python -m src.retrieval "laptop for students"
python -m unittest discover -s tests -v       # expect: Ran 44 tests, OK (skipped=6)
RUN_MODEL_TESTS=1 python -m unittest discover -s tests   # expect: Ran 44 tests, OK
python scripts/retrieval_report.py            # expect: 12/14 passed (F1, F2 documented)
python scripts/sync_prd.py --check
```

The verified environment was Windows 11 ARM64 running x64 CPython 3.12.16 under emulation. It used torch 2.15.0+cpu, sentence-transformers 6.3.0, transformers 5.22.2, chromadb 1.5.9, numpy 2.3.5 and pandas 2.2.3.

## Validation

| Check | Expected | Actual or evidence | Status | Owner |
| --- | --- | --- | --- | --- |
| Phase 1 input reproduced | 288 rows, cleaned hash `f13d7836…` | Byte-identical hash | PASS | M2 |
| Dependencies | Clean install | `No broken requirements found.` | PASS | M2 |
| Index build | All products indexed with metadata | 288 → 863 chunks, 863 stored | PASS | M2 |
| Repeated ingestion has no duplicates | Same count, 0 new | `0 new, 863 updated`; 863 IDs, 863 unique | PASS | M2 |
| Stale chunks removed on smaller input | Count shrinks | `test_rebuild_removes_stale_chunks` | PASS | M2 |
| Identity on every chunk | Name, ID, price and source in text and metadata | `test_long_record_is_split_and_every_chunk_keeps_identity`, report identity check on all 14 queries | PASS | M2 |
| Unknown price is never zero and never within budget | `price=None`, excluded by `max_price` | `test_unknown_price_is_none_not_zero`, `test_budget_filter_excludes_expensive_and_unknown_prices` | PASS | M2 |
| Model mismatch guarded | Error | `test_model_mismatch_is_rejected` | PASS | M2 |
| "laptop for students" returns relevant records | Laptops in top five | Both catalogue laptops at ranks 1–2 | PASS | M2 |
| Router, headphone and charging queries | At least 3 of 5 in category | `RealIndexTests` and report Q2–Q5, Q7, Q8 | PASS | M2 |
| Speaker query | At least 3 of 5 Speakers | 2 of 5. The only Bluetooth speaker ranks #1. Failure F1. | FAIL (data limit; tracked) | M2 → M3 |
| Power-bank query | At least 2 of 5 Power Banks | 1 of 5, ranked #1. Failure F2. | FAIL (data limit; tracked) | M2 → M3 |
| Budget queries | All results have known prices within the limit | Q13 (≤1000) and Q14 (≤1500) respected | PASS | M2 |
| Unit and integration tests | All pass | `Ran 44 tests … OK` with and without `RUN_MODEL_TESTS=1` | PASS | M2 |
| Compile | Exit 0 | Exit 0 | PASS | M2 |
| GitHub Actions | Green | Pending PR | NOT RUN | M2 |
| M3 independent reproduction | Rebuild or open index and run retrieval | Pending | NOT RUN | M3 |
| QA review | Decision recorded | Pending | NOT RUN | M5 |

## Issues and transition

| Issue | Severity | Impact | Owner and next step |
| --- | --- | --- | --- |
| F1 and F2: semantically similar categories (home theatre and chargers) outrank sparse categories | Nonblocking | 1–2 of the top five are off-category for speaker and power-bank queries. The correct item still ranks #1. | M3: detect the product type in the query and pass `categories=`. M4: Hybrid RAG keyword boost. |
| Catalogue has 2 laptops and 0 phones | Nonblocking, known since Phase 1 | No broad laptop or phone comparisons are possible | M1, M2 and M3: choose demo questions from accessory and networking records |
| Native Windows ARM64 cannot install the pinned stack | Nonblocking | Setup friction on ARM laptops | Use x64 Python 3.12, as in build log §4 |
| Phase 1 acceptance not recorded | Process | Phase 2 merge order | M2: record the decision in issue #4 |

**Receiving phase (M3):** connect an LLM to `Retriever.search()`. First tasks:

1. Reproduce this index and run the CLI.
2. Implement budget and category extraction that feeds `max_price` and `categories`.
3. Build the grounded prompt from `RetrievedChunk.text`, using `product_id` as the citation, with an insufficient-evidence fallback.

Interface constraints: `price is None` means unknown. Do not use raw cosine score alone as the evidence threshold without testing. See build log §8.

## Acceptance

- [x] Completed scope meets the Phase 2 acceptance criteria. Relevant records are returned, and evidence can be inspected before reaching an LLM.
- [ ] Receiving lead independently reproduced the result at the recorded commit.
- [ ] Reviewer recorded evidence, decision and any outstanding items.
- [ ] The reviewed work was merged and the accepted snapshot tagged.

Decision: **Pending.** Ready for M3 reproduction and M5 review.

| Role | Name | Date | Commit | Decision or evidence |
| --- | --- | --- | --- | --- |
| Outgoing lead (M2) | Pending | 2026-11-12 | Record at PR | Ready for review |
| Receiving lead (M3) | Pending | | | Pending independent reproduction |
| QA reviewer (M5) | Pending | | | Pending |
