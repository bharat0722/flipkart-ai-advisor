# Evaluation

Phase 1 checks CSV validation, allowed-category matching, deduplication, stable identifiers, price handling, description quality, provenance and reproducibility. Run `python -m unittest discover -s tests -v`. See [observed data-quality results](data_quality.md) and the [handoff](handoffs/phase-01.md).

M5 will own the later evaluation corpus. The project plan calls for approximately 12–20 factual, comparative, multipart and unsupported queries, top-five retrieval success and at least two actual failure analyses. The `data/evaluation/` directory is reserved for that work.
