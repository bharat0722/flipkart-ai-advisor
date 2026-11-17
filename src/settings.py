"""Shared Phase 2 configuration for indexing and retrieval.

Indexing and querying must use the same values. The build script records them in
the collection metadata and in ``index_manifest.json`` so a mismatch is detected
before a query runs.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Inputs and outputs
PROCESSED_CSV = ROOT / "data" / "processed" / "electronics.csv"
INDEX_DIR = ROOT / "chroma_db"
MANIFEST_NAME = "index_manifest.json"

# Embedding model (Sentence Transformers). Do not change without rebuilding.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
EMBEDDING_BATCH_SIZE = 64

# Vector store
COLLECTION_NAME = "flipkart_electronics_v1"
DISTANCE_METRIC = "cosine"

# Chunking. Short records stay whole; long bodies are split into overlapping windows.
MAX_RECORD_CHARS = 800   # body length at or below this is kept as one chunk
CHUNK_SIZE = 700         # target window size for long bodies (plan range 500-800)
CHUNK_OVERLAP = 75       # characters repeated between consecutive windows

# Retrieval
DEFAULT_TOP_K = 5
CANDIDATE_MULTIPLIER = 4  # fetch extra chunks so per-product de-duplication still yields k products

INDEX_SCHEMA_VERSION = 1

# Phase 3: grounded answers
PROMPT_VERSION = "v3"
HISTORY_MESSAGES = 6          # most recent chat messages passed to the LLM (follow-up understanding only)
# Weak-evidence gate. Deliberately low: Phase 2 notes that MiniLM scores of ~0.3-0.6 are typical, so the
# score only catches clearly unrelated queries. The prompt's insufficient-evidence rule does the real work.
MIN_EVIDENCE_SCORE = 0.20
# LLM: any OpenAI-compatible endpoint. Names only; values come from the environment (.env).
LLM_API_KEY_ENV = "OPENAI_API_KEY"
LLM_BASE_URL_ENV = "OPENAI_BASE_URL"
LLM_MODEL_ENV = "LLM_MODEL"
DEFAULT_LLM_MODEL = "gpt-4o-mini"
NAMED_MATCH_MIN_OVERLAP = 0.6  # share of a named product's words that must appear in a product name
NAMED_CANDIDATES = 10  # candidates searched per named product
LLM_TIMEOUT_SECONDS = 15.0  # per request; a stalled request is retried (max_retries=2). Gemini Flash-Lite answers in 1.5-7 s but occasionally stalls ~40 s
# Phase 5 reliability fix: if the primary model fails (timeout, 5xx, or similar transient error) even
# after its own retries, try once more with a different, slower-but-steadier model before giving up,
# instead of making the person resend the question by hand. The fallback gets its own longer timeout
# because it is deliberately a different (often slower) model than the primary.
LLM_FALLBACK_MODEL_ENV = "LLM_FALLBACK_MODEL"
DEFAULT_FALLBACK_LLM_MODEL = "gemini-3.5-flash"
LLM_FALLBACK_TIMEOUT_SECONDS = 45.0

# Phase 4 Hybrid RAG (src/hybrid.py). RETRIEVAL_MODE in the environment overrides the default.
RETRIEVAL_MODE_ENV = "RETRIEVAL_MODE"
DEFAULT_RETRIEVAL_MODE = "hybrid"  # adopted on docs/hybrid_evaluation.md evidence
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60  # standard Reciprocal Rank Fusion constant
# Phase 5 fix: a flat score bonus for a chunk matching the question's connectivity preference
# ("wireless"/"wired"). Far larger than any possible RRF increment (max ~2/(RRF_K+1) ~= 0.033),
# so a matching product always outranks a same-category non-matching one, however it was found.
CONNECTIVITY_BOOST = 1.0


def retrieval_mode() -> str:
    return os.getenv(RETRIEVAL_MODE_ENV) or DEFAULT_RETRIEVAL_MODE
