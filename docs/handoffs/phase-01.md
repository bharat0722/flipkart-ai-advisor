# Phase 1 handoff — Project foundation and dataset engineering

**Prepared 11 November 2026.** Outgoing lead M1 (Data & Foundation). Receiving lead M2 (Retrieval & Index). QA M5 (Evaluation & Release). Team member names are pending.

## Objective and completed scope

Establish a reproducible Python repository and produce a traceable electronics catalogue from the selected Flipkart snapshot. Phase 1 has a validated CSV pipeline, audit, nine automated tests, a CI workflow, and a reproducible handoff. The audited build retained **288 records from 20,000 raw rows**. There were 389 approved-category candidates and 387 usable unique records before curation. One duplicate PID and one listing without usable product evidence were excluded. The networking cap excluded another 99 rows.

## Snapshot and review links

| Item | Value |
| --- | --- |
| Local repository | `flipkart-ai-advisor` |
| GitHub repository URL | [bharat0722/flipkart-ai-advisor](https://github.com/bharat0722/flipkart-ai-advisor) |
| Stable branch | `main` |
| Phase 1 branch | `feat/phase-01-dataset-foundation` |
| Verified local implementation commit | `8b61761a69c11948b17cb7140080ca2ca347352c` |
| Handoff revision | This document is tracked on the feature branch. Record the exact reviewed branch tip during sign-off. |
| Milestone, issues and PR | [Milestones](https://github.com/bharat0722/flipkart-ai-advisor/milestones) · [Issues](https://github.com/bharat0722/flipkart-ai-advisor/issues) · [Pull requests](https://github.com/bharat0722/flipkart-ai-advisor/pulls) |
| Accepted release tag | Pending M2 review, QA sign-off and merge. |

The verified local commit identifies the original reproduction run. For independent reproduction, use the GitHub Phase 1 PR head and record its exact SHA in the sign-off table.

## Data source, cleaning and output

Original file `flipkart_com-ecommerce_sample.csv` from Kaggle Flipkart Products, PromptCloud, version 1. Kaggle lists CC BY-SA 4.0. See attribution, license conditions, actual category distributions and field coverage in the [data-quality report](../data_quality.md). Prices and related purchase claims reflect a 2015–2016 crawl. The curated set supports accessories and networking, with two laptop listings and no handsets.

The pipeline validates source columns and record widths, filters approved category paths, normalizes source text and prices, and requires a source ID, URL, product name and meaningful evidence. It keeps the highest-ranked row for duplicate source identifiers and caps the largest category at 100. Ten historical discounted prices are unknown. See exact filter rules and the 17-column [data dictionary](../data_dictionary.md).

| Changed files | Purpose |
| --- | --- |
| `src/preprocess.py` | CLI `python -m src.preprocess`. The `build(input_path, output_path, report_path)` function writes the cleaned CSV and JSON report and returns audit metrics. Invalid input raises a readable error. |
| `data/raw/`, `data/processed/`, `data/evaluation/`, `scripts/` | Tracked directory placeholders. Raw and processed data files are local rebuild artifacts. |
| `tests/test_preprocess.py` | Nine unit/integration tests using synthetic fixtures and the CLI. |
| `app.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md` | Future app entry point, pinned dependencies, credential-free setup and repository conventions. |
| `docs/architecture.md`, `docs/data_dictionary.md`, `docs/data_quality.md`, `docs/evaluation.md`, `docs/presentation.md` | Approved architecture, schema, observed data evidence and later-phase notes. |
| `docs/github_workflow.md`, `docs/handoffs/`, `.github/` | Milestone and issue links, PR and issue templates, acceptance process, handoffs and automated checks. |
| `docs/PRD.md`, `docs/phase_status.json`, `docs/HANDOFF_PROMPT.md`, `scripts/sync_prd.py`, `AGENTS.md` | Detailed phase requirements, generated status table and instructions for future phase owners. |

## Reproduce from a clean checkout

Check out the reviewed feature branch or implementation SHA. From the repository root, run the commands below. For Windows activation, see the [README](../../README.md).

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
curl -fL 'https://www.kaggle.com/api/v1/datasets/download/promptcloudhq/flipkart-products' -o flipkart-products.zip
python -m zipfile -e flipkart-products.zip data/raw
python -m src.preprocess
python -m unittest discover -s tests -v
python -m compileall -q app.py src tests
shasum -a 256 data/raw/flipkart_com-ecommerce_sample.csv data/processed/electronics.csv
```

Verified environment was Python 3.12.14 on macOS arm64, with Pandas 2.2.3, NumPy 2.3.5, python-dateutil 2.9.0.post0, pytz 2025.2, six 1.17.0 and tzdata 2025.2. The CI workflow targets Python 3.12. Phase 1 requires no credentials or environment variables.

| Expected artifact | Expected evidence |
| --- | --- |
| `data/raw/flipkart_com-ecommerce_sample.csv` | 20,000 data rows, SHA-256 `56f8f699c9e847356666c2eab3c3ab1244340f6a98ad08e39ea2199ebe993ad1` |
| `data/processed/electronics.csv` | 288 rows, SHA-256 `f13d7836d8530b4506500738b418e9fe3f54c3711644f04722036aacbd434bc9` |
| `data/processed/data_quality.json` | 389 candidates, 387 usable after deduplication and evidence checks, mutually exclusive dispositions and both file hashes |

## Validation evidence

| Check | Status | Observed result |
| --- | --- | --- |
| Official Kaggle acquisition and metadata | PASS | Original archive extracted, version and license confirmed, SHA-256 matched. |
| `python -m pip install -r requirements.txt` and `python -m pip check` | PASS | Clean environment installed all six pinned packages. `No broken requirements found.` |
| `python -m src.preprocess` | PASS | `Retained 288 of 20000 records from 389 candidates.` |
| `python -m unittest discover -s tests -v` | PASS | `Ran 9 tests` and `OK` from the clean checkout. |
| `python -m compileall -q app.py src tests` | PASS | Exit code 0. |
| Build from a fresh local checkout | PASS | Independently created a new virtual environment in a fresh clone of the implementation commit and extracted the official archive. CSV and JSON matched the first run byte for byte. This was an implementation check by Codex. |
| Source trace and contract checks | PASS | Verified the schema, unique product IDs, ten unknown prices, and matching `uniq_id`, `pid` and URL at the raw ordinal for all 288 cleaned records. |
| GitHub Actions | NOT RUN | Workflow file exists. A remote PR and run are pending. |
| M2 independent reproduction and QA review | NOT RUN | M2 and M5 must record their own evidence and decisions. |

## Transition to M2

1. **M1:** Give M2 access to the private repository and direct them to the Phase 1 PR. Confirm that published history contains no raw or generated datasets.
2. **M2:** Reproduce the documented build in a fresh checkout, confirm the hashes, and verify that source references and unknown prices are preserved. Record the result on the PR and in the sign-off table.
3. **M1 and M2:** Agree that the accessory and networking coverage fits the assignment. If broad laptop or phone comparisons are required, record the dataset decision before indexing. M2 should consume the cleaned CSV fields and preserve product ID and provenance on every future chunk.
4. **M5:** Review audit evidence and unresolved limitations. Record the outcome before the phase is tagged.

## Acceptance checklist

- [x] Reproducible Python setup, schema, source and dataset limitations documented.
- [x] Real CSV inspected, cleaned and audited within the 150–300 target.
- [x] Stable IDs, source references, positive known prices and blank unknowns verified.
- [x] Nine tests pass and local clean-checkout outputs match.
- [x] Private GitHub repository, five milestones and initial issues created and linked.
- [ ] Phase 1 code and project documents published, PR opened and CI evidence linked.
- [ ] M2 reproduces the result and confirms coverage is suitable.
- [ ] QA review and acceptance are recorded. Merge and tag follow approval.

**Decision pending.** The local snapshot is ready for independent technical review. Remote review and phase acceptance remain open.

| Role | Name | Date | Reviewed commit | Decision or evidence |
| --- | --- | --- | --- | --- |
| M1 outgoing lead | Pending | | | Pending |
| M2 receiving lead | Pending | | | Pending independent reproduction |
| M5 QA reviewer | Pending | | | Pending |
