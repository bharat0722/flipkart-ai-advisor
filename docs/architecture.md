# Architecture

The Flipkart AI Electronics Advisor helps shoppers find and compare electronics using product evidence. It gives an insufficient-evidence response when the historical catalogue cannot support a claim. This repository follows the team's `Flipkart_AI_Electronics_Advisor_Project_Plan.pdf`.

| Phase | Lead | Scope |
| --- | --- | --- |
| 1. Project foundation and dataset engineering | M1 | Python and Pandas prepare a clean, traceable catalogue from the selected Kaggle CSV. |
| 2. Embeddings, chunking and vector database | M2 | Keep short product records whole. Start long-text chunking at 500–800 characters with 75-character overlap. Embed with Sentence Transformers `all-MiniLM-L6-v2`, persist in ChromaDB, and retrieve roughly five records with source metadata. |
| 3. AI reasoning, grounded answers and safeguards | M3 | Connect the selected LLM API, restrict generation to evidence, preserve source IDs, filter numeric budgets and handle missing evidence. |
| 4. Streamlit application and RAG enhancement | M4 | Display answers and sources in Streamlit. Evaluate Hybrid RAG as the optional enhancement if feasible and covered in class. |
| 5. Testing, evaluation, optimization and presentation | M5 | Test approximately 12–20 questions, document two actual failure cases and rehearse the five-minute group demo. |

Phase 1 reads the original CSV, validates its shape, maps observed category paths, normalizes and curates the rows, and writes the cleaned CSV and audit JSON. The output preserves stable product IDs, source IDs, historical price and factual text. [Data dictionary](data_dictionary.md)

The planned application is a modular Python project. ChromaDB will retain product identity and source metadata alongside the embedded text. Streamlit will call the retrieval and answer pipeline when those phases are implemented. The choice of LLM provider is deferred to Phase 3.
