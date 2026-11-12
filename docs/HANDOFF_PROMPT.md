# Copyable team handoff prompt

Give your coding assistant the prompt below together with the repository URL. The current prompt is for **M3 (Grounded RAG)**, who receives Phase 2 and owns Phase 3. The team member needs access to the private repository through GitHub or a local clone.

```text
Repository: https://github.com/bharat0722/flipkart-ai-advisor
I am M3, the receiving lead for Phase 2 (Embeddings, chunking and vector database) and the owner of Phase 3 (AI reasoning, grounded answers and safeguards).

Before changing anything, read AGENTS.md, docs/PRD.md (Phase 3 section), docs/phase_status.json, docs/architecture.md, docs/handoffs/phase-02.md, docs/phase2_build_log.md (especially section 8, "Integration contract for M3", and section 7, "Observed failure cases"), docs/retrieval_evidence.md and pages 7 and 13-14 of docs/Flipkart_AI_Electronics_Advisor_Project_Plan.pdf. Inspect main, open issues in the Phase 2 and Phase 3 milestones and the latest Actions runs.

PART A - Phase 2 receiving review (do this first)
1. In a fresh checkout of main at or after commit 8e5326b, using Python 3.12, follow the Reproduction section of docs/handoffs/phase-02.md exactly. On Windows ARM64 use an x64 Python 3.12 as in build log section 4. Install CPU-only torch first: python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
2. Get the Kaggle data, run python -m src.preprocess and confirm the cleaned SHA-256 is f13d7836d8530b4506500738b418e9fe3f54c3711644f04722036aacbd434bc9 (288 rows).
3. Run python scripts/build_index.py twice. Expect "Indexed 288 products as 863 chunks (254 products split)", then "0 new, 863 updated, 0 stale deleted, 863 stored" (no duplicate chunks).
4. Run python -m src.retrieval "laptop for students" and python -m src.retrieval "headphones" --max-price 1000. Confirm that every result carries product_id, name, historical price (or unknown), source_ref and an identity header in its text.
5. Run python -m unittest discover -s tests -v (expect 44 tests, OK, 6 skipped), then the same with RUN_MODEL_TESTS=1 (expect 44 OK), then python scripts/retrieval_report.py (expect 12/14, with failures F1 and F2 documented).
6. Phase 2 was pushed directly to main without a PR. Review commit 8e5326b as the code review and leave comments on issue #5.
7. Record your actual results in the Validation and sign-off tables of docs/handoffs/phase-02.md. Give a decision: Accept, Accept with tracked issues, or Changes required. Only if you accept, set Phase 2 to "accepted" in docs/phase_status.json with accepted_by set to your role or name and the date, then run python scripts/sync_prd.py and python scripts/sync_prd.py --check. Never record an unrun check as passed. If something fails, report the concrete failure to M2 instead of fixing Phase 2 yourself.

PART B - Phase 3 implementation (after Part A)
Branch from current main, for example feat/phase-03-grounded-rag. Implement, against docs/PRD.md Phase 3 and plan page 7:
1. Choose an available LLM provider and model. Read the API key only from an environment variable or .streamlit/secrets.toml. Add the variable NAME (never a value) to .env.example. Never commit keys.
2. Add src/prompts.py, with a versioned, controlled system prompt that restricts answers to retrieved evidence, cites product_id for every claim, labels prices as historical 2015-16 catalogue values and never claims current stock, availability or launch dates.
3. Add src/rag_pipeline.py, which calls src.retrieval.Retriever.search() and passes each RetrievedChunk.text with its product_id to the prompt. Return a structured result: answer text, cited product IDs and source_refs, and the retrieved evidence, for M4's UI.
4. Extract budgets such as "under 50,000", "below Rs 2000" and "under 2k" into max_price, and obvious product types such as speaker, power bank, router, headphones and charger into categories=[...]. Use the valid category names in build log section 8. This should also address Phase 2 failures F1 and F2; re-run retrieval_report.py and record the effect. price is None means unknown: never treat it as 0 or as within budget.
5. Implement recommendations and side-by-side comparisons using only retrieved facts.
6. Add an insufficient-evidence fallback for unknown products, missing specs, future availability, current prices and empty or filtered-out results. Do not rely on a raw cosine-score threshold alone without testing it on real queries.
7. Add minimal chat history so follow-ups work, without older messages overriding retrieved evidence.
8. Add tests/test_rag.py, which runs in CI without an API key by mocking the LLM: prompt contents, citations, budget extraction, category mapping, fallback and history handling. Add an optional live-LLM test gated behind an environment variable.
9. Demonstrate, outside any UI, a recommendation, a comparison, a budget query and an unsupported question against the real index. Record the question, retrieved product IDs, answer and citations.

Use only real catalogue records. The catalogue has 2 laptops and 0 phones, so choose demo questions from accessories and networking. Keep credentials, raw data, processed data and chroma_db/ out of Git. Update requirements.txt with exact pins and keep pip check clean.

Before review, write docs/handoffs/phase-03.md from docs/handoffs/TEMPLATE.md, with exact commands, provider and model, configuration variable names (no values), prompt version, the answer and source return format, observed results, issues, limitations and M4 as the receiving lead. Set Phase 3 to ready_for_review in docs/phase_status.json, run python scripts/sync_prd.py and python scripts/sync_prd.py --check, and run the full test suite. Open a PR to main linked to the Phase 3 milestone and issues, with the handoff and evidence. Leave acceptance to M4. Report the PR link and status, then stop after Phase 3.
```

To hand off later phases, change the role, predecessor, phase number, handoff filename and phase-specific checks. Use `docs/handoffs/TEMPLATE.md` and the relevant PRD section for acceptance criteria.
