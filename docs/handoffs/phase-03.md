# Phase 3 handoff

## Objective and scope

- Phase and date: Phase 3, AI reasoning, grounded answers and safeguards. Prepared 12 November 2026 as a **draft**.
- Outgoing lead M3 (Grounded RAG), receiving lead M4 (Streamlit & Integration), QA reviewer M5. Team member names are pending.
- Objective: connect `Retriever.search()` to an LLM so answers come only from retrieved evidence, with budget and category extraction, an insufficient-evidence fallback and minimal chat history.
- Completed (code and mocked tests): tasks 01-08 of the Phase 3 plan. See the table below.
- Not done, because it needs the built index and an API key: the live demonstration against the real index (recommendation, comparison, budget query, unsupported question) and the re-run of `scripts/retrieval_report.py` to measure the effect on failures F1 and F2. These are recorded as NOT RUN.
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
result.grounded              # False when the fixed fallback was returned and the LLM was not called
result.reason                # "answered" | "no_evidence" | "weak_evidence" | "no_budget_match"
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
| Full unit suite | 44 Phase 2 tests still pass, new tests pass | 63 tests OK, 7 skipped (6 real-index, 1 live LLM). Python 3.11.6 | PASS (local) | M3 |
| Budget extraction | "under 50,000", "below Rs 2000", "under 2k", ranges; spec numbers (16GB, 10000 mAh) ignored | `tests/test_rag.py` BudgetTests | PASS | M3 |
| Category mapping | Speaker, power bank, router, headphones, charger etc. map to valid index labels | `tests/test_rag.py` CategoryTests | PASS | M3 |
| Prompt and context | Grounding rules, product ID and historical/unknown price in context | PromptTests | PASS | M3 |
| Fallback without LLM call | Empty, budget-filtered and weak results never call the LLM | PipelineTests | PASS | M3 |
| History handling | Last 6 clean user/assistant turns, before the evidence-bearing question; system role in history dropped | PipelineTests | PASS | M3 |
| LLM failure / missing key | Friendly `LLMUnavailableError` | PipelineTests | PASS | M3 |
| CI on Python 3.12 with pinned stack, `pip check` | Green | Not run | NOT RUN | M3 |
| Live demo on real index: recommendation, comparison, budget query, unsupported question | Grounded answers with citations; fallback for unsupported | Needs index and API key | NOT RUN | M3 |
| Failures F1 and F2 (speaker, power bank) with `categories=` | Off-category results removed | Not re-run; `scripts/retrieval_report.py` needs the built index | NOT RUN | M3 |
| Threshold `MIN_EVIDENCE_SCORE` on real out-of-dataset queries | Unrelated queries fall back, relevant ones do not | Not tested | NOT RUN | M3 |
| Live LLM test | Fallback wording for an unsupported question | Skipped without a key | NOT RUN | M3 |

## Issues and transition

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

Decision: **Pending.** Draft: code and mocked tests are complete; the live real-index demonstration and F1/F2 re-run are NOT RUN.

| Role | Name | Date | Commit | Decision or evidence |
| --- | --- | --- | --- | --- |
| Outgoing lead (M3) | Pending | | | Pending live run |
| Receiving lead (M4) | Pending | | | Pending |
| QA reviewer (M5) | Pending | | | Pending |
