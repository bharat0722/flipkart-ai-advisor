# Phase 3 handoff

## Objective and scope

- Phase and date: Phase 3, AI reasoning, grounded answers and safeguards. Prepared 12 November 2026 as a **draft**.
- Outgoing lead M3 (Grounded RAG), receiving lead M4 (Streamlit & Integration), QA reviewer M5. Team member names are pending.
- Objective: connect `Retriever.search()` to an LLM so answers come only from retrieved evidence, with budget and category extraction, an insufficient-evidence fallback and minimal chat history.
- Completed (code and mocked tests): tasks 01-08 of the Phase 3 plan. See the table below.
- Done on the real index (including the live Gemini demo): rebuild, full suite, F1/F2 retrieval with category filters and a first look at the evidence gate. Prompt rule 3 did reject "Sony PlayStation 5 games" and "best smartphone camera", which pass the score gate. Still NOT RUN: CI on Python 3.12.
- Deferred: Hybrid RAG (Phase 4 option); resolving follow-up questions in retrieval (see limitations).
- Decisions:
  - Rule-based query understanding instead of an extra LLM call: simple to explain, deterministic and testable without a key.
  - The score gate is deliberately low (`MIN_EVIDENCE_SCORE = 0.20`) because the Phase 2 notes say MiniLM scores of about 0.3-0.6 are typical. It only blocks clearly unrelated queries; the prompt's insufficient-evidence rule does the rest. The value is **untested on real queries** and must be tuned in the live run.
  - The answer's `[product_id]` citations are checked against the retrieved IDs, and invented IDs are reported in `invalid_citations`.

| Plan task | Where |
| --- | --- |
| 01 LLM API | `src/rag_pipeline.py` (`make_client`, `_call_llm`), any OpenAI-compatible endpoint |
| 02 Controlled prompt | `src/prompts.py` (`SYSTEM_PROMPT`, version in `settings.PROMPT_VERSION`) |
| 03 Product details and source IDs in context | `src/prompts.py` (`build_context`) |
| 04 Recommendations and comparisons | Prompt rules 7-8 (behaviour needs the live run to verify) |
| 05 Budget extraction and numeric filters | `src/query_understanding.py` feeding `Retriever.search(max_price, min_price, categories)` |
| 06 No unsupported claims | Prompt rules 2, 5, 6; citation check |
| 07 Fallback | `src/rag_pipeline.py`: no results, filtered-out budget, weak score; prompt rule 3 |
| 08 Minimal chat history | `_clean_history`: last 6 user/assistant turns; prompt rule 9 |

## Snapshot and artifacts

- Repository: https://github.com/bharat0722/flipkart-ai-advisor, base `main` at `473f091`, branch `feat/p3-grounded-rag`.
- Reviewed commit, PR, milestone, issues and tag: pending (local commit only; nothing pushed).
- Changed files: `src/prompts.py`, `src/query_understanding.py`, `src/rag_pipeline.py`, `src/settings.py` (Phase 3 constants), `tests/test_rag.py`, `requirements.txt`, `.env.example`, this handoff, `docs/phase_status.json`, `docs/PRD.md` (generated table).
- Module interface:

```python
from src.rag_pipeline import answer_question, LLMUnavailableError
result = answer_question("Suggest a router under 1500", history=[{"role": "user", "content": "..."}, ...])
result.answer                # str
result.grounded              # False for any fallback, and for an LLM reply that cites no retrieved product
result.reason                # "answered" | "no_support" | "no_evidence" | "weak_evidence" | "no_budget_match"
result.cited_product_ids     # ids cited in the answer that were really retrieved
result.invalid_citations     # cited ids that were not retrieved (should be empty)
result.sources               # list[RetrievedChunk] in rank order: product_id, name, price (None = unknown), source_ref, text, score ...
result.constraints           # .max_price, .min_price, .categories actually applied
result.to_dict()             # JSON-safe
```

- Index and data: unchanged from Phase 2 (288 products, 863 chunks, `all-MiniLM-L6-v2`, collection `flipkart_electronics_v1`).

## Reproduction

