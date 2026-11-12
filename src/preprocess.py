"""Build a curated electronics CSV and a data-quality report from Kaggle v1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

import pandas as pd


DATASET = "PromptCloudHQ/flipkart-products"
DATASET_VERSION = 1
TARGET_MIN, TARGET_MAX = 150, 300
NETWORK_LIMIT = 100
REQUIRED_INPUT = {
    "uniq_id", "pid", "product_url", "product_name", "product_category_tree",
    "description", "brand", "discounted_price", "product_specifications",
}
OUTPUT_COLUMNS = [
    "product_id", "name", "category", "brand", "price", "description",
    "specifications", "source_ref", "source_uniq_id", "source_pid", "source_url",
    "source_row", "source_category", "crawl_timestamp", "retail_price",
    "description_source", "specification_format",
]
CATEGORY_PATHS = {
    "Computers >> Network Components >> Routers": "Routers & Networking",
    "Computers >> Laptops": "Laptops",
    "Computers >> Storage >> Pen Drives": "USB Storage",
    "Computers >> Laptop Accessories >> Keyboards": "Keyboards",
    "Computers >> Tablet Accessories >> Keyboards": "Keyboards",
    "Computers >> Laptop Accessories >> Laptop Adapters": "Chargers & Adapters",
    "Computers >> Laptop Accessories >> Adapters": "Chargers & Adapters",
    "Cameras & Accessories >> Camera Accessories >> Battery chargers": "Chargers & Adapters",
    "Mobiles & Accessories >> Tablet Accessories >> Keyboards": "Keyboards",
    "Mobiles & Accessories >> Mobile Accessories >> Headphones": "Headphones & Earphones",
    "Mobiles & Accessories >> Mobile Accessories >> Headphones (With Mic)": "Headphones & Earphones",
    "Mobiles & Accessories >> Mobile Accessories >> Bluetooth Headphones (With Mic)": "Headphones & Earphones",
    "Mobiles & Accessories >> Mobile Accessories >> Speakers": "Speakers",
    "Mobiles & Accessories >> Mobile Accessories >> Chargers": "Chargers & Adapters",
    "Mobiles & Accessories >> Mobile Accessories >> Mobile Chargers": "Chargers & Adapters",
    "Mobiles & Accessories >> Mobile Accessories >> Charging Pads": "Chargers & Adapters",
    "Mobiles & Accessories >> Mobile Accessories >> Power Banks": "Power Banks",
    "Home Entertainment >> Home Audio >> Speakers": "Speakers",
    "Home Entertainment >> MP3 players/Ipods Accessories >> Headphones": "Headphones & Earphones",
    "Home Entertainment >> Video Players & Accessories >> Home Theaters": "Home Theater",
    "Gaming >> Gaming Accessories >> Headphones (With Mic)": "Headphones & Earphones",
    "Gaming >> Gaming Accessories >> Mouse": "Mice",
    "Gaming >> Gaming Accessories >> Gaming Speakers": "Speakers",
}
MISSING = {"", "nan", "null", "none", "n/a", "not available", "no rating available"}
SPEC_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"(?:\s*=>)?')
WORD = re.compile(r"[^\W_]+")
PRICE = re.compile(r"(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})+,\d{3})(?:\.\d+)?")
PRICE_PREFIX = re.compile(r"^(?:₹|INR\b|Rs\.?\s*)\s*", re.IGNORECASE)
PRICE_MENTION = re.compile(r"\bPrice:\s*(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?", re.IGNORECASE)
SHOPPING_BOILERPLATE = re.compile(
    r"\bat best prices with free shipping\s*&\s*cash on delivery\.?"
    r"|\bonly genuine products\.?|\b30 day replacement guarantee\.?"
    r"|\b(?:only\s+)?for Rs\.?\s*[\d,]+(?:\.\d+)?\s+(?:online|from flipkart\.com)\.?"
    r"|\bonline for Rs\.?\s*[\d,]+(?:\.\d+)?"
    r"|,\s*also get\s+.*?\s+(?:specifications|specs)\s*&\s*features\.?"
    r"|\bfree shipping\.?|\bcash on delivery[.!]?", re.IGNORECASE,
)


def normalize_text(value: str) -> str:
    """Normalize Unicode and whitespace while preserving wording and case."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def optional_text(value: str) -> str:
    value = normalize_text(value)
    return "" if value.casefold() in MISSING else value


def normalize_price(value: str) -> float | None:
    value = PRICE_PREFIX.sub("", normalize_text(value))
    if not PRICE.fullmatch(value):
        return None
    price = float(value.replace(",", ""))
    return price if math.isfinite(price) and price > 0 else None


