# GitHub collaboration

| Milestone | Accountable lead | Receiving review |
| --- | --- | --- |
| [Phase 1 — Project foundation and dataset engineering](https://github.com/bharat0722/flipkart-ai-advisor/milestone/1) | M1 | M2 |
| [Phase 2 — Embeddings, chunking and vector database](https://github.com/bharat0722/flipkart-ai-advisor/milestone/2) | M2 | M3 |
| [Phase 3 — AI reasoning, grounded answers and safeguards](https://github.com/bharat0722/flipkart-ai-advisor/milestone/3) | M3 | M4 |
| [Phase 4 — Streamlit application and RAG enhancement](https://github.com/bharat0722/flipkart-ai-advisor/milestone/4) | M4 | M5 |
| [Phase 5 — Testing, evaluation, optimization and presentation](https://github.com/bharat0722/flipkart-ai-advisor/milestone/5) | M5 | All five members |

Assign member names when the team is ready. Use one issue per actionable task. Add its owner, milestone, acceptance checks and dependencies. Branch from `main`, link the issue and verification evidence in the PR, and keep review feedback on the PR. The CI workflow runs dependency, unittest and compilation checks. Require one non-author approval and passing checks where the repository plan supports branch protection.

## Live PRD updates

The phase owner records actual evidence and the handoff path in `docs/phase_status.json`. Run `python scripts/sync_prd.py` before opening a PR to regenerate the status table in `docs/PRD.md`. Pull request checks run `python scripts/sync_prd.py --check` so reviewers see the same status they are approving. When phase records change on `main`, GitHub Actions regenerates the table and publishes any resulting change. A reviewed PR with a current table needs no bot commit. If repository rules block bot pushes, keep the rendered update in the same reviewed PR.

Use `planned`, `in_progress`, `blocked`, `ready_for_review`, or `accepted`. `accepted` requires the receiving lead's actual sign-off and their identity in `accepted_by`. Keep the evidence in the handoff and link the reviewed PR there.

The outgoing lead records the final handoff. The receiving lead independently reproduces the milestone output, and QA records the result. After approval and merge, tag the accepted `main` snapshot `phase-1-complete` through `phase-5-complete` as appropriate. Create `v1.0.0` from the final accepted snapshot. Keep raw and generated data and secrets out of Git.

## Initial GitHub issues

| Title | Owner | Acceptance evidence |
| --- | --- | --- |
| [#1 Repository and CI](https://github.com/bharat0722/flipkart-ai-advisor/issues/1) | M1 | A stable `main`, a dedicated Phase 1 branch, pinned dependencies, and automated checks. |
| [#2 Dataset audit and source terms](https://github.com/bharat0722/flipkart-ai-advisor/issues/2) | M1 | Version, checksum, schema, duplicates, missing fields, category distribution and license recorded. |
| [#3 Clean and validate the catalogue](https://github.com/bharat0722/flipkart-ai-advisor/issues/3) | M1 | Traceable curated CSV, deterministic reruns and tests covering the data contract. |
| [#4 Independently reproduce and review Phase 1](https://github.com/bharat0722/flipkart-ai-advisor/issues/4) | M2 | Fresh checkout, matching hashes, schema and provenance checks, and a recorded acceptance decision. |
| [#5 Phase 2 retrieval index and handoff](https://github.com/bharat0722/flipkart-ai-advisor/issues/5) | M2 | Rebuildable ChromaDB index, verified retrieval and a handoff for M3. |

## Phase 1 PR draft

**Title**: Build reproducible Phase 1 electronics dataset

**Body**: Curate 288 traceable electronics records from Kaggle Flipkart Products v1, with a deterministic Pandas pipeline, audit report, tests and a receiving-lead handoff. The catalogue is strong in accessories and networking and contains two laptops. Verify the raw and cleaned hashes, run the nine tests, and reproduce the audit in a fresh checkout. Link the Phase 1 issues before requesting review.
