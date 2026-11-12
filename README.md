# Flipkart AI Electronics Advisor

University project for an electronics shopping assistant grounded in a historical Flipkart catalogue. Phase 1 builds a reproducible dataset for later retrieval. The audited build retains 288 records across ten categories, with strong accessory coverage and only two laptops.

[Live PRD](docs/PRD.md) · [Architecture and phase plan PDF](docs/Flipkart_AI_Electronics_Advisor_Project_Plan.pdf) · [Copyable handoff prompt](docs/HANDOFF_PROMPT.md)

## Setup

Run from the repository root using Python 3.12.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

On Windows PowerShell, use `py -3.12 -m venv .venv` and `.venv\Scripts\Activate.ps1`. No credentials are needed for preprocessing or unit tests.

## Download and prepare the dataset

Download version 1 of [Flipkart Products by PromptCloud on Kaggle](https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products). Extract `flipkart_com-ecommerce_sample.csv` into `data/raw/`. The following commands use the same official download route as the audited build.

```sh
curl -fL 'https://www.kaggle.com/api/v1/datasets/download/promptcloudhq/flipkart-products' -o flipkart-products.zip
python -m zipfile -e flipkart-products.zip data/raw
python -c "import hashlib; p='data/raw/flipkart_com-ecommerce_sample.csv'; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"
```

Verify that the raw SHA-256 is `56f8f699c9e847356666c2eab3c3ab1244340f6a98ad08e39ea2199ebe993ad1`. Use the same input before comparing audit results. If the API returns an HTML page, download the file from the Kaggle listing instead. Keep the temporary ZIP outside Git.

```sh
python -m src.preprocess
python -m unittest discover -s tests -v
python -m compileall -q app.py src tests
```

`data/processed/electronics.csv` is the input for Phase 2. `data/processed/data_quality.json` contains counts, category distributions, exclusions, missing fields and both file hashes. Use `python -m src.preprocess --help` for path overrides. The observed snapshot is in [the data-quality report](docs/data_quality.md), and the format is in [the data dictionary](docs/data_dictionary.md).

## Phase 2: build and query the retrieval index

Phase 2 embeds the cleaned catalogue with Sentence Transformers `all-MiniLM-L6-v2` and stores it in a persistent ChromaDB collection under `chroma_db/`, which Git ignores. No credentials are needed. The first build downloads the model, about 90 MB.

```sh
python scripts/build_index.py                       # 288 products → 863 chunks; safe to re-run (no duplicates)
python -m src.retrieval "laptop for students"       # top-5 evidence with product ID, price and source
python -m src.retrieval "headphones" --max-price 1000 --json
python scripts/retrieval_report.py                  # writes docs/retrieval_evidence.md
RUN_MODEL_TESTS=1 python -m unittest discover -s tests -v
```

On Linux CI, install CPU-only torch first with `python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`. On Windows ARM64, use an x64 Python 3.12. See the [Phase 2 build log](docs/phase2_build_log.md) for design, settings, the chunk-size experiment and failure cases. See the [Phase 2 handoff](docs/handoffs/phase-02.md) for acceptance and [retrieval evidence](docs/retrieval_evidence.md) for sample results.

## Team workflow

Use `main` as the stable branch. Review Phase 1 on `feat/phase-01-dataset-foundation`. See the [GitHub workflow](docs/github_workflow.md) and [Phase 1 handoff](docs/handoffs/phase-01.md) for acceptance and release tagging.

The catalogue was collected in 2015–2016. Prices and descriptions are historical. Dataset files are rebuilt locally. See the [source and license notes](docs/data_quality.md#source-and-terms).
