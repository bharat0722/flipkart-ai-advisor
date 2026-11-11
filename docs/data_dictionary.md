# Phase 1 data dictionary

`data/processed/electronics.csv` is UTF-8 with a header, one row per selected product, and `\n` line endings. Empty fields represent unknown or unavailable values. Use the raw input hash and the stable `source_uniq_id` to look up source evidence.

| Field | Type | Source and interpretation |
| --- | --- | --- |
| `product_id` | Required string | `P-` plus `source_uniq_id`. Stable across rebuilds of the same source record. |
| `name` | Required string | `product_name` with whitespace and Unicode normalized. |
| `category` | Required string | Controlled label derived from an approved prefix in `product_category_tree`. |
| `brand` | Nullable string | Source brand with Unicode and whitespace normalized. Source case and spelling are preserved. |
| `price` | Nullable decimal, INR | Positive finite `discounted_price` from the crawl. Invalid, blank and zero values are unknown. `retail_price` is available separately. |
| `description` | Required string | Meaningful normalized source prose with known marketing and price boilerplate removed, or the product name plus parsed source specifications. |
| `specifications` | Nullable string | Source facts formatted `Key: value \| Key: value`. Value-only facts are kept. Unparsed nonempty source text is preserved verbatim apart from Unicode and whitespace. |
| `source_ref` | Required string | `kaggle:PromptCloudHQ/flipkart-products/v1#uniq_id=<source_uniq_id>` provenance identifier. |
| `source_uniq_id` | Required string | `uniq_id` from the original CSV. |
| `source_pid` | Nullable string | Flipkart `pid`. Used with `uniq_id` and source URL to detect duplicate identities. |
| `source_url` | Required string | Product URL in the source snapshot. |
| `source_row` | Required integer | One-based CSV data record ordinal, excluding the header. Quoted multiline fields may span more than one physical line. |
| `source_category` | Required string | Complete source category path with normalized whitespace. |
| `crawl_timestamp` | Nullable string | Source timestamp including its timezone, when present. |
| `retail_price` | Nullable decimal, INR | Positive finite source retail price, kept separately from `price`. |
| `description_source` | Required enum | `source_description` or `source_specifications`. If sourced from specifications, avoid repeating the same specification string in Phase 2 documents. |
| `specification_format` | Required enum | `parsed`, `source_text`, or `missing`. Treat `source_text` as unstructured evidence. |

## Cleaning and selection

1. Validate the input header, UTF-8 decoding and CSV record widths. Parse the source's single-element category arrays. Require an exact two-level or three-level path match. The approved mapping is in `CATEGORY_PATHS` in [`src/preprocess.py`](../src/preprocess.py). For example, `Computers >> Laptops` is separate from `Computers >> Laptop Accessories`. Tablet cases, pouches, clothing and other out-of-scope paths are excluded.
2. Require product name, source `uniq_id` and source URL. Normalize whitespace and Unicode. Parse positive prices, including well-formed grouping and INR prefixes. Preserve blank and invalid prices as unknown.
3. Normalize source descriptions and remove observed catalogue boilerplate such as checkout price, shipping and replacement phrases. Require at least 40 characters and five distinct tokens beyond the title and a small list of listing filler words. When source prose is thin, render the product name plus source specifications if at least two distinct named facts parse successfully. Exclude rows when neither form provides sufficient evidence.
4. Rank by known price, parsed specifications, a meaningful original description, description length capped at 1,200 for ranking, then source `uniq_id` and original record number. Retain the highest-ranked record for an overlapping `uniq_id`, nonempty `pid` or product URL. Different source products with similar titles can represent variants.
5. Retain up to 100 items from `Routers & Networking` and up to 300 items overall. Select other approved categories first, then fill from the ranked networking list. Sort the CSV by `product_id`. Report the count if coverage is below 150. A zero-record run fails with an audit report and leaves any prior CSV untouched.

The 15 original columns and observed missing counts are listed in the [data-quality report](data_quality.md). Image arrays, retailer flags and ratings are outside the cleaned contract. Source columns remain available through the original row references.
