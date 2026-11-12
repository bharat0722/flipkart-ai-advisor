# Phase 1 data-quality report

## Source and terms

**Flipkart Products**, PromptCloud (PromptCloudHQ), Kaggle version 1, published 15 September 2017. The original file is `flipkart_com-ecommerce_sample.csv`, 38,114,963 bytes. The Kaggle download and metadata were retrieved on 11 November 2026. [Dataset listing](https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products) · [Official metadata](https://www.kaggle.com/api/v1/datasets/view/promptcloudhq/flipkart-products)

The Kaggle metadata lists **CC BY-SA 4.0**. That license permits sharing and adaptation with attribution, a license link, indication of changes and ShareAlike for distributed adaptations. The raw and cleaned CSVs remain local. If sharing the cleaned data, credit PromptCloud, link the source and license, and describe the filtering, normalization and subset selection. [License terms](https://creativecommons.org/licenses/by-sa/4.0/)

| Fingerprint | SHA-256 |
| --- | --- |
| Raw CSV | `56f8f699c9e847356666c2eab3c3ab1244340f6a98ad08e39ea2199ebe993ad1` |
| Cleaned CSV | `f13d7836d8530b4506500738b418e9fe3f54c3711644f04722036aacbd434bc9` |

## Observed counts

| Stage or exclusion | Rows |
| --- | ---: |
| Raw records, 15 columns | 20,000 |
| Outside approved category scope | 19,611 |
| In-scope candidates before cleaning | 389 |
| Missing name, source ID or URL | 0 |
| Insufficient description and specifications | 1 |
| Duplicate product identity removed among usable candidates | 1 |
| Unique usable candidates | 387 |
| Excluded by the 100-row networking cap | 99 |
| Final cleaned records | **288** |

There were zero exact duplicate raw rows, zero repeated `uniq_id` values, and zero repeated product URLs. Two raw rows repeated a `pid` after its first occurrence. One was in the approved scope and removed, and one was outside scope. All source category paths parsed. The largest source groups were Clothing (6,198), Jewellery (3,531), Footwear (1,227), Mobiles & Accessories (1,099) and Automotive (1,012). The full original distribution is in the generated audit JSON.

| Normalized category | In-scope raw | Cleaned |
| --- | ---: | ---: |
| Chargers & Adapters | 103 | 102 |
| Routers & Networking | 199 | 100 |
| Headphones & Earphones | 52 | 51 |
| Speakers | 14 | 14 |
| Home Theater | 5 | 5 |
| Power Banks | 5 | 5 |
| Keyboards | 4 | 4 |
| USB Storage | 3 | 3 |
| Laptops | 2 | 2 |
| Mice | 2 | 2 |
| **Total** | **389** | **288** |

## Field availability

| Original field | Missing |
| --- | ---: |
| `uniq_id` | 0 |
| `crawl_timestamp` | 0 |
| `product_url` | 0 |
| `product_name` | 0 |
| `product_category_tree` | 0 |
| `pid` | 0 |
| `retail_price` | 78 |
| `discounted_price` | 78 |
| `image` | 3 |
| `is_FK_Advantage_product` | 0 |
| `description` | 2 |
| `product_rating` | 18,151 |
| `overall_rating` | 18,151 |
| `brand` | 5,861 |
| `product_specifications` | 14 |

Missing counts include blank cells and source placeholders such as `No rating available`. The raw price columns had zero invalid nonblank values. In the cleaned CSV, `price` and `retail_price` each have 10 missing values. Every other output column is populated. Of 288 descriptions, 176 use cleaned source prose and 112 use the title plus parsed source facts. There are 287 parsed specification strings and one preserved unstructured string.

## Coverage and constraints

- The raw timestamps span 1 December 2015 to 28 June 2016. Price, warranty and other purchase-related statements should be treated as historical source evidence. Current stock, prices and offers cannot be inferred.
- The dataset meets the 150–300 target for this accessory and networking use case. The approved selection contains two laptops and no phones. Use router, headphone, speaker and charging queries for retrieval validation. If the assignment requires broad laptop or smartphone coverage, M1 and M2 should agree on a revised data source or scope before indexing.
- Source taxonomy can be broad. The networking label includes source-listed extenders, and `Chargers & Adapters` includes adapters and charging accessories. Product facts can be missing, inconsistent, or unverified even when a row passes the quality rules.
- Each of the 288 output rows was checked against the original `uniq_id` and URL at its `source_row` ordinal. The source hash anchors the audit to the inspected file.
