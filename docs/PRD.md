# Flipkart AI Electronics Advisor — Live PRD

This university project helps shoppers discover and compare electronics in a historical Flipkart catalogue. The assistant retrieves relevant products, explains recommendations using their specifications and prices, and cites the records it used. The team delivers a working Streamlit application, a reproducible evaluation, and a five-minute demonstration.

[Original architecture and phase plan (PDF)](Flipkart_AI_Electronics_Advisor_Project_Plan.pdf) · [Architecture and data flow](architecture.md) · [Copyable handoff prompt](HANDOFF_PROMPT.md) · [GitHub milestones](https://github.com/bharat0722/flipkart-ai-advisor/milestones) · [GitHub workflow](github_workflow.md)

## Current phase status

The status table is generated from [phase status](phase_status.json). Each implementation PR updates the relevant phase, links its handoff, and includes the generated table. The GitHub workflow also reconciles the table when phase records change on `main`.

<!-- BEGIN PHASE STATUS -->
| Phase | Lead | Status | Handoff | Evidence and next decision |
| --- | --- | --- | --- | --- |
| 1. Project foundation and dataset engineering | M1 | Accepted | [Handoff](handoffs/phase-01.md) | 288 of 20,000 records, 9 passing tests, CI green. M2 independently reproduced the build with matching hashes. M5 QA pending. Accepted by M2 (12 Nov 2026, accept with tracked issues). |
| 2. Embeddings, chunking and vector database | M2 | Ready for review | [Handoff](handoffs/phase-02.md) | 288 products as 863 chunks (all-MiniLM-L6-v2, 700/75). Idempotent rebuild, 44 passing tests, CI green, 12/14 sample queries pass with 2 documented data-limited failures. Awaiting M3 reproduction. |
| 3. AI reasoning, grounded answers and safeguards | M3 | In progress | [Handoff](handoffs/phase-03.md) | Code, prompt v1, budget/category extraction, fallback and history done. 63 unit tests pass locally (LLM mocked). Rebuilt index and real-index suite pass; F1/F2 fixed by category filters (5/5 each). Live Gemini demo run on 8 questions: citations valid, fallbacks work; its 2 defects (comparison picks wrong named product, refusals flagged grounded) fixed and re-verified; client timeout added; prompt v2; 69 tests pass. CI NOT RUN; Phase 2 acceptance by M3 still pending. |
| 4. Streamlit application and RAG enhancement | M4 | Planned | Pending | Depends on grounded answers and stable source metadata. |
| 5. Testing, evaluation, optimization and presentation | M5 | Planned | Pending | Depends on a working Streamlit application and documented setup. |
<!-- END PHASE STATUS -->

## Product requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| R1 | Recommend products based on a shopper's needs and budget. | Compare the result with eligible source records and verify every quoted price against the historical snapshot. |
| R2 | Answer product specification questions and compare products. | Check that the correct records were retrieved and that each comparison uses the right product's facts. |
| R3 | Cite the evidence behind each recommendation. | The response includes product/source IDs and the interface lets the user inspect supporting records. |
| R4 | Acknowledge missing or insufficient evidence. | Unsupported questions do not produce invented products, specifications, prices, stock or availability. |
| R5 | Provide a usable Streamlit chat experience. | A shopper can ask a question, follow up, inspect sources, clear the chat and recover from an error. |
| R6 | Make the result reproducible for the next teammate. | A clean checkout can rebuild the data and index, run tests and launch the app using the documented commands. |

The first release targets accessories and networking queries. The Phase 1 dataset contains 288 items across 10 categories, including two laptops and zero phones. Validate demo questions against actual records. Confirm catalogue scope with the receiving lead before indexing if broad laptop or phone coverage is expected.

## System design

**Offline** — Download the original Kaggle CSV, clean and filter electronics with Pandas, build product documents, keep short records whole, and chunk longer records before encoding them with Sentence Transformers `all-MiniLM-L6-v2`. Store vectors and source metadata in persistent ChromaDB.

**Online** — Accept questions through Streamlit. Interpret product type, preferences and numeric constraints. Retrieve roughly five relevant results, applying numeric budget filters where possible. Pass the question and supporting evidence to an LLM. Return grounded recommendations, comparisons, or a fallback with source IDs. Select the LLM provider in Phase 3.

The application is modular Python. Preserve product identity, source reference, category and known numeric price on every chunk. Keep historical pricing distinct from current availability and do not treat an unknown price as zero. Hybrid retrieval is the preferred enhancement if feasible and covered in class. Query Decomposition RAG is an alternative optional enhancement. Authentication, payments, live inventory, fine-tuning and microservices are outside this assignment.

## Phase 1 — Project foundation and dataset engineering

**Lead and receiving reviewer** — M1 Data & Foundation → M2 Retrieval & Index.

1. Establish the Python repository, pinned dependencies, setup instructions and automated checks.
2. Download and inspect Kaggle Flipkart Products v1. Document source license, schema, historical limitations and audit counts.
3. Filter real electronics categories, remove duplicate or unusable records, normalize prices and text, and retain approximately 150–300 high-quality products where coverage permits.
4. Preserve stable product IDs and traceability. Document the normalized schema and exact rebuild commands.

**Deliverables** — Clean CSV, audit, data dictionary, tests, README and formal handoff. **Acceptance** — A clean checkout reproduces the hashes, each retained record has a unique ID, usable description and source reference, unknown prices remain blank, and M2 independently checks the result and agrees on scope.

## Phase 2 — Embeddings, chunking and vector database

**Lead and receiving reviewer** — M2 Retrieval & Index → M3 Grounded RAG.

1. Reproduce the approved Phase 1 CSV and verify the raw and cleaned hashes and schema.
2. Build documents from name, description and specifications. Keep short records intact. Start long text at 500–800 characters with 75-character overlap and document measured changes.
3. Embed with `all-MiniLM-L6-v2` and persist the collection in ChromaDB. Store stable chunk IDs, product ID, category, known numeric price and source metadata. Make rebuilds repeatable without duplicate chunks.
4. Implement semantic retrieval with approximately five relevant results. Make results inspectable without an LLM. Validate real router, headphone, speaker and charging queries against known catalogue records.

**Deliverables** — Document builder, index build command, persistent local ChromaDB collection, retrieval module, evidence examples and tests. **Acceptance** — A fresh checkout can rebuild or reopen the index and recover expected products with accurate metadata. M3 independently runs the documented search and verifies evidence suitable for generation. Keep generated indexes out of Git.

## Phase 3 — AI reasoning, grounded answers and safeguards

**Lead and receiving reviewer** — M3 Grounded RAG → M4 Streamlit & Integration.

1. Select and configure an available LLM provider. Document configuration names and local secret setup.
2. Pass retrieved evidence and source IDs to a controlled prompt. Implement recommendations and product comparisons, respecting numeric budget limits.
3. Prevent invented specifications, prices and availability. Give an explicit fallback when context is insufficient. Add minimal history that cannot override evidence.
4. Verify answer, source IDs, budget filtering, unsupported requests and follow-ups outside the UI.

**Deliverables** — End-to-end answer pipeline, prompt templates, evidence-aware output contract, tests and handoff. **Acceptance** — Claims are supported by retrieved records, budget constraints hold, and M4 reproduces recommendations, comparisons and fallback behavior using the documented setup.

## Phase 4 — Streamlit application and RAG enhancement

**Lead and receiving reviewer** — M4 Streamlit & Integration → M5 Evaluation & Release.

1. Build the Streamlit chat interface with conversation history, clear-chat, example prompts, loading and error states.
2. Show product recommendations, specifications and prices with inspectable source records. Label historical pricing in the app.
3. If feasible and covered in class, implement Hybrid RAG by combining keyword and semantic retrieval and compare results to the baseline. Record any deferral.
4. Test launch and representative chat flows on the presentation machine.

**Deliverables** — Working Streamlit app, verified launch instructions, optional enhancement evidence and handoff. **Acceptance** — M5 can launch the app, use its core flows, inspect sources, clear history and verify an honest fallback.

## Phase 5 — Testing, evaluation, optimization and presentation

**Lead and receiving reviewers** — M5 Evaluation & Release → all five members.

1. Prepare approximately 12–20 factual lookup, comparison, multipart and unsupported queries. The assignment minimum is 3–4.
2. Evaluate top-five retrieval success on answerable questions, relevance, evidence coverage, faithfulness, budget compliance and unsupported answers.
3. Document at least two observed failure cases, causes and fixes. Retest affected questions and record remaining limits.
4. Finish the README and architecture explanation. Rehearse a five-minute demo with one minute for the problem, three for the demo and one for Q&A.

**Deliverables** — Results, failure analysis, verified setup, presentation material and final handoff. **Acceptance** — All five members reproduce the demo or validate the submission, record final approval and confirm the demo fits five minutes. Release from the reviewed snapshot.

## Review and release

Phase completion requires an outgoing handoff, independent reproduction by the receiving lead, and an approval record. The PRD records `ready_for_review` before approval and `accepted` only with reviewer evidence. Link issues, changed files, exact commands, real results, limitations, and next steps from the phase handoff. Tag the reviewed snapshot after the merge.

The grading focus is problem and dataset 15%, RAG pipeline 50%, grounding and fallback 15%, Streamlit 10%, and testing and error analysis 10%.
