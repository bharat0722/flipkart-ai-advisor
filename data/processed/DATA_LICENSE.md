# Data licence

`electronics.csv` and `product_display.json` are adapted from [Flipkart Products](https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products) (version 1) by PromptCloud, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). These adapted files are shared under the same licence.

Changes: rows were filtered to electronics, appliance and device-accessory categories, deduplicated and normalized by `src/preprocess.py` (see `docs/data_quality.md`). Image links were rewritten to HTTPS and ratings parsed by `scripts/build_display_data.py`.

These files are committed only on the `deploy` branch, for the hosted demo. `main` keeps generated data out of Git.
