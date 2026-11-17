# Synthetic demo records

The Kaggle sample has only 2 laptops, 2 mice, 4 keyboards, 3 pen drives and 5 power banks, and the raw file holds no further real ones (checked: the other name matches are laptop bags, skins with mouse pads, keyboard cases and USB lamps). So 18 **invented** records fill those categories, as the assignment brief allows when labelled.

| Category | Records |
| --- | ---: |
| Laptops | 5 |
| Mice | 4 |
| Keyboards | 4 |
| USB Storage | 3 |
| Power Banks | 2 |

- **Source:** `scripts/make_synthetic.py` writes `data/synthetic/synthetic_electronics.csv` (tracked in Git). Brands are fictional (Veltrix, Nexora, Orbis); prices are illustrative 2015-16 style values.
- **Labelling:** product IDs start with `S-`, `source_ref` is `SYNTHETIC`, and every chunk carries the line "Record type: SYNTHETIC demo record, invented, not a real Flipkart listing". The prompt (v4) tells the model to say so whenever it mentions one, and the Streamlit cards show "synthetic demo record".
- **Indexing:** `python scripts/build_index.py` adds them by default (306 products, 881 chunks). Use `--no-synthetic` to index only the real catalogue.
- **Evaluation:** the Phase 5 numbers and the data-quality report describe the real 288 records. Do not cite synthetic answers as real catalogue facts.
