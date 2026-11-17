# Flipkart AI Electronics Advisor

University project for an electronics shopping assistant grounded in a historical Flipkart catalogue. Phase 1 builds a reproducible dataset for later retrieval. The audited Phase 1 build retained 288 records across ten categories. The scope has since been widened to every electronics, appliance and device-accessory category in the source: 1,993 records across 28 categories. The source still has only two laptops and no phones.

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
python scripts/build_index.py                       # 1993 products → 4050 chunks; safe to re-run (no duplicates)
python -m src.retrieval "laptop for students"       # top-5 evidence with product ID, price and source
python -m src.retrieval "headphones" --max-price 1000 --json
python scripts/retrieval_report.py                  # writes docs/retrieval_evidence.md
RUN_MODEL_TESTS=1 python -m unittest discover -s tests -v
```

On Linux CI, install CPU-only torch first with `python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`. On Windows ARM64, use an x64 Python 3.12. See the [Phase 2 build log](docs/phase2_build_log.md) for design, settings, the chunk-size experiment and failure cases. See the [Phase 2 handoff](docs/handoffs/phase-02.md) for acceptance and [retrieval evidence](docs/retrieval_evidence.md) for sample results.

## Phase 4: run the Streamlit app

The app answers from the Phase 2 index through the Phase 3 pipeline. It needs the cleaned CSV and index from the steps above, product images and ratings, and an LLM key.

```sh
python scripts/build_display_data.py                # images and ratings for the product cards (1993 products, 267 rated)
cp .env.example .env                                # then set OPENAI_API_KEY, OPENAI_BASE_URL and LLM_MODEL
streamlit run app.py                                # opens http://localhost:8501
```

Use a Gemini key from [Google AI Studio](https://aistudio.google.com/apikey) with `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/` and `LLM_MODEL=gemini-3.1-flash-lite`. Answers take about 2 s. `gemini-3.5-flash` also works but takes about 38 s because it reasons before answering. A stalled request is retried after 15 s.

Answers cite products as `[1]`, `[2]`, matching the product cards below the answer. Clicking a card's image or name opens the 2015-16 Flipkart listing. Every retrieved record is under "All retrieved records". Follow-up questions that name no product category, such as "which is the best?", continue the previous topic. Repeated questions are answered from an in-memory cache, which clears when the app restarts. Before a demo, ask the demo questions once to warm the cache.

## Team workflow

Use `main` as the stable branch. Review Phase 1 on `feat/phase-01-dataset-foundation`. See the [GitHub workflow](docs/github_workflow.md) and [Phase 1 handoff](docs/handoffs/phase-01.md) for acceptance and release tagging.

The catalogue was collected in 2015–2016. Prices and descriptions are historical. Dataset files are rebuilt locally. See the [source and license notes](docs/data_quality.md#source-and-terms).