def read_source(path: Path) -> pd.DataFrame:
    """Validate CSV record widths before building the Pandas frame."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            columns = next(reader, [])
            if not columns:
                raise ValueError("Input CSV is empty.")
            if len(columns) != len(set(columns)):
                raise ValueError("Input CSV has duplicate column names.")
            missing = REQUIRED_INPUT.difference(columns)
            if missing:
                raise ValueError(f"Input CSV is missing required columns: {', '.join(sorted(missing))}")
            records = []
            for source_row, row in enumerate(reader, start=1):
                if len(row) != len(columns):
                    raise ValueError(f"CSV data record {source_row} has {len(row)} fields; expected {len(columns)}.")
                records.append(row)
    except (csv.Error, UnicodeDecodeError) as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc
    if not records:
        raise ValueError("Input CSV contains a header but no data records.")
    return pd.DataFrame(records, columns=columns)


def category_parts(value: str) -> tuple[str, ...]:
    try:
        path = json.loads(value)
    except json.JSONDecodeError:
        return ()
    if not isinstance(path, list) or len(path) != 1 or not isinstance(path[0], str):
        return ()
    parts = tuple(normalize_text(part) for part in path[0].split(">>"))
    return parts if all(parts) else ()


def electronics_category(parts: tuple[str, ...]) -> str | None:
    three_levels = CATEGORY_PATHS.get(" >> ".join(parts[:3]))
    return three_levels or CATEGORY_PATHS.get(" >> ".join(parts[:2]))


def normalize_specifications(value: str) -> tuple[str, str, int]:
    """Render source key/value facts. Keep unparsed text available as evidence."""
    value = optional_text(value)
    if not value:
        return "", "missing", 0
    # Replace Ruby-style separators outside quoted strings only.
    converted = SPEC_TOKEN.sub(
        lambda match: match[0][:-2].rstrip() + ":" if match[0].endswith("=>") else match[0],
        value,
    )
    try:
        decoded = json.loads(converted)
    except json.JSONDecodeError:
        return value, "source_text", 0
    facts = decoded.get("product_specification") if isinstance(decoded, dict) else None
    if not isinstance(facts, list):
        return value, "source_text", 0

    entries = []
    keyed = set()
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("value"), str):
            return value, "source_text", 0
        text = optional_text(fact["value"])
        if not text:
            continue
        key = fact.get("key")
        if key is not None and not isinstance(key, str):
            return value, "source_text", 0
        key = optional_text(key or "")
        if key:
            keyed.add(key.casefold())
            entries.append(f"{key}: {text}")
        else:
            entries.append(text)
    if not entries:
        return "", "missing", 0
    return " | ".join(dict.fromkeys(entries)), "parsed", len(keyed)


def normalize_description(value: str, name: str, specs: str, spec_keys: int) -> tuple[str, str]:
    value = PRICE_MENTION.sub("", optional_text(value))
    value = normalize_text(SHOPPING_BOILERPLATE.sub("", value)).strip(" ,.;!")
    extra_words = set(WORD.findall(value.casefold())) - set(WORD.findall(name.casefold()))
    extra_words -= {"at", "buy", "flipkart", "for", "from", "in", "online", "on", "the", "www", "com"}
    if len(value) >= 40 and len(extra_words) >= 5:
        return value, "source_description"
    if spec_keys >= 2:
        return f"{name}. Specifications: {specs}", "source_specifications"
    return "", "missing"


def value_counts(values: pd.Series) -> dict[str, int]:
    return {key: int(count) for key, count in values.value_counts().sort_index().items()}


def curate(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return cleaned records and mutually exclusive row dispositions."""
    paths = raw["product_category_tree"].map(category_parts)
    categories = paths.map(electronics_category)
    in_scope = categories.notna()
    candidates = raw.loc[in_scope].copy()
    candidates["category"] = categories.loc[in_scope]
    candidates["source_category"] = paths.loc[in_scope].map(" >> ".join)
    candidates["source_row"] = candidates.index + 1
    candidates = candidates.rename(columns={
        "uniq_id": "source_uniq_id", "pid": "source_pid",
        "product_url": "source_url", "product_name": "name",
    })
    for column in ("source_uniq_id", "source_pid", "source_url", "name", "brand"):
        candidates[column] = candidates[column].map(optional_text)
    candidates["crawl_timestamp"] = candidates.get("crawl_timestamp", pd.Series("", index=candidates.index)).map(optional_text)
    candidates["retail_price"] = candidates.get("retail_price", pd.Series("", index=candidates.index)).map(normalize_price).astype("Float64")
    candidates["price"] = candidates["discounted_price"].map(normalize_price).astype("Float64")

    exclusions = {"outside_category_scope": int((~in_scope).sum())}
    missing_identity = candidates[["source_uniq_id", "source_url", "name"]].eq("").any(axis=1)
    exclusions["missing_required_identity"] = int(missing_identity.sum())
    candidates = candidates.loc[~missing_identity].copy()
    specs = [normalize_specifications(value) for value in candidates["product_specifications"]]
    candidates["specifications"] = [text for text, _, _ in specs]
    candidates["specification_format"] = [kind for _, kind, _ in specs]
    descriptions = [
        normalize_description(value, name, text, key_count)
        for value, name, (text, _, key_count) in zip(candidates["description"], candidates["name"], specs)
    ]
    candidates["description"] = [text for text, _ in descriptions]
    candidates["description_source"] = [kind for _, kind in descriptions]
    usable = candidates["description"].ne("")
    exclusions["insufficient_description_and_specs"] = int((~usable).sum())
    candidates = candidates.loc[usable].copy()

    # Rank on inspectable evidence quality, with a stable source-ID tie break.
    candidates["has_price"] = candidates["price"].notna()
    candidates["has_parsed_specs"] = candidates["specification_format"].eq("parsed")
    candidates["has_source_description"] = candidates["description_source"].eq("source_description")
    candidates["description_length"] = candidates["description"].map(len).clip(upper=1200)
    candidates = candidates.sort_values(
        ["has_price", "has_parsed_specs", "has_source_description", "description_length", "source_uniq_id", "source_row"],
        ascending=[False, False, False, False, True, True],
    )
    # Deduplicate on any source identity, retaining the highest-ranked record.
    seen_ids, seen_pids, seen_urls = set(), set(), set()
    unique_indices = []
    for row in candidates.itertuples():
        if row.source_uniq_id in seen_ids or row.source_pid in seen_pids or row.source_url in seen_urls:
            continue
        unique_indices.append(row.Index)
        seen_ids.add(row.source_uniq_id)
        if row.source_pid:
            seen_pids.add(row.source_pid)
        seen_urls.add(row.source_url)
    unique = candidates.loc[unique_indices].copy()
    exclusions["duplicate_usable_record"] = len(candidates) - len(unique)

    # Retain a varied catalogue rather than letting one large class dominate it.
    network = unique["category"].eq("Routers & Networking")
    limited_network = unique.loc[network].head(NETWORK_LIMIT)
    others = unique.loc[~network].head(TARGET_MAX)
    selected = pd.concat([others, limited_network.head(TARGET_MAX - len(others))]).copy()
    exclusions["curation_limit"] = len(unique) - len(selected)

    selected["product_id"] = "P-" + selected["source_uniq_id"]
    selected["source_ref"] = (
        f"kaggle:{DATASET}/v{DATASET_VERSION}#uniq_id=" + selected["source_uniq_id"]
    )
    cleaned = selected[OUTPUT_COLUMNS].sort_values("product_id", ignore_index=True)
    report = {
        "dataset": DATASET,
        "dataset_version": DATASET_VERSION,
        "raw_rows": len(raw),
        "raw_columns": raw.columns.tolist(),
        "raw_missing_values": {column: int(raw[column].map(optional_text).eq("").sum()) for column in raw},
        "raw_exact_duplicate_rows_after_first": int(raw.duplicated().sum()),
        "raw_repeated_identity_after_first": {
            col: int(raw.loc[raw[col].ne(""), col].duplicated().sum()) for col in ("uniq_id", "pid", "product_url")
        },
        "raw_top_level_categories": value_counts(paths.map(lambda parts: parts[0] if parts else "[unparseable]")),
        "raw_unparseable_category_paths": int(paths.map(len).eq(0).sum()),
        "raw_nonempty_invalid_prices": {
            col: sum(bool(optional_text(value)) and normalize_price(value) is None for value in raw[col])
            for col in ("discounted_price", "retail_price") if col in raw
        },
        "electronics_candidates": int(in_scope.sum()),
        "candidate_categories": value_counts(categories),
        "unique_usable_candidates": len(unique),
        "usable_categories": value_counts(unique["category"]),
        "excluded_rows_by_reason": exclusions,
        "cleaned_rows": len(cleaned),
        "cleaned_categories": value_counts(cleaned["category"]),
        "cleaned_missing_values": {
            column: int((cleaned[column].isna() | cleaned[column].eq("")).sum()) for column in cleaned
        },
        "cleaned_description_sources": value_counts(cleaned["description_source"]),
        "cleaned_specification_formats": value_counts(cleaned["specification_format"]),
        "target_minimum_met": len(cleaned) >= TARGET_MIN,
    }
    return cleaned, report


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build(input_path: Path, output_path: Path, report_path: Path) -> dict:
    paths = {path.resolve() for path in (input_path, output_path, report_path)}
    if len(paths) != 3:
        raise ValueError("Input, cleaned CSV and report must be different files.")
    cleaned, report = curate(read_source(input_path))
    report["source_sha256"] = sha256(input_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if len(cleaned):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(output_path, index=False, lineterminator="\n", encoding="utf-8")
        report["cleaned_sha256"] = sha256(output_path)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    if cleaned.empty:
        raise ValueError("No usable electronics records. Review the report before continuing.")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/flipkart_com-ecommerce_sample.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/electronics.csv"))
    parser.add_argument("--report", type=Path, default=Path("data/processed/data_quality.json"))
    args = parser.parse_args()
    try:
        report = build(args.input, args.output, args.report)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Preprocessing failed: {exc}\n")
    print(f"Retained {report['cleaned_rows']} of {report['raw_rows']} records from {report['electronics_candidates']} candidates.")
    print(f"Cleaned CSV: {args.output}\nData quality report: {args.report}")
    if not report["target_minimum_met"]:
        print(f"Coverage below {TARGET_MIN} records. Review dataset suitability before Phase 2.")


if __name__ == "__main__":
    main()