- Runtime: tests were run on Python 3.11.6 on Windows with openai 3.49.0 and python-dotenv 1.2.4. **Not yet run on Python 3.12 or in CI.**
- Setup: `python -m pip install -r requirements.txt`, then copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
- Configuration variable names: `OPENAI_API_KEY`, `OPENAI_BASE_URL` (optional), `LLM_MODEL` (optional, default `gpt-4o-mini`), `RUN_LLM_TESTS` (optional). Provider/model for the demo is not chosen yet; any OpenAI-compatible provider works.
- Data and index: follow the Phase 2 handoff (`python -m src.preprocess`, `python scripts/build_index.py`).
- Tests: `python -m unittest discover -s tests -v` (no key needed). Live test: `RUN_LLM_TESTS=1 python -m unittest tests.test_rag -v`.
- Checks: `python -m compileall -q app.py src tests scripts`, `python scripts/sync_prd.py --check`.

## Validation

| Check | Expected | Actual or evidence | PASS / FAIL / NOT RUN | Owner |
| --- | --- | --- | --- | --- |
| Full unit suite | 44 Phase 2 tests still pass, new tests pass | 69 tests OK with the rebuilt index and `RUN_MODEL_TESTS=1`, 1 skipped (live LLM). Earlier run before the fixes: 63 OK. Python 3.11.6 | PASS (local) | M3 |
| Budget extraction | "under 50,000", "below Rs 2000", "under 2k", ranges; spec numbers (16GB, 10000 mAh) ignored | `tests/test_rag.py` BudgetTests | PASS | M3 |
| Category mapping | Speaker, power bank, router, headphones, charger etc. map to valid index labels | `tests/test_rag.py` CategoryTests | PASS | M3 |
| Prompt and context | Grounding rules, product ID and historical/unknown price in context | PromptTests | PASS | M3 |
| Fallback without LLM call | Empty, budget-filtered and weak results never call the LLM | PipelineTests | PASS | M3 |
| History handling | Last 6 clean user/assistant turns, before the evidence-bearing question; system role in history dropped | PipelineTests | PASS | M3 |
| LLM failure / missing key | Friendly `LLMUnavailableError` | PipelineTests | PASS | M3 |
| CI on Python 3.12 with pinned stack, `pip check` | Green | Not run | NOT RUN | M3 |
| Live demo on real index: recommendation, comparison, budget query, unsupported question | Grounded answers with citations; fallback for unsupported | Run with Gemini `gemini-3.5-flash` via the OpenAI-compatible endpoint, 8 questions. Router and power-bank recommendations, a 10000 mAh under-1500 query and a comparison were answered with `[product_id]` citations and no `invalid_citations`; "laptop under 30000" and "capital of France" fell back without an LLM call; "best smartphone camera" and "Sony PlayStation 5 games" reached the LLM and it declined from the evidence. Two defects found and fixed, see Issues | PASS (defects fixed, re-run) | M3 |
| Live LLM test | Fallback wording for an unsupported question | `RUN_MODEL_TESTS=1 RUN_LLM_TESTS=1` with `gemini-3.5-flash`: 63 tests OK, 0 skipped (92 s), run before the comparison and `no_support` fixes and tests were added | PASS (local) | M3 |
| Index rebuild | 288 products, 863 chunks, input SHA-256 `f13d7836…4bc9`, raw SHA-256 `56f8f699…93ad1` | Official Kaggle archive re-downloaded, hashes matched, `Indexed 288 products as 863 chunks` | PASS (local) | M3 |
| Failures F1 and F2 (speaker, power bank) with `categories=` | Off-category results removed | Unfiltered `scripts/retrieval_report.py` still 12/14 (Q6 2/5, Q9 1/5 as in Phase 2). With the category filter that `understand()` derives: "portable bluetooth speaker" returns 5/5 Speakers, "power bank to charge my phone while travelling" returns 5/5 Power Banks | PASS (retrieval only; LLM answer not run) | M3 |
| Threshold `MIN_EVIDENCE_SCORE` (0.20) on real queries | Unrelated queries fall back, relevant ones do not | Top scores on the real index: "what is the capital of France" 0.122 (falls back); "Sony PlayStation 5 games" 0.402 and "best smartphone camera" 0.330 (pass the gate, so only prompt rule 3 can reject them); "laptop under 30000" returns no results (`no_budget_match`); in-catalogue queries 0.43-0.59. The gate catches only clearly unrelated text | PARTIAL | M3 |

