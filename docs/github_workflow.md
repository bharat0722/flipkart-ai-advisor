# GitHub collaboration

| Milestone | Accountable lead | Receiving review |
| --- | --- | --- |
| Phase 1 — Project foundation and dataset engineering | M1 | M2 |
| Phase 2 — Embeddings, chunking and vector database | M2 | M3 |
| Phase 3 — AI reasoning, grounded answers and safeguards | M3 | M4 |
| Phase 4 — Streamlit application and RAG enhancement | M4 | M5 |
| Phase 5 — Testing, evaluation, optimization and presentation | M5 | All five members |

Assign member names when the team is ready. Use one issue per actionable task. Add its owner, milestone, acceptance checks and dependencies. Branch from `main`, link the issue and verification evidence in the PR, and keep review feedback on the PR. The CI workflow runs dependency, unittest and compilation checks. Require one non-author approval and passing checks where the repository plan supports branch protection.

The outgoing lead records the final handoff. The receiving lead independently reproduces the milestone output, and QA records the result. After approval and merge, tag the accepted `main` snapshot `phase-1-complete` through `phase-5-complete` as appropriate. Create `v1.0.0` from the final accepted snapshot. Keep raw and generated data and secrets out of Git.

## Phase 1 issue drafts

| Title | Owner | Acceptance evidence |
| --- | --- | --- |
| Establish the Phase 1 repository and CI | M1 | A stable `main`, a dedicated Phase 1 branch, pinned dependencies, and automated checks. |
| Audit the original Flipkart dataset and source terms | M1 | Version, checksum, schema, duplicates, missing fields, category distribution and license recorded. |
| Clean and validate the electronics catalogue | M1 | Traceable curated CSV, deterministic reruns and tests covering the data contract. |
| Independently reproduce the Phase 1 handoff | M2 | Fresh checkout, matching hashes, schema and provenance checks, and a recorded acceptance decision. |

## Phase 1 PR draft

**Title**: Build reproducible Phase 1 electronics dataset

**Body**: Curate 288 traceable electronics records from Kaggle Flipkart Products v1, with a deterministic Pandas pipeline, audit report, tests and a receiving-lead handoff. The catalogue is strong in accessories and networking and contains two laptops. Verify the raw and cleaned hashes, run the nine tests, and reproduce the audit in a fresh checkout. Link the Phase 1 issues before requesting review.