## Issues and transition

- **Fixed: named-product comparison picked the wrong product.** `extract_comparison_targets()` (`src/query_understanding.py`) pulls the product names out of "compare A and B", "A vs B" and "difference between A and B"; `_retrieve_named()` (`src/rag_pipeline.py`) searches once per name, ranks candidates by word overlap with the product name before similarity, and adds a `NOTE` to the prompt when a named product is not found (prompt rule 10). Live re-run: "Compare the TP-LINK TL-WR841N and the iBall 150M router" now compares the iBall 150M eXtreme (INR 929), and "Compare the iBall 150M and the Cisco RV340 router" says the Cisco was not found. Limits: only the first three names are used, and the match is word overlap, so a misspelt model name may be reported as not found.
- **Fixed: refusals were flagged `grounded=True`.** An LLM reply that cites no retrieved product now returns `grounded=False, reason="no_support"` (also when it cites only invented IDs). Live re-run: "best smartphone camera" and "Sony PlayStation 5 games" return `no_support`. M4 can show these like the other fallbacks.
- **Fixed during this run:** the OpenAI client had no timeout (SDK default 600 s, 3 retries), so a stalled provider hung `answer_question()` for 10+ minutes. Now `LLM_TIMEOUT_SECONDS = 45`, `max_retries=2` (`src/settings.py`, `src/rag_pipeline.py`).
- **Provider notes:** with the Gemini key, `gemini-2.5-flash` returned 404 and `gemini-flash-latest` timed out; `gemini-3.5-flash`, `gemini-3.1-flash-lite` and `gemini-2.5-flash-lite` worked. Set `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/` and `LLM_MODEL=gemini-3.5-flash` in `.env`. Answers were not scored for quality beyond citation validity.

- **Phase 2 not yet accepted.** The Phase 2 handoff still awaits M3's independent reproduction (Part A of `HANDOFF_PROMPT.md`). Phase 3 should not be accepted before that.
- Limitation: retrieval uses only the current question, so a follow-up such as "and the cheaper one?" retrieves on those words alone; the history reaches the LLM but evidence comes from the new retrieval. Proposed fix: rewrite follow-ups into standalone queries, or add the previous user question to the retrieval query. Owner M3/M4.
- Limitation: ambiguous queries ("laptop charger") map to several categories. Intended; both are searched.
- Limitation: the catalogue has 2 laptops and 0 phones, so phone and broad laptop questions should hit the fallback. Demo questions should use accessories and networking.
- Limitation: keyword category detection can miss new phrasings ("wireless internet box"). Unrecognised queries run unfiltered semantic search.
- Receiving phase (M4): build the Streamlit chat on `answer_question()`: show `answer`, `sources` (price, source_ref), `grounded`/`reason`, handle `LLMUnavailableError`, keep `history` as a list of `{role, content}`.
- Interface constraints: `price is None` means unknown. Never show the prices as current.

## Acceptance

- [ ] Completed scope meets phase acceptance criteria.
- [ ] Receiving lead independently reproduced the result at the recorded commit.
- [ ] Reviewer recorded evidence, decision and any outstanding items.
- [ ] The reviewed work was merged and the accepted snapshot tagged.

Decision: **Pending.** Draft: code, mocked tests, real-index suite and F1/F2 retrieval re-run are done; the live Gemini demo is done, its two defects (wrong product in comparisons, refusals flagged grounded) are fixed and re-verified live; CI is NOT RUN.

| Role | Name | Date | Commit | Decision or evidence |
| --- | --- | --- | --- | --- |
| Outgoing lead (M3) | Pending | | | Pending live run |
| Receiving lead (M4) | Pending | | | Pending |
| QA reviewer (M5) | Pending | | | Pending |
